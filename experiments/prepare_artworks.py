"""Download a stratified CC0 pilot sample from the Cleveland Museum of Art."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from PIL import Image


API = "https://openaccess-api.clevelandart.org/api/artworks/"
API_FIELDS = ",".join((
    "id", "accession_number", "share_license_status", "title", "technique",
    "support_materials", "type", "images", "creators", "url",
    "conservation_statement", "state_of_the_work", "description",
))
STRATA = {
    "oil_canvas": (("oil on canvas", "Painting"),),
    "oil_wood": (("oil on wood", "Painting"), ("oil on panel", "Painting")),
    "watercolor_paper": (("watercolor", "Drawing"), ("watercolor", "Painting")),
    "ink_paper": (("ink on paper", "Painting"),),
}
FIELDS = (
    "artwork_id", "stratum", "image_path", "title", "artist", "medium",
    "source_url", "image_url", "rights",
)
OIL_WOOD = re.compile(
    r"oil on (?:panel|wood(?:en)?(?: panel)?|"
    r"(?:oak|poplar|walnut|pine|mahogany|cedar|linden|limewood|spruce|beech|maple|"
    r"chestnut|birch|fruitwood)(?: panel)?)"
)
INK_PAPER = re.compile(r"ink on (?:[a-z-]+ )*paper")
WATERCOLOR_PAPER = re.compile(
    r"(?:transparent )?watercolou?r(?: (?:and|over|with) (?:traces of )?(?:black )?"
    r"(?:graphite|pencil)(?: underdrawing| and scraping)?)?"
    r"|(?:black )?(?:graphite|pencil) and (?:transparent )?watercolou?r"
)
COMPOSITE_SUPPORT = re.compile(r"\b(?:mounted|laid down|joined|board|cardboard|canvas|silk|vellum|parchment|fabric)\b")
MULTIPART = re.compile(
    r"\b(?:fragment(?:ary)?|diptych|triptych|polyptych|pair of|set of|folding screen|"
    r"calligraphy|verso|double-sided)\b"
)
FUNCTIONAL_OBJECT = re.compile(
    r"(?:[a-z-]+ ){0,3}(?:doors?|cabinet|cupboard|chest|shutters?|desk|wardrobe|drawer|lid)(?: panels?)?"
)
VISIBLE_DAMAGE = re.compile(
    r"\b(?:damaged|losses of (?:paint|pigment)|paint loss|pigment loss|"
    r"missing (?:paint|pigment)|severe abrasion|severely abraded|water damage)\b"
)
MIN_SIDE = 640
MAX_ASPECT_RATIO = 2.8
MAX_IMAGE_BYTES = 20_000_000


@dataclass(frozen=True)
class Candidate:
    accession: str
    object_id: int
    title: str
    artist_id: int
    artist: str
    medium: str
    source_url: str
    images: tuple[tuple[str, str], ...]


def fetch(url: str, limit: int) -> bytes:
    request = Request(url, headers={"User-Agent": "CMA Open Access pilot research/1.0"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=25) as response:
                data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError(f"Response exceeds {limit:,} bytes")
            return data
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        sleep(2 ** attempt)
    raise RuntimeError("Unreachable request retry state")


def dimensions_ok(width: int, height: int) -> bool:
    shortest, longest = sorted((width, height))
    return shortest >= MIN_SIDE and longest <= shortest * MAX_ASPECT_RATIO


def in_stratum(medium: str, supports: list[dict], stratum: str) -> bool:
    value = " ".join(medium.casefold().split())
    if stratum == "oil_canvas":
        return value == "oil on canvas"
    if stratum == "oil_wood":
        return OIL_WOOD.fullmatch(value) is not None
    if stratum == "watercolor_paper":
        paint, _, support = value.partition(" on ")
        support_notes = " ".join(item.get("description") or "" for item in supports).casefold()
        return (
            WATERCOLOR_PAPER.fullmatch(paint) is not None
            and re.search(r"\bpaper\b", support or support_notes) is not None
            and COMPOSITE_SUPPORT.search(f"{support} {support_notes}") is None
        )
    if MULTIPART.search(value):
        return False
    # The catalog can prefix the painting medium with its mount or format.
    value = re.split(r"[;,]", value)[-1].strip()
    return INK_PAPER.fullmatch(value) is not None


def get_candidate(record: dict, stratum: str, artwork_type: str) -> Candidate | None:
    if record.get("share_license_status") != "CC0" or record.get("type") != artwork_type:
        return None
    medium = record.get("technique") or ""
    title = record.get("title") or ""
    supports = record.get("support_materials") or []
    if not title or MULTIPART.search(title.casefold()) or not in_stratum(medium, supports, stratum):
        return None
    if stratum == "oil_wood" and FUNCTIONAL_OBJECT.fullmatch(title.strip().casefold()):
        return None
    condition = " ".join(
        str(record.get(key) or "")
        for key in ("state_of_the_work", "conservation_statement", "description")
    )
    if VISIBLE_DAMAGE.search(condition.casefold()):
        return None
    artists = [
        artist for artist in record.get("creators") or []
        if artist.get("id") and artist.get("description") and artist.get("role") in {"artist", "painter"}
    ]
    if len(artists) != 1 or re.search(r"\b(?:unknown|unidentified|anonymous)\b", artists[0]["description"], re.I):
        return None
    accession = record.get("accession_number")
    object_id = record.get("id")
    source_url = record.get("url") or ""
    page = urlsplit(source_url)
    if not accession or not object_id or page.scheme != "https" or page.hostname not in {
        "clevelandart.org", "www.clevelandart.org",
    }:
        return None
    images = []
    for rendition in ("web", "print"):
        metadata = (record.get("images") or {}).get(rendition) or {}
        location = urlsplit(metadata.get("url") or "")
        if location.scheme != "https" or location.hostname != "openaccess-cdn.clevelandart.org":
            continue
        try:
            width, height = int(metadata["width"]), int(metadata["height"])
        except (KeyError, TypeError, ValueError):
            continue
        if dimensions_ok(width, height):
            images.append((rendition, metadata["url"]))
    if not images:
        return None
    if stratum == "watercolor_paper" and "paper" not in medium.casefold():
        support_label = ", ".join(item["description"] for item in supports if item.get("description"))
        medium = f"{medium}; support: {support_label}"
    artist = artists[0]
    return Candidate(accession, object_id, title, artist["id"], artist["description"], medium, source_url, tuple(images))


def get_candidates(stratum: str, count: int, exclude_ids: set[str]) -> list[Candidate]:
    candidates = {}
    page_size = 150
    for medium, artwork_type in STRATA[stratum]:
        for offset in range(0, 600, page_size):
            params = {"cc0": 1, "has_image": 1, "type": artwork_type, "medium": medium,
                      "limit": page_size, "skip": offset, "fields": API_FIELDS}
            try:
                result = json.loads(fetch(API + "?" + urlencode(params), 10_000_000))
            except (OSError, ValueError) as error:
                print(f"Catalog query failed for {stratum} ({medium}, offset {offset}): {error}", file=sys.stderr)
                break
            for record in result["data"]:
                if f"cma-{record.get('id')}" in exclude_ids:
                    continue
                candidate = get_candidate(record, stratum, artwork_type)
                if candidate is not None:
                    candidates[candidate.accession] = candidate
            if offset + page_size >= result["info"]["total"] or len({c.artist_id for c in candidates.values()}) >= 3 * count:
                break
    return list(candidates.values())


def atomic_write(path: Path, data: bytes) -> None:
    temporary = NamedTemporaryFile(dir=path.parent, delete=False)
    staging = Path(temporary.name)
    try:
        with temporary:
            temporary.write(data)
        staging.replace(path)
    finally:
        staging.unlink(missing_ok=True)


def download_candidate(candidate: Candidate, output: Path, stratum: str) -> tuple[dict, str] | None:
    object_key = f"cma-{candidate.object_id}"
    for rendition, image_url in candidate.images:
        relative = Path("images") / f"{object_key}-{rendition}.jpg"
        target = output / relative
        try:
            content = target.read_bytes() if target.is_file() else fetch(image_url, MAX_IMAGE_BYTES)
            with Image.open(io.BytesIO(content)) as image:
                if image.format != "JPEG" or not dimensions_ok(*image.size):
                    raise ValueError("expected a JPEG suitable for the 512-pixel center crop")
                image.load()
            if not target.is_file():
                atomic_write(target, content)
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            print(f"Skipping {object_key} {rendition}: {error}", file=sys.stderr)
            continue
        row = {
            "artwork_id": object_key, "stratum": stratum, "image_path": relative.as_posix(),
            "title": candidate.title, "artist": candidate.artist, "medium": candidate.medium,
            "source_url": candidate.source_url, "image_url": image_url, "rights": "CC0",
        }
        return row, hashlib.sha256(content).hexdigest()
    return None


def prepare(output: Path, count: int, seed: int, exclude_ids: set[str]) -> list[dict]:
    (output / "images").mkdir(parents=True, exist_ok=True)
    rows = []
    seen_accessions = set()
    seen_images = set()
    with ThreadPoolExecutor(max_workers=4) as pool:
        candidate_jobs = {stratum: pool.submit(get_candidates, stratum, count, exclude_ids) for stratum in STRATA}
        for stratum, job in candidate_jobs.items():
            candidates = job.result()
            candidates.sort(key=lambda a: hashlib.sha256(f"{seed}:{a.object_id}".encode()).digest())
            seen_artists = set()
            selected = 0
            while candidates and selected < count:
                batch = []
                busy_artists = set()
                for candidate in candidates:
                    if candidate.accession in seen_accessions or candidate.artist_id in seen_artists | busy_artists:
                        continue
                    batch.append(candidate)
                    busy_artists.add(candidate.artist_id)
                    if len(batch) == min(4, count - selected):
                        break
                if not batch:
                    break
                downloads = [pool.submit(download_candidate, candidate, output, stratum) for candidate in batch]
                for candidate, download in zip(batch, downloads, strict=True):
                    candidates.remove(candidate)
                    item = download.result()
                    if item is None or item[1] in seen_images:
                        continue
                    row, digest = item
                    rows.append(row)
                    seen_artists.add(candidate.artist_id)
                    seen_accessions.add(candidate.accession)
                    seen_images.add(digest)
                    selected += 1
            print(f"{stratum}: {selected}/{count}", flush=True)
            if selected != count:
                raise RuntimeError(f"Insufficient verified candidates for {stratum}: {selected}/{count}.")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Directory for artworks.csv and images/")
    parser.add_argument("--per-stratum", default=15, type=int, help="Artwork count per stratum (default: 15)")
    parser.add_argument("--seed", default=20261118, type=int, help="Deterministic catalog selection seed")
    parser.add_argument("--exclude-id", action="append", default=[], metavar="CMA-ID",
                        help="Exclude a catalog ID such as cma-123456 before sampling (repeatable)")
    args = parser.parse_args()
    if args.per_stratum < 1:
        parser.error("--per-stratum must be positive")
    exclude_ids = set(args.exclude_id)
    if any(re.fullmatch(r"cma-\d+", object_id) is None for object_id in exclude_ids):
        parser.error("--exclude-id values must have the form cma-123456")
    output = args.output.resolve()
    try:
        rows = prepare(output, args.per_stratum, args.seed, exclude_ids)
        manifest = io.StringIO(newline="")
        writer = csv.DictWriter(manifest, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
        path = output / "artworks.csv"
        atomic_write(path, manifest.getvalue().encode("utf-8"))
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        parser.exit(1, f"Artwork preparation failed: {error}\n")
    print(path)


if __name__ == "__main__":
    main()
