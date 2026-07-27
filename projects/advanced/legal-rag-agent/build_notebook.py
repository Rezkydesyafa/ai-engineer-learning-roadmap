#!/usr/bin/env python3
"""Builder: rakit legal_rag_agent.ipynb dari cells_*.py.

Pakai:
  python build_notebook.py          # tulis .ipynb
  python build_notebook.py --test   # exec sel deterministik untuk validasi
"""
import glob
import importlib
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

CELL_FILES = sorted(glob.glob("cells_*.py"))
NB_PATH = Path("legal_rag_agent.ipynb")


def get_cells() -> list:
    all_cells = []
    for fname in CELL_FILES:
        mod_name = fname[:-3]
        if mod_name in sys.modules:
            mod = importlib.reload(sys.modules[mod_name])
        else:
            mod = importlib.import_module(mod_name)
        cells = getattr(mod, "CELLS", [])
        all_cells.extend(cells)
    return all_cells


def build() -> int:
    cells = get_cells()
    nb = new_notebook()
    nb.cells = []
    for item in cells:
        kind = item[0]
        src = item[1].strip()
        if kind == "md":
            nb.cells.append(new_markdown_cell(src))
        elif kind == "code":
            nb.cells.append(new_code_cell(src))
        else:
            raise ValueError(f"Jenis sel tak dikenal: {kind}")

    with open(NB_PATH, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    print(f"OK -> {NB_PATH} ({len(nb.cells)} sel)")
    return 0


def run_test() -> int:
    cells = get_cells()
    ns = {}
    ran = 0
    for i, item in enumerate(cells, 1):
        kind, src = item[0], item[1]
        tag = item[2] if len(item) > 2 else ""
        if kind != "code" or tag != "det":
            continue
        ran += 1
        print(f"[{ran}] Exec sel {i}...")
        try:
            exec(src, ns, ns)
        except Exception as e:
            print(f"GAGAL sel {i} ({tag}): {e}", file=sys.stderr)
            raise
    print(f"DETERMINISTIC OK: {ran} sel dieksekusi tanpa exception")
    return 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        raise SystemExit(run_test())
    raise SystemExit(build())
