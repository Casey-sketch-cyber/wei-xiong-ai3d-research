from __future__ import annotations

import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode

import httpx


HERE = Path(__file__).resolve().parent
API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}

QUERIES = [
    "all:visibility AND all:transition AND all:3D",
    "all:visibility AND all:sequence AND all:layout",
    "all:visibility AND all:trajectory AND all:layout",
    "all:progressive AND all:reveal AND all:3D",
    "all:reveal AND all:order AND all:scene",
    "all:narrative AND all:visibility AND all:layout",
    "all:serial AND all:vision AND all:design",
    "all:visitor AND all:path AND all:visibility",
    "all:visitor AND all:route AND all:visibility",
    "all:museum AND all:exhibit AND all:visibility",
    "all:exhibition AND all:path AND all:visibility",
    "all:occlusion AND all:staging AND all:optimization",
    "all:fixed AND all:route AND all:visibility AND all:repair",
    "all:minimal AND all:edit AND all:visibility AND all:scene",
    "all:layout AND all:repair AND all:occlusion",
]


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def fetch(client: httpx.Client, query: str, sort_by: str) -> list[dict[str, object]]:
    params = {
        "search_query": query,
        "start": "0",
        "max_results": "50",
        "sortBy": sort_by,
        "sortOrder": "descending" if sort_by == "submittedDate" else "ascending",
    }
    response = client.get(
        API,
        params=urlencode(params),
        headers={"User-Agent": "M05RevealNoveltyScan/1.0 (mailto:xiongwei@guit.edu.cn)"},
    )
    response.raise_for_status()
    root = ET.fromstring(response.text)
    rows: list[dict[str, object]] = []
    for entry in root.findall("a:entry", NS):
        raw_id = clean(entry.findtext("a:id", namespaces=NS))
        arxiv_id = re.sub(r"v\d+$", "", raw_id.rsplit("/abs/", 1)[-1])
        rows.append(
            {
                "arxiv_id": arxiv_id,
                "title": clean(entry.findtext("a:title", namespaces=NS)),
                "abstract": clean(entry.findtext("a:summary", namespaces=NS)),
                "published": clean(entry.findtext("a:published", namespaces=NS)),
                "authors": [
                    clean(node.findtext("a:name", namespaces=NS))
                    for node in entry.findall("a:author", NS)
                ],
                "url": raw_id,
                "query": query,
                "sort_by": sort_by,
            }
        )
    return rows


def main() -> None:
    client = httpx.Client(timeout=90.0, follow_redirects=True)
    records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for index, query in enumerate(QUERIES, start=1):
        print(f"[{index:02d}/{len(QUERIES)}] {query}", flush=True)
        for sort_by in ("relevance", "submittedDate"):
            try:
                rows = fetch(client, query, sort_by)
                records.extend(rows)
                print(f"  {sort_by}: {len(rows)}", flush=True)
            except Exception as exc:
                failures.append(
                    {"query": query, "sort_by": sort_by, "error": repr(exc)}
                )
                print(f"  {sort_by}: FAILED {exc!r}", flush=True)
            time.sleep(3.1)
    client.close()

    by_id: dict[str, dict[str, object]] = {}
    for record in records:
        key = str(record["arxiv_id"])
        if key not in by_id:
            item = dict(record)
            item["queries"] = [item.pop("query")]
            item["sort_modes"] = [item.pop("sort_by")]
            by_id[key] = item
            continue
        if record["query"] not in by_id[key]["queries"]:
            by_id[key]["queries"].append(record["query"])
        if record["sort_by"] not in by_id[key]["sort_modes"]:
            by_id[key]["sort_modes"].append(record["sort_by"])

    deduped = sorted(by_id.values(), key=lambda row: str(row["published"]), reverse=True)
    (HERE / "arxiv_reveal_raw.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (HERE / "arxiv_reveal_deduplicated.json").write_text(
        json.dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (HERE / "arxiv_reveal_failures.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "query_count": len(QUERIES),
                "raw_count": len(records),
                "deduplicated_count": len(deduped),
                "failure_count": len(failures),
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
