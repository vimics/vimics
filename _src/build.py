"""Builds the static site from _src/*.src.html.

Run:  python3 -I web/_src/build.py [preview_dir]
- Inlines the logo and Material Symbols icons, writes index.html and dicom/index.html.
- Upload link for /dicom comes from UPLOAD_URL below (OneDrive "Request files" link).
- With preview_dir, also writes a copy without the document skeleton for the artifact preview.
"""
import os, re, shutil, sys

UPLOAD_URL = ""  # paste the OneDrive "Request files" link here, then rebuild

SRC = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(SRC)

logo = open(os.path.join(SRC, "parts", "logo-h.svg"), encoding="utf-8").read()
logo = logo.replace('role="img" aria-label="VIMICS"', 'role="img" aria-label="Vimics, Care Beyond Boundaries"')

def icon(name):
    s = open(os.path.join(WEB, "assets", "icons", name + ".svg"), encoding="utf-8").read()
    d = re.search(r'<path d="([^"]+)"', s).group(1)
    return f'<svg class="ic" viewBox="0 -960 960 960" aria-hidden="true"><path d="{d}"/></svg>'

def render(src):
    s = open(os.path.join(SRC, src), encoding="utf-8").read()
    s = s.replace("{{LOGO}}", logo).replace("{{UPLOAD_URL}}", UPLOAD_URL or "#upload-pending")
    return re.sub(r"\{\{I:([a-z_]+)\}\}", lambda m: icon(m.group(1)), s)

pages = {"index.html": render("index.src.html"), "dicom/index.html": render("dicom.src.html")}
for path, html in pages.items():
    os.makedirs(os.path.dirname(os.path.join(WEB, path)) or WEB, exist_ok=True)
    open(os.path.join(WEB, path), "w", encoding="utf-8").write(html)

mono = open(os.path.join(SRC, "parts", "monogram.svg"), encoding="utf-8").read().replace("var(--logo-monogram)", "#26497F")
open(os.path.join(WEB, "assets", "img", "favicon.svg"), "w", encoding="utf-8").write(mono)
open(os.path.join(WEB, "CNAME"), "w").write("vimics.vet\n")
print("built:", ", ".join(pages))

if len(sys.argv) > 1:
    out = sys.argv[1]
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(os.path.join(WEB, "assets"), os.path.join(out, "assets"), ignore=shutil.ignore_patterns("icons"))
    def strip(h):
        h = re.sub(r"<!doctype html>\s*", "", h, flags=re.I)
        h = re.sub(r"</?(html|head|body)[^>]*>\s*", "", h)
        return re.sub(r'<meta (charset|name="viewport")[^>]*>\s*', "", h)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(strip(pages["index.html"]).replace('href="dicom/"', 'href="dicom/index.html"'))
    os.makedirs(os.path.join(out, "dicom"), exist_ok=True)
    open(os.path.join(out, "dicom", "index.html"), "w", encoding="utf-8").write(pages["dicom/index.html"].replace('href="../"', 'href="../index.html"'))
    print("preview:", out)
