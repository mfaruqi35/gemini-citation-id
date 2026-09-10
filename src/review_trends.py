"""Penyimpanan dan validasi tinjauan manual sumber Trends (library standar)."""

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


STATUSES = {"unreviewed", "ready_for_synthesis", "needs_paa", "needs_review", "excluded"}
DOMAINS = {"kesehatan", "keuangan", "teknologi"}
FIELDS = [
    "topic_id", "source_text", "source_ids", "source_files", "source_domains",
    "source_lists", "occurrences", "research_domain", "status", "reason",
    "language", "intent", "reviewed_at",
]
EDITABLE = {"research_domain", "status", "reason", "language", "intent"}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def load_review(source_path, review_path):
    sources = read_csv(source_path)
    if not sources:
        raise ValueError("CSV sumber kosong.")
    required = {"source_id", "source_text", "source_file", "domain", "source_list"}
    if not required.issubset(sources[0]):
        raise ValueError("Kolom sumber tidak lengkap. Jalankan merge_trends.py dahulu.")
    ids = [row["source_id"] for row in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("source_id pada CSV gabungan tidak unik.")
    groups = {}
    for source in sources:
        text = source["source_text"]
        if not text.strip():
            raise ValueError("Teks sumber kosong.")
        groups.setdefault(text, []).append(source)

    previous = read_csv(review_path) if Path(review_path).exists() else []
    if previous and not set(FIELDS).issubset(previous[0]):
        raise ValueError("Kolom tabel keputusan tidak lengkap.")
    saved = {row["topic_id"]: row for row in previous}
    if len(saved) != len(previous):
        raise ValueError("topic_id pada tabel keputusan tidak unik.")
    reviews = []
    for text, members in groups.items():
        topic_id = "topic_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        domains = sorted({row["domain"] for row in members})
        row = {
            "topic_id": topic_id,
            "source_text": text,
            "occurrences": str(len(members)),
            "research_domain": domains[0] if len(domains) == 1 else "",
            "status": "unreviewed", "reason": "", "language": "",
            "intent": "", "reviewed_at": "",
        }
        for output, original in (
            ("source_ids", "source_id"), ("source_files", "source_file"),
            ("source_domains", "domain"), ("source_lists", "source_list"),
        ):
            row[output] = json.dumps(sorted({item[original] for item in members}), ensure_ascii=False)
        old = saved.get(topic_id)
        if old:
            # Jangan menerapkan keputusan lama pada sumber yang berubah diam-diam.
            provenance = ("source_text", "source_ids", "source_files", "source_domains", "source_lists")
            if any(old[key] != row[key] for key in provenance):
                raise ValueError(f"Sumber {topic_id} berubah. Arsipkan tinjauan lama sebelum meninjau batch baru.")
            for key in EDITABLE | {"reviewed_at"}:
                row[key] = old[key]
        reviews.append(row)
    if set(saved) - {row["topic_id"] for row in reviews}:
        raise ValueError("Ada topik tersimpan yang hilang dari sumber. Arsipkan tinjauan lama terlebih dahulu.")
    validate_reviews(reviews)
    return reviews


def validate_reviews(rows):
    for row in rows:
        status = row["status"]
        if status not in STATUSES:
            raise ValueError(f"Status tidak dikenal: {status}")
        if row["research_domain"] and row["research_domain"] not in DOMAINS:
            raise ValueError(f"Domain tidak dikenal: {row['research_domain']}")
        if status != "unreviewed" and not row["reason"].strip():
            raise ValueError(f"Alasan wajib diisi untuk {row['topic_id']}.")
        if status in {"ready_for_synthesis", "needs_paa"}:
            if not row["research_domain"] or not row["language"].strip():
                raise ValueError("Sumber siap sintesis/PAA harus memiliki domain dan bahasa.")
        if status == "ready_for_synthesis" and not row["intent"].strip():
            raise ValueError("Sumber siap sintesis harus memiliki intent yang jelas.")


def apply_decisions(rows, decisions):
    updated = [dict(row) for row in rows]
    by_id = {row["topic_id"]: row for row in updated}
    for topic_id, changes in decisions.items():
        if topic_id not in by_id:
            raise ValueError(f"ID tidak ditemukan: {topic_id}")
        if set(changes) - EDITABLE:
            raise ValueError(f"Kolom yang boleh diedit: {sorted(EDITABLE)}")
        if any(not isinstance(value, str) for value in changes.values()):
            raise ValueError("Semua nilai keputusan harus berupa teks.")
        row = by_id[topic_id]
        if any(row[key] != value for key, value in changes.items()):
            row.update(changes)
            row["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    validate_reviews(updated)
    return updated


def save_review(rows, review_path, output_dir):
    validate_reviews(rows)
    write_csv(review_path, rows)
    output_dir = Path(output_dir)
    for status in sorted(STATUSES):
        write_csv(output_dir / f"{status}.csv", [row for row in rows if row["status"] == status])
    return dict(Counter(row["status"] for row in rows))
