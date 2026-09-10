# Progres penelitian

Terakhir diperbarui: **10 September 2026**.

## Tujuan dan posisi saat ini

Penelitian mengikuti [CONTEXT.md](../CONTEXT.md): memprediksi keterkutipan artikel web berbahasa Indonesia oleh Gemini dengan Google Search Grounding menggunakan XGBoost, membandingkannya dengan Logistic Regression dan Random Forest, serta menganalisis kontribusi fitur melalui SHAP dan ablation study.

Unit analisis dataset utama nantinya adalah **pasangan query–artikel**. Target awal sekitar 300 query final dan maksimal 3.000 pasangan sebelum pembersihan. Target terdekat adalah memperoleh dataset awal yang dapat dibawa ke bimbingan dan dilanjutkan menjadi dataset pemodelan.

**Progres implementasi saat ini baru sampai pengumpulan dan seleksi sumber query Google Trends.** Data yang sudah tersedia belum merupakan query final, label keterkutipan, atau dataset pasangan query–artikel. Pengambilan PAA dan sintesis belum dijalankan dalam rangkaian pekerjaan ini. CONTEXT.md mencatat pilot terdahulu 40 query; pilot tersebut belum diintegrasikan atau diaudit ulang dalam pekerjaan ini.

## Pekerjaan yang telah selesai

1. Meninjau rancangan penelitian dan menyusun alur kerja bertahap dengan Python untuk proses berulang serta Jupyter Notebook untuk peninjauan dan analisis.
2. Mengumpulkan CSV Google Trends secara manual oleh peneliti, tanpa kata kunci awal, menggunakan periode setahun terakhir dan kategori Kesehatan, Keuangan, serta Komputer & elektronik. Nama ekspor mencantumkan wilayah ID dan rentang 10 September 2025–10 September 2026. Tautan Explore, jenis pencarian, dan metadata kategori terperinci masih perlu dicatat dalam manifest sumber.
3. Memisahkan enam ekspor sumber di `data/before/` dan enam CSV hasil seleksi di `data/`. Ekspor asli tidak diubah oleh skrip penggabungan/review.
4. Membuat dan menjalankan [src/merge_trends.py](../src/merge_trends.py). Skrip menggabungkan enam CSV terpilih, mempertahankan teks serta nilai Trends asli, dan menambahkan ID, domain, jenis daftar, file asal, serta nomor baris data.
5. Membuat [notebook peninjauan](../notebooks/01_review_trends_sources.ipynb) dan [modul review](../src/review_trends.py). Notebook mengelompokkan teks identik, menampilkan filter, menerima keputusan manual, menyimpan progres, dan mengekspor daftar per status.
6. Memasang `ipykernel` pada virtual environment proyek. Dependensi notebook dicatat dalam [requirements-notebooks.txt](../requirements-notebooks.txt). Penggabungan dan penyimpanan CSV menggunakan library standar Python.
7. Melengkapi keputusan review berdasarkan arahan peneliti, termasuk alasan serta intent untuk sumber siap sintesis. Keputusan yang sudah ditulis peneliti dan sesuai aturan terbaru dipertahankan.
8. Mengeluarkan enam sumber GTK, memperbarui penggabungan, menyelaraskan kembali asal sumber, dan memperbarui dictionary keputusan serta ekspor notebook.

## Pilot People Also Ask selesai

Pengambil [src/collect_paa.py](../src/collect_paa.py) telah dijalankan dengan [konfigurasi pilot](../configs/paa_pilot.json), maksimal 15 pencarian. Konfigurasi: Google Indonesia, negara ID, bahasa ID, lokasi Indonesia, desktop, hanya PAA pada respons awal. Topik dipilih secara purposif (lima per domain) dari daftar `needs_paa`, bukan sampel acak. Respons disimpan per request dan pengambilan dapat dilanjutkan tanpa mengirim ulang request tersimpan.

| Domain | Pencarian | Menghasilkan PAA | Tanpa PAA | Pertanyaan |
|---|---:|---:|---:|---:|
| Kesehatan | 5 | 5 | 0 | 20 |
| Keuangan | 5 | 5 | 0 | 20 |
| Teknologi | 5 | 3 | 2 | 12 |
| **Total** | **15** | **13** | **2** | **52** |

Seluruh 52 pertanyaan memiliki teks unik setelah normalisasi huruf dan spasi. `github` dan `lacak hp gmail` berhasil dicari tetapi tidak menghasilkan PAA. Tidak ada pencarian pengganti atau ekspansi otomatis.

Kuota akun yang diperiksa: sebelum batch **213 terpakai, 37 tersisa** dari 250; sesudah batch **228 terpakai, 22 tersisa**. Penggunaan batch adalah 15 pencarian. Tidak ada pengambilan tambahan setelah batch ini.

Hasil berada di `data/interim/paa/paa_pilot_01/questions.csv` dan `searches.csv`; respons mentah dengan redaksi kredensial serta manifest berada di `data/raw/paa/`. Semua pertanyaan berstatus `unreviewed`. Pengaturan bahasa Indonesia tidak menjamin bahasa hasil; sebagai contoh PAA `icd 10` berbahasa Inggris dan perlu ditinjau sebelum diterjemahkan/sintesis. Review sumber Trends tidak diubah menjadi status selesai PAA; status pengambilan dicatat terpisah pada `searches.csv`.

Gunakan [notebook inspeksi PAA](../notebooks/02_inspect_paa_pilot.ipynb) untuk bahan bimbingan tanpa memanggil API. [Panduan pengambilan dan resume](PAA_COLLECTION.md) menjelaskan struktur hasil, pengamanan kuota, dan penambahan batch menuju dataset utama. Empat tes lokal tanpa jaringan mencakup penggunaan kembali hasil, kuota tidak cukup, kegagalan tanpa retry, dan redaksi rahasia.

## Dataset sumber terkini

| Domain | Top | Rising | Total baris sumber | Teks unik aktif |
|---|---:|---:|---:|---:|
| Kesehatan | 29 | 29 | 58 | 57 |
| Keuangan | 46 | 41 | 87 | 76 |
| Teknologi | 47 | 41 | 88 | 76 |
| **Total** | **122** | **111** | **233** | **209** |

Penggabungan mempertahankan seluruh 233 kemunculan sumber. Review memiliki satu baris per teks yang persis sama, sehingga berisi 209 baris. Pengelompokan ini belum menghapus duplikasi semantik atau kesamaan intent.

## Keputusan review yang berlaku

Keputusan berikut merupakan arahan peneliti, **bukan hasil LLM Judgment**. Top/Rising menunjukkan asal daftar, bukan ukuran kualitas query.

- Kesehatan Top: `needs_paa`.
- Kesehatan Rising: `ready_for_synthesis`, dengan pengecualian di bawah.
- `icd 10`: diperbarui dari `needs_review` menjadi `needs_paa` setelah penjelasan klasifikasi penyakit dan masalah kesehatan diverifikasi melalui [WHO](https://icd.who.int/browse10/2019/en) dan disetujui peneliti. Intent tetap kosong karena kebutuhan informasi belum spesifik.
- Sumber setelah `icd 10` sampai `abu vulkanik` dalam urutan review: `needs_paa`.
- `best sunscreen for face`: `needs_paa`, untuk menelusuri kebutuhan yang lebih spesifik melalui PAA tanpa mengarang jenis kulit dalam query.
- `campak`, yang muncul pada Top dan Rising: `needs_paa`; keputusan rentang/Top didahulukan.
- Keuangan dan teknologi: seluruh sumber aktif menjadi `needs_paa`.
- Keputusan `best pillow for side sleepers` tetap `ready_for_synthesis`, dengan intent mencari rekomendasi bantal untuk orang yang tidur menyamping.

| Domain | `needs_paa` | `ready_for_synthesis` | `needs_review` | Total |
|---|---:|---:|---:|---:|
| Kesehatan | 31 | 26 | 0 | 57 |
| Keuangan | 76 | 0 | 0 | 76 |
| Teknologi | 76 | 0 | 0 | 76 |
| **Total** | **183** | **26** | **0** | **209** |

Tidak ada sumber aktif berstatus `unreviewed` atau `needs_review`. Bahasa yang belum dapat ditetapkan dengan yakin ditandai `unknown`. Intent untuk `needs_paa` dikosongkan agar tidak menciptakan kebutuhan informasi sebelum pertanyaan sumber diperoleh.

## Pengeluaran GTK dan jejak perubahan

Alasan peneliti: GTK lebih berkaitan dengan pendidikan dan tidak sesuai cakupan teknologi penelitian ini.

Enam teks yang dikeluarkan:

- `gtk`
- `info gtk`
- `info gtk kemendikdasmen`
- `info gtk 2026`
- `emis gtk`
- `ruang gtk`

Peneliti telah menghapus empat kueri pada Rising. Saat pemeriksaan, dua kueri pada Top masih tersedia dan kemudian dikeluarkan dengan alasan yang sama.

Sebelum perubahan ini, dataset gabungan memuat 239 baris dan review memuat 215 teks unik. Setelah perubahan: 233 baris dan 209 teks unik. Jumlah `needs_paa` saat pengeluaran GTK turun dari 188 menjadi 182; keputusan sumber lainnya dipertahankan. Setelah keputusan lanjutan untuk `icd 10`, jumlah terkini menjadi 183.

Jejak pengeluaran tersimpan terpisah di [data/manual/gtk_exclusions.csv](../data/manual/gtk_exclusions.csv), termasuk ID dan referensi sumber sebelumnya, alasan, serta waktu pengeluaran. Karena keenam sumber telah dihapus dari masukan aktif, mereka tidak muncul dalam `data/interim/review/excluded.csv`; daftar pengeluaran GTK harus dibaca bersama ekspor status aktif saat melaporkan seleksi.

Cadangan sebelum penyelarasan tersedia di `outputs/review_backups/20260910T041943791901Z/`. Cadangan ini menyimpan notebook, review, gabungan lama, serta CSV terpilih pada saat pemeriksaan; empat penghapusan Rising oleh peneliti sudah terjadi sebelum cadangan tersebut. Ekspor asli tetap berada di `data/before/`.

`source_id` berasal dari nomor baris dan dapat berubah setelah penghapusan. Pada penyelarasan ini, keputusan lama dipertahankan melalui `topic_id` berbasis hash teks, setelah kecocokan teks dan domain diperiksa; referensi ke baris masukan dibentuk ulang. Validasi perubahan sumber pada `load_review` tetap aktif agar perubahan berikutnya tidak diterima diam-diam.

## Berkas kerja dan cara melanjutkan

| Berkas | Fungsi |
|---|---|
| `data/top_*.csv`, `data/rising_*.csv` | Enam CSV sumber terpilih |
| `data/before/` | Ekspor asli Google Trends |
| `data/interim/trends_sources.csv` | Seluruh kemunculan sumber hasil penggabungan |
| `data/manual/trends_review.csv` | Progres keputusan untuk teks unik aktif |
| `data/manual/gtk_exclusions.csv` | Catatan sumber GTK yang dikeluarkan |
| `data/interim/review/needs_paa.csv` | 183 topik untuk penelusuran PAA |
| `data/interim/review/ready_for_synthesis.csv` | 26 sumber untuk persiapan sintesis |
| `data/interim/review/needs_review.csv` | Kosong; seluruh sumber aktif telah diputuskan |

Jalankan penggabungan dari direktori utama proyek:

```powershell
.\venv\Scripts\python.exe .\src\merge_trends.py
```

Buka notebook dan pilih interpreter `venv/Scripts/python.exe`. Jalankan sel dari atas ke bawah. Untuk koreksi keputusan, cari komentar teks sumber di blok **Isi keputusan manual**, edit dictionary, lalu jalankan sel keputusan dan sel simpan. Dictionary menerapkan keputusan yang tertulis di dalamnya; jangan mengedit CSV keputusan secara terpisah tanpa menyelaraskannya dengan notebook.

Jika sumber CSV berubah lagi, arsipkan dan selaraskan review sebelum menjalankan notebook; menjalankan penggabungan saja tidak memigrasikan keputusan lama. Folder data dan outputs saat ini diabaikan Git sesuai `.gitignore`, sehingga arsip data perlu disimpan secara terpisah dari kode.

## Pemeriksaan yang dilakukan

- Penggabungan enam file dengan pemeriksaan struktur dan query kosong.
- Eksekusi seluruh sel kode notebook secara berurutan menggunakan Python virtual environment.
- Pemeriksaan keunikan ID topik dan jumlah kemunculan sumber.
- Pemeriksaan bahwa kueri GTK tidak berada pada sumber, review, atau dictionary keputusan aktif.
- Pemeriksaan bahwa keputusan sumber yang dipertahankan tidak berubah akibat pembaruan nomor baris.
- Pemeriksaan pemuatan ulang review, konsistensi ekspor per status, dan kestabilan penerapan ulang keputusan.

## Skrip pilot Gemini disiapkan

[src/pilot_gemini_grounding.py](../src/pilot_gemini_grounding.py) dan [konfigurasi pilot](../configs/gemini_grounding_pilot.json) telah dibuat untuk sembilan pertanyaan PAA asli berbahasa Indonesia, tiga per domain. Dua kondisi (A: Google Search aktif; B: sama dengan tambahan instruksi pencarian) diuji dua kali, sehingga rencana maksimal 36 pemanggilan. Kedua kondisi memiliki instruksi bahasa Indonesia yang sama. Model mengikuti pilihan peneliti, `gemini-3.5-flash`, tanpa pergantian otomatis.

Mode bawaan adalah pratinjau lokal; `--run --max-new-calls 2` memulai dua pemanggilan baru dan `--run` melanjutkan sisa rencana. Implementasi memakai REST generateContent dan library standar Python. Respons mentah, metadata sitasi, token, serta hasil resolusi URL segera per respons disimpan untuk dapat dilanjutkan tanpa pengulangan API yang tidak disengaja.

Pada tahap pembuatan skrip, pratinjau menunjukkan 36 percobaan belum dikirim dan tidak ada pemanggilan Gemini atau penggunaan kuota SerpApi. Lima tes awal tanpa jaringan untuk pilot Gemini lulus. Peneliti kemudian menjalankan seluruh pilot; hasil terkini dijelaskan di bawah.

Panduan eksekusi, batas biaya, interpretasi metrik, dan penanganan error ada di [GEMINI_GROUNDING_PILOT.md](GEMINI_GROUNDING_PILOT.md). Pilot teknis ini memakai PAA asli tanpa sintesis; tidak menggantikan sintesis dan penilaian query untuk dataset utama. Sebelum menjalankan, periksa anggaran Gemini, lalu mulai dari pasangan A/B pertama.

## Hasil pilot Gemini lengkap dan ekspor URL tujuan

Seluruh **36 percobaan selesai**, dengan finish reason `STOP`, tanpa error API pada hasil akhir. Model yang dilaporkan respons adalah `gemini-3.5-flash`.

| Kondisi | Respons dengan sitasi / selesai | Proporsi |
|---|---:|---:|
| A: Google Search aktif | 8/18 | 44,4% |
| B: ditambah instruksi pencarian | 18/18 | 100% |

Per domain, kondisi A memiliki sitasi pada 2/6 respons kesehatan, 4/6 keuangan, dan 2/6 teknologi. Kondisi B memiliki sitasi pada 6/6 respons di setiap domain. Ini hasil eksploratif sembilan query dan dua pengulangan, bukan jaminan seluruh query akan menghasilkan sitasi.

Ada 292 kemunculan sumber dengan hubungan sitasi di metadata. Setelah mencoba ulang lima kegagalan resolusi tanpa pemanggilan Gemini atau SerpApi, 290 kemunculan sumber memiliki URL tujuan (159 URL tujuan unik), dan dua kemunculan dari `lombokbaratkab.go.id` masih belum memiliki URL tujuan. Sebanyak 236 kemunculan berstatus `resolved`, 54 `destination_http_error` (45 HTTP 403 dan 9 HTTP 503), serta dua `network_or_url_error`. Angka kemunculan bukan jumlah artikel layak; seleksi video, toko, dan jenis halaman lainnya belum dilakukan.

Gunakan [source_links.csv](../data/interim/gemini_pilot/gemini_grounding_pilot_01/source_links.csv) untuk tautan tujuan tanpa kolom redirect Google, atau [report.md](../data/interim/gemini_pilot/gemini_grounding_pilot_01/report.md) untuk ringkasan dan tautan yang bisa diklik. `sources.csv` tetap menyimpan `raw_url` sebagai jejak data dan kini menambahkan `source_url` sebagai kolom tujuan untuk digunakan. URL yang belum diketahui tidak diganti dengan tebakan atau tautan redirect. JSON respons asli tetap dipertahankan.

Mode `--resolve-missing-only` ditambahkan untuk mencoba ulang resolusi sumber tanpa URL tujuan, dengan riwayat hasil sebelumnya. Ekspor ulang dengan `--export-only` tidak memerlukan jaringan. Tiga belas tes lokal lulus, termasuk pengujian bahwa ekspor pembaca tidak memakai fallback redirect dan resolusi ulang tidak memanggil model. Pemeriksaan hasil aktual memastikan ekspor tautan dan laporan tidak memuat URL redirect Google.

## Pekerjaan berikutnya

### Catatan eksekusi dan perbaikan penyimpanan

Peneliti mulai menjalankan pilot Gemini pada 10 September 2026. Pasangan pertama untuk pertanyaan penyebab campak berhasil: kondisi A tanpa metadata grounding, kondisi B memiliki enam sumber yang terhubung ke sitasi dan berhasil diresolusi. Ini hasil satu pasangan, belum kesimpulan keseluruhan.

Eksekusi berikutnya mengalami Windows `PermissionError` saat mengganti JSON checkpoint `trial_28ddb36b5b4fc613c5db0ba7`. Respons Gemini sudah tersimpan; file sementara memiliki progres dua URL dibanding satu URL pada JSON lama. Progres sementara telah dipulihkan setelah kecocokan respons dan identitas trial diperiksa, dengan cadangan di `outputs/checkpoint_recovery/20260910T080615523953Z/`. Perbaikan penyimpanan menambahkan retry terbatas hanya untuk operasi penggantian file. Dua belas tes lokal lulus, termasuk simulasi lock sementara dan permanen. Ekspor lokal diperbarui tanpa pemanggilan Gemini tambahan; resume akan melanjutkan resolusi respons tersimpan.

1. Lengkapi manifest pengumpulan Trends dan pemetaan ekspor asli ke file terpilih; jangan mengasumsikan metadata yang tidak tersedia di CSV.
2. Tinjau metadata bahasa yang masih `unknown` bila diperlukan untuk tahap berikutnya; pemeriksaan makna `icd 10` telah selesai.
3. Tinjau hasil pilot PAA dan evaluasi konfigurasi sebelum membekukan prosedur pengumpulan utama; konfigurasi batch pilot sudah disimpan.
4. Seleksi 52 pertanyaan PAA yang telah dikumpulkan berdasarkan bahasa, cakupan, kejelasan intent, dan duplikasi. Pertahankan hubungan ke `topic_id` Trends. Tambahkan batch hanya setelah mempertimbangkan sisa kuota; 15 dari 183 topik sudah dicoba.
5. Susun rubrik dan prompt penilai Judgment pertama, lalu susun, nilai, dan revisi prompt sintesis sebelum dipakai.
6. Uji sintesis pada batch kecil dari sumber siap sintesis dan PAA yang telah diterima. Pertahankan makna sumber, terjemahkan sesuai aturan, dan hindari tambahan fakta atau batasan.
7. Lanjutkan pemeriksaan deterministik, Judgment kedua, dan audit manual.
8. Setelah instrumen siap, lanjutkan pilot/pengumpulan Google dan Gemini, resolusi URL langsung, crawling artikel, label, dan fitur untuk dataset awal bimbingan.

Jumlah pengulangan Gemini, ambang kelayakan grounding, ambang keterkutipan, dan definisi fitur final masih perlu dibekukan sesuai CONTEXT.md. Status `ready_for_synthesis` belum berarti query final atau lolos grounding.
