#!/usr/bin/env python3
"""Downloader korpus hukum ketenagakerjaan Indonesia (sumber resmi JDIH BPK).

Dokumen adalah produk hukum negara -> domain publik.
PDF mentah TIDAK di-commit (lihat .gitignore); jalankan script ini untuk mengunduh.

Pakai:
    python download_corpus.py
"""
import sys
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

# nama_file -> (url resmi, deskripsi)
CORPUS = {
    "UU-13-2003-Ketenagakerjaan.pdf": (
        "https://peraturan.bpk.go.id/Download/31128/UU%20Nomor%2013%20Tahun%202003.pdf",
        "UU 13/2003 Ketenagakerjaan — UU dasar",
    ),
    "UU-6-2023-CiptaKerja.pdf": (
        "https://peraturan.bpk.go.id/Download/302681/UU%20Nomor%206%20Tahun%202023.pdf",
        "UU 6/2023 Cipta Kerja — pengubah terkini (filter klaster ketenagakerjaan saat ingest)",
    ),
    "PP-35-2021-Ketenagakerjaan.pdf": (
        "https://peraturan.bpk.go.id/Download/154582/PP%20Nomor%2035%20Tahun%202021.pdf",
        "PP 35/2021 — PKWT, alih daya, waktu kerja, PHK (turunan operasional)",
    ),
}

RAW = Path(__file__).parent / "data" / "raw"


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    for name, (url, desc) in CORPUS.items():
        dest = RAW / name
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"[skip] {name} sudah ada ({dest.stat().st_size // 1024} KB)")
            continue
        print(f"[get ] {name} — {desc}")
        try:
            download(url, dest)
            print(f"       OK {dest.stat().st_size // 1024} KB")
        except Exception as e:  # noqa: BLE001
            print(f"       GAGAL: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
