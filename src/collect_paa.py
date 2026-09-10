"""Ambil PAA awal SerpApi dengan batas batch, snapshot, dan checkpoint per request."""

import argparse
import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
QUESTION_FIELDS = [
    "paa_id", "question_key", "topic_id", "research_domain", "source_type",
    "source_text", "retrieval_query", "question", "position", "result_type",
    "retrieved_at", "search_id", "request_id", "batch_id", "raw_path",
    "source_url", "review_status",
]
SEARCH_FIELDS = [
    "topic_id", "research_domain", "retrieval_query", "request_id", "status",
    "question_count", "retrieved_at", "search_id", "raw_path", "error_type",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def replace_with_retry(temp, path):
    """Retry file replacement only; retain the temp file if Windows keeps it locked."""
    for attempt in range(7):
        try:
            temp.replace(path)
            return
        except PermissionError:
            if attempt == 6:
                raise PermissionError(
                    f"Tidak dapat mengganti {path.name} setelah 7 percobaan. "
                    f"Tutup aplikasi yang membuka file tersebut. Data terbaru tetap "
                    f"tersimpan di {temp}. Tidak ada retry API; pulihkan file sementara "
                    "sebelum melanjutkan jika checkpoint JSON belum memuat respons terbaru."
                ) from None
            time.sleep(0.1 * (2 ** attempt))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    replace_with_retry(temp, path)


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    replace_with_retry(temp, path)


def api_key():
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    env_path = ROOT / ".env"
    if not key and env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            name, separator, value = line.partition("=")
            if separator and name.strip() == "SERPAPI_API_KEY":
                key = value.strip().strip("\"'")
                break
    if not key:
        raise ValueError("Isi SERPAPI_API_KEY di .env atau environment.")
    return key


def fetch(endpoint, params, key):
    # Never log the URL: authentication uses a query parameter.
    url = "https://serpapi.com/" + endpoint + "?" + urlencode({**params, "api_key": key})
    try:
        with urlopen(url, timeout=45) as response:
            data = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"SerpApi HTTP {error.code}; batch dihentikan.") from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError("Jaringan SerpApi gagal; tidak ada retry otomatis.") from None
    except (ValueError, UnicodeError):
        raise RuntimeError("Respons SerpApi bukan JSON yang valid.") from None
    if not isinstance(data, dict):
        raise RuntimeError("Struktur respons SerpApi tidak valid.")
    return data


def quota(key):
    data = fetch("account.json", {}, key)
    remaining = data.get("total_searches_left")
    if data.get("error") or not isinstance(remaining, int):
        raise RuntimeError("Kuota tidak dapat diverifikasi; pencarian tidak dijalankan.")
    # Account response includes secrets and email; only persist usage fields.
    return {"checked_at": now(), **{name: data.get(name) for name in (
        "total_searches_left", "plan_searches_left", "searches_per_month", "this_month_usage"
    )}}


def sanitize(data, key):
    if isinstance(data, dict):
        return {name: ("[REDACTED]" if name.lower() == "api_key" else sanitize(value, key))
                for name, value in data.items()}
    if isinstance(data, list):
        return [sanitize(value, key) for value in data]
    if isinstance(data, str):
        return re.sub(r"(?i)(api_key=)[^&\s\"<>]+", r"\1[REDACTED]", data.replace(key, "[REDACTED]"))
    return data


def plan(config, source_path):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", config["batch_id"]):
        raise ValueError("batch_id hanya boleh berisi huruf, angka, _ atau -.")
    if not isinstance(config["max_searches"], int) or config["max_searches"] < 1:
        raise ValueError("max_searches harus bilangan positif.")
    if not isinstance(config["quota_reserve"], int) or config["quota_reserve"] < 0:
        raise ValueError("quota_reserve tidak valid.")
    params = config["parameters"]
    if params.get("engine") != "google" or set(params) - {
        "engine", "google_domain", "gl", "hl", "location", "device"
    }:
        raise ValueError("Hanya Google Search awal dan parameter lokasi/bahasa yang didukung.")
    with source_path.open(encoding="utf-8-sig", newline="") as handle:
        sources = {(r["research_domain"], r["source_text"]): r for r in csv.DictReader(handle)}
    jobs = []
    for domain, texts in config["topics"].items():
        for text in texts:
            row = sources.get((domain, text))
            if not row or row["status"] != "needs_paa":
                raise ValueError(f"Topik tidak ditemukan dalam needs_paa: {domain} / {text}")
            parameters = {**params, "q": text}
            request_id = digest(json.dumps(parameters, sort_keys=True, ensure_ascii=False))
            jobs.append({"topic_id": row["topic_id"], "research_domain": domain,
                         "source_text": text, "source_ids": row["source_ids"],
                         "parameters": parameters, "request_id": request_id})
    if not jobs or len(jobs) > config["max_searches"]:
        raise ValueError("Jumlah topik kosong atau melampaui max_searches batch.")
    if len({j["request_id"] for j in jobs}) != len(jobs):
        raise ValueError("Query identik dalam batch; hapus duplikasinya.")
    return {"config": config, "jobs": jobs}


def extract_questions(payload, job, record, raw_path):
    items = payload.get("related_questions", [])
    if not isinstance(items, list):
        raise ValueError("related_questions harus berupa list.")
    rows = []
    for position, item in enumerate(items, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("question"), str):
            continue
        question = item["question"]
        if not question.strip():
            continue
        rows.append({
            "paa_id": "paa_" + digest(job["request_id"] + str(position) + question),
            "question_key": digest(" ".join(question.casefold().split())),
            "topic_id": job["topic_id"], "research_domain": job["research_domain"],
            "source_type": "people_also_ask", "source_text": job["source_text"],
            "retrieval_query": job["parameters"]["q"], "question": question,
            "position": position, "result_type": item.get("type", ""),
            "retrieved_at": record["retrieved_at"], "search_id": record.get("search_id", ""),
            "request_id": job["request_id"], "batch_id": record["batch_id"],
            "raw_path": raw_path, "source_url": item.get("link", ""),
            "review_status": "unreviewed",
        })
    return rows


def export(manifest, data_root):
    questions, searches = [], []
    for job in manifest["jobs"]:
        path = data_root / "raw/paa/requests" / (job["request_id"] + ".json")
        record = read_json(path) if path.exists() else {"status": "not_requested"}
        raw_path = str(path.relative_to(data_root.parent).as_posix()) if path.exists() else ""
        extracted = []
        if record["status"] in {"success", "no_paa"}:
            extracted = extract_questions(record["response"], job, record, raw_path)
        questions.extend(extracted)
        searches.append({
            "topic_id": job["topic_id"], "research_domain": job["research_domain"],
            "retrieval_query": job["parameters"]["q"], "request_id": job["request_id"],
            "status": record["status"], "question_count": len(extracted),
            "retrieved_at": record.get("retrieved_at", ""), "search_id": record.get("search_id", ""),
            "raw_path": raw_path, "error_type": record.get("error_type", ""),
        })
    output = data_root / "interim/paa" / manifest["config"]["batch_id"]
    write_csv(output / "questions.csv", questions, QUESTION_FIELDS)
    write_csv(output / "searches.csv", searches, SEARCH_FIELDS)
    return questions, searches


def collect(manifest, data_root, key, fetcher=fetch, quota_reader=quota):
    config = manifest["config"]
    batch_dir = data_root / "raw/paa/batches" / config["batch_id"]
    batch_dir.mkdir(parents=True, exist_ok=True)
    # Prevent concurrent runs from spending quota twice for the same batch.
    lock_path = batch_dir / "running.lock"
    with lock_path.open("x") as lock:
        lock.write(str(os.getpid()))
    try:
        snapshot = batch_dir / "manifest.json"
        if snapshot.exists() and read_json(snapshot) != manifest:
            raise ValueError("Batch sudah dibekukan. Gunakan batch_id baru untuk daftar/config baru.")
        jobs = [job for job in manifest["jobs"] if not
                (data_root / "raw/paa/requests" / (job["request_id"] + ".json")).exists()]
        if not jobs:
            return export(manifest, data_root)
        before = quota_reader(key)
        if before["total_searches_left"] < len(jobs) + config["quota_reserve"]:
            raise RuntimeError("Sisa kuota tidak cukup untuk batch dan cadangan; tidak ada pencarian dikirim.")
        write_json(snapshot, manifest)
        write_json(batch_dir / ("quota_before_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"), before)
        for job in jobs:
            path = data_root / "raw/paa/requests" / (job["request_id"] + ".json")
            record = {"batch_id": config["batch_id"], "request_id": job["request_id"],
                      "parameters": job["parameters"], "retrieved_at": now(), "status": "started"}
            # Reserve before sending. An interrupted/failed request is never retried automatically.
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False)
            try:
                payload = sanitize(fetcher("search.json", job["parameters"], key), key)
                record["response"] = payload
                record["search_id"] = payload.get("search_metadata", {}).get("id", "")
                if payload.get("error") or payload.get("search_metadata", {}).get("status") != "Success":
                    raise RuntimeError("SerpApi melaporkan respons tidak berhasil.")
                found = extract_questions(payload, job, record, str(path))
                record["status"] = "success" if found else "no_paa"
            except (RuntimeError, ValueError, TypeError, AttributeError) as error:
                record["status"] = "error"
                record["error_type"] = type(error).__name__
                write_json(path, record)
                export(manifest, data_root)
                raise RuntimeError("Satu request gagal; batch dihentikan. Periksa log sebelum melanjutkan.") from None
            write_json(path, record)
            export(manifest, data_root)
            print(f"{job['research_domain']} | {job['source_text']}: {record['status']} ({len(found)} PAA)", flush=True)
        try:
            write_json(batch_dir / "quota_after.json", quota_reader(key))
        except RuntimeError:
            print("Data tersimpan; kuota akhir belum dapat diperiksa.")
        return export(manifest, data_root)
    finally:
        lock_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/paa_pilot.json")
    parser.add_argument("--run", action="store_true", help="Kirim request; tanpa flag ini hanya pratinjau lokal.")
    args = parser.parse_args()
    manifest = plan(read_json(args.config), ROOT / "data/interim/review/needs_paa.csv")
    print("Batch:", manifest["config"]["batch_id"], "| batas:", manifest["config"]["max_searches"])
    for job in manifest["jobs"]:
        cached = (ROOT / "data/raw/paa/requests" / (job["request_id"] + ".json")).exists()
        print(job["research_domain"], "|", job["source_text"], "|", "tersimpan, lewati" if cached else "belum diambil")
    if args.run:
        questions, searches = collect(manifest, ROOT / "data", api_key())
        print(f"Tersimpan: {len(searches)} catatan pencarian, {len(questions)} kemunculan pertanyaan PAA.")
    else:
        print("Pratinjau saja: tidak ada request atau kuota yang digunakan. Tambahkan --run untuk mengambil data.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, FileExistsError) as error:
        print(str(error))
        raise SystemExit(1)
