# Pilot teknis Gemini: pengaruh instruksi pencarian

## Rancangan

Skrip [pilot_gemini_grounding.py](../src/pilot_gemini_grounding.py) mengambil sembilan pertanyaan PAA asli dari data lokal, tiga per domain. Tiap pertanyaan diberikan pada dua kondisi, masing-masing dua pengulangan: **maksimal 36 pemanggilan generateContent**.

- **A:** Google Search aktif, instruksi menjawab dalam bahasa Indonesia.
- **B:** konfigurasi yang sama, ditambah instruksi tetap untuk mencari dan mendukung klaim dengan sitasi.

Query tidak disintesis atau diterjemahkan. Pilihan pertanyaan bersifat purposif untuk pilot teknis, bukan sampel acak atau keputusan kelayakan dataset utama. Urutan A/B dibalik antarpertanyaan dan pengulangan untuk mengurangi perbedaan waktu yang sistematis; ini bukan randomisasi penuh.

| Domain | Pertanyaan asli PAA |
|---|---|
| Kesehatan | Apa penyebab penyakit campak? |
| Kesehatan | vitamin C ada di makanan apa? |
| Kesehatan | Apa saja sunscreen spf 50 pa++++? |
| Keuangan | Syarat bikin NPWP apa saja? |
| Keuangan | Apa yang dimaksud dividen? |
| Keuangan | Berapa harga emas di Pegadaian hari ini? |
| Teknologi | Apa resiko VPN gratis? |
| Teknologi | Rumus apa saja di Excel? |
| Teknologi | Laptop ASUS harga berapa? |

Model di [konfigurasi](../configs/gemini_grounding_pilot.json) adalah `gemini-3.5-flash`, mengikuti model yang dilaporkan peneliti. Ketersediaannya pada akun belum diverifikasi dengan request langsung. Jika model tidak dapat diakses, skrip mencatat error dan berhenti; tidak mengganti model diam-diam. Model/version, konfigurasi, prompt, identitas PAA, dan respons dicatat untuk reproduksibilitas.

Implementasi menggunakan REST `v1beta/models/{model}:generateContent`, yaitu operasi yang sama dengan `client.models.generate_content`, memakai library standar Python sehingga tidak memerlukan instalasi tambahan. Referensi: [generateContent](https://ai.google.dev/api/generate-content), [grounding metadata](https://ai.google.dev/api/generate-content#GroundingMetadata), dan [Google Search Grounding](https://ai.google.dev/gemini-api/docs/google-search).

## Menjalankan bertahap

Dari direktori utama proyek, tampilkan rencana tanpa jaringan:

```powershell
.\venv\Scripts\python.exe .\src\pilot_gemini_grounding.py
```

Periksa dahulu anggaran/rate limit pada akun Gemini dan [halaman harga resmi](https://ai.google.dev/gemini-api/docs/pricing). Batas 36 adalah jumlah pemanggilan model, **bukan batas biaya uang atau jumlah pencarian internal Google**. Token dan grounding dapat memiliki komponen biaya tersendiri sesuai model/tier. Skrip tidak memanggil SerpApi atau menggunakan 22 sisa pencarian SerpApi.

Untuk mulai dengan dua pemanggilan baru (pasangan A/B pertanyaan pertama):

```powershell
.\venv\Scripts\python.exe .\src\pilot_gemini_grounding.py --run --max-new-calls 2
```

Lanjutkan seluruh percobaan yang belum dikirim:

```powershell
.\venv\Scripts\python.exe .\src\pilot_gemini_grounding.py --run
```

Gunakan `--max-new-calls 2` lagi jika ingin melanjutkan dua pemanggilan per eksekusi. Kunci dibaca dari `GEMINI_API_KEY` pada environment atau `.env`; tidak dicetak. Setiap request independen tanpa riwayat percakapan.

Ekspor ulang hasil lokal tanpa Gemini atau resolusi URL:

```powershell
.\venv\Scripts\python.exe .\src\pilot_gemini_grounding.py --export-only
```

Konfigurasi dibekukan dalam manifest saat `--run` dimulai. Gunakan `experiment_id` baru jika mengubah model, prompt, daftar sumber, atau jumlah pengulangan setelah itu. File raw dan checkpoint lama tetap dipertahankan.

## Hasil dan interpretasi

| Lokasi | Isi |
|---|---|
| `data/raw/gemini_pilot/gemini_grounding_pilot_01/manifest.json` | Rencana 36 percobaan, snapshot query, dan kondisi |
| `data/raw/gemini_pilot/gemini_grounding_pilot_01/trials/` | Respons JSON dan hasil resolusi URL per percobaan |
| `data/interim/gemini_pilot/gemini_grounding_pilot_01/trials.csv` | Status, metadata, jumlah sumber/sitasi, finish reason, serta token |
| `data/interim/gemini_pilot/gemini_grounding_pilot_01/sources.csv` | Sumber web, penanda hubungan sitasi, URL mentah dan tujuan |
| `data/interim/gemini_pilot/gemini_grounding_pilot_01/source_links.csv` | Ekspor untuk dibaca: `source_url` memakai URL tujuan, tanpa kolom tautan pengalihan Google |
| `data/interim/gemini_pilot/gemini_grounding_pilot_01/report.md` | Ringkasan A/B, hasil per query, dan tautan tujuan unik yang bisa diklik |
| `data/interim/gemini_pilot/gemini_grounding_pilot_01/summary.csv` | Perbandingan A/B |

Sumber di `groundingChunks` belum tentu ditautkan pada jawaban. `is_cited` hanya bernilai benar jika indeks sumber web muncul di `groundingSupports.groundingChunkIndices`. Pemeriksaan ini menunjukkan hubungan metadata, bukan audit bahwa seluruh klaim benar atau sepenuhnya didukung sumber.

`n_search_queries` mencatat kueri pencarian yang dilaporkan metadata; nilai nol tidak membuktikan bahwa model sama sekali tidak mencari. `has_web_citation` mencatat ada/tidaknya hubungan sitasi web. Tidak ada label artikel terkutip/tidak terkutip untuk pemodelan yang dibuat pada tahap ini.

`citation_rate_completed` menggunakan penyebut seluruh percobaan berstatus `completed`, termasuk respons tanpa kandidat, terblokir, atau terpotong. Periksa `finish_reason`, `has_text`, `error_code`, dan JSON sebelum menetapkan aturan kelayakan penelitian. Error jaringan/API tidak dimasukkan ke penyebut ini dan dilaporkan terpisah. Dua pengulangan per kondisi hanya memberi gambaran awal, bukan estimasi kestabilan yang kuat.

## Penanganan kegagalan dan URL

- Gunakan `source_url` atau `source_links.csv` untuk membaca tautan; URL tujuan yang belum diketahui dibiarkan kosong, tanpa fallback ke redirect Google. Respons mentah dan `raw_url` dalam `sources.csv` tetap dipertahankan untuk audit. Tautan HTTP 403/503 berarti tujuan diketahui tetapi akses gagal, bukan kegagalan menemukan URL.
- Untuk mencoba ulang hanya sumber tanpa URL tujuan, jalankan `python ./src/pilot_gemini_grounding.py --resolve-missing-only`. Perintah ini mengakses web, tidak memanggil Gemini/SerpApi, mempertahankan riwayat resolusi sebelumnya, dan tidak mengubah jawaban maupun keputusan sitasi model.
- Penulisan JSON/CSV mencoba ulang penggantian file hingga tujuh kali jika Windows mengembalikan `PermissionError`, dengan jeda bertahap (total maksimal sekitar 6,3 detik). Yang diulang hanya operasi file, bukan pemanggilan API. Jika tetap gagal, file `.tmp` dipertahankan untuk pemulihan; jangan menghapusnya sebelum memeriksa isi terbaru.
- Checkpoint `started` ditulis sebelum request. `completed`, `error`, dan `started` tidak dikirim ulang otomatis. Proses yang terputus saat request mungkin sudah menggunakan kuota; periksa sebelum memutuskan retry.
- Error API, termasuk 404/429, menghentikan batch. Menjalankan lagi melanjutkan percobaan yang belum memiliki checkpoint, bukan mencoba ulang error. Periksa dan tangani penyebab error terlebih dahulu.
- Respons disimpan dengan status `response_saved` sebelum resolusi URL. Bila resolusi terputus, eksekusi berikutnya melanjutkan resolusi dari respons tersebut tanpa memanggil Gemini lagi.
- Semua URL sumber web diresolusi segera setelah setiap respons, dengan HEAD lalu GET bila perlu, tanpa membaca isi artikel. URL mentah dan tujuan disimpan. Kegagalan resolusi tetap dicatat; tidak diubah menjadi bukti artikel tidak dikutip.
- `destination_http_error` berarti alamat tujuan diketahui tetapi server mengembalikan HTTP error; itu bukan bukti artikel berhasil diambil. Resolusi belum melakukan normalisasi URL, verifikasi canonical, atau crawling artikel.
- Lock mencegah eksekusi bersamaan. Jika proses dihentikan paksa, pastikan prosesnya sudah mati sebelum menghapus `running.lock` yang tertinggal.

## Status implementasi dan langkah berikutnya

Skrip diverifikasi dengan respons simulasi dan pratinjau lokal. **36 pemanggilan Gemini belum dijalankan oleh asisten pada tahap pembuatan skrip.** Belum ada hasil perbandingan A/B yang dapat disimpulkan.

Setelah pilot dijalankan, tinjau proporsi sitasi, kelengkapan sumber, perubahan hasil antarulangan, token, dan kegagalan resolusi. Gunakan hasilnya untuk memilih konfigurasi pengumpulan utama. Protokol sintesis/penilaian query dan aturan label utama tetap mengikuti CONTEXT.md dan harus dibekukan terpisah.
