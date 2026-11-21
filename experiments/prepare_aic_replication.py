"""Freeze, acquire and prepare the independent Art Institute of Chicago cohort."""

import argparse
import hashlib
import io
import json
import re
import shutil
import tarfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

import numpy as np
from PIL import Image, ImageCms

from patch_design import MASK_AREAS, MASK_FAMILIES, SIZE, design_mask, native_crop
from prepare_artworks import FUNCTIONAL_OBJECT, MULTIPART, atomic_write, dimensions_ok, in_stratum
from run_followup import NATIVE_SEED, PAIRED_SEED, prepared_dirs
from run_pilot import STRATA, WORKS_PER_STRATUM, read_json, save_png, sha256, write_json


CATALOG_SHA256 = "632d9b8796015c577ca54120a5466a8cd916ad24ff522b2650a9ef29573f7892"
SELECTION_SEED = 20261121
RENDITION_WIDTH = 1686
SMALLER_RENDITION_WIDTHS = (112, 200, 400, 600, 800, 843, 1200)
PROTOCOL = "native-aic-v1"
CANDIDATE_FILE = "candidate-order.json"
MANIFEST_FILE = "artworks.json"
API = "https://api.artic.edu/api/v1/artworks"
IIIF = "https://www.artic.edu/iiif/2"
RIGHTS_POLICY = "https://www.artic.edu/open-access/open-access-images"
IMAGE_ID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
UNKNOWN_ARTIST = re.compile(r"\b(?:anonymous|unidentified|unknown)\b", re.I)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def matches_stratum(row, stratum):
    title = (row.get("title") or "").strip().casefold()
    kind = row.get("artwork_type_title")
    types = {"Painting", "Drawing and Watercolor"} if stratum == "watercolor_paper" else {"Painting"}
    return (
        kind in types and bool(title) and MULTIPART.search(title) is None
        and (stratum != "oil_wood" or FUNCTIONAL_OBJECT.fullmatch(title) is None)
        and in_stratum(row.get("medium_display") or "", [], stratum)
    )


def catalog_size(row):
    thumb = row.get("thumbnail") or {}
    width, height = thumb.get("width"), thumb.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or not dimensions_ok(width, height):
        return None
    return [width, height]


def identifiable_artist(row):
    artist_id = row.get("artist_id")
    artist = (row.get("artist_title") or "").strip()
    return artist_id if isinstance(artist_id, int) and artist_id > 0 and artist and not UNKNOWN_ARTIST.search(artist) else None


def candidate_rank(stratum, numeric_id):
    return hashlib.sha256(f"{SELECTION_SEED}|{stratum}|{numeric_id}".encode()).hexdigest()


def freeze_candidates(snapshot, data_dir, prereg_commit, prereg_utc):
    if sha256(snapshot) != CATALOG_SHA256:
        raise ValueError("AIC metadata export differs from the preregistered snapshot")
    target = data_dir / CANDIDATE_FILE
    if target.exists():
        existing = read_json(target)
        if (existing["prereg_commit"], existing["prereg_utc"]) != (prereg_commit, prereg_utc):
            raise ValueError("Candidate order already belongs to another preregistration")
        return target
    started_at = utc_now()
    if not re.fullmatch(r"[0-9a-f]{40}", prereg_commit) or not prereg_utc.endswith("Z"):
        raise ValueError("Expected complete Git commit SHA and preregistration UTC ending in Z")
    if datetime.fromisoformat(prereg_utc) > datetime.fromisoformat(started_at):
        raise ValueError("Preregistration time is later than candidate ordering")
    eligible = {stratum: [] for stratum in STRATA}
    exclusions = {stratum: Counter() for stratum in STRATA}
    ids = set()
    with tarfile.open(snapshot, "r|bz2") as archive:
        for member in archive:
            if not member.isfile() or "/artworks/" not in f"/{member.name}" or not member.name.endswith(".json"):
                continue
            with archive.extractfile(member) as stream:
                record = json.load(stream)
                row = record.get("data", record)
            numeric_id = row["id"]
            if numeric_id in ids:
                raise ValueError(f"Duplicate AIC catalog object: {numeric_id}")
            ids.add(numeric_id)
            for stratum in STRATA:
                if not matches_stratum(row, stratum):
                    continue
                image_id = row.get("image_id") or ""
                artist_id = identifiable_artist(row)
                source_size = catalog_size(row)
                if row.get("is_public_domain") is not True or not IMAGE_ID.fullmatch(image_id):
                    exclusions[stratum]["public_domain_or_primary_image_missing"] += 1
                elif source_size is None:
                    exclusions[stratum]["catalog_image_size"] += 1
                elif artist_id is None:
                    exclusions[stratum]["no_identifiable_primary_artist"] += 1
                else:
                    eligible[stratum].append({
                        "artwork_id": f"aic-{numeric_id}", "numeric_id": numeric_id,
                        "stratum": stratum, "rank_sha256": candidate_rank(stratum, numeric_id),
                        "artist_id": artist_id, "artist": row["artist_title"], "title": row["title"],
                        "medium": row["medium_display"], "catalog_source_size": source_size,
                        "image_id": image_id, "source_url": f"https://www.artic.edu/artworks/{numeric_id}",
                        "image_url": f"{IIIF}/{image_id}/full/{RENDITION_WIDTH},/0/default.jpg",
                    })
    for stratum, rows in eligible.items():
        rows.sort(key=lambda row: (row["rank_sha256"], row["numeric_id"]))
        artists = len({row["artist_id"] for row in rows})
        print(f"{stratum}: {len(rows)} written candidates, {artists} unique primary artists", flush=True)
        if artists < WORKS_PER_STRATUM:
            raise ValueError(f"Too few identifiable artists for {stratum}: {artists}")
    data_dir.mkdir(parents=True, exist_ok=True)
    write_json(target, {
        "protocol": PROTOCOL, "selection_seed": SELECTION_SEED, "catalog_sha256": CATALOG_SHA256,
        "catalog_object_count": len(ids), "prereg_commit": prereg_commit, "prereg_utc": prereg_utc,
        "ordering_started_utc": started_at, "ordering_completed_utc": utc_now(),
        "catalog_exclusions_after_medium_filter": exclusions, "candidates": eligible,
    })
    return target


class MuseumRedirect(RuntimeError):
    def __init__(self, status, source, target):
        super().__init__(f"AIC returned HTTP {status}: {source} -> {target}")
        self.status = status
        self.target = target


class SurfaceRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        response.close()
        raise MuseumRedirect(code, request.full_url, new_url)


class MuseumRequests:
    """Keep a single request in flight and wait at least one second after completion."""

    def __init__(self):
        self.last_end = 0.0
        self.opener = build_opener(SurfaceRedirect())

    def get(self, url, limit, mime):
        headers = {"User-Agent": "Painting inpainting research/1.0", "Accept": mime}
        if url.startswith(API):
            headers["AIC-User-Agent"] = headers["User-Agent"]
        for attempt in range(3):
            sleep(max(0.0, self.last_end + 1 - monotonic()))
            try:
                with self.opener.open(Request(url, headers=headers), timeout=45) as response:
                    if response.geturl() != url:
                        raise RuntimeError(f"AIC endpoint redirected: {url}")
                    data = response.read(limit + 1)
                    if len(data) > limit or response.headers.get_content_type() != mime:
                        raise ValueError(f"Unexpected AIC response size or format: {url}")
                    return data
            except HTTPError as error:
                if error.code not in {500, 502, 503, 504} or attempt == 2:
                    raise
            except (URLError, TimeoutError):
                if attempt == 2:
                    raise
            finally:
                self.last_end = monotonic()
            sleep(2 ** (attempt + 1))
        raise RuntimeError("AIC request retry exhausted")


def verify_candidate_file(data_dir, expected_sha):
    path = data_dir / CANDIDATE_FILE
    if sha256(path) != expected_sha:
        raise ValueError("Candidate order SHA-256 mismatch")
    plan = read_json(path)
    if (plan["protocol"], plan["catalog_sha256"], plan["selection_seed"]) != (PROTOCOL, CATALOG_SHA256, SELECTION_SEED):
        raise ValueError("Candidate order does not follow the AIC preregistration")
    return plan


def verify_source(data_dir, artwork):
    image = data_dir / "images" / f"{artwork['artwork_id']}.jpg"
    if sha256(image) != artwork["source_image_sha256"]:
        raise ValueError(f"Acquired source SHA-256 mismatch: {image.name}")
    return image


def current_metadata(requests, rows):
    fields = "id,is_public_domain,image_id,artist_id,title,medium_display,artwork_type_title,reference_number"
    url = API + "?" + urlencode({"ids": ",".join(str(row["numeric_id"]) for row in rows), "fields": fields})
    payload = requests.get(url, 8_000_000, "application/json")
    result = json.loads(payload)
    if result["config"]["iiif_url"] != IIIF:
        raise ValueError("AIC API points to a different IIIF service")
    proof = {"metadata_checked_utc": utc_now(), "metadata_request_url": url,
             "metadata_response_sha256": hashlib.sha256(payload).hexdigest()}
    return {row["id"]: row for row in result["data"]}, proof


def read_candidate_image(requests, row):
    try:
        payload = requests.get(row["image_url"], 32_000_000, "image/jpeg")
    except HTTPError as error:
        if error.code in {404, 410}:
            return None, None, f"image_http_{error.code}"
        raise  # Authorization or throttling is a service failure, not a reserve exclusion.
    except ValueError:
        return None, None, "invalid_image_response"
    try:
        with Image.open(io.BytesIO(payload)) as image:
            if image.format != "JPEG":
                return None, None, "not_jpeg"
            width, height = image.size
            if not dimensions_ok(width, height) or width > RENDITION_WIDTH:
                return None, None, "image_dimensions"
            image.verify()
    except (OSError, ValueError, Image.DecompressionBombError):
        return None, None, "image_decode"
    return payload, [width, height], None


def acquire(data_dir, candidate_sha):
    plan = verify_candidate_file(data_dir, candidate_sha)
    manifest_file = data_dir / MANIFEST_FILE
    if manifest_file.exists():
        manifest = read_json(manifest_file)
        if manifest["candidate_order_sha256"] != candidate_sha:
            raise ValueError("Existing AIC acquisition belongs to a different order")
        for artwork in manifest["artworks"]:
            verify_source(data_dir, artwork)
        return manifest_file

    lock = data_dir / "acquire.in-progress"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(utc_now() + "\n")
    try:
        return acquire_sequentially(data_dir, candidate_sha, plan, manifest_file)
    finally:
        lock.unlink()


def acquire_sequentially(data_dir, candidate_sha, plan, manifest_file):
    image_dir = data_dir / "images"
    image_dir.mkdir(exist_ok=True)
    journal_file = data_dir / "acquisition-journal.json"
    if journal_file.exists():
        journal = read_json(journal_file)
        if journal["candidate_order_sha256"] != candidate_sha:
            raise ValueError("AIC acquisition journal uses a different candidate order")
    else:
        journal = {"candidate_order_sha256": candidate_sha, "started_utc": utc_now(), "decisions": {}}
        write_json(journal_file, journal)
    if datetime.fromisoformat(journal["started_utc"]) < datetime.fromisoformat(plan["ordering_completed_utc"]):
        raise ValueError("AIC acquisition must follow the candidate freeze")
    decisions = journal["decisions"]
    requests = MuseumRequests()
    images, source_hashes, used_ids = set(), set(), set()
    artworks = []

    for group_index, stratum in enumerate(STRATA):
        candidates = plan["candidates"][stratum]
        artists = set()
        current = {}
        proof = None
        for index, row in enumerate(candidates):
            if len(artists) == WORKS_PER_STRATUM:
                break
            artwork_id = row["artwork_id"]
            if artwork_id not in decisions:
                reason = None
                if row["artist_id"] in artists:
                    reason = "artist_already_selected_in_stratum"
                elif artwork_id in used_ids or row["image_id"] in images:
                    reason = "object_or_image_id_already_selected"
                decision = {"stratum": stratum, "rank_sha256": row["rank_sha256"], "decided_utc": utc_now()}
                if reason is None:
                    if row["numeric_id"] not in current:
                        current, proof = current_metadata(requests, candidates[index:index + 15])
                    live = current.get(row["numeric_id"])
                    decision.update({**proof, "object_metadata": live})
                    if not live or live.get("is_public_domain") is not True or live.get("image_id") != row["image_id"]:
                        reason = "current_public_domain_or_image_id_mismatch"
                    elif not matches_stratum(live, stratum):
                        reason = "current_medium_or_object_type_mismatch"
                    else:
                        try:
                            payload, dimensions, reason = read_candidate_image(requests, row)
                        except MuseumRedirect as redirect:
                            documented_fallbacks = {
                                f"{IIIF}/{row['image_id']}/full/{width},/0/default.jpg"
                                for width in SMALLER_RENDITION_WIDTHS
                            }
                            if unquote(redirect.target) not in documented_fallbacks:
                                raise
                            decision["image_redirect"] = {"status": redirect.status, "target": redirect.target}
                            reason = "image_1686_unavailable_documented_fallback"
                if reason is None:
                    digest = hashlib.sha256(payload).hexdigest()
                    if digest in source_hashes:
                        reason = "duplicate_image_sha256"
                    else:
                        destination = image_dir / f"{artwork_id}.jpg"
                        atomic_write(destination, payload)
                        crop_seed = NATIVE_SEED + 1000 + group_index * 100 + len(artists)
                        try:
                            native_crop(destination, crop_seed)
                        except (OSError, ValueError, ImageCms.PyCMSError):
                            reason = "image_crop_decode"
                            destination.unlink()
                if reason is None:
                    decision["artwork"] = {
                        **row, "rights": "CC0", "rights_policy": RIGHTS_POLICY,
                        "metadata_checked_utc": proof["metadata_checked_utc"],
                        "object_api_url": f"{API}/{row['numeric_id']}",
                        "source_image_sha256": digest, "image_path": f"images/{artwork_id}.jpg",
                        "source_size": dimensions, "source_rendition": "aic_iiif_1686_jpeg",
                    }
                else:
                    decision["reason"] = reason
                decision["decided_utc"] = utc_now()
                decisions[artwork_id] = decision
                write_json(journal_file, journal)

            artwork = decisions[artwork_id].get("artwork")
            if artwork is None:
                continue
            verify_source(data_dir, artwork)
            artists.add(artwork["artist_id"])
            used_ids.add(artwork_id)
            images.add(artwork["image_id"])
            source_hashes.add(artwork["source_image_sha256"])
            artworks.append(artwork)
            print(f"{stratum}: {len(artists)}/{WORKS_PER_STRATUM} accepted ({artwork_id})", flush=True)
        if len(artists) != WORKS_PER_STRATUM:
            raise ValueError(f"AIC stratum yielded only {len(artists)} distinct artists: {stratum}")

    write_json(manifest_file, {
        "protocol": PROTOCOL, "catalog_sha256": CATALOG_SHA256, "candidate_order_sha256": candidate_sha,
        "prereg_commit": plan["prereg_commit"], "prereg_utc": plan["prereg_utc"],
        "acquisition_started_utc": journal["started_utc"], "acquisition_completed_utc": utc_now(),
        "acquisition_journal_sha256": sha256(journal_file), "artworks": artworks,
        "exclusion_counts": Counter(d["reason"] for d in decisions.values() if "reason" in d),
    })
    return manifest_file


def prepare(data_dir, run_dir, candidate_sha):
    verify_candidate_file(data_dir, candidate_sha)
    manifest_file = data_dir / MANIFEST_FILE
    manifest_sha = sha256(manifest_file)
    manifest = read_json(manifest_file)
    if manifest["candidate_order_sha256"] != candidate_sha or manifest["protocol"] != PROTOCOL:
        raise ValueError("AIC image manifest does not belong to this candidate order")
    if not run_dir.resolve().is_absolute() or run_dir.resolve().is_relative_to(data_dir.resolve()):
        raise ValueError("Prepared case directory must be separate from its source data")
    artworks = manifest["artworks"]
    by_stratum = {stratum: [row for row in artworks if row["stratum"] == stratum] for stratum in STRATA}
    n_expected = len(STRATA) * WORKS_PER_STRATUM
    if len(artworks) != n_expected or any(
        len({row[field] for row in artworks}) != n_expected
        for field in ("artwork_id", "image_id", "source_image_sha256")
    ):
        raise ValueError("AIC manifest must contain independent artworks and source images")
    for stratum, cohort in by_stratum.items():
        if len(cohort) != WORKS_PER_STRATUM or len({row["artist_id"] for row in cohort}) != WORKS_PER_STRATUM:
            raise ValueError(f"AIC stratum has incorrect artwork or artist count: {stratum}")
        if any(row["rights"] != "CC0" for row in cohort):
            raise ValueError(f"AIC stratum contains a source missing CC0: {stratum}")
    sources = {row["artwork_id"]: verify_source(data_dir, row) for row in artworks}

    lock = run_dir / "prepared.json"
    if lock.exists():
        previous = read_json(lock)
        if previous["protocol"] != PROTOCOL or previous["manifest_sha256"] != manifest_sha:
            raise ValueError("Prepared directory already belongs to another dataset")
        for case in previous["cases"]:
            for file, digest in (
                (run_dir / "originals" / f"{case['case_id']}.png", case["crop_sha256"]),
                (run_dir / "masks" / case["mask_file"], case["mask_sha256"]),
            ):
                if sha256(file) != digest:
                    raise ValueError(f"Prepared artifact changed: {file}")
        return lock

    prepared_dirs(run_dir)
    recorded_masks = {}
    for slot in range(WORKS_PER_STRATUM):
        for family_index, family in enumerate(MASK_FAMILIES):
            for area_index, area in enumerate(MASK_AREAS):
                mask_seed = NATIVE_SEED + slot * 100 + family_index * 10 + area_index
                mask = design_mask(family, area, mask_seed)
                filename = f"mask_{slot:02}_{family}_{int(100 * area):02}.png"
                path = run_dir / "masks" / filename
                save_png(path, mask.astype(np.uint8) * 255)
                recorded_masks[slot, family, area] = {
                    "mask_seed": mask_seed, "mask_pixels": int(mask.sum()),
                    "mask_file": filename, "mask_sha256": sha256(path),
                }

    cases = []
    for group_index, (stratum, cohort) in enumerate(by_stratum.items()):
        for slot, row in enumerate(cohort):
            crop_seed = NATIVE_SEED + 1000 + group_index * 100 + slot
            pixels, (left, top) = native_crop(sources[row["artwork_id"]], crop_seed)
            if pixels.shape != (SIZE, SIZE, 3):
                raise ValueError(f"Invalid RGB crop for {row['artwork_id']}")
            original = None
            for family in MASK_FAMILIES:
                for area in MASK_AREAS:
                    case_id = f"{stratum}_{slot:02}_{family}_{int(100 * area):02}"
                    target = run_dir / "originals" / f"{case_id}.png"
                    if original is None:
                        save_png(target, pixels)
                        original = target
                        crop_sha = sha256(target)
                    else:
                        shutil.copyfile(original, target)
                    cases.append({
                        **row, **recorded_masks[slot, family, area], "case_id": case_id,
                        "family": family, "target_area": area, "crop_seed": crop_seed,
                        "crop_left_top": [left, top], "crop_sha256": crop_sha,
                        "source_url_image": row["image_url"],
                    })
    write_json(lock, {
        "protocol": PROTOCOL, "seed": PAIRED_SEED, "manifest_sha256": manifest_sha,
        "candidate_order_sha256": candidate_sha, "catalog_sha256": CATALOG_SHA256,
        "collection": "Art Institute of Chicago", "source_rendition": "aic_iiif_1686_jpeg",
        "prereg_commit": manifest["prereg_commit"], "prereg_utc": manifest["prereg_utc"],
        "artwork_order_by_stratum": {s: [row["artwork_id"] for row in cohort] for s, cohort in by_stratum.items()},
        "artwork_manifest_completed_utc": manifest["acquisition_completed_utc"],
        "prepared_utc": utc_now(), "cases": cases,
    })
    print(f"Prepared {len(cases)} conditions across {len(artworks)} AIC artworks", flush=True)
    return lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    stages = parser.add_subparsers(dest="stage", required=True)
    freeze_parser = stages.add_parser("freeze")
    freeze_parser.add_argument("--snapshot", type=Path, required=True)
    freeze_parser.add_argument("--data-dir", type=Path, required=True)
    freeze_parser.add_argument("--prereg-commit", required=True)
    freeze_parser.add_argument("--prereg-utc", required=True)
    for stage in ("acquire", "prepare"):
        subparser = stages.add_parser(stage)
        subparser.add_argument("--data-dir", type=Path, required=True)
        subparser.add_argument("--candidate-sha256", required=True)
        if stage == "prepare":
            subparser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "freeze":
        path = freeze_candidates(args.snapshot, args.data_dir, args.prereg_commit, args.prereg_utc)
    elif args.stage == "acquire":
        path = acquire(args.data_dir, args.candidate_sha256)
    else:
        path = prepare(args.data_dir, args.run_dir, args.candidate_sha256)
    print(f"{path}\nSHA-256 {sha256(path)}", flush=True)


if __name__ == "__main__":
    main()
