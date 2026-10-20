# Revisi 1 — Fokus penelitian dan rancangan pemodelan

Tanggal: 19 Oktober 2026

## Fokus penelitian — keputusan nomor 1

Status: fokus penelitian telah dikonfirmasi. Cakupan dataset dijelaskan pada keputusan nomor 2; definisi label dan penggunaan kelompok dalam pelatihan masih perlu ditetapkan.

Penelitian berfokus pada karakteristik sumber yang disitasi oleh Gemini, dengan Google Top 10 sebagai pembanding. Pertanyaan utama yang dikonfirmasi adalah:

> Apa yang membedakan artikel yang dikutip dari yang tidak, dan apakah pola itu berbeda antara artikel yang juga ada di Top 10 dan yang tidak?

Fokus tersebut memuat dua bagian analisis:

1. Menganalisis perbedaan karakteristik sumber berdasarkan keterkutipannya oleh Gemini.
2. Menganalisis perbedaan pola karakteristik sumber sitasi Gemini berdasarkan keberadaannya di dalam atau di luar Google Top 10 yang dikumpulkan untuk kueri yang sama.

Gemini menjadi objek pengamatan keterkutipan, sedangkan Google Top 10 menyediakan konteks pembanding. Keberadaan dalam Top 10 tidak langsung ditafsirkan sebagai ukuran kualitas SEO, dan sumber di luar Top 10 tidak berarti tidak terindeks oleh Google. Analisis diarahkan pada hubungan atau perbedaan karakteristik yang teramati, bukan pembuktian penyebab internal Gemini memilih suatu sumber.

### Konsekuensi metodologis yang perlu diselesaikan

- Pertanyaan tentang sumber yang dikutip dan tidak dikutip memerlukan kelompok pembanding yang tidak dikutip. Google-only tetap tercakup sebagai pembanding sesuai keputusan nomor 2. Pembentukan subset untuk pelatihan dan interpretasi akan mengikuti definisi target yang disepakati.
- Dataset yang berasal dari gabungan Google Top 10 dan sitasi Gemini belum menyediakan sampel sumber di luar Top 10 yang tidak disitasi. Karena itu, data tersebut dapat mendukung perbandingan karakteristik sumber yang disitasi di dalam dan di luar Top 10, tetapi belum mendukung perbandingan dikutip versus tidak dikutip secara terpisah pada kedua kelompok posisi tersebut.
- Istilah “dikutip” dan “tidak dikutip” pada pertanyaan utama masih perlu dibuat operasional. Label lama memakai proporsi sitasi ≥0,5; label 0 dapat mencakup sumber yang pernah disitasi satu kali dari tiga percobaan valid. Definisi label klasifikasi dan syarat pembentukan kelompok sitasi akan ditetapkan pada keputusan nomor 3 dan 4.
- Unit analisis tetap perlu dibaca sebagai pasangan kueri–sumber: sumber yang sama dapat memiliki status keterkutipan dan posisi kelompok berbeda untuk kueri yang berbeda.

## Cakupan dataset — keputusan nomor 2

Status: dikonfirmasi. Gemini-only masuk sebagai bagian dataset utama penelitian, bukan hanya sebagai dataset tambahan. Google-only dan Google∩Gemini tetap dipertahankan untuk menjawab fokus pada keputusan nomor 1.

| Kelompok | Definisi berdasarkan pengamatan untuk kueri yang sama |
| --- | --- |
| Google-only | Sumber dalam Google Top 10 yang tidak teramati disitasi Gemini pada percobaan valid. |
| Google∩Gemini | Sumber dalam Google Top 10 yang pernah disitasi Gemini pada percobaan valid. |
| Gemini-only | Sumber yang pernah disitasi Gemini pada percobaan valid, tetapi tidak ditemukan dalam Google Top 10 yang dikumpulkan. |

Google Top 10 merupakan gabungan Google-only dan Google∩Gemini, sehingga tidak dihitung kembali sebagai kelompok keempat. Definisi asal sumber di atas mengikuti keberadaan sitasi yang teramati; definisi tersebut belum menggantikan aturan label berbasis proporsi sitasi.

Masuknya ketiga kelompok ke dataset utama penelitian tidak otomatis berarti seluruh baris harus digabung dalam satu tugas klasifikasi. Subset analisis, target model, dan penanganan perbedaan cara sumber masuk ke sampel masih perlu ditentukan. Seluruh kelompok harus memenuhi rubrik kelayakan yang konsisten sebelum digunakan.

## Target dan pelabelan — keputusan nomor 3 masih terbuka

Keputusan nomor 2 menetapkan cakupan sumber, tetapi belum menetapkan arti kelas yang diprediksi. Dua definisi keterkutipan yang perlu dipilih adalah:

1. **Pernah disitasi:** kelas 1 apabila disitasi minimal sekali pada percobaan valid; kelas 0 apabila tidak teramati disitasi pada seluruh percobaan valid, dengan pencocokan sitasi yang telah dipastikan. Label ini menyatakan keterkutipan yang teramati dalam protokol pengumpulan, bukan peluang mutlak suatu sumber akan disitasi di masa depan.
2. **Memenuhi ambang proporsi sitasi:** mempertahankan aturan lama, kelas 1 apabila `n_cited / n_valid ≥ 0,5`, dan kelas 0 apabila di bawah ambang. Kelas 0 tidak dapat seluruhnya disebut “tidak pernah dikutip”.

Kedua definisi tetap memerlukan penetapan syarat percobaan valid dan penanganan pencocokan URL yang tidak pasti. Ambang pelabelan dataset berbeda dari ambang probabilitas prediksi model.

Jika targetnya pernah disitasi, seluruh Gemini-only masuk kelas positif berdasarkan cara pengumpulannya. Sementara itu, sumber di luar Top 10 yang tidak disitasi tidak tersedia dalam sampel. Menggabungkan semua kelompok dalam satu model perlu mempertimbangkan keterbatasan pemilihan sampel ini; atribut asal kelompok dan informasi sitasi pembentuk label tidak boleh menjadi fitur prediktor. Keputusan pelatihan gabungan belum ditetapkan.

Perbandingan Google∩Gemini dengan Gemini-only menjawab pertanyaan perbedaan karakteristik di antara sumber yang sudah disitasi. Jika dibuat model terpisah untuk perbandingan tersebut, targetnya adalah keanggotaan kelompok dalam/luar Top 10, bukan dikutip/tidak dikutip. Pemodelan terpisah ini belum diputuskan.

## Keputusan pemodelan

Pemodelan membandingkan tiga algoritma berikut:

1. Logistic Regression.
2. Random Forest.
3. XGBoost.

Tidak ada algoritma yang ditetapkan sejak awal sebagai model utama. XGBoost menjadi salah satu kandidat yang dievaluasi, dengan kedudukan yang sama dalam perbandingan. Dukungan penelitian terdahulu digunakan sebagai landasan pemilihan kandidat, bukan sebagai jaminan bahwa salah satunya akan menghasilkan kinerja terbaik pada dataset penelitian ini.

Transformer tidak digunakan sebagai model klasifikasi langsung dalam rancangan ini. Penggunaan transformer sebagai pembentuk embedding untuk fitur relevansi semantik tetap dipertahankan. Dengan demikian, fitur `semantic_cosine` tetap dapat digunakan sebagai masukan bagi ketiga model tabular tersebut.

## Prosedur perbandingan dan pemilihan model

- Ketiga model dibandingkan menggunakan dataset, definisi target, kelompok fitur, serta pembagian data yang sama. Prapemrosesan disesuaikan dengan kebutuhan masing-masing algoritma.
- Pembagian data mempertimbangkan kelompok kueri dan dokumen yang berulang untuk mengurangi kebocoran informasi antarbagian data.
- Penyetelan hiperparameter dan pemilihan model dilakukan melalui validasi pada bagian data latih. Dalam validasi silang bersarang, kegiatan tersebut dilakukan pada validasi internal, sedangkan bagian evaluasi luar digunakan untuk menilai prosedur pemodelan.
- Statistik BM25, imputasi, penskalaan, dan transformasi lain yang mempelajari statistik korpus atau data dihitung hanya dari bagian latih pada pembagian yang bersangkutan, termasuk pembagian validasi internal.
- F1 untuk kelas positif tetap menjadi metrik utama sesuai rancangan evaluasi. Precision, recall, MCC, ROC-AUC, Average Precision, serta confusion matrix melengkapi penilaian. Makna kelas positif mengikuti definisi target penelitian yang akhirnya disepakati.
- Kestabilan hasil antar-fold dan kinerja per domain turut dilaporkan. Aturan pemilihan model ditetapkan sebelum melihat hasil evaluasi akhir. Data uji akhir, apabila digunakan, tidak dipakai untuk memilih model, hiperparameter, atau ambang probabilitas prediksi.
- Model untuk interpretasi utama dipilih berdasarkan prosedur validasi tersebut. Interpretasi dan ablation study tetap diarahkan untuk menjelaskan kontribusi kelompok fitur terhadap prediksi model, bukan untuk menyatakan hubungan sebab-akibat atau menjelaskan mekanisme internal Gemini.

## Penyesuaian proposal

| Bagian | Penyesuaian |
| --- | --- |
| Judul | Tidak mengunci penelitian pada XGBoost. Rumusan judul lengkap mengikuti kesepakatan cakupan penelitian. |
| Rumusan masalah dan tujuan | Jika membahas kinerja model, gunakan rumusan perbandingan ketiga algoritma tanpa mengasumsikan keunggulan XGBoost. |
| Tinjauan pustaka | Pertahankan landasan Logistic Regression, Random Forest, dan XGBoost. Jelaskan transformer pada bagian embedding atau relevansi semantik. |
| Prosedur pemodelan | Ganti pernyataan “XGBoost sebagai model utama” dengan perbandingan tiga kandidat dan pemilihan berdasarkan validasi. |
| Interpretasi hasil | Sesuaikan metode penjelasan dengan model yang dipilih dan pertahankan analisis kontribusi kelompok fitur. |

## Draft paragraf pemodelan

Pemodelan dilakukan dengan membandingkan Logistic Regression, Random Forest, dan XGBoost untuk mengolah fitur tabular yang telah disusun. Ketiga algoritma dipilih berdasarkan karakteristiknya dan dukungan penelitian terdahulu, tanpa menetapkan salah satunya sebagai model utama sebelum evaluasi. Perbandingan menggunakan pembagian data yang sama, dengan prapemrosesan dan penyetelan hiperparameter yang disesuaikan untuk masing-masing algoritma. Pemilihan model dilakukan melalui validasi pada bagian data latih berdasarkan metrik yang telah ditetapkan, sedangkan kinerja pada bagian evaluasi dilaporkan secara keseluruhan dan per domain. Model yang dipilih digunakan untuk mendukung interpretasi kontribusi kelompok fitur melalui metode penjelasan yang sesuai dan ablation study. Transformer digunakan untuk menghasilkan representasi semantik kueri dan dokumen, bukan sebagai model klasifikasi langsung.

## Batas revisi

Catatan ini menetapkan fokus penelitian pada keputusan nomor 1, cakupan dataset utama pada keputusan nomor 2, serta perubahan rancangan pemodelan. Perubahan bahasa sumber, penerimaan PDF atau dokumen lain, penggunaan setiap kelompok dalam pelatihan, serta definisi target klasifikasi belum ditetapkan melalui revisi ini. Opsi dan konsekuensi metodologis yang ditandai belum diputuskan bukan keputusan tambahan yang telah dikonfirmasi. Revisi ini belum mengubah kode maupun dataset yang sudah tersimpan.
