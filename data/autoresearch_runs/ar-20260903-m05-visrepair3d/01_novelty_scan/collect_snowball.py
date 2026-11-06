from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx


HERE = Path(__file__).resolve().parent
API = "https://api.openalex.org"
MAILTO = "xiongwei@guit.edu.cn"

SEEDS = [
    {"label": "Make It Home", "doi": "10.1145/1964921.1964981"},
    {"label": "Automated staging", "doi": "10.1145/3274247.3274500"},
    {"label": "Interactive staging and shooting", "doi": "10.1145/3424636.3426893"},
    {"label": "Visibility transition planning", "doi": "10.1145/1599470.1599478"},
    {"label": "Artwork placement", "doi": "10.1145/3631134"},
    {"label": "DT-MUSE", "doi": "10.1145/3802133.3802238"},
    {"label": "Curatorial intent navigation", "doi": "10.31436/japcm.v16i1.1071"},
    {"label": "Perception-driven path optimization", "doi": "10.1016/j.buildenv.2026.114544"},
    {"label": "Roomer", "openalex": "W7172557125"},
    {"label": "ScenePilot", "openalex": "W7204958718"},
]


def reconstruct_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        words.extend((position, word) for position in positions)
    return " ".join(word for _, word in sorted(words))


def compact(work: dict[str, Any], relation: str, seed: str) -> dict[str, Any]:
    primary = work.get("primary_location") or {}
    return {
        "openalex_id": str(work.get("id") or "").rsplit("/", 1)[-1],
        "doi": work.get("doi"),
        "title": work.get("display_name"),
        "year": work.get("publication_year"),
        "type": work.get("type"),
        "venue": (primary.get("source") or {}).get("display_name"),
        "landing_page_url": primary.get("landing_page_url"),
        "cited_by_count": work.get("cited_by_count"),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "relation": relation,
        "seed": seed,
    }


def get_json(client: httpx.Client, url: str) -> dict[str, Any]:
    response = client.get(url)
    response.raise_for_status()
    return response.json()


def resolve_seed(client: httpx.Client, seed: dict[str, str]) -> dict[str, Any] | None:
    if "openalex" in seed:
        return get_json(client, f"{API}/works/{seed['openalex']}?mailto={MAILTO}")
    if "doi" in seed:
        value = quote(seed["doi"], safe="")
        data = get_json(
            client,
            f"{API}/works?filter=doi:{value}&per-page=1&mailto={MAILTO}",
        )
    else:
        raise ValueError(f"unresolvable seed: {seed}")
    results = data.get("results") or []
    return results[0] if results else None


def get_works_by_ids(client: httpx.Client, ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset in range(0, len(ids), 50):
        chunk = "|".join(value.rsplit("/", 1)[-1] for value in ids[offset : offset + 50])
        data = get_json(
            client,
            f"{API}/works?filter=openalex_id:{chunk}&per-page=50&mailto={MAILTO}",
        )
        rows.extend(data.get("results") or [])
        time.sleep(0.2)
    return rows


def main() -> None:
    client = httpx.Client(
        timeout=90.0,
        follow_redirects=True,
        headers={"User-Agent": f"M05NoveltySnowball/1.0 (mailto:{MAILTO})"},
    )
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    seed_records: list[dict[str, Any]] = []

    for index, seed in enumerate(SEEDS, start=1):
        label = seed["label"]
        print(f"[{index:02d}/{len(SEEDS)}] {label}", flush=True)
        try:
            work = resolve_seed(client, seed)
            if not work:
                raise RuntimeError("seed not resolved")
            seed_records.append(compact(work, "seed", label))

            reference_ids = work.get("referenced_works") or []
            related_ids = work.get("related_works") or []
            for related in get_works_by_ids(client, reference_ids + related_ids):
                relation = (
                    "reference" if related.get("id") in reference_ids else "related"
                )
                rows.append(compact(related, relation, label))

            openalex_id = str(work["id"]).rsplit("/", 1)[-1]
            citations = get_json(
                client,
                f"{API}/works?filter=cites:{openalex_id}&sort=cited_by_count:desc&per-page=100&mailto={MAILTO}",
            )
            rows.extend(
                compact(citing, "citation", label)
                for citing in citations.get("results") or []
            )
            print(
                f"  refs={len(reference_ids)} related={len(related_ids)} "
                f"citing={len(citations.get('results') or [])}",
                flush=True,
            )
        except Exception as exc:
            failures.append({"seed": label, "error": repr(exc)})
            print(f"  FAILED {exc!r}", flush=True)
        time.sleep(0.5)
    client.close()

    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["openalex_id"] or row["doi"] or row["title"]
        if key not in by_id:
            item = dict(row)
            item["relations"] = [item.pop("relation")]
            item["seeds"] = [item.pop("seed")]
            by_id[key] = item
            continue
        if row["relation"] not in by_id[key]["relations"]:
            by_id[key]["relations"].append(row["relation"])
        if row["seed"] not in by_id[key]["seeds"]:
            by_id[key]["seeds"].append(row["seed"])

    deduped = sorted(
        by_id.values(),
        key=lambda row: (int(row.get("year") or 0), int(row.get("cited_by_count") or 0)),
        reverse=True,
    )
    (HERE / "snowball_seeds.json").write_text(
        json.dumps(seed_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (HERE / "snowball_candidates.json").write_text(
        json.dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (HERE / "snowball_failures.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "seed_count": len(SEEDS),
                "resolved_seed_count": len(seed_records),
                "deduplicated_candidate_count": len(deduped),
                "failure_count": len(failures),
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
