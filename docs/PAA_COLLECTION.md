# Pengambilan People Also Ask

## Batch awal untuk bimbingan

[configs/paa_pilot.json](../configs/paa_pilot.json) menetapkan **maksimal 15 pencarian**, masing-masing lima topik kesehatan, keuangan, dan teknologi. Topik dipilih secara purposif dari `needs_paa.csv` untuk variasi topik. Batch ini bukan sampel acak atau kumpulan query final.

| Domain | Topik |
|---|---|
| Kesehatan | icd 10, obat batuk, campak, vitamin c, sunscreen |
| Keuangan | pajak, npwp, pegadaian, pinjaman daring, dividen |
| Teknologi | vpn, github, excel, laptop asus, lacak hp gmail |

Pencarian menggunakan teks Trends persis, Google Indonesia, `gl=id`, `hl=id`, lokasi Indonesia, dan perangkat desktop. `hl=id` tidak menjamin seluruh pertanyaan berbahasa Indonesia; bahasa dan relevansi tetap perlu diperiksa.

Skrip hanya membaca `related_questions` dari respons Google Search awal. Tidak ada ekspansi pertanyaan, pagination, pengambilan jawaban lanjutan, atau penggantian otomatis topik yang tidak menghasilkan PAA. Pertanyaan yang tersedia seluruhnya disimpan; jumlah PAA per pencarian tidak dipaksakan. Hasil kosong merupakan catatan observasi yang sah, bukan error jaringan.

Referensi implementasi: [Google Search API](https://serpapi.com/search-api), [Related Questions](https://serpapi.com/related-questions), dan [Account API](https://serpapi.com/account-api). Pertanyaan bertipe AI Overview tetap diberi `result_type` sesuai respons; skrip tidak mengambil isi AI Overview melalui permintaan tambahan.

## Menjalankan

Tidak perlu library tambahan; skrip memakai library standar Python. Kunci dibaca dari environment `SERPAPI_API_KEY` atau `.env` di direktori proyek. Nilai kunci tidak dicetak; respons yang disimpan dibersihkan dari nilai kunci jika muncul.

Pratinjau lokal, tanpa panggilan API:

```powershell
.\venv\Scripts\python.exe .\src\collect_paa.py
```

Mengambil batch atau melanjutkan topik yang belum pernah dikirim:

```powershell
.\venv\Scripts\python.exe .\src\collect_paa.py --run
```

Sebelum pencarian baru, skrip memeriksa Account API untuk jumlah kuota tersisa. Angka `213/250` dari antarmuka tidak diasumsikan sebagai kuota terpakai atau tersisa. Batch hanya berjalan jika kuota cukup untuk seluruh permintaan baru dan cadangan lima pencarian. Snapshot kuota hanya menyimpan angka penggunaan dan waktu; identitas akun dan API key tidak disimpan.

## Berkas hasil

| Lokasi | Isi |
|---|---|
| `data/raw/paa/batches/paa_pilot_01/manifest.json` | Snapshot konfigurasi dan hubungan topik ke sumber Trends |
| `data/raw/paa/batches/paa_pilot_01/quota_*.json` | Snapshot kuota sebelum/sesudah |
| `data/raw/paa/requests/<request_id>.json` | Parameter, waktu, status, dan respons JSON asli dengan redaksi kredensial |
| `data/interim/paa/paa_pilot_01/searches.csv` | Status dan jumlah PAA untuk seluruh topik pada batch |
| `data/interim/paa/paa_pilot_01/questions.csv` | Satu baris per kemunculan pertanyaan PAA |

Pertanyaan memiliki `paa_id`, `topic_id` sumber Trends, teks pencarian, domain, posisi, waktu, search ID SerpApi, jenis hasil, dan referensi data mentah. `question_key` menandai teks pertanyaan yang sama setelah normalisasi huruf dan spasi tanpa menghapus hubungannya dengan topik berbeda. Semua pertanyaan awal berstatus `unreviewed`.

`source_url` adalah tautan sumber PAA jika tersedia. Cuplikan dan jawaban tetap ada dalam JSON untuk jejak data, tetapi tabel masukan sintesis sebaiknya hanya memakai pertanyaan dan hubungan topiknya. Tidak semua pertanyaan PAA otomatis cocok dengan domain atau populasi artikel penelitian.

## Melanjutkan dan menjaga kuota

- Identitas request ditentukan oleh query dan parameter pencarian. Request tersimpan dipakai kembali, termasuk lintas batch dengan parameter identik.
- Hasil `success`, `no_paa`, `error`, atau `started` tidak dikirim ulang otomatis. Checkpoint dibuat sebelum pemanggilan untuk menghindari biaya ganda ketika proses terputus.
- Status `started` berarti hasil belum diketahui, bukan bukti bahwa kuota tidak terpakai. Periksa dashboard/arsip SerpApi sebelum memutuskan pengambilan ulang.
- Satu kegagalan menghentikan batch. Pemanggilan berikutnya hanya melanjutkan topik yang belum memiliki checkpoint; topik gagal tetap terlihat di `searches.csv`.
- Konfigurasi batch dibekukan setelah pemeriksaan kuota berhasil. Gunakan `batch_id` baru untuk mengubah daftar atau parameter.
- Lock mencegah proses bersamaan untuk batch yang sama. Jika proses dihentikan paksa dan `running.lock` tertinggal, pastikan proses lama berhenti sebelum menghapus file lock tersebut. Jangan menjalankan beberapa batch bersamaan.
- File ekspor dapat dibentuk ulang tanpa request baru dari checkpoint yang sama. Simpan keputusan review PAA di tabel terpisah agar tidak tertimpa ekspor.

Untuk perluasan dataset utama: salin konfigurasi ke file baru, gunakan batch ID baru, pilih topik tambahan yang masih `needs_paa`, serta tentukan `max_searches` secara eksplisit sesuai anggaran batch. Contoh menjalankan konfigurasi tambahan:

```powershell
.\venv\Scripts\python.exe .\src\collect_paa.py --config .\configs\paa_batch_02.json
```

File contoh `paa_batch_02.json` belum dibuat. Pratinjau daftar terlebih dahulu, kemudian tambahkan `--run` untuk mengambilnya. Memperbesar jumlah topik tidak mengubah data pilot yang sudah disimpan. Penggunaan pilot dalam dataset utama tetap bergantung pada kesesuaian protokol final.

## Pemeriksaan lokal

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tes menggunakan respons simulasi tanpa jaringan untuk memeriksa resume, hasil PAA kosong, kuota tidak cukup, kegagalan tanpa retry otomatis, relasi topik, dan redaksi kunci.
