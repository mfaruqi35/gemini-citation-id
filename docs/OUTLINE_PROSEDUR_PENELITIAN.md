# Outline Bab Metodologi: Prosedur Penelitian

Disusun: 19 September 2026.

Dokumen ini khusus untuk subbab **Prosedur Penelitian**. Nomor subbab dapat disesuaikan dengan struktur laporan. Flowchart disimpan terpisah di [FLOWCHART_PROSEDUR_PENELITIAN.md](FLOWCHART_PROSEDUR_PENELITIAN.md).

## Kedudukan rancangan

Penelitian bertujuan memprediksi keterkutipan artikel web berbahasa Indonesia oleh Gemini API dengan Google Search Grounding, membandingkan XGBoost dengan Logistic Regression dan Random Forest, serta menganalisis kontribusi fitur menggunakan SHAP dan ablation study.

Rancangan aktif menggunakan query asli dari Google Trends dan People Also Ask (PAA), tanpa sintesis atau parafrasa query oleh LLM. Dataset pemodelan utama dibatasi pada pasangan query–artikel dari hasil organik Google Top 10. Artikel yang disitasi Gemini di luar Top 10 disimpan sebagai dataset tambahan.

Pengumpulan dan pembentukan dataset sudah dilakukan secara bertahap. Pemodelan, evaluasi, SHAP, dan ablation study di bawah adalah **rencana tahap berikutnya**, bukan kegiatan yang sudah selesai. Jumlah data akhir, jumlah fold, dan hiperparameter final perlu diisi setelah ditetapkan. Angka progres sementara tidak diperlakukan sebagai ukuran dataset final.

## 1. Penetapan rancangan dan protokol penelitian

Menetapkan tujuan, cakupan, unit analisis, dan aturan operasional pengumpulan data.

- Cakupan domain: kesehatan, keuangan, dan teknologi.
- Unit analisis: satu pasangan query–artikel. Artikel yang sama dapat berhubungan dengan beberapa query.
- Sumber kandidat utama: hasil organik Google posisi 1–10 untuk query yang diterima.
- Pengamatan keterkutipan: tiga slot percobaan Gemini per query, dengan minimal dua percobaan valid.
- Ambang label positif: proporsi keterkutipan ≥0,5.
- Batas operasional waktu pengumpulan Google dan Gemini: enam jam per query.
- Protokol mencatat model, prompt, parameter pencarian, versi konfigurasi, serta aturan kelayakan artikel.

Uji teknis awal digunakan untuk memeriksa pengumpulan, grounding, dan penyimpanan respons sebelum protokol utama diterapkan. Respons pilot tidak digabungkan dengan percobaan utama.

**Keluaran:** protokol pengumpulan dan definisi operasional yang terdokumentasi.

## 2. Pengumpulan kata kunci dari Google Trends

Mengumpulkan kata kunci Google Trends dengan wilayah Indonesia, periode satu tahun terakhir, serta kategori kesehatan, keuangan, dan komputer & elektronik, tanpa memasukkan kata kunci awal.

Daftar Top dan Rising dari ketiga kategori diunduh menjadi enam CSV, kemudian digabungkan dengan mempertahankan kategori, jenis daftar, periode, dan sumber berkas. Kata kunci diseleksi berdasarkan kesesuaiannya dengan domain penelitian. Berkas asli dan hasil seleksi disimpan terpisah agar perubahan dapat ditelusuri.

**Keluaran:** daftar kata kunci sumber yang diterima beserta asal dan keputusan seleksinya.

## 3. Pengumpulan dan seleksi query People Also Ask

Menggunakan kata kunci Trends yang diterima untuk mengambil pertanyaan PAA melalui SerpApi. Pertanyaan tambahan dapat diekstrak dari respons pencarian Google yang sudah tersimpan, dengan mempertahankan hubungan terhadap kata kunci atau query induknya.

Seleksi mempertimbangkan:

- Kejelasan kebutuhan informasi tanpa menebak konteks yang tidak tersedia.
- Kesesuaian dengan domain penelitian.
- Penggunaan bahasa Indonesia.
- Kebutuhan informasi yang dapat dijawab melalui artikel.
- Duplikasi teks atau pengulangan intent yang tidak diperlukan.

Keputusan akhir dicatat sebagai `accepted` atau `excluded`, beserta alasan. Teks sumber dipertahankan tanpa sintesis, penerjemahan, atau parafrasa diam-diam. Bantuan asisten LLM dalam seleksi dilaporkan sebagai **penilaian berbantuan LLM**, dengan keputusan yang dapat ditinjau peneliti; tidak disebut penilaian manusia independen. Query tidak diterima atau ditolak berdasarkan dugaan keberhasilan sitasi Gemini.

**Keluaran:** daftar query accepted dengan jejak sumber dan keputusan seleksi.

## 4. Pengumpulan hasil Google Search dan respons Gemini

Setiap query accepted digunakan untuk mengambil hasil organik Google posisi 1–10 melalui SerpApi. Apabila respons menyediakan kurang dari sepuluh hasil, jumlah sebenarnya dicatat tanpa penggantian kandidat secara diam-diam.

Query yang sama diberikan kepada Gemini sebanyak tiga slot percobaan menggunakan Google Search Grounding dan instruksi pencarian serta sitasi yang dibekukan. Model, prompt, parameter, waktu pengumpulan, respons mentah, dan penggunaan token disimpan.

Pengumpulan berjalan bertahap dengan checkpoint. Kegagalan jaringan dapat dipulihkan melalui recovery eksplisit, maksimal satu retry per slot sesuai implementasi saat ini. Riwayat kegagalan dipertahankan, respons berhasil tidak diulang, dan waktu retry dicatat sebagai waktu percobaan aktif. Retry transport tidak menjadi ulangan tambahan dalam perhitungan proporsi sitasi.

**Keluaran:** tabel hasil Google, percobaan Gemini, sumber sitasi, dan respons mentah yang dapat diaudit.

## 5. Validasi percobaan dan pencocokan URL sitasi

Percobaan Gemini dinyatakan valid apabila respons selesai dengan `finishReason=STOP`, memiliki teks jawaban, dan metadata `groundingSupports` menghubungkan sitasi dengan setidaknya satu sumber web. Definisi ini menunjukkan grounding yang dapat diamati, bukan menjamin kebenaran seluruh jawaban.

Query memenuhi syarat jumlah percobaan jika memiliki minimal dua percobaan valid. Waktu pengumpulan diperiksa terhadap batas operasional enam jam. Batas tersebut merupakan keputusan protokol penelitian, bukan ketentuan ilmiah universal.

URL redirect Gemini diresolusikan ke URL tujuan, lalu dinormalisasi secara konservatif dan dibandingkan dengan kandidat Google. URL mentah, URL tujuan, serta status resolusi tetap disimpan. Ketidakpastian pencocokan tidak langsung diubah menjadi label negatif. Alias URL diperiksa agar beberapa alamat untuk artikel yang sama tidak menyebabkan pencocokan yang keliru.

**Keluaran:** percobaan yang memenuhi syarat, sumber tersitasi yang dapat dicocokkan, dan catatan ketidakpastian.

## 6. Pembentukan kelompok kandidat dan label keterkutipan

Pasangan query–artikel dibagi berdasarkan sumbernya untuk query yang sama.

| Kelompok | Cakupan | Penggunaan |
| --- | --- | --- |
| Utama | Semua kandidat Google Top 10, termasuk yang disitasi Gemini | Pemodelan klasifikasi |
| Tambahan | URL yang disitasi Gemini tetapi tidak ditemukan dalam Google Top 10 | Analisis deskriptif tambahan |
| Gabungan | Union kandidat utama dan tambahan, tanpa menggandakan pasangan yang sama | Scraping dan audit |

Proporsi keterkutipan dihitung sebagai:

\[
p_{q,a}=\frac{\text{jumlah percobaan valid yang menyitasi artikel }a}{\text{jumlah percobaan valid untuk query }q}
\]

Label biner ditetapkan sebagai:

\[
y_{q,a}=\begin{cases}
1, & p_{q,a}\geq 0{,}5 \\
0, & p_{q,a}<0{,}5
\end{cases}
\]

Satu sitasi dari dua percobaan valid menghasilkan label 1; satu sitasi dari tiga percobaan valid menghasilkan label 0. Label 0 berarti tidak mencapai ambang keterkutipan, sehingga tidak selalu berarti tidak pernah disitasi. Label ditunda jika syarat query atau kepastian pencocokan URL belum terpenuhi.

**Keluaran:** pasangan kandidat beserta asal, jumlah percobaan valid, jumlah sitasi, proporsi, dan label.

## 7. Scraping dan pembersihan isi artikel

URL kandidat utama dan tambahan diakses langsung untuk mengambil HTML dan metadata. Pengambilan mencatat URL awal dan akhir, waktu, status HTTP, serta jenis kegagalan, dengan memperhatikan `robots.txt` dan pembatasan akses.

Isi utama diekstrak dengan membuang navigasi, iklan, footer, daftar artikel terkait, dan elemen lain di luar badan artikel. Ekstraktor disesuaikan jika struktur website menyebabkan isi tidak terbaca dengan benar. HTML asli disimpan terpisah dari teks hasil ekstraksi.

URL dideduplikasi dalam manifest scraping sambil mempertahankan seluruh hubungan query–artikel. Pada implementasi saat ini, checkpoint antar-ID dataset terpisah; penggunaan ulang otomatis HTML lintas batch belum tersedia. Karena itu duplikasi lintas batch juga diperiksa pada penyatuan dataset final.

**Keluaran:** HTML mentah, teks hasil ekstraksi, metadata, serta status pengambilan setiap URL.

## 8. Pemeriksaan kelayakan artikel dan ekstraksi fitur

Artikel diperiksa berdasarkan keberhasilan ekstraksi, bahasa, jenis halaman, dan kecukupan isi. Status ambigu ditinjau menggunakan teks hasil ekstraksi dan halaman sumber. Keputusan `accepted` atau `excluded` disimpan bersama alasan dan identitas penilai. Halaman tidak diterima hanya untuk meningkatkan jumlah data.

Fitur dikelompokkan sebagai berikut:

| Kelompok fitur | Contoh |
| --- | --- |
| Struktur dokumen | Jumlah kata, paragraf, heading, daftar, tabel, dan gambar |
| Kualitas penyajian konten | WPS, CPW, angka/statistik, kutipan, dan rujukan eksternal |
| Metadata dan otoritas domain | Keberadaan penulis/tanggal, umur artikel, serta level otoritas 1 atau 2 |
| Relevansi leksikal | Skor BM25 antara query dan artikel |
| Relevansi semantik | Kemiripan kosinus embedding query dan artikel |

Indikator kualitas konten adalah karakteristik terukur, bukan bukti langsung kebenaran informasi. WPS merupakan jumlah kata per kalimat dan CPW merupakan jumlah karakter per kata menurut definisi ekstraktor.

Otoritas domain menggunakan `domain_authority_level`: 2 untuk kategori tinggi sesuai rubrik institusi/suffix/daftar host dan 1 sebagai default. `credibility_evidence`, `credibility_reason`, basis aturan, dan versi aturan disimpan untuk audit, bukan sebagai prediktor.

Relevansi semantik memakai representasi query dan artikel dari model embedding yang terdokumentasi. Artikel panjang diproses dengan strategi potongan teks yang tetap. Model klasifikasi menerima skor kemiripan, bukan seluruh vektor embedding.

**Keluaran:** fitur artikel dan pasangan query–artikel, serta metadata audit yang terpisah dari fitur model.

## 9. Penyusunan dan pemeriksaan dataset siap pemodelan

Menggabungkan fitur, query, dan label, lalu memeriksa ID, hubungan antartabel, duplikasi, alias URL, nilai hilang, distribusi kelas, distribusi domain, dan alasan eksklusi.

| Berkas | Peran |
| --- | --- |
| `articles.csv` | Artikel, teks, fitur, dan status pengambilan |
| `dataset.csv` | Seluruh pasangan kandidat utama, termasuk yang belum layak |
| `dataset_gemini_only.csv` | Pasangan tambahan di luar Top 10 |
| `dataset_union.csv` | Arsip gabungan untuk audit |
| `model_ready.csv` | Subset kandidat utama yang lolos pemeriksaan pipeline |

Status siap-model menunjukkan kelulusan aturan pipeline, bukan otomatis verifikasi manual seluruh artikel. Pemeriksaan akhir peneliti dilakukan sebelum dataset final dibekukan. Jika menggunakan audit sampel, prosedur sampling dan batas cakupannya harus dijelaskan secara eksplisit.

Jumlah sitasi, proporsi sitasi, asal kandidat, metadata keputusan Gemini, dan informasi pembentuk label dikeluarkan dari prediktor. Dataset tambahan tidak digabungkan ke pelatihan utama. Distribusi kelas asli dipertahankan pada arsip, dan jumlah data yang dikeluarkan dilaporkan beserta alasannya.

**Keluaran:** snapshot dataset final, daftar prediktor, dan laporan kualitas data.

## 10. Pembagian data dan pelatihan model

Validasi silang direncanakan menggunakan kelompok query agar seluruh pasangan dari query yang sama berada pada fold yang sama. Artikel identik lintas query diperiksa; bila diperlukan, query yang terhubung melalui artikel yang sama ditempatkan dalam satu kelompok. Hubungan topik induk juga dipertimbangkan untuk menilai kemiripan antarkelompok.

Jumlah fold ditentukan setelah kecukupan kelompok dan kelas diketahui. Seluruh model menggunakan fold yang sama. Imputasi, penskalaan, penanganan ketidakseimbangan, dan pemilihan hiperparameter dipelajari hanya dari bagian latih. Pemilihan parameter menggunakan validasi internal bagian latih, bukan hasil fold uji.

**Statistik BM25 untuk evaluasi harus dipelajari dari korpus latih setiap fold.** Skor BM25 hasil build seluruh dataset belum otomatis bebas kebocoran dan perlu dihitung ulang sesuai pembagian evaluasi. Embedding pralatih yang dibekukan dapat dipakai tanpa pelatihan pada data uji; setiap penyesuaian berbasis dataset tetap dibatasi pada data latih.

Model yang dibandingkan:

- Logistic Regression sebagai baseline linear.
- Random Forest sebagai baseline berbasis pohon.
- XGBoost sebagai model utama.

**Keluaran:** model terlatih per fold, parameter terpilih, dan prediksi pada data uji fold.

## 11. Evaluasi kinerja klasifikasi

Evaluasi menggunakan ROC-AUC, PR-AUC, precision, recall, F1-score, dan confusion matrix. Nilai rata-rata dan variasi antarfold dilaporkan. Definisi perhitungan PR-AUC atau average precision yang dipakai perlu ditetapkan secara konsisten.

PR-AUC mendapat perhatian khusus apabila kelas terkutip lebih sedikit. Evaluasi per domain dilakukan apabila jumlah data mencukupi. Analisis kesalahan membahas contoh salah prediksi positif dan negatif. Ambang klasifikasi model, jika disesuaikan, dipilih pada data latih/validasi; ambang ini berbeda dari ambang 0,5 untuk pembentukan label penelitian.

**Keluaran:** perbandingan kinerja model dan analisis kesalahan prediksi.

## 12. Interpretasi SHAP dan ablation study

SHAP digunakan pada XGBoost untuk menjelaskan kontribusi fitur secara global, arah kontribusi, distribusi nilai kontribusi, dan contoh prediksi individual. Data penjelasan serta model/fold yang digunakan dicatat.

Ablation study membandingkan enam konfigurasi:

1. Seluruh kelompok fitur.
2. Tanpa fitur struktural.
3. Tanpa fitur kualitas konten.
4. Tanpa metadata dan otoritas domain.
5. Tanpa relevansi leksikal.
6. Tanpa relevansi semantik.

Setiap konfigurasi dilatih ulang dengan fold dan prosedur pemilihan parameter yang sebanding. Perubahan performa dibandingkan dengan konfigurasi lengkap digunakan untuk menilai kontribusi prediktif kelompok fitur.

SHAP dan ablation menjelaskan model klasifikasi yang dibangun. Keduanya tidak membuktikan mekanisme internal Gemini atau hubungan sebab-akibat.

**Keluaran:** interpretasi fitur dan perbandingan kontribusi lima kelompok fitur.

## 13. Pembahasan dan penarikan kesimpulan

Mengintegrasikan statistik pengumpulan, perbandingan model, SHAP, dan ablation untuk menjawab pertanyaan penelitian. Analisis tambahan membandingkan sumber sitasi di dalam dan di luar Google Top 10 berdasarkan hasil pencocokan URL yang dapat diamati.

Temuan di luar Top 10 berarti sumber tidak ditemukan pada hasil Google yang dikumpulkan untuk query dan konfigurasi tersebut. Temuan itu tidak membuktikan bahwa sumber sama sekali tidak ditemukan Google. Ketidakpastian URL tetap diperhitungkan saat menafsirkan proporsi.

Kesimpulan pemodelan dibatasi pada prediksi keterkutipan di antara kandidat Google Top 10, model Gemini yang digunakan, tiga domain, dan periode pengumpulan. Keterbatasan meliputi seleksi query, grounding, kegagalan scraping, nilai hilang, perubahan isi web/model, ketidakpastian URL, dan keterwakilan sampel. Hasil bersifat prediktif, bukan kausal.

**Keluaran:** jawaban atas pertanyaan penelitian, keterbatasan, serta saran pengembangan.

## Catatan penyusunan naskah akhir

- Gunakan bentuk rencana untuk kegiatan yang belum dilaksanakan; ubah setelah hasil tersedia.
- Isi periode pengumpulan, versi model, jumlah data final, jumlah fold, dan konfigurasi akhir dari log serta artefak yang benar-benar digunakan.
- Petakan setiap fitur ke tepat satu kelompok ablation sebelum pelatihan.
- Pisahkan hasil numerik eksperimen ke bab hasil dan pembahasan; subbab prosedur menjelaskan cara memperolehnya.
- Simpan konfigurasi, keputusan review, data mentah, checkpoint, daftar fold, dan keluaran eksperimen untuk reproduksibilitas.
