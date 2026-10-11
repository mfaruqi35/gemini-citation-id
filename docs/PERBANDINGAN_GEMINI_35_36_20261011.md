# Perbandingan awal respons Gemini 3.5 dan 3.6 Flash

Perbandingan ini menggunakan ekspor pengumpulan **main_04** dan **main_05** yang tersimpan pada 11 Oktober 2026. [Catatan rilis Google](https://ai.google.dev/gemini-api/docs/changelog) menyatakan bahwa permintaan ke `gemini-3.5-flash` dialihkan ke `gemini-3.6-flash`. Metadata respons lokal mencatat `gemini-3.5-flash` pada seluruh 135 percobaan main_04 dan `gemini-3.6-flash` pada seluruh 270 percobaan main_05, walaupun konfigurasi main_05 masih meminta nama model lama.

Batch 4 dan 5 dipilih karena keduanya memiliki jumlah query yang seimbang di tiga domain: 15 per domain pada main_04 (45 query) dan 30 per domain pada main_05 (90 query). Semua query yang dibandingkan telah selesai, mempunyai hasil Google, dan minimal dua respons Gemini valid. Main_04 memiliki 134/135 percobaan valid; main_05 memiliki 270/270. Unit analisis adalah **query**, sehingga tiga percobaan dan seluruh URL dari satu query tidak dihitung sebagai observasi yang saling bebas.

| Ukuran, rata-rata per query | Gemini 3.5, main_04 | Gemini 3.6, main_05 | Selisih 3.6 − 3.5 | Interval bootstrap 95% | Uji permutasi |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sumber yang benar-benar disitasi per percobaan valid | 11,00 | 8,42 | −2,58 | [−3,64; −1,50] | p < 0,001 |
| Bagian Google Top 10 yang pernah muncul dalam sitasi Gemini | 10,56% | 13,28% | +2,72 poin persentase | [−4,08; +9,19] poin | p = 0,472 |
| Bagian sitasi unik yang berada di luar Google Top 10 | 94,83% | 91,78% | −3,05 poin persentase | [−6,78; +0,88] poin | p = 0,192 |
| Bagian pasangan Top 10 berlabel positif di antara pasangan yang pencocokan URL-nya pasti | 11,58% | 7,70% | −3,44 poin persentase | [−10,83; +3,11] poin | p = 0,323 |

Label positif mengikuti aturan penelitian, yaitu artikel dikutip pada **≥0,5** dari percobaan valid. Denominator label positif terbatas pada pasangan dengan `label_status=labeled_candidate`; jumlahnya 319 di main_04 dan 751 di main_05. Terdapat 71 dan 26 pasangan `url_matching_uncertain` yang tidak diberi label pasti. Oleh karena itu, proporsi label positif tidak boleh disamakan dengan proporsi artikel yang *pernah* disitasi.

Jumlah sumber yang disitasi per jawaban turun sekitar **23%** dan selisihnya tampak kuat pada uji eksploratif. Rata-rata jumlah pencarian grounding per respons valid juga turun dari sekitar **2,73** menjadi **1,87**, sedangkan token keluaran rata-rata turun dari **979** menjadi **757**. Dua perubahan terakhir hanya deskriptif; hubungan sebab akibatnya belum diuji. Keberhasilan grounding tetap tinggi pada kedua batch.

Selisih irisan Top 10 secara keseluruhan kecil dibanding variasi antarkueri. Bahkan arah perubahan per domain tidak sama:

| Domain | Irisan Top 10 main_04 | Irisan Top 10 main_05 |
| --- | ---: | ---: |
| Kesehatan | 19,63% | 8,01% |
| Keuangan | 6,02% | 16,08% |
| Teknologi | 6,02% | 15,74% |

Angka dalam tabel domain adalah rerata proporsi per query. Batch memakai **query yang berbeda** dan dikumpulkan pada waktu yang berbeda; versi model berimpit dengan identitas batch. Uji permutasi menjaga komposisi domain dan bootstrap mengambil ulang query di dalam tiap domain, tetapi keduanya tidak dapat memisahkan pengaruh versi model dari perbedaan topik/hasil Google. Nilai p bersifat eksploratif untuk empat ukuran yang dibandingkan, bukan bukti kausal bahwa pergantian model mengubah kecenderungan sitasi Top 10.

Untuk analisis penelitian, simpan `model_version` yang dikembalikan API per percobaan dan laporkan hasil per versi. Periksa kepekaan kesimpulan model klasifikasi terhadap pemisahan batch/versi, karena label dan komposisi query dapat berubah bersama. Jangan menamai seluruh korpus sebagai satu versi Gemini.

Perhitungan dapat diulang tanpa panggilan API:

```powershell
python outputs/model_version_comparison_20261011/analyze.py
```

Skrip membaca ekspor `queries.csv`, `trials.csv`, `sources.csv`, `query_article_pairs.csv`, dan `query_article_pairs_union.csv`. Hasil rinci per query tersimpan di `outputs/model_version_comparison_20261011/per_query.csv` dan ringkasan beserta interval/uji di `summary.json`. Uji permutasi dua sisi memakai 20.000 pengacakan berstrata domain; interval persentil memakai 5.000 pengambilan ulang berstrata, seed `20261011`. Pemeriksaan silang memastikan jumlah `is_cited=True` di `sources.csv` sesuai `n_cited_sources` untuk semua respons selesai pada kedua batch.
