#!/usr/bin/env python3
"""Generate evaluation dataset LexID M3 (84 cases, reproducible, human-readable JSON)."""
import json
from pathlib import Path

INTENTS = [
    ("definisi tenaga kerja", "UU-13-2003", "1", ["apa definisi tenaga kerja?", "siapa yang dimaksud tenaga kerja?", "jelaskan pengertian tenaga kerja"]),
    ("dasar pembangunan ketenagakerjaan", "UU-13-2003", "2", ["apa dasar pembangunan ketenagakerjaan?", "pembangunan ketenagakerjaan berlandaskan apa?", "apa landasan ketenagakerjaan?"]),
    ("perlakuan tanpa diskriminasi", "UU-13-2003", "6", ["apakah pekerja berhak tanpa diskriminasi?", "bagaimana hak perlakuan yang sama bagi pekerja?", "bolehkah pengusaha mendiskriminasi pekerja?"]),
    ("pelatihan kerja", "UU-13-2003", "9", ["bagaimana aturan pelatihan kerja?", "apa hak pekerja untuk pelatihan kerja?", "jelaskan ketentuan pelatihan tenaga kerja"]),
    ("isi perjanjian kerja", "UU-13-2003", "54", ["apa yang wajib ada dalam perjanjian kerja?", "apa isi minimal kontrak kerja?", "jelaskan syarat isi perjanjian kerja"]),
    ("berakhir perjanjian kerja", "UU-13-2003", "61", ["kapan perjanjian kerja berakhir?", "apa penyebab kontrak kerja berakhir?", "bagaimana ketentuan berakhirnya perjanjian kerja?"]),
    ("waktu kerja", "UU-13-2003", "77", ["berapa jam waktu kerja normal?", "bagaimana aturan jam kerja?", "jelaskan batas waktu kerja pekerja"]),
    ("lembur", "UU-13-2003", "78", ["bagaimana aturan lembur?", "apa syarat kerja lembur?", "kapan pengusaha boleh meminta lembur?"]),
    ("istirahat mingguan", "UU-13-2003", "79", ["apa hak istirahat mingguan?", "berapa lama istirahat pekerja?", "jelaskan hak waktu istirahat"]),
    ("cuti melahirkan", "UU-13-2003", "82", ["bagaimana hak cuti melahirkan?", "berapa lama cuti pekerja yang melahirkan?", "apa hak pekerja perempuan saat melahirkan?"]),
    ("keselamatan kerja", "UU-13-2003", "86", ["bagaimana perlindungan keselamatan kerja?", "apa hak pekerja atas K3?", "jelaskan hak keselamatan dan kesehatan kerja"]),
    ("pengupahan", "UU-13-2003", "88", ["bagaimana kewajiban pembayaran upah?", "apa hak pekerja terhadap upah?", "jelaskan kebijakan pengupahan pekerja"]),
    ("upah minimum", "UU-13-2003", "89", ["bagaimana aturan upah minimum?", "siapa yang menetapkan upah minimum?", "jelaskan ketentuan upah minimum"]),
    ("prosedur PHK", "UU-13-2003", "151", ["bagaimana prosedur pemutusan hubungan kerja?", "apa tahapan PHK pekerja?", "bagaimana pengusaha melakukan PHK?"]),
    ("pesangon", "UU-13-2003", "156", ["apa komponen uang pesangon?", "bagaimana perhitungan hak pesangon?", "apa hak pekerja saat PHK terkait pesangon?"]),
    ("kompensasi PKWT", "PP-35-2021", "15", ["bagaimana uang kompensasi PKWT?", "kapan kompensasi kontrak diberikan?", "apa hak kompensasi pekerja PKWT?"]),
    ("alih daya", "PP-35-2021", "18", ["bagaimana aturan alih daya?", "apa ketentuan outsourcing?", "siapa bertanggung jawab pada pekerja alih daya?"]),
    ("PHK dan pesangon PP", "PP-35-2021", "40", ["apa kewajiban pengusaha saat PHK?", "berapa komponen hak akibat PHK?", "apa aturan pesangon berdasarkan PP 35?"]),
    ("PHK efisiensi", "PP-35-2021", "43", ["bagaimana PHK karena efisiensi?", "apa hak pekerja jika perusahaan melakukan efisiensi?", "bolehkah PHK karena efisiensi perusahaan?"]),
    ("PHK pensiun", "PP-35-2021", "56", ["bagaimana PHK karena pensiun?", "apa hak pekerja yang memasuki usia pensiun?", "jelaskan PHK akibat usia pensiun"]),
]

VERSION_SENSITIVE = [
    ("berapa jam kerja yang berlaku setelah Cipta Kerja?", "UU-13-2003", "77", "UU-6-2023", "77"),
    ("bagaimana aturan lembur terbaru?", "UU-13-2003", "78", "UU-6-2023", "78"),
    ("bagaimana waktu istirahat setelah perubahan Cipta Kerja?", "UU-13-2003", "79", "UU-6-2023", "79"),
    ("apa aturan pengupahan yang berlaku saat ini?", "UU-13-2003", "88", "UU-6-2023", "88"),
    ("apa aturan upah minimum setelah Cipta Kerja?", "UU-13-2003", "89", "UU-6-2023", "89"),
    ("bagaimana prosedur PHK versi terbaru?", "UU-13-2003", "151", "UU-6-2023", "151"),
    ("apa larangan PHK menurut aturan terbaru?", "UU-13-2003", "153", "UU-6-2023", "153"),
    ("apa ketentuan pesangon terbaru?", "UU-13-2003", "156", "UU-6-2023", "156"),
    ("bagaimana dasar perhitungan pesangon terbaru?", "UU-13-2003", "157", "UU-6-2023", "157"),
    ("bagaimana aturan outsourcing terbaru?", "UU-13-2003", "66", "UU-6-2023", "66"),
    ("bagaimana PHK karena pelanggaran terbaru?", "UU-13-2003", "161", "UU-6-2023", "161"),
    ("bagaimana PHK karena perubahan perusahaan terbaru?", "UU-13-2003", "163", "UU-6-2023", "163"),
]

REFUSALS = [
    "berapa tarif pajak pertambahan nilai?", "bagaimana pembagian warisan menurut KUHPerdata?",
    "apa ancaman pidana korupsi?", "bagaimana prosedur perceraian?", "siapa pemilik sertifikat tanah?",
    "apa syarat pendirian perseroan terbatas?", "bagaimana izin usaha pertambangan?",
    "apa hukuman pencemaran nama baik?", "bagaimana hak asuh anak setelah cerai?",
    "berapa pajak penghasilan badan?", "bagaimana sengketa merek dagang?", "apa aturan kepailitan perusahaan?",
]

cases = []
for intent, doc, art, questions in INTENTS:
    for q in questions:
        cases.append({"question": q, "expected_document": doc, "expected_article": art, "should_refuse": False, "category": intent})
for q, doc, art, current_doc, current_art in VERSION_SENSITIVE:
    cases.append({"question": q, "expected_document": doc, "expected_article": art, "should_refuse": False,
                  "expected_current_document": current_doc, "expected_current_article": current_art, "category": "version-sensitive"})
for q in REFUSALS:
    cases.append({"question": q, "expected_document": None, "expected_article": None, "should_refuse": True, "category": "out-of-scope"})

assert len(cases) == 84, len(cases)
out = Path(__file__).parent / "eval_dataset_m3.json"
out.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OK -> {out.name}: {len(cases)} cases")
print("answerable=72 | version-sensitive=12 | refusal=12")
