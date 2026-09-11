# Progres penelitian

Terakhir diperbarui: **10 September 2026**.

## Pembaruan terbaru: jalur query asli tanpa sintesis

Rancangan dilanjutkan menggunakan query asli Trends/PAA, tanpa sintesis LLM. Untuk batch awal, teks berbahasa Inggris dipisahkan tanpa diterjemahkan. [Protokol terbaru](MAIN_DATASET.md#query-asli) dan catatan di awal CONTEXT.md menggantikan tahapan sintesis yang masih muncul sebagai riwayat dalam dokumen ini.

[prepare_original_queries.py](../src/prepare_original_queries.py) dan [notebook 03](../notebooks/03_review_original_queries.ipynb) telah dijalankan secara lokal. Dari 52 pertanyaan PAA dan 26 sumber Trends yang sebelumnya dianggap cukup spesifik, tersedia **49 kandidat berbahasa Indonesia**: 17 kesehatan, 20 keuangan, 12 teknologi. Sumber tersebut terdiri dari 48 PAA dan satu Trends. **29 sumber Inggris** diarsipkan sebagai ditunda, tanpa parafrasa atau terjemahan. Seluruh teks hasil telah diperiksa identik dengan sumbernya.

CSV kandidat berada di `data/interim/original_queries/candidates_id.csv`. Semua kandidat masih `pending` untuk penilaian kualitas; ini belum 49 query final atau pasangan query–artikel. Notebook menerima keputusan memakai teks query, menyimpan progres ke `data/manual/original_query_decisions.csv`, dan mengekspor query yang diterima. Tidak ada API atau kuota tambahan yang digunakan.

**Pekerjaan terdekat:** seleksi kualitas 49 kandidat, periksa duplikasi intent dan cakupan, lalu pilih batch untuk pengumpulan Google Top-10 dan Gemini. Sintesis dan Judgment prompt sintesis tidak lagi menjadi prasyarat jalur ini; rencana lama di bawah dibaca sebagai riwayat.

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

Catatan rencana lama di atas telah diperbarui oleh protokol query asli dan pengumpulan utama di bawah. Status `ready_for_synthesis` tetap merupakan nama historis, bukan proses sintesis yang dijalankan saat ini.

## Dataset utama: tiga percobaan, minimal dua valid

Peneliti memilih melanjutkan langsung dataset utama tanpa sintesis LLM dan menetapkan tiga percobaan Gemini per query dengan minimal dua valid. [MAIN_DATASET.md](MAIN_DATASET.md) menjadi pedoman terbaru; langkah sintesis/pilot tambahan dalam catatan historis tidak lagi berlaku.

Seleksi awal asisten pada 49 kandidat Indonesia menghasilkan 41 accepted, tujuh needs_review, dan satu excluded. Batch `main_01` berisi 15 kesehatan, 14 keuangan, dan 12 teknologi dengan maksimal 41 pencarian Google organik dan 123 panggilan Gemini. Akun SerpApi aktif terverifikasi memiliki kuota 250 sebelum pengumpulan dimulai. Respons pilot tidak digunakan ulang sebagai respons utama.

Skrip `src/collect_main_dataset.py` menggunakan checkpoint, pembekuan manifest, batas kuota, serta ekspor query, percobaan, sumber, hasil Google, dan pasangan kandidat. Minimum valid mengacu pada respons STOP dengan teks dan sitasi web pada metadata. Resolusi gagal menjadi ketidakpastian pencocokan, bukan label negatif. Ambang biner belum ditetapkan; crawling artikel dan ekstraksi fitur merupakan tahap selanjutnya. Sebanyak 21 tes lokal lulus tanpa API, termasuk tiga percobaan/dua valid, resume, error, kuota, dan penanganan URL.

Pengumpulan nyata sudah dimulai. Snapshot awal setelah tiga query selesai: sembilan percobaan, 24 pasangan kandidat, dua query memenuhi minimal dua valid. Satu query keuangan mengalami `MAX_TOKENS` pada ketiga percobaan dan belum layak dilabeli; ini kegagalan penyelesaian respons, bukan bukti tidak adanya sitasi. Progres berikutnya dapat dilihat di notebook 04, yang seluruh selnya telah diperiksa dengan hasil lokal tanpa API. Data pasangan masih memerlukan crawling, seleksi artikel, fitur, dan pelabelan.

## Penambahan query dari kuota tersedia

Batch `paa_expansion_01` menyelesaikan 30 pencarian dari 30 topik Trends baru (10 per domain), menghasilkan 96 PAA dan enam hasil tanpa PAA. Ditambah 96 kemunculan PAA dari respons utama tersimpan, snapshot berisi 192 kemunculan, 188 query unik berdasarkan domain/teks, dan 183 kandidat tambahan setelah lima query lama dipisahkan. Seleksi awal asisten menerima 123, menunda 29, dan mengeluarkan 31. Daftar diterima tambahan tersimpan terpisah; 41 query utama pertama tetap dipertahankan. Total daftar diterima awal + tambahan adalah 164, belum seluruhnya dikumpulkan Google/Gemini.

Sisa kuota SerpApi pada snapshot setelah pengumpulan PAA adalah 197. Pipeline lokal `prepare_query_expansion.py` dan notebook 05 dapat mengekstrak PAA berikutnya tanpa API sambil mempertahankan keputusan lama, teks asli, hubungan induk, kedalaman PAA, dan asal topik Trends. Sebanyak 24 tes lokal lulus. Panduan serta alasan seleksi ada di [QUERY_EXPANSION.md](MAIN_DATASET.md#penambahan-query).

Saat pemeriksaan ini, proses pengumpulan Gemini utama telah berhenti akibat HTTP 429 pada percobaan kedua query `Fungsi Excel apa saja?`. Checkpoint tersimpan dan penambahan query tidak menggunakan Gemini. Status ini memperbarui laporan sebelumnya bahwa pengumpulan masih berjalan.

## Gabungan Google Top-10 dan semua sitasi Gemini

Sesuai permintaan peneliti, ekspor pasangan kini juga menghasilkan `query_article_pairs_union.csv`, gabungan hasil organik Google dan seluruh URL tujuan yang disitasi pada percobaan Gemini valid. Metadata sitasi lengkap sebenarnya sudah disimpan; pembatasan sebelumnya terletak pada himpunan kandidat pasangan Google. URL berulang per query digabung dan sitasi dihitung sekali per percobaan, sementara sumber tidak valid/belum teresolusi tetap diarsipkan.

Ekspor lokal tanpa API menghasilkan 554 pasangan gabungan (515 URL kandidat unik), dibanding 202 pasangan Google. Asalnya: 132 Google saja, 70 keduanya, 352 Gemini saja. Contoh query batuk memiliki 21 kandidat gabungan dari sembilan Google dan 15 URL sitasi, dengan tiga URL beririsan. Ini kandidat sebelum crawling dan seleksi halaman. Notebook 04 kini menampilkan tabel gabungan. Dua puluh delapan tes lokal lulus, termasuk semua sumber sitasi, deduplikasi per percobaan, respons tidak valid, dan URL belum diketahui. Protokol serta implikasi sampling tercatat di [CANDIDATE_UNION.md](MAIN_DATASET.md#gabungan-kandidat).

## Pemeriksaan dan kelanjutan 11 September 2026

Implementasi gabungan kandidat, notebook 04, dan dokumentasi telah selesai. Sesuai permintaan untuk melanjutkan, satu panggilan Gemini baru dikirim pada slot ketiga query `Fungsi Excel apa saja?`; API kembali mengembalikan HTTP 429 dengan status `RESOURCE_EXHAUSTED`. Tidak ada pencarian organik Google baru pada percobaan melanjutkan ini. API tidak memberikan rincian quota metric atau retry delay pada respons yang diterima, sehingga jenis batas (per menit/per hari/batas lain) belum dapat dipastikan.

Ketiga slot query Excel sudah tercatat (satu respons valid, dua error 429); tidak ada percobaan keempat. Checkpoint dituntaskan secara lokal tanpa API. Jeda Google dan percobaan terakhir juga telah melampaui enam jam, sehingga query ini belum layak. Snapshot terbaru: 24 dari 41 query selesai diproses, 21 memenuhi minimal dua valid, 17 belum dimulai, dan 72 catatan percobaan. Tabel gabungan tetap 554 pasangan/515 URL kandidat unik. Selesai diproses tidak berarti semuanya berhasil atau siap pemodelan.

Penyimpanan error ditambah dengan rincian kuota yang diizinkan bila tersedia (status, quota metric/ID/value, retry delay), tanpa URL permintaan, API key, pesan provider bebas, atau identitas akun/proyek. Error pada slot terakhir kini langsung menuntaskan status query agar resume tidak menganggapnya masih memerlukan percobaan. Sebanyak 31 tes lokal lulus. Pengumpulan berhenti setelah 429; periksa batas akun Gemini sebelum mencoba 17 query berikutnya. [Dokumentasi batas Gemini](https://ai.google.dev/gemini-api/docs/rate-limits) membedakan batas per menit, token, dan per hari; pergantian tanggal WIB tidak cukup untuk menyimpulkan kuota sudah reset.

## Pemulihan pencarian SerpApi yang terputus

Setelah peneliti melanjutkan, pencarian `vitamin C untuk apa fungsinya?` tercatat gagal koneksi tanpa respons lokal, sementara akun SerpApi menunjukkan 55/250 terpakai. Account API berhasil diakses dan menunjukkan 195 tersisa. Pemulihan satu permintaan identik berhasil mendapatkan respons Google tersimpan, dengan delapan hasil organik. Metadata mencatat waktu pemrosesan 52,49 detik, melampaui batas tunggu lama 45 detik; ini mendukung diagnosis timeout, meski jenis exception asli tidak tersimpan. Kuota sebelum/sesudah pemulihan tetap 55 terpakai dan 195 tersisa.

`collect_paa.fetch` kini menunggu hingga 120 detik, mengklasifikasikan error jaringan, dan tetap memverifikasi TLS tanpa retry otomatis. `recover_main_google.py` memungkinkan pemulihan eksplisit satu query Google gagal yang belum memiliki respons/percobaan Gemini, dengan riwayat checkpoint, pemeriksaan kuota, cache default, dan waktu pencarian asli. Respons yang sudah tersimpan tidak dikirim ulang. Sebanyak 36 tes lokal lulus. Checkpoint vitamin C sudah `response_saved` dengan nol panggilan Gemini selama pemulihan; perintah kolektor biasa dapat melanjutkannya. Ekspor setelah pemulihan berisi 210 pasangan Google dan 562 pasangan gabungan; 24 query selesai diproses, satu menunggu resolusi/Gemini, dan 16 belum dimulai.

## Pengumpulan main_01 selesai — 11 September 2026

Peneliti melanjutkan skrip dan seluruh 41 query kini selesai diproses. Seluruh pengambilan Google berstatus completed dan tidak ada lock proses aktif. Terdapat 123 catatan percobaan Gemini: 114 valid (STOP dengan sitasi), tujuh selesai dengan MAX_TOKENS, dan dua error 429 yang tetap dipertahankan. Sebanyak 38 query memenuhi minimal dua valid dan jendela waktu pengumpulan.

Hasil Google berisi 348 kemunculan organik. Gabungan Google dan sitasi valid menghasilkan **983 pasangan query–artikel dengan 903 URL kandidat unik**: 216 Google saja, 132 keduanya, dan 635 Gemini saja. Tabel sumber memiliki 1.360 kemunculan; 21 kemunculan sitasi belum memiliki URL tujuan. Angka URL unik berdasarkan normalisasi konservatif, belum membuktikan jumlah artikel unik/layak setelah crawling dan canonical.

Dari tabel gabungan, 942 pasangan berasal dari 38 query yang memenuhi syarat. Di dalamnya, 757 pasangan mempunyai proporsi pasti tetapi ambang label belum ditetapkan, dan 185 masih memiliki ketidakpastian pencocokan URL. Sebanyak 41 pasangan lain berasal dari tiga query belum layak: `Gaji 6 juta pajak berapa?` (nol valid), `Rumus apa saja di Excel?` (satu valid), dan `Fungsi Excel apa saja?` (satu valid serta jeda melebihi enam jam). Tiga query tersebut tetap diarsipkan.

Lihat notebook 04 dan `data/interim/main/main_01/queries.csv`, `query_article_pairs_union.csv`, serta `sources.csv`. Pengumpulan batch pertama selesai, sedangkan pengambilan isi artikel, seleksi halaman/bahasa, pencocokan URL lanjutan, keputusan ambang label, dan ekstraksi fitur masih diperlukan. Daftar 123 query tambahan tetap merupakan kandidat untuk batch berikutnya dan tidak tercakup dalam 41 query main_01 ini.


## 11 September 2026 ? perapian proyek dan rencana pengolahan artikel

- Menghapus sembilan cache `.pyc` dan empat panduan yang isinya telah digabungkan ke `docs/MAIN_DATASET.md` (protokol query asli, ekspansi query, gabungan kandidat, dan petunjuk penggabungan Trends dari `src/README.md`). Total 13 file dihapus; isi panduan dipertahankan dan tautannya diperbarui.
- Mengisi README utama sebagai pintu masuk proyek. Data penelitian, konfigurasi, notebook, checkpoint, serta cadangan pemulihan dipertahankan. Modul pilot tetap diperlukan oleh kolektor utama.
- Verifikasi: 36 pengujian unit lulus; tidak menjalankan pengumpulan API nyata atau menulis kode pipeline baru.
- Prioritas berikut: unduh isi URL unik dengan checkpoint, tinjau kelayakan artikel, periksa alias/canonical dan pencocokan sitasi yang belum pasti, tetapkan ambang label sebelum pemodelan, lalu ekstrak fitur dan bentuk dataset siap pakai. Halaman gagal diakses tidak otomatis menjadi label negatif.
- Pemisahan peran: Python untuk crawling, ekstraksi, pencocokan, serta ekspor yang dapat dilanjutkan; Jupyter untuk review artikel, distribusi domain/label, dan pemeriksaan kualitas.
- Anggaran yang dilaporkan pengguna: Gemini Rp82.000; SerpApi 71/250 (diasumsikan 71 terpakai, sehingga tersisa 179). Pengambilan halaman langsung tidak memakai panggilan Gemini/SerpApi. Setelah jumlah artikel layak diketahui, pertimbangkan batch baru 15?30 query dari kandidat tambahan yang tersedia: maksimal 15?30 pencarian Google dan 45?90 percobaan Gemini. Periksa biaya aktual per blok kecil sebelum melanjutkan; belum ada pengeluaran baru yang dilakukan.
