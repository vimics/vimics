"""Builds the static site from _src/*.src.html.

Run:  python3 -I web/_src/build.py [preview_dir]
- Inlines the logo and Material Symbols icons, writes index.html, dicom/index.html, vicage/index.html.
- Upload link for /dicom comes from UPLOAD_URL below (OneDrive "Request files" link).
- ViCage size table, size matrix labels and order rows all come from VICAGE_SIZES.
- With preview_dir, also writes a copy without the document skeleton for the artifact preview.
"""
import os, re, shutil, sys

UPLOAD_URL = "https://veterinaryinnovative-my.sharepoint.com/:f:/g/personal/onur_vimics_vet/IgCo2K8lpHwgSoMGd9iU_6-0AYI3-HqiHVtY8swIqAfh2CU"  # OneDrive "Request files" link (upload only), verified 2026-10-26

# ViCage set: (length mm, width mm, nominal height mm, overall height over ridges mm).
# Footprint and nominal height follow the production file names; overall height is the
# bounding box of the production STLs in ~/Downloads/Production STLs (measured 2026-10-15).
VICAGE_SIZES = [
    (8, 7, 4.5, 5.96), (8, 7, 5.5, 7.08),
    (10, 8, 5.0, 6.54), (10, 8, 6.0, 7.55),
    (11, 9, 5.5, 6.99), (11, 9, 6.5, 8.00),
    (13, 10, 6.0, 7.61), (13, 10, 7.0, 8.61),
    (15, 11, 6.5, 8.10), (15, 11, 7.5, 9.10),
]
VICAGE_INSERTER = ("VC-INS-150", "ViCage inserter", "150 mm")

def vc_code(L, W, H):
    return f"VC-{L:02d}{W:02d}-{round(H * 10):03d}"

def fmt(x):
    return f"{x:g}"

SRC = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(SRC)

logo = open(os.path.join(SRC, "parts", "logo-h.svg"), encoding="utf-8").read()
logo = logo.replace('role="img" aria-label="VIMICS"', 'role="img" aria-label="Vimics, Care Beyond Boundaries"')

def icon(name):
    s = open(os.path.join(WEB, "assets", "icons", name + ".svg"), encoding="utf-8").read()
    d = re.search(r'<path d="([^"]+)"', s).group(1)
    return f'<svg class="ic" viewBox="0 -960 960 960" aria-hidden="true"><path d="{d}"/></svg>'

# Size matrix render (ViCage/Gorseller/final/MATRIS_*_5444x2480.png): orthographic top view,
# 92 mm wide frame, 5444 x 2480 px. Columns sit at x = -38, -19, 0, 19, 38 mm, the lower
# height of each footprint at y = +8 mm (top row) and the higher one at y = -8 mm.
MATRIS_W_MM = 92.0
MATRIS_H_MM = MATRIS_W_MM * 2480 / 5444

def matrix_figure():
    labels, foots = [], []
    for i, (L, W, H, _) in enumerate(VICAGE_SIZES):
        col, row = i // 2, i % 2
        sx, sy = -38 + 19 * col, (8 if row == 0 else -8)
        x = (sx + MATRIS_W_MM / 2) / MATRIS_W_MM * 100
        y_center = MATRIS_H_MM / 2 - sy
        y = (y_center + W / 2 + 1.0) / MATRIS_H_MM * 100
        labels.append(f'<span class="et" style="left:{x:.2f}%;top:{y:.2f}%"><b>{fmt(H)} mm</b>{vc_code(L, W, H)}</span>')
        if row == 0:
            foots.append(f'<span class="ayak" style="left:{x:.2f}%">{L}×{W}</span>')
    alt = "All ten ViCage sizes seen from above at one scale: five footprints in columns, two heights per footprint"
    return ('<div class="matris-sar"><figure class="matris"><div class="matris-gorsel">'
            f'<img class="tema-acik" src="../assets/img/vicage/matris-acik.webp" width="5444" height="2480" loading="lazy" alt="{alt}">'
            f'<img class="tema-koyu" src="../assets/img/vicage/matris-koyu.webp" width="5444" height="2480" loading="lazy" alt="{alt}">'
            + "".join(labels) + '</div><div class="ayaklar">' + "".join(foots) + '</div>'
            '<figcaption>Top view, all sizes at one scale. Footprint in mm, length × width.</figcaption></figure></div>')

def size_rows(order=False):
    rows, prev = [], None
    for L, W, H, Hmax in VICAGE_SIZES:
        code = vc_code(L, W, H)
        first = ' class="grup-ilk"' if prev and prev != (L, W) else ""
        prev = (L, W)
        cells = (f'<td class="kod">{code}</td><td>{L} × {W}</td><td class="sayi">{fmt(H)}</td>')
        if order:
            cells += (f'<td class="sayi"><input type="number" id="adet-{code}" data-kod="{code}" data-ad="ViCage {fmt(H)} - {L}x{W}" '
                      f'min="0" max="99" step="1" value="0" inputmode="numeric" aria-label="Quantity of {code}"></td>')
        else:
            cells += f'<td class="sayi">{Hmax:.1f}</td>'
        rows.append(f"<tr{first}>{cells}</tr>")
    if order:
        code, name, length = VICAGE_INSERTER
        rows.append(f'<tr class="grup-ilk"><td class="kod">{code}</td><td colspan="2">{name}, {length}</td>'
                    f'<td class="sayi"><input type="number" id="adet-{code}" data-kod="{code}" data-ad="{name}" min="0" max="99" step="1" value="0" inputmode="numeric" aria-label="Quantity of {code}"></td></tr>')
    return "\n".join(rows)

def render(src):
    s = open(os.path.join(SRC, src), encoding="utf-8").read()
    s = s.replace("{{LOGO}}", logo).replace("{{UPLOAD_URL}}", UPLOAD_URL or "#upload-pending")
    s = s.replace("{{VC_MATRIS}}", matrix_figure()).replace("{{VC_TABLO}}", size_rows()).replace("{{VC_SIPARIS}}", size_rows(order=True))
    s = s.replace("{{VC_ADET}}", str(len(VICAGE_SIZES)))
    return re.sub(r"\{\{I:([a-z_]+)\}\}", lambda m: icon(m.group(1)), s)

pages = {
    "index.html": render("index.src.html"),
    "dicom/index.html": render("dicom.src.html"),
    "vicage/index.html": render("vicage.src.html"),
}
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
    def dirlinks(h):
        return re.sub(r'href="((?:\.\./)?(?:dicom|vicage)/|\.\./|\./)(#[^"]*)?"',
                      lambda m: f'href="{m.group(1) if m.group(1) not in ("./",) else ""}index.html{m.group(2) or ""}"', h)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(dirlinks(strip(pages["index.html"])))
    for sub in ("dicom", "vicage"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
        open(os.path.join(out, sub, "index.html"), "w", encoding="utf-8").write(dirlinks(pages[f"{sub}/index.html"]))
    print("preview:", out)
