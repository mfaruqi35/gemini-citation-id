# Flowchart Prosedur Penelitian

Pendamping [outline subbab Prosedur Penelitian](OUTLINE_PROSEDUR_PENELITIAN.md). Disusun 19 September 2026.

Disederhanakan pada 19 September 2026 agar lebih mudah ditempatkan pada satu halaman A4. Pilih satu versi ringkas di bawah untuk laporan; versi detail tetap tersedia sebagai referensi.

Salin isi salah satu blok kode ke Mermaid Live Editor, tanpa tanda pembatas tiga backtick. Diagram menunjukkan prosedur lengkap yang direncanakan, bukan penanda seluruh tahap telah selesai.

## Pilihan 1 — Ringkas vertikal untuk A4 portrait (disarankan)

Versi ini menggunakan sembilan tahap utama. Seleksi, validasi, recovery, dan alasan eksklusi dijelaskan dalam teks metodologi sehingga tidak perlu menjadi cabang tersendiri pada gambar.

```mermaid
%%{init: {"theme": "neutral", "flowchart": {"rankSpacing": 16, "nodeSpacing": 20}, "themeVariables": {"fontSize": "14px"}}}%%
flowchart TD
    A["1. Penetapan rancangan dan protokol"]
    B["2. Pengumpulan Trends dan PAA<br/>serta seleksi query"]
    C["3. Pengumpulan Google Top 10<br/>dan tiga percobaan Gemini"]
    D["4. Validasi, pencocokan URL,<br/>dan pelabelan sitasi"]
    E["5. Scraping, pembersihan,<br/>dan pemeriksaan artikel"]
    F["6. Ekstraksi fitur dan penyusunan<br/>dataset siap pemodelan"]
    G["7. Pembagian data berkelompok<br/>dan pelatihan LR, RF, XGBoost"]
    H["8. Evaluasi kinerja,<br/>SHAP, dan ablation study"]
    I["9. Pembahasan dan kesimpulan"]
    A --> B --> C --> D --> E --> F --> G --> H --> I
```

## Pilihan 2 — Horizontal tiga kelompok untuk A4 landscape

Sembilan tahap disusun dalam tiga kolom, masing-masing berisi tiga tahap. Susunan ini menghindari satu baris horizontal panjang yang akan membuat tulisan terlalu kecil. Baca tiap kolom dari atas ke bawah, kemudian lanjut ke kolom kanan sesuai nomor tahap.

```mermaid
%%{init: {"theme": "neutral", "flowchart": {"rankSpacing": 22, "nodeSpacing": 18}, "themeVariables": {"fontSize": "14px"}}}%%
flowchart LR
    subgraph P1["Persiapan dan pengumpulan"]
        direction TB
        A["1. Rancangan<br/>dan protokol"]
        B["2. Trends dan PAA<br/>serta seleksi query"]
        C["3. Google Top 10<br/>dan tiga percobaan Gemini"]
        A --> B --> C
    end

    subgraph P2["Pembentukan dataset"]
        direction TB
        D["4. Validasi, pencocokan URL,<br/>dan pelabelan sitasi"]
        E["5. Scraping, pembersihan,<br/>dan pemeriksaan artikel"]
        F["6. Ekstraksi fitur<br/>dan dataset siap pemodelan"]
        D --> E --> F
    end

    subgraph P3["Pemodelan dan analisis"]
        direction TB 
        G["7. Pembagian berkelompok<br/>dan pelatihan LR, RF, XGBoost"]
        H["8. Evaluasi kinerja,<br/>SHAP, dan ablation study"]
        I["9. Pembahasan<br/>dan kesimpulan"]
        G --> H --> I
    end

    P1 --> P2 --> P3
```

## Keterangan untuk kedua versi ringkas

- LR: Logistic Regression; RF: Random Forest.
- Tahap 1 mencakup uji teknis awal dan pembekuan protokol utama.
- Tahap 4 mempertahankan ketentuan minimal dua percobaan valid, jendela pengumpulan, label dengan ambang proporsi ≥0,5, dan penanganan ketidakpastian URL.
- Tahap 6 memisahkan dataset utama Google Top 10 untuk model dari dataset tambahan Gemini-only untuk analisis deskriptif.
- Tahap 7 mencakup pencegahan kebocoran data, prapemrosesan, penghitungan ulang statistik BM25 dari korpus latih setiap fold, serta pemilihan hiperparameter.
- Tahap 8 mencakup evaluasi model dan pelatihan ulang pada setiap konfigurasi ablation. Tahap 9 juga menggunakan analisis deskriptif dataset tambahan.

**Usulan caption:** Gambar X. Prosedur penelitian klasifikasi keterkutipan artikel web berbahasa Indonesia oleh Gemini.

Untuk laporan dengan orientasi portrait tetap, gunakan pilihan 1. Jika pedoman kampus mengizinkan halaman landscape, pilihan 2 dapat memakai lebar halaman. Ekspor sebagai SVG agar teks tetap tajam saat diubah ukurannya. Sesuaikan ukuran akhir dengan area cetak setelah margin dan caption; keterbacaan perlu diperiksa pada ukuran cetak sebenarnya.

## Versi detail — Referensi, bukan gambar utama satu halaman

```mermaid
flowchart TD
    A(["Mulai"]) --> B["Penetapan tujuan, cakupan, dan protokol penelitian"]
    B --> C["Uji teknis awal dan pembekuan protokol utama"]
    C --> D["Pengumpulan Google Trends<br/>Top dan Rising pada tiga domain"]
    D --> E["Seleksi kata kunci sesuai domain"]
    E --> F["Pengumpulan People Also Ask"]
    F --> G["Seleksi query asli dan pencatatan alasan"]
    G --> H{"Query diterima?"}

    H -- Tidak --> X["Arsip kandidat dan alasan eksklusi"]
    H -- Ya --> I["Google organik Top 10 melalui SerpApi"]
    H -- Ya --> J["Tiga percobaan Gemini<br/>dengan Google Search Grounding"]

    I --> K["Validasi percobaan dan waktu pengumpulan<br/>Resolusi serta pencocokan URL"]
    J --> K
    K --> L{"Minimal dua percobaan valid<br/>dan jendela waktu terpenuhi?"}

    L -- Tidak --> Y["Arsip hasil belum layak<br/>Recovery transport terbatas bila memenuhi syarat"]
    Y -. Evaluasi ulang hasil recovery .-> K

    L -- Ya --> M["Pembentukan pasangan query-artikel<br/>Proporsi dan label jika pencocokan pasti"]
    M --> N["Kandidat utama<br/>Google Top 10"]
    M --> O["Kandidat tambahan<br/>Sitasi Gemini di luar Top 10"]

    N --> P["Scraping URL dan penyimpanan HTML mentah"]
    O --> P
    P --> Q["Ekstraksi isi utama dan pemeriksaan artikel"]
    Q --> R{"Artikel layak?"}

    R -- Tidak --> Z["Catat kegagalan atau alasan eksklusi<br/>Pertahankan data untuk audit"]
    R -- Ya --> S["Ekstraksi lima kelompok fitur<br/>Simpan bukti otoritas sebagai metadata audit"]
    S --> T["Gabungkan fitur dan label<br/>Ambang proporsi sitasi minimal 0.5"]
    T --> U["Pemeriksaan kualitas dan pembekuan dataset<br/>Tunda baris dengan label atau URL belum pasti"]

    U --> V["Dataset utama siap pemodelan<br/>Google Top 10 yang lolos pemeriksaan"]
    U --> W["Dataset tambahan Gemini-only<br/>Analisis deskriptif"]

    V --> AA["Pembagian data berkelompok<br/>Cegah kebocoran query dan artikel"]
    AA --> AB["Prapemrosesan dan statistik BM25<br/>dipelajari pada data latih tiap fold"]
    AB --> AC["Pelatihan dan pemilihan parameter<br/>Logistic Regression, Random Forest, XGBoost"]
    AC --> AD["Evaluasi klasifikasi<br/>ROC-AUC, PR-AUC, precision, recall, F1"]
    AD --> AE["Interpretasi XGBoost dengan SHAP"]
    AD --> AF["Ablation study<br/>Latih ulang dengan satu kelompok fitur dihapus"]

    AE --> AG["Pembahasan hasil dan keterbatasan"]
    AF --> AG
    W --> AG
    AG --> AH["Penarikan kesimpulan dan saran"]
    AH --> AI(["Selesai"])
```

## Catatan pembacaan

- Cabang Google dan Gemini merupakan dua sumber pengumpulan untuk query yang sama; diagram tidak mensyaratkan eksekusi paralel.
- Recovery hanya untuk kegagalan transport yang memenuhi aturan retry dan jendela waktu, bukan mengulang jawaban valid sampai mendapat label yang diinginkan.
- Ketidakpastian pencocokan URL tetap disimpan dan tidak diubah menjadi label negatif.
- Dataset utama adalah kandidat Google Top 10; Gemini-only digunakan untuk analisis tambahan.
- Statistik BM25 pada tahap pemodelan dihitung dari data latih tiap fold, meskipun skor awal sudah tersedia dalam dataset hasil build.
- Ablation menggunakan pembagian data dan prosedur evaluasi yang sama dengan eksperimen fitur lengkap.
