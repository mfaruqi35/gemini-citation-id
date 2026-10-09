# Verifikasi artikel Google Top 10, 6 Oktober 2026

Verifikasi ini mencakup artikel yang telah di-crawl dan muncul pada dataset utama Google Top 10, dengan status awal `needs_language_review`, `needs_page_type_review`, atau `needs_extraction_review`. Cakupannya adalah **218 artikel unik / 237 pasangan query–artikel** dari dua batch. Artikel yang hanya berada pada dataset tambahan Gemini-only tidak menjadi sampel model utama dan tidak termasuk antrean ini.

Keputusan dibuat melalui pemeriksaan berbantuan LLM atas teks hasil ekstraksi, judul, jenis halaman, bagian awal/tengah/akhir, dan HTML lokal bila ekstraksi diragukan. Ini **bukan verifikasi manual independen oleh peneliti** dan bukan pemeriksaan kebenaran medis, keuangan, atau teknis setiap klaim. Label sitasi tidak dipakai untuk menentukan kelayakan artikel. Artikel/panduan informasional berbahasa Indonesia diterima bila badan teksnya substantif dan cukup utuh; katalog, listing/tag, halaman alat atau promosi tanpa uraian mandiri, dan pratinjau dokumen yang tidak lengkap dikeluarkan atau ditahan sesuai bukti.

| Domain | Artikel ditinjau | Diterima | Dikecualikan | Perlu perbaikan ekstraksi |
| --- | ---: | ---: | ---: | ---: |
| Kesehatan | 96 | 91 | 5 | 0 |
| Keuangan | 66 | 44 | 20 | 2 |
| Teknologi | 56 | 28 | 25 | 3 |
| **Total** | **218** | **163** | **50** | **5** |

Audit per artikel tersimpan di `outputs/article_verification_20261006/{kesehatan,keuangan,teknologi}.csv`: ID, URL, judul, keputusan, bahasa, alasan, cuplikan bukti, penilai, dan tanggal. `scope.json` menyimpan hash dua dataset sebelum review; `article_review_before_20261006.csv` adalah cadangan keputusan aktif sebelumnya; `merge_report.json` merangkum penggabungan. Keputusan aktif ada di `data/manual/article_review.csv` dengan `reviewer=llm_assistant_article_review`. Dua keputusan lama `needs_extraction_review` untuk Cobisnis dan JDIH Sukoharjo tetap dipertahankan beserta identitas penilai semula.

Dua artikel Hello Sehat sebelumnya hanya mengekstrak daftar referensi Inggris. HTML lokal ternyata memuat badan artikel Indonesia. Selektor khusus `.unique-content-wrapper` pada ekstraktor memulihkan badan artikel tentang obat batuk alami (1.762 kata) dan paracetamol saat hamil (632 kata), lalu keduanya diterima. Bukti sebelum/sesudah, hash HTML, dan cuplikan awal/akhir teks tercatat pada `outputs/article_verification_20261006/hellosehat_extraction_recovery.csv`. Perbaikan ini juga berlaku pada halaman Hello Sehat lain; build ulang menghitung ulang fitur tekstual dan BM25 sesuai korpus yang diperbarui.

Dua halaman tambahan dipulihkan dari HTML lokal: Rumah Ginjal memakai selector `.g-font-size-16.g-line-height-1_8.g-mb-30` (817 kata, daftar kata kunci dikeluarkan), dan AXA Mandiri memakai `.box-full-content.font-opensans` (1.582 kata, kartu artikel/footer dikeluarkan). Dua paragraf promosi yang merupakan bagian penutup artikel AXA tetap dipertahankan. Masing-masing host hanya memiliki satu contoh HTML lokal, sehingga konsistensi selector pada halaman lain belum diuji. Bukti disimpan di `outputs/article_verification_20261006/additional_extraction_recovery.json`.

Lima artikel masih ditahan dengan `needs_extraction_review`:

| Domain | Artikel / ID | Hambatan |
| --- | --- | --- |
| Keuangan | JDIH Sukoharjo: pencairan BPJS Ketenagakerjaan (`article_3412cae508eb697d3d877a65`) | Salinan lokal berhenti di tengah panduan JMO. |
| Keuangan | Cobisnis: cek NIK/NPWP (`article_7645f726765d12492fc9fcf4`) | Teks masih memuat deretan tautan spam dari HTML. |
| Teknologi | Azure: pengertian VPN (`article_44845bed22d24b7a930900c6`) | Ekstraksi melewatkan beberapa bagian utama yang ada pada HTML. |
| Teknologi | Microsoft Support: pengertian Excel (`article_68522548da40d4595f0ab2ed`) | Teks terpotong di tengah instruksi. |
| Teknologi | Scribd: panduan Excel Android (`article_e974ad09002eed1dd9540136`) | Hanya pratinjau sebagian dokumen yang tersedia. |

Status tersebut tidak boleh diganti menjadi `accepted` hanya dari judul atau niat halaman. Perlu pemulihan ekstraksi yang terbukti, atau keputusan pengecualian bila salinan utuh tidak tersedia. Baris gagal crawling, `too_short`, dan `not_extracted` di luar antrean review ini tetap mengikuti status teknisnya. Pencocokan URL/sitasi yang tidak pasti juga memerlukan audit tersendiri; keputusan artikel tidak otomatis memperbaiki label.

Kedua build selesai dengan embedding lokal: `main_01/model_ready.csv` bertambah dari 153 menjadi 186 pasangan, dan `main_02/model_ready.csv` dari 308 menjadi 453 pasangan. Total **639 pasangan model-ready**, bertambah **178**. Dari 179 pasangan yang artikelnya diterima dalam review ini, satu masih ditahan oleh `url_matching_uncertain` (`article_f50dcb328ae89b892c5d25f1`). Lima pasangan tetap membutuhkan perbaikan ekstraksi.

Tidak ada lagi status review bahasa/jenis halaman pada dataset utama. Sebanyak 586 dari 1.225 pasangan utama masih belum model-ready karena beragam hambatan teknis/kelayakan; jumlah ini tidak sama dengan antrean verifikasi. Pada 191 pasangan model-ready, usia publikasi masih kosong dan memerlukan penanganan nilai hilang dalam pipeline model.

**13 tes ekstraktor lulus**. Pemeriksaan sebelum/sesudah membuktikan ID pasangan, label, `n_cited`, dan `n_valid` seluruh 1.225 pasangan utama tetap sama. Laporan angka dan pemeriksaan ada di `outputs/article_verification_20261006/build_validation.json` serta `docs/PROGRESS.md`. Tidak ada pemanggilan SerpApi atau Gemini untuk verifikasi/build ini.
