"""Builds the static site from _src/*.src.html.

Run:  python3 -I web/_src/build.py [preview_dir]
- Inlines the logo and Material Symbols icons, writes index.html, dicom/index.html, vicage/index.html.
- Upload link for /dicom comes from UPLOAD_URL below (OneDrive "Request files" link).
- ViCage size table, scale drawing and order rows all come from VICAGE_SIZES.
- With preview_dir, also writes a copy without the document skeleton for the artifact preview.
"""
import os, re, shutil, sys

UPLOAD_URL = ""  # paste the OneDrive "Request files" link here, then rebuild

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

def scale_drawing():
    """Top view and side view of every size, all drawn at 9 px per mm."""
    s, col, top = 9, 168, 40
    groups = []
    for L, W, H, _ in VICAGE_SIZES:
        if not groups or groups[-1][0] != (L, W):
            groups.append(((L, W), []))
        groups[-1][1].append(H)
    out = []
    for i, ((L, W), hs) in enumerate(groups):
        cx = 24 + i * col + col / 2
        out.append(f'<text class="yazi" x="{cx}" y="22" text-anchor="middle">{L}×{W}</text>')
        out.append(f'<rect class="kutu" x="{cx - L * s / 2:.1f}" y="{top + (11 - W) * s / 2:.1f}" width="{L * s}" height="{W * s}"/>')
        y0 = top + 11 * s + 36
        for j, H in enumerate(hs):
            yb = y0 + j * 96 + 7.5 * s
            out.append(f'<rect class="yan" x="{cx - L * s / 2:.1f}" y="{yb - H * s:.1f}" width="{L * s}" height="{H * s:.1f}"/>')
            out.append(f'<text class="yazi-k" x="{cx}" y="{yb + 18:.1f}" text-anchor="middle">{fmt(H)} mm</text>')
    h = top + 11 * s + 36 + 96 + 7.5 * s + 52
    w = 48 + len(groups) * col
    y_ruler = h - 8
    out.append(f'<line class="cizgi" x1="24" y1="{y_ruler}" x2="{24 + 10 * s}" y2="{y_ruler}"/>')
    out.append(f'<line class="cizgi" x1="24" y1="{y_ruler - 5}" x2="24" y2="{y_ruler + 1}"/><line class="cizgi" x1="{24 + 10 * s}" y1="{y_ruler - 5}" x2="{24 + 10 * s}" y2="{y_ruler + 1}"/>')
    out.append(f'<text class="yazi-k" x="{24 + 10 * s + 8}" y="{y_ruler + 4}">10 mm</text>')
    return (f'<svg viewBox="0 0 {w} {h + 6}" role="img" aria-label="ViCage sizes drawn to scale: top view of each footprint and side view of each height">'
            + "".join(out) + "</svg>")

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
    s = s.replace("{{VC_OLCEK}}", scale_drawing()).replace("{{VC_TABLO}}", size_rows()).replace("{{VC_SIPARIS}}", size_rows(order=True))
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
