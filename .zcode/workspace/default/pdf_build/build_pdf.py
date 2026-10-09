# -*- coding: utf-8 -*-
"""Two-pass PDF builder: build DOCX, measure real heading pages, rebuild with exact TOC."""
import importlib.util
import re
import subprocess
import sys

import pymupdf

SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.com"
PROFILE = "-env:UserInstallation=file:///C:/Users/ilayl/AppData/Local/Temp/lo_profile_rvm"
WORK = r"C:\Users\ilayl\.zcode\workspace\default\pdf_build"
FINAL_DOCX = r"C:\Users\ilayl\.zcode\workspace\default\ronaldo_vs_messi_deep_research.docx"
FINAL_PDF = r"C:\Users\ilayl\.zcode\workspace\default\ronaldo_vs_messi_deep_research.pdf"

spec = importlib.util.spec_from_file_location("bd", WORK + r"\build_docx.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)


def convert(docx_path):
    subprocess.run(
        [SOFFICE, "--headless", PROFILE, "--convert-to", "pdf",
         "--outdir", str(docx_path.rsplit("\\", 1)[0]), docx_path],
        check=True, capture_output=True, timeout=300,
    )
    return docx_path[:-5] + ".pdf"


def norm(s):
    return re.sub(r"\s+", "", s)


def measure(pdf_path, headings, first_body_page):
    """Return {heading_text: 1-based page} for the first page containing the heading."""
    doc = pymupdf.open(pdf_path)
    page_texts = [norm(p.get_text()) for p in doc]
    result = {}
    for level, text in headings:
        needle = norm(text)
        for pno in range(first_body_page - 1, len(page_texts)):
            if needle in page_texts[pno]:
                result[text] = pno + 1
                break
        else:
            result[text] = None
    doc.close()
    return result


def main():
    title, meta_lines, blocks = bd.parse_md()
    headings = [(1 if kind == "h2" else 2, text) for kind, text in blocks if kind in ("h2", "h3")]
    print(f"{len(headings)} headings")

    # pass A: no TOC, body starts on page 2
    pass_a_docx = WORK + r"\pass_a.docx"
    bd.build(pass_a_docx, None)
    pass_a_pdf = convert(pass_a_docx)
    pages = measure(pass_a_pdf, headings, first_body_page=2)
    missing = [t for t, p in pages.items() if p is None]
    if missing:
        print("MISSING HEADINGS:", missing)
        sys.exit(2)

    # pass B: insert single-page TOC -> body shifts +1
    toc_entries = [(lvl, txt, pages[txt] + 1) for lvl, txt in headings]
    bd.build(FINAL_DOCX, toc_entries)
    convert(FINAL_DOCX)

    # verify against the final PDF; iterate once if pagination drifted
    for attempt in range(2):
        actual = measure(FINAL_PDF, headings, first_body_page=3)
        bad = {t: (toc_num, actual[t]) for (lvl, t), toc_num
               in zip(headings, [e[2] for e in toc_entries]) if actual[t] != toc_num}
        if not bad:
            print("TOC verified: all page numbers match")
            break
        print(f"attempt {attempt + 1}: fixing {len(bad)} drifted entries")
        corrected = [(lvl, txt, actual[txt]) for lvl, txt in headings]
        bd.build(FINAL_DOCX, corrected)
        convert(FINAL_DOCX)
        toc_entries = corrected
    else:
        print("WARNING: TOC still drifting after retry")

    doc = pymupdf.open(FINAL_PDF)
    print("final pages:", len(doc))
    doc.close()


if __name__ == "__main__":
    main()
