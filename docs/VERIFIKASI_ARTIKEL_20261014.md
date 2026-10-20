# Verifikasi artikel utama — 14 Oktober 2026

## Cakupan dan metode

Audit yang dimulai 13 Oktober dan diselesaikan 14 Oktober menilai **598 ID artikel baru** menggunakan [rubrik kelayakan artikel](RUBRIK_SELEKSI_ARTIKEL.md), versi `article_eligibility_20261006_v1`. Kandidat berasal dari artikel Google Top 10, termasuk irisan dengan Gemini, yang sudah berhasil diunduh dan memiliki teks minimal 100 kata tetapi belum memiliki keputusan manual. Snapshot mencakup batch 1–7; kandidat baru pertama kali ditemukan pada batch 6 (130 ID) dan batch 7 (468 ID).

Status awal kandidat: 328 eligible_auto, 127 needs_language_review, 111 needs_page_type_review, 23 not_article, dan 9 non_indonesian otomatis. Dengan demikian, pemeriksaan mencakup keputusan otomatis yang belum ditinjau. Gemini-only tidak menjadi kandidat tersendiri; keputusan tetap diterapkan ketika ID artikel yang sama juga digunakan pada dataset tambahan.

Asisten LLM menilai judul serta cuplikan awal, tengah dan akhir setiap kandidat. Sebanyak **61 kasus** diperiksa melalui teks lebih panjang dan HTML lokal. Tiga versi teks berbeda diperiksa tersendiri: dua versi tetap merupakan artikel layak, sedangkan satu versi batch lama gagal HTTP dan tidak menjadi layak hanya karena salinan lain diterima. Penerapan memeriksa hash **612 salinan lintas batch**. Tiga koreksi keputusan selama audit dicatat dalam `decision_revisions.json`.

Penilaian memakai bahasa, jenis halaman, kecukupan isi, serta keutuhan/kebersihan ekstraksi. Label sitasi tidak ditampilkan dalam materi penilaian; otoritas sumber dan dugaan hasil penelitian tidak menentukan penerimaan. Penilaian tidak memeriksa kebenaran setiap klaim maupun relevansi setiap pasangan kueri-artikel, dan tidak diklaim sebagai pembacaan setiap kata atau verifikasi manusia independen.

## Hasil keputusan

**468 accepted, 80 excluded, dan 50 needs_extraction_review.** Seluruh **2.113 keputusan sebelumnya dipertahankan identik**, termasuk 164 kasus ekstraksi lama. Tabel aktif kini berisi **2.711 ID artikel**: 2.108 accepted, 389 excluded, dan 214 needs_extraction_review.

| Asal pertama kandidat | Accepted | Excluded | Needs extraction review |
| --- | ---: | ---: | ---: |
| main_06 | 99 | 17 | 14 |
| main_07 | 369 | 63 | 36 |

Contoh penerapan:

| Contoh | Keputusan | Alasan |
| --- | --- | --- |
| Artikel Alodokter dan Halodoc dengan istilah/referensi Inggris | accepted | Narasi utama Indonesia dengan pembahasan mandiri. |
| Dokumen analisis keuangan BCA di Scribd | accepted | Isi analisis dan kesimpulan tersedia; bukan hanya abstrak/metadata. |
| Kategori Lazada dan listing aplikasi Play Store | excluded | Fungsi halaman berupa katalog atau unduhan, bukan artikel. |
| Agregasi posting Lemon8 | excluded | Tidak memiliki satu badan artikel mandiri. |
| Artikel vertigo RS Pondok Indah | needs_extraction_review | Daftar gejala, penyebab dan penanganan ada di HTML tetapi hilang dari teks ekstraksi. |
| Tips KUR BRI Sinar Mas Land | needs_extraction_review | Teks berhenti pada tips ketiga; HTML masih memuat tips keempat, kelima dan penutup. |
| Artikel bersambung atau berita bercampur blok rekomendasi panjang | needs_extraction_review | Badan belum utuh atau teks lain dapat memengaruhi fitur. |

## Hasil build lokal

Batch 1, 2, 6 dan 7 dibangun ulang karena memakai ID dengan keputusan baru. Batch 3–5 tidak memerlukan build. Ekstraksi tersimpan diperiksa kesesuaiannya dengan teks, metadata, fitur dan HTML lokal sebelum digunakan kembali. Embedding tersimpan digunakan kembali dan yang belum tersedia dihitung lokal. BM25 dihitung ulang karena korpus artikel eligible berubah; memoisasi tokenisasi diperiksa menghasilkan skor yang sama. Kode ekstraktor produksi tidak diubah.

| Batch | Pasangan utama | Siap model sebelum | Masuk | Ditarik | Siap model sesudah |
| --- | ---: | ---: | ---: | ---: | ---: |
| main_01 | 325 | 181 | 0 | 0 | 181 |
| main_02 | 2.165 | 848 | 0 | 0 | 848 |
| main_03 | 571 | 215 | 0 | 0 | 215 |
| main_04 | 390 | 131 | 0 | 0 | 131 |
| main_05 | 777 | 340 | 0 | 0 | 340 |
| main_06 | 385 | 77 | 55 | 13 | 119 |
| main_07 | 896 | 286 | 126 | 30 | 382 |
| **Total** | **5.509** | **2.078** | **181** | **43** | **2.216** |

Hasil akhir adalah **2.216 pasangan siap model**, mencakup **2.047 ID artikel unik** dan **562 ID kueri**. Perubahan bersih +138 pasangan: 181 masuk dan 43 ditarik setelah peninjauan. Angka sebelum audit sudah mencakup scraping baru batch 6–7, sehingga berbeda dari laporan 11 Oktober.

| Domain | Siap model | Label 0 | Label 1 |
| --- | ---: | ---: | ---: |
| kesehatan | 954 | 803 | 151 |
| keuangan | 794 | 650 | 144 |
| teknologi | 468 | 366 | 102 |

Model-ready merupakan subset dari **5.509 pasangan utama**. Sebanyak **3.293 pasangan utama belum siap**. Dataset tambahan tetap terpisah, berisi **1.565 pasangan Gemini-only**. Baris pasangan bukan jumlah URL unik: satu artikel dapat dipakai oleh beberapa kueri.

## Pekerjaan yang masih tersisa

Pada snapshot ini, **tidak ada lagi artikel utama yang berhasil diunduh dengan teks minimal 100 kata tetapi belum mempunyai keputusan**. Antrean needs_language_review/needs_page_type_review pada pasangan utama tersisa **0**. Seluruh baris model-ready menggunakan artikel accepted.

Masih ada **225 pasangan dari 214 ID artikel** dalam antrean ekstraksi, termasuk kasus lama. Kasus ini sudah dinilai tetapi belum dapat diterima sebelum teks diperbaiki dan ditinjau ulang. Daftar tersedia pada [needs_extraction_review.csv](../outputs/article_verification_20261013/needs_extraction_review.csv); kolom `is_new_decision` menandai kasus baru.

Kegagalan crawling, teks kosong/pendek, artikel excluded, ketidakpastian label/pencocokan URL dan alias tetap disimpan. Sebanyak **14 pasangan dari artikel accepted baru** masih tertahan oleh pemeriksaan pasangan. Berkas `technical_blockers.json` menyimpan 2.532 kemunculan lintas batch yang tidak masuk penyaringan isi saat snapshot; ini bukan hitungan artikel unik atau pasangan.

Model-ready juga tidak berarti semua fitur terisi. Ada **554 baris** dengan setidaknya satu fitur kosong: mean_paragraph_word_count: 22, publication_age_days: 541. Jumlah per fitur dapat beririsan. Nilai tidak direkayasa; imputasi, jika digunakan, dipelajari hanya dari bagian data latih.

## Validasi dan berkas

Validasi memastikan keputusan lama identik; hash teks dan penerapan keputusan cocok; seluruh ID pasangan, observasi percobaan, sitasi, proporsi dan label tetap; model-ready sama persis dengan subset siap model pada dataset utama; dan semua perubahan keanggotaan dapat ditelusuri ke keputusan audit ini. Sebanyak **12.841 berkas konfigurasi/checkpoint JSON** juga identik menurut hash sebelum dan sesudah.

- [Keputusan aktif beserta alasan](../data/manual/article_review.csv).
- [Audit 598 artikel beserta cuplikan, hash dan reviewer](../outputs/article_verification_20261013/review_audit.csv).
- [Perubahan keanggotaan model-ready](../outputs/article_verification_20261013/membership_changes.csv).
- [Validasi](../outputs/article_verification_20261013/validation_report.json) dan [sensus akhir](../outputs/article_verification_20261013/final_census.json).
- Hasil dataset: `data/processed/articles_main_01/` sampai `articles_main_07/`; lihat `dataset.csv`, `model_ready.csv`, `articles.csv`, dan `dataset_gemini_only.csv`.
- Backup, keputusan per kandidat, pemeriksaan versi, log build dan skrip audit lokal: `outputs/article_verification_20261013/`. Nama folder mengikuti tanggal mulai audit.

Proses memakai **0 panggilan Gemini dan 0 pencarian SerpApi**, tanpa scraping baru. Seleksi dilakukan oleh asisten LLM dalam sesi Codex; belum ada pengujian kesepakatan antarpenilai dalam audit ini. Hasil crawling/build yang ditambahkan setelah snapshot perlu masuk putaran verifikasi berikutnya.
