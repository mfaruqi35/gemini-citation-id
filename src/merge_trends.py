"""Gabungkan enam CSV Trends tanpa mengubah sumber atau membuang duplikasi."""

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "interim" / "trends_sources.csv"
INPUT_COLUMNS = ["query", "search interest", "increase percent"]
OUTPUT_COLUMNS = [
    "source_id", "source_type", "domain", "source_list", "source_file",
    "source_row", "source_text", "search_interest", "increase_percent",
]


def merge_trends() -> None:
    """Validasi semua masukan sebelum menulis hasil gabungan berformat UTF-8."""
    merged = []
    counts = []
    for domain in ("kesehatan", "keuangan", "teknologi"):
        for source_list in ("top", "rising"):
            source_path = DATA_DIR / f"{source_list}_{domain}.csv"
            with source_path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames != INPUT_COLUMNS:
                    raise ValueError(
                        f"Kolom tidak sesuai pada {source_path.name}: {reader.fieldnames}"
                    )
                count = 0
                for source_row, row in enumerate(reader, start=1):
                    if None in row or any(value is None for value in row.values()):
                        raise ValueError(
                            f"Jumlah kolom tidak sesuai: {source_path.name}, baris data {source_row}"
                        )
                    if not row["query"].strip():
                        raise ValueError(
                            f"Query kosong: {source_path.name}, baris data {source_row}"
                        )
                    merged.append({
                        "source_id": f"trends_{domain}_{source_list}_{source_row:04d}",
                        "source_type": "google_trends",
                        "domain": domain,
                        "source_list": source_list,
                        "source_file": source_path.relative_to(PROJECT_ROOT).as_posix(),
                        "source_row": source_row,
                        "source_text": row["query"],
                        "search_interest": row["search interest"],
                        "increase_percent": row["increase percent"],
                    })
                    count += 1
                if count == 0:
                    raise ValueError(f"Tidak ada data dalam {source_path.name}")
                counts.append((source_path.name, count))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(merged)

    for filename, count in counts:
        print(f"{filename}: {count} baris")
    print(f"Total: {len(merged)} baris")
    print(f"Teks unik (persis): {len({row['source_text'] for row in merged})}")
    print(f"Hasil: {OUTPUT_PATH}")


if __name__ == "__main__":
    merge_trends()
