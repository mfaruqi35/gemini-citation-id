# Memulai batch utama `main_03`

Persiapan lokal dilakukan pada **7 Oktober 2026**. Batch 3 belum mengirim permintaan SerpApi/Gemini. Semua berkas persiapan sudah tersedia:

| Berkas | Fungsi |
| --- | --- |
| `data/manual/main_03_queries.csv` | Snapshot 75 pertanyaan PAA: 25 kesehatan, 25 keuangan, 25 teknologi. |
| `configs/main_03_query_selection.json` | Daftar teks asli yang dipilih dan aturan pemilihan. |
| `data/manual/query_expansion_01_decisions.csv` | Keputusan LLM untuk 75 pertanyaan tersebut, termasuk alasan dan reviewer. |
| `configs/main_dataset_03.json` | Protokol Google Top 10 + tiga percobaan Gemini. |
| `configs/article_dataset_03.json` | Scraping artikel untuk `main_03`. |
| `configs/article_features_03.json` | Build fitur serta embedding untuk `articles_main_03`. |

PAA berasal dari respons Google `main_02` yang sudah tersimpan. Ekstraksi lokal menghasilkan 925 kandidat baru berstatus pending; 75 yang jelas maksudnya dan tidak mengulang teks kueri batch terdahulu dipilih untuk awal batch ini. **850 kandidat sisanya belum dinilai/dijadwalkan**, bukan otomatis excluded. Daftar awal diseimbangkan per domain supaya contoh batch ini mencakup ketiganya. Teks pertanyaan tidak disintesis ulang. Keputusan seleksi adalah penilaian LLM, bukan verifikasi manusia independen; peneliti dapat meninjau snapshot sebelum pengumpulan. Source `main_02` tetap memiliki empat kueri Google yang belum selesai dan tidak dipindahkan ke batch 3.

## 1. Pratinjau tanpa biaya API

Jalankan dari direktori akar proyek dengan environment Python aktif:

```powershell
python src/continue_main_dataset.py --config configs/main_dataset_03.json --max-queries 5 --check-every 5
```

Preview yang sudah diuji menampilkan `Batch: main_03 | Query: 75 {'kesehatan': 25, 'keuangan': 25, 'teknologi': 25}`. Jika ingin membaca setiap teks lebih dahulu, buka `data/manual/main_03_queries.csv`.

## 2. Kumpulkan lima kueri pertama

```powershell
python src/continue_main_dataset.py --config configs/main_dataset_03.json --run --max-queries 5 --check-every 5
```

Ulangi perintah ini untuk mengisi batch secara bertahap. Maksimal **75 pencarian SerpApi dan 225 panggilan Gemini** bila seluruh kueri dan tiga slotnya dijalankan; lima kueri pertama maksimal lima pencarian dan 15 panggilan. Runner memeriksa kuota SerpApi dan mencatat token Gemini dari respons, tetapi tidak mengetahui saldo rupiah Gemini. Periksa saldo di layanan Gemini sebelum menjalankan. Cadangan SerpApi pada konfigurasi adalah 10 pencarian. `--max-queries` membatasi jumlah kueri per eksekusi, bukan ukuran snapshot 75 kueri.

Saat persiapan ini dibuat, pencarian SerpApi pada beberapa kueri `main_02` berulang kali menghasilkan HTTP 503 meskipun kuota masih ada. Jika hal itu terjadi juga di `main_03`, hentikan proses dan periksa checkpoint; mengulang perintah biasa pada checkpoint Google `error`/`started` akan berhenti lagi. Gunakan `src/recover_main_google.py --config configs/main_dataset_03.json --query-id ... --run` untuk pemulihan eksplisit setelah masalah pencarian reda. Jangan hapus respons/manifest lama. `--unstarted-only` dapat melewati checkpoint gagal tetapi tidak menyelesaikannya.

### Jika Gemini yang gagal dengan 503 / UNAVAILABLE

Hentikan pengumpulan query baru saat error berulang. `--max-queries` yang lebih kecil tidak mengatasi gangguan layanan; memakai `--unstarted-only` lagi akan mengambil Google untuk query berikutnya. Setelah jeda, periksa kelayakan recovery lokal:

```powershell
python src/recover_main_gemini.py --config configs/main_dataset_03.json --finish-incomplete
```

Jika ada `ready`, uji kelanjutan dengan maksimal satu panggilan Gemini:

```powershell
python src/recover_main_gemini.py --config configs/main_dataset_03.json --finish-incomplete --run --max-new-calls 1
```

Jika berhasil, perintah yang sama dapat diulang dengan batas 3 untuk melanjutkan slot tersisa. Ini memakai Gemini, **0 pencarian SerpApi**, serta mempertahankan seluruh respons yang sudah tersimpan. `--max-new-calls` mencakup retry dan slot baru bersama-sama. Satu slot error mendapat paling banyak satu retry; jika gagal lagi, proses berhenti. Tidak ada pergantian model atau pengulangan respons selesai yang tidak memiliki grounding.

`google_not_completed` harus dipulihkan terpisah melalui `recover_main_google.py`. `collection_window_expired` berarti tidak boleh melanjutkan panggilan dalam batch lama karena melewati enam jam; perlu pengumpulan ulang terencana dalam batch baru. `uncertain_trial_checkpoint` perlu pemeriksaan manual, sedangkan `retry_limit_reached` berarti retry slot sudah terpakai. Jangan menghapus checkpoint atau mengubah waktunya. Setelah gangguan reda, pengumpulan query baru dapat dilanjutkan dengan perintah `continue_main_dataset.py --unstarted-only` di atas.

Hasil kueri berada di `data/interim/main/main_03/`; respons dan riwayat percobaan tersimpan di `data/raw/main/main_03/`.

## 3. Scraping Google Top 10 dan build artikel

Setelah paling sedikit satu kueri `main_03` selesai dengan data layak, pratinjau URL Google Top 10:

```powershell
python src/scrape_articles.py --config configs/article_dataset_03.json --extend-manifest --primary-only --max-new-urls 50
```

Jika daftar URL sesuai, jalankan:

```powershell
python src/scrape_articles.py --config configs/article_dataset_03.json --extend-manifest --primary-only --run --max-new-urls 50
python src/build_article_dataset.py --config configs/article_features_03.json --with-embeddings
```

Ulangi scraper untuk URL Top 10 berikutnya sampai preview menunjukkan `Belum diambil/diizinkan ulang: 0`, lalu build lagi. `--extend-manifest` diperlukan saat hasil kueri baru menambah pasangan/URL setelah manifest pertama dibekukan; checkpoint sebelumnya tetap digunakan. Scraping mengakses website langsung dan build memakai HTML/cache embedding lokal; keduanya tidak memakai kredit pencarian SerpApi atau token Gemini. URL yang gagal/ditolak robots tetap tercatat. Artikel yang masih memerlukan review bahasa, jenis halaman, atau ekstraksi belum otomatis masuk `model_ready.csv`.

Hasil utama: `data/processed/articles_main_03/dataset.csv` dan `model_ready.csv`. Gemini-only tetap di `data/processed/articles_main_03/dataset_gemini_only.csv`. Jika kelak model dilatih pada gabungan batch 1–3, satukan artikel/pasangan berdasarkan identitas dan hitung ulang BM25 pada satu korpus yang konsisten; jangan langsung menumpuk nilai BM25 per batch.
