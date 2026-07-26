#!/usr/bin/env python3
"""Builder: rakit sales_insight_agent.ipynb dari cells_*.py.

Pakai:
  python build_notebook.py          # tulis .ipynb
  python build_notebook.py --test   # exec cell deterministik (tanpa LLM) untuk verifikasi
"""
import sys
import nbformat as nbf

from cells_01_intro_setup import CELLS as C1
from cells_02_dataset_db import CELLS as C2
from cells_03_guardrail_exec import CELLS as C3
from cells_04_llm_agent import CELLS as C4
from cells_05_demo_security import CELLS as C5
from cells_06_eval import CELLS as C6

ALL_CELLS = C1 + C2 + C3 + C4 + C5 + C6


def build(path: str = "sales_insight_agent.ipynb") -> None:
    nb = nbf.v4.new_notebook()
    cells = []
    for kind, src, *rest in ALL_CELLS:
        src = src.strip("\n")
        if kind == "md":
            cells.append(nbf.v4.new_markdown_cell(src))
        else:
            cells.append(nbf.v4.new_code_cell(src))
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    }
    with open(path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    n_md = sum(1 for k, *_ in ALL_CELLS if k == "md")
    n_code = sum(1 for k, *_ in ALL_CELLS if k == "code")
    print(f"OK -> {path} ({len(ALL_CELLS)} cells: {n_md} md, {n_code} code)")


def test_deterministic() -> None:
    """Exec berurutan hanya cell code yang di-tag deterministik (tag ke-3 == 'det').

    Ini mensimulasikan 'Run All' untuk bagian yang tidak butuh LLM/network,
    sehingga kita yakin dataset, DuckDB, guardrail, security test, dan
    pembanding evaluasi benar-benar jalan.
    """
    g: dict = {}
    ran = 0
    for kind, src, *rest in ALL_CELLS:
        if kind != "code":
            continue
        tag = rest[0] if rest else ""
        if tag != "det":
            continue
        exec(compile(src, "<cell>", "exec"), g, g)
        ran += 1
    print(f"DETERMINISTIC OK: {ran} cells executed, no exception")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test_deterministic()
    else:
        build()
