"""Pilot A/B Google Search lewat REST generateContent; default tanpa jaringan."""

import argparse
import csv
import ipaddress
import json
import os
import re
import socket
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from collect_paa import digest, now, read_json, sanitize, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
TRIAL_FIELDS = [
    "trial_id", "paa_id", "topic_id", "domain", "question", "condition", "repetition",
    "status", "started_at", "completed_at", "model_version", "finish_reason",
    "has_text", "has_grounding_metadata", "n_search_queries", "n_web_sources",
    "n_cited_sources", "has_web_citation", "n_resolved_sources", "n_url_errors",
    "prompt_tokens", "output_tokens", "thought_tokens", "total_tokens", "error_code", "raw_path",
]
SOURCE_FIELDS = [
    "trial_id", "paa_id", "domain", "condition", "chunk_index", "title", "source_url", "raw_url",
    "is_cited", "resolved_url", "resolution_status", "http_status", "resolved_at",
]


def load_key():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    path = ROOT / ".env"
    if not key and path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "GEMINI_API_KEY":
                key = value.strip().strip("\"'")
                break
    if not key:
        raise ValueError("GEMINI_API_KEY belum tersedia pada environment atau .env.")
    return key


def build_plan(config):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", config["experiment_id"]):
        raise ValueError("experiment_id tidak valid.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", config["model"]):
        raise ValueError("Gunakan ID model tanpa prefix models/.")
    for field in ("max_calls", "repetitions"):
        if type(config[field]) is not int or config[field] < 1:
            raise ValueError(f"{field} harus bilangan bulat positif.")
    if config["generation_config"].get("candidateCount") != 1:
        raise ValueError("Pilot memakai satu kandidat per percobaan.")
    if not config["search_instruction"].strip():
        raise ValueError("Instruksi pencarian B tidak boleh kosong.")
    source_path = (ROOT / config["paa_csv"]).resolve()
    source_path.relative_to(ROOT)
    with source_path.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    by_id = {r["paa_id"]: r for r in source_rows}
    if len(by_id) != len(source_rows):
        raise ValueError("ID PAA tidak unik.")
    ids = config["paa_ids"]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Daftar ID kosong atau duplikat.")
    selected = []
    for paa_id in ids:
        if paa_id not in by_id:
            raise ValueError(f"ID PAA tidak tersedia: {paa_id}")
        row = by_id[paa_id]
        selected.append({k: row[k] for k in (
            "paa_id", "topic_id", "research_domain", "question", "retrieval_query", "raw_path"
        )})
    if len({" ".join(r["question"].casefold().split()) for r in selected}) != len(selected):
        raise ValueError("Pertanyaan terpilih berulang.")
    jobs = []
    # Alternate A/B then B/A to reduce a systematic time/order difference.
    for repetition in range(1, config["repetitions"] + 1):
        for index, row in enumerate(selected):
            order = ("A", "B") if (index + repetition) % 2 else ("B", "A")
            for condition in order:
                instruction = config["common_instruction"]
                if condition == "B":
                    instruction += "\n\n" + config["search_instruction"]
                request = {
                    "contents": [{"role": "user", "parts": [{"text": row["question"]}]}],
                    "tools": [{"google_search": {}}],
                    "systemInstruction": {"parts": [{"text": instruction}]},
                    "generationConfig": config["generation_config"],
                }
                trial_id = "trial_" + digest(json.dumps({
                    "experiment": config["experiment_id"], "model": config["model"],
                    "request": request, "repetition": repetition,
                    "condition": condition, "paa_id": row["paa_id"],
                }, ensure_ascii=False, sort_keys=True))
                jobs.append({"trial_id": trial_id, "source": row, "condition": condition,
                             "repetition": repetition, "request": request})
    if len(jobs) > config["max_calls"]:
        raise ValueError("Rencana melampaui max_calls; tidak ada request dikirim.")
    return {"config": config, "selected_sources": selected, "jobs": jobs,
            "api": "v1beta/models:generateContent", "implementation_version": 1}


class GenerationError(RuntimeError):
    def __init__(self, code):
        self.code = str(code)
        super().__init__(f"Pemanggilan Gemini gagal ({self.code}); detail rahasia tidak dicetak.")


def generate(model, request, key):
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + quote(model, safe="") + ":generateContent"
    req = Request(url, data=json.dumps(request).encode("utf-8"), method="POST",
                  headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urlopen(req, timeout=55) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise GenerationError(error.code) from None
    except (URLError, TimeoutError, OSError):
        raise GenerationError("network_or_timeout") from None
    except (ValueError, UnicodeError):
        raise GenerationError("invalid_json") from None
    if not isinstance(payload, dict) or payload.get("error"):
        raise GenerationError("invalid_response")
    return sanitize(payload, key)


def validate_public_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL tidak diperbolehkan.")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Alamat URL bukan web publik.")


class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def is_grounding_redirect(url):
    parsed = urlsplit(url)
    return parsed.hostname == "vertexaisearch.cloud.google.com" and "grounding-api-redirect" in parsed.path


def resolve_url(url):
    result = {"raw_url": url, "resolved_url": "", "resolution_status": "failed",
              "http_status": "", "resolved_at": now()}
    opener = build_opener(PublicRedirect())
    try:
        validate_public_url(url)
        # GET fallback also handles sources which reject HEAD; never download the body.
        for method in ("HEAD", "GET"):
            request = Request(url, method=method, headers={"User-Agent": "Mozilla/5.0"})
            try:
                with opener.open(request, timeout=10) as response:
                    final, status = response.geturl(), response.status
            except HTTPError as error:
                final, status = error.geturl(), error.code
                error.close()
                if method == "HEAD":
                    continue
            result["http_status"] = status
            if not is_grounding_redirect(final):
                result.update(resolved_url=final, resolution_status=(
                    "resolved" if 200 <= status < 400 else "destination_http_error"))
                return result
        result["resolution_status"] = "unresolved_redirect"
    except (URLError, TimeoutError, OSError, ValueError):
        result["resolution_status"] = "network_or_url_error"
    return result


def grounding(payload):
    candidates = payload.get("candidates") or []
    candidate = candidates[0] if candidates else {}
    metadata = candidate.get("groundingMetadata") or {}
    chunks = metadata.get("groundingChunks") or []
    web = {i: c["web"] for i, c in enumerate(chunks) if isinstance(c.get("web"), dict) and c["web"].get("uri")}
    cited = {i for support in metadata.get("groundingSupports") or []
             for i in support.get("groundingChunkIndices") or [] if isinstance(i, int) and i in web}
    text = "".join(p.get("text", "") for p in candidate.get("content", {}).get("parts", []) if not p.get("thought"))
    return candidate, metadata, web, cited, text


def finish_resolution(path, record, resolver):
    _, _, web, _, _ = grounding(record["response"])
    resolutions = record.setdefault("url_resolutions", {})
    for item in web.values():
        url = item["uri"]
        if url not in resolutions:
            resolutions[url] = resolver(url)
            write_json(path, record)
    record.update(status="completed", completed_at=now())
    write_json(path, record)


def export_results(manifest, data_root):
    experiment = manifest["config"]["experiment_id"]
    raw_dir = data_root / "raw/gemini_pilot" / experiment
    trials, sources = [], []
    for job in manifest["jobs"]:
        path = raw_dir / "trials" / (job["trial_id"] + ".json")
        rec = read_json(path) if path.exists() else {"status": "not_requested"}
        payload = rec.get("response", {})
        candidate, meta, web, cited, text = grounding(payload)
        resolutions = rec.get("url_resolutions", {})
        usage = payload.get("usageMetadata") or {}
        row = {k: "" for k in TRIAL_FIELDS}
        row.update(trial_id=job["trial_id"], paa_id=job["source"]["paa_id"],
                   topic_id=job["source"]["topic_id"], domain=job["source"]["research_domain"],
                   question=job["source"]["question"], condition=job["condition"], repetition=job["repetition"],
                   status=rec["status"], started_at=rec.get("started_at", ""),
                   completed_at=rec.get("completed_at", ""), model_version=payload.get("modelVersion", ""),
                   finish_reason=candidate.get("finishReason", ""), has_text=bool(text),
                   has_grounding_metadata=bool(meta), n_search_queries=len(meta.get("webSearchQueries") or []),
                   n_web_sources=len(web), n_cited_sources=len(cited), has_web_citation=bool(cited),
                   n_resolved_sources=sum(bool(r.get("resolved_url")) for r in resolutions.values()),
                   n_url_errors=sum(r.get("resolution_status") != "resolved" for r in resolutions.values()),
                   prompt_tokens=usage.get("promptTokenCount", ""), output_tokens=usage.get("candidatesTokenCount", ""),
                   thought_tokens=usage.get("thoughtsTokenCount", ""), total_tokens=usage.get("totalTokenCount", ""),
                   error_code=rec.get("error_code", ""), raw_path=path.relative_to(data_root.parent).as_posix() if path.exists() else "")
        trials.append(row)
        for i, source in web.items():
            resolution = resolutions.get(source["uri"], {})
            sources.append({"trial_id": job["trial_id"], "paa_id": job["source"]["paa_id"],
                            "domain": row["domain"], "condition": job["condition"], "chunk_index": i,
                            "title": source.get("title", ""), "source_url": destination_url(resolution),
                            "raw_url": source["uri"], "is_cited": i in cited,
                            **{k: resolution.get(k, "") for k in ("resolved_url", "resolution_status", "http_status", "resolved_at")}})
    output = data_root / "interim/gemini_pilot" / experiment
    write_csv(output / "trials.csv", trials, TRIAL_FIELDS)
    write_csv(output / "sources.csv", sources, SOURCE_FIELDS)
    # Reader-facing export has no Google redirect URLs, even when resolution failed.
    link_fields = ["trial_id", "paa_id", "domain", "condition", "chunk_index", "title", "source_url",
                   "is_cited", "resolution_status", "http_status"]
    write_csv(output / "source_links.csv", [{k: r[k] for k in link_fields} for r in sources], link_fields)
    summary = []
    for condition in ("A", "B"):
        group = [r for r in trials if r["condition"] == condition]
        completed = [r for r in group if r["status"] == "completed"]
        cited = sum(r["has_web_citation"] for r in completed)
        summary.append({"condition": condition, "scheduled": len(group), "completed": len(completed),
                        "errors": sum(r["status"] == "error" for r in group),
                        "with_web_sources": sum(r["n_web_sources"] > 0 for r in completed),
                        "with_citations": cited, "citation_rate_completed": cited / len(completed) if completed else ""})
    write_csv(output / "summary.csv", summary, list(summary[0]))
    write_pilot_report(output, manifest, summary, trials, sources)
    return trials


def destination_url(resolution):
    url = resolution.get("resolved_url", "")
    if urlsplit(url).scheme not in {"http", "https"} or is_grounding_redirect(url):
        return ""
    return url


def write_pilot_report(output, manifest, summary, trials, sources):
    lines = ["# Hasil pilot Gemini Grounding", "", f"Model: `{manifest['config']['model']}`.",
             "Query PAA asli; dua kondisi dengan instruksi bahasa yang sama, dua pengulangan per query.", "",
             "| Kondisi | Selesai | Dengan sitasi web | Proporsi |", "|---|---:|---:|---:|"]
    for row in summary:
        rate = f"{100 * row['citation_rate_completed']:.1f}%" if row['completed'] else "Belum tersedia"
        lines.append(f"| {row['condition']} | {row['completed']} | {row['with_citations']} | {rate} |")
    lines += ["", "A: Google Search aktif. B: Google Search aktif dengan tambahan instruksi pencarian.",
              "Hasil bersifat eksploratif untuk sembilan query; bukan jaminan keberhasilan pada seluruh query.", "",
              "## Kelengkapan URL", "",
              f"- Kemunculan sumber: {len(sources)} (bukan jumlah artikel unik).",
              f"- URL tujuan tersedia: {sum(bool(r['source_url']) for r in sources)}.",
              f"- URL tujuan belum tersedia: {sum(not r['source_url'] for r in sources)}.",
              f"- Destinasi dengan HTTP error: {sum(r['resolution_status'] == 'destination_http_error' for r in sources)}.",
              "", "URL tujuan yang diketahui tidak menjamin isi artikel berhasil diambil. Video, toko, dan jenis halaman lain masih perlu diseleksi.",
              "", "## Hasil per query", "", "| Query | Domain | A: sitasi/selesai | B: sitasi/selesai |", "|---|---|---:|---:|"]
    for source in manifest["selected_sources"]:
        values = []
        for condition in ("A", "B"):
            subset = [r for r in trials if r['paa_id'] == source['paa_id'] and r['condition'] == condition and r['status'] == 'completed']
            values.append(f"{sum(r['has_web_citation'] for r in subset)}/{len(subset)}")
        question = source['question'].replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {question} | {source['research_domain']} | {values[0]} | {values[1]} |")
    lines += ["", "## Tautan tujuan unik", "", "Daftar berikut memakai URL hasil resolusi, tanpa fallback ke tautan pengalihan Google.", ""]
    urls = sorted({r['source_url'] for r in sources if r['source_url']})
    for url in urls:
        safe = url.replace('<', '%3C').replace('>', '%3E').replace('\n', '%0A').replace('\r', '%0D')
        lines.append(f"- [{urlsplit(url).hostname}](<{safe}>)")
    (output / "report.md").write_text('\n'.join(lines) + '\n', encoding='utf-8')


def resolve_missing(manifest, data_root, resolver=resolve_url):
    """Retry URL resolution only; never generates a model response."""
    raw = data_root / "raw/gemini_pilot" / manifest["config"]["experiment_id"]
    if not (raw / "manifest.json").exists() or read_json(raw / "manifest.json") != manifest:
        raise ValueError("Manifest tersimpan tidak tersedia atau berbeda.")
    lock = raw / "running.lock"
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    attempts = 0
    try:
        for job in manifest['jobs']:
            path = raw / 'trials' / (job['trial_id'] + '.json')
            if not path.exists():
                continue
            record = read_json(path)
            if 'response' not in record:
                continue
            _, _, web, _, _ = grounding(record['response'])
            resolutions = record.setdefault('url_resolutions', {})
            for url in dict.fromkeys(item['uri'] for item in web.values()):
                previous = resolutions.get(url, {})
                if destination_url(previous):
                    continue
                updated = resolver(url)
                record.setdefault('resolution_history', []).append({
                    'raw_url': url, 'previous': previous, 'retried_at': now()})
                resolutions[url] = updated
                write_json(path, record)
                attempts += 1
                print(f"Resolusi {attempts}: {updated['resolution_status']}", flush=True)
        export_results(manifest, data_root)
        print(f"Percobaan resolusi URL: {attempts}; pemanggilan Gemini: 0.")
    finally:
        lock.unlink(missing_ok=True)


def run_pilot(manifest, data_root, key, max_new_calls=None, generator=generate, resolver=resolve_url):
    raw = data_root / "raw/gemini_pilot" / manifest["config"]["experiment_id"]
    raw.mkdir(parents=True, exist_ok=True)
    lock = raw / "running.lock"
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    try:
        frozen = raw / "manifest.json"
        if frozen.exists() and read_json(frozen) != manifest:
            raise ValueError("Konfigurasi/sumber batch berubah. Gunakan experiment_id baru.")
        write_json(frozen, manifest)
        sent = 0
        for job in manifest["jobs"]:
            path = raw / "trials" / (job["trial_id"] + ".json")
            if path.exists():
                rec = read_json(path)
                if rec["status"] == "response_saved":
                    finish_resolution(path, rec, resolver)
                continue
            if max_new_calls is not None and sent >= max_new_calls:
                break
            rec = {"status": "started", "started_at": now(), "job": job,
                   "requested_model": manifest["config"]["model"]}
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as handle:
                json.dump(rec, handle, ensure_ascii=False)
            sent += 1
            try:
                rec["response"] = generator(manifest["config"]["model"], job["request"], key)
            except GenerationError as error:
                rec.update(status="error", error_code=error.code, completed_at=now())
                write_json(path, rec)
                export_results(manifest, data_root)
                raise
            rec.update(status="response_saved", response_received_at=now(), url_resolutions={})
            write_json(path, rec)  # Save before redirect links can expire or resolution fails.
            finish_resolution(path, rec, resolver)
            export_results(manifest, data_root)
            print(f"{job['condition']} / ulangan {job['repetition']} / {job['source']['question']}: tersimpan", flush=True)
        result = export_results(manifest, data_root)
        print("Pemanggilan Gemini baru:", sent)
        return result
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/gemini_grounding_pilot.json")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--max-new-calls", type=int, help="Batasi panggilan baru pada eksekusi ini, misalnya 2.")
    parser.add_argument("--export-only", action="store_true", help="Ekspor ulang dari file lokal tanpa jaringan.")
    parser.add_argument("--resolve-missing-only", action="store_true", help="Coba ulang URL tanpa tujuan; tidak memanggil Gemini.")
    args = parser.parse_args()
    if sum([args.run, args.export_only, args.resolve_missing_only]) > 1:
        parser.error("Pilih salah satu: --run, --export-only, --resolve-missing-only.")
    if args.max_new_calls is not None and args.max_new_calls < 1:
        parser.error("--max-new-calls harus positif.")
    manifest = build_plan(read_json(args.config))
    raw = ROOT / "data/raw/gemini_pilot" / manifest["config"]["experiment_id"]
    if (raw / "manifest.json").exists() and read_json(raw / "manifest.json") != manifest:
        raise ValueError("Manifest berbeda; gunakan experiment_id baru.")
    print("Model:", manifest["config"]["model"])
    print("Pertanyaan:", len(manifest["selected_sources"]), "| percobaan terjadwal:", len(manifest["jobs"]))
    for row in manifest["selected_sources"]:
        print(row["research_domain"], "|", row["question"])
    counts = Counter(read_json(raw / "trials" / (j["trial_id"] + ".json"))["status"]
                     if (raw / "trials" / (j["trial_id"] + ".json")).exists() else "not_requested" for j in manifest["jobs"])
    print("Status:", dict(counts))
    if args.run:
        run_pilot(manifest, ROOT / "data", load_key(), args.max_new_calls)
    elif args.export_only:
        export_results(manifest, ROOT / "data")
    elif args.resolve_missing_only:
        resolve_missing(manifest, ROOT / "data")
    else:
        print("Pratinjau lokal: tidak ada pemanggilan Gemini atau SerpApi. Gunakan --run untuk mengeksekusi.")


if __name__ == "__main__":
    try:
        main()
    except (GenerationError, ValueError, FileExistsError) as error:
        print(str(error))
        raise SystemExit(1)
