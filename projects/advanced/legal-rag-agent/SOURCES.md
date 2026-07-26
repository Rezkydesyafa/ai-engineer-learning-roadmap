# Sumber Dokumen Korpus — Hukum Ketenagakerjaan Indonesia

Semua dokumen adalah **produk hukum negara → domain publik**. Sumber utama: **JDIH BPK** (`peraturan.bpk.go.id`), portal resmi dokumentasi peraturan.

> PDF mentah **tidak di-commit** ke repo (ukuran besar). Jalankan `python download_corpus.py` untuk mengunduh ke `data/raw/`.

## Korpus v1 (scope: Ketenagakerjaan)

| Dokumen | Status | Halaman | Peran | Sumber resmi |
|---|---|---|---|---|
| **UU 13/2003** Ketenagakerjaan | Berlaku (sebagian diubah) | 128 | UU dasar | [bpk.go.id/details/43013](https://peraturan.bpk.go.id/details/43013) · [PDF](https://peraturan.bpk.go.id/Download/31128/UU%20Nomor%2013%20Tahun%202003.pdf) |
| **UU 6/2023** Cipta Kerja | Berlaku | 1126 | Pengubah terkini | [bpk.go.id/Details/246523](https://peraturan.bpk.go.id/Details/246523/uu-no-6-tahun-2023) · [PDF](https://peraturan.bpk.go.id/Download/302681/UU%20Nomor%206%20Tahun%202023.pdf) |
| **PP 35/2021** PKWT/Alih Daya/PHK | Berlaku | 56 | Turunan operasional | [bpk.go.id/Details/161904](https://peraturan.bpk.go.id/Details/161904/pp-no-35-tahun-2021) · [PDF](https://peraturan.bpk.go.id/Download/154582/PP%20Nomor%2035%20Tahun%202021.pdf) |

### Konteks versi (untuk version graph)
- **UU 11/2020** Cipta Kerja mengubah banyak pasal **UU 13/2003**.
- **UU 11/2020** kemudian ditetapkan ulang lewat **UU 6/2023** (dari Perppu 2/2022) → **UU 6/2023 adalah versi berlaku**.
- Rujukan status di JDIH BPK: [UU 11/2020](https://peraturan.bpk.go.id/Details/149750/uu-no-11-tahun-2020) menautkan ke UU 6/2023 sebagai status terbaru.
- Implikasi retrieval: pasal ketenagakerjaan yang diubah **harus** dipetakan ke versi UU 6/2023, bukan teks asli UU 13/2003.

## Catatan teknis ingestion
- Ketiga PDF **text-based** (bukan hasil scan) → tidak butuh OCR, `pymupdf` cukup.
- UU 6/2023 mencakup **semua sektor** Cipta Kerja (1126 hal). Sesuai scope, ingestion **memfilter hanya klaster ketenagakerjaan** (bagian yang mengubah UU 13/2003).

## Sumber cadangan / verifikasi silang
- **peraturan.go.id** — portal peraturan pemerintah (JDIH Nasional).
- **jdih.kemnaker.go.id** — JDIH Kementerian Ketenagakerjaan (mirror resmi).

## Lisensi & etika
Produk hukum negara Indonesia tidak memiliki hak cipta (UU Hak Cipta 28/2014 Pasal 42). Aman untuk diproses, dievaluasi, dan diunggah ke Hugging Face untuk keperluan portofolio. Sistem ini adalah **alat bantu riset regulasi, bukan nasihat hukum**.
