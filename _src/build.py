"""Builds the static site from _src/*.src.html.

Run:  python3 -I web/_src/build.py [preview_dir]
- Inlines the logo and Material Symbols icons, writes index.html, dicom/index.html, vcage/index.html.
- vicage/index.html is a redirect to /vcage/ (product renamed ViCage -> VCage on 2026-10-22; old links keep working).
- Upload link for /dicom comes from UPLOAD_URL below (OneDrive "Request files" link).
- VCage size table, size matrix labels and order rows all come from VCAGE_SIZES.
- Blog: blog/index.html and one folder per post (BLOG_POSTS); posts share the footer from {{FOOTER:<prefix>}}.
- Writes sitemap.xml and robots.txt for search engines.
- With preview_dir, also writes a copy without the document skeleton for the artifact preview.
"""
import os, re, shutil, sys

UPLOAD_URL = "https://veterinaryinnovative-my.sharepoint.com/:f:/g/personal/onur_vimics_vet/IgCo2K8lpHwgSoMGd9iU_6-0AYI3-HqiHVtY8swIqAfh2CU"  # OneDrive "Request files" link (upload only), verified 2026-10-26

# Google Search Console "HTML tag" verification token (content="..." value only). Empty: no tag.
# A DNS TXT verification at GoDaddy (Domain property) does not need this.
GSC_TOKEN = ""

# VCage set: (length mm, width mm, nominal height mm, overall height over ridges mm).
# Footprint and nominal height follow the production file names; overall height is the
# bounding box of the production STLs in ~/Downloads/Production STLs (measured 2026-10-15).
VCAGE_SIZES = [
    (8, 7, 4.5, 5.96), (8, 7, 5.5, 7.08),
    (10, 8, 5.0, 6.54), (10, 8, 6.0, 7.55),
    (11, 9, 5.5, 6.99), (11, 9, 6.5, 8.00),
    (13, 10, 6.0, 7.61), (13, 10, 7.0, 8.61),
    (15, 11, 6.5, 8.10), (15, 11, 7.5, 9.10),
]
VCAGE_INSERTER = ("VC-INS-150", "VCage inserter", "150 mm")

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

# Size matrix render (VCage‡Gorseller/final/MATRIS_*_5444x2480.png): orthographic top view,
# 92 mm wide frame, 5444 x 2480 px. Columns sit at x = -38, -19, 0, 19, 38 mm, the lower
# height of each footprint at y = +8 mm (top row) and the higher one at y = -8 mm.
MATRIS_W_MM = 92.0
MATRIS_H_MM = MATRIS_W_MM * 2480 / 5444

def matrix_figure():
    labels, foots = [], []
    for i, (L, W, H, _) in enumerate(VCAGE_SIZES):
        col, row = i // 2, i % 2
        sx, sy = -38 + 19 * col, (8 if row == 0 else -8)
        x = (sx + MATRIS_W_MM / 2) / MATRIS_W_MM * 100
        y_center = MATRIS_H_MM / 2 - sy
        y = (y_center + W / 2 + 1.0) / MATRIS_H_MM * 100
        labels.append(f'<span class="et" style="left:{x:.2f}%;top:{y:.2f}%"><b>{fmt(H)} mm</b>{vc_code(L, W, H)}</span>')
        if row == 0:
            foots.append(f'<span class="ayak" style="left:{x:.2f}%">{L}×{W}</span>')
    alt = "All ten VCage sizes seen from above at one scale: five footprints in columns, two heights per footprint"
    return ('<div class="matris-sar"><figure class="matris"><div class="matris-gorsel">'
            f'<img class="tema-acik" src="../assets/img/vcage/matris-acik.webp" width="5444" height="2480" loading="lazy" alt="{alt}">'
            f'<img class="tema-koyu" src="../assets/img/vcage/matris-koyu.webp" width="5444" height="2480" loading="lazy" alt="{alt}">'
            + "".join(labels) + '</div><div class="ayaklar">' + "".join(foots) + '</div>'
            '<figcaption>Top view, all sizes at one scale. Footprint in mm, length × width.</figcaption></figure></div>')

def size_rows(order=False):
    rows, prev = [], None
    for L, W, H, Hmax in VCAGE_SIZES:
        code = vc_code(L, W, H)
        first = ' class="grup-ilk"' if prev and prev != (L, W) else ""
        prev = (L, W)
        cells = (f'<td class="kod">{code}</td><td>{L} × {W}</td><td class="sayi">{fmt(H)}</td>')
        if order:
            cells += (f'<td class="sayi"><input type="number" id="adet-{code}" data-kod="{code}" data-ad="VCage {fmt(H)} - {L}x{W}" '
                      f'min="0" max="99" step="1" value="0" inputmode="numeric" aria-label="Quantity of {code}"></td>')
        else:
            cells += f'<td class="sayi">{Hmax:.1f}</td>'
        rows.append(f"<tr{first}>{cells}</tr>")
    if order:
        code, name, length = VCAGE_INSERTER
        rows.append(f'<tr class="grup-ilk"><td class="kod">{code}</td><td colspan="2">{name}, {length}</td>'
                    f'<td class="sayi"><input type="number" id="adet-{code}" data-kod="{code}" data-ad="{name}" min="0" max="99" step="1" value="0" inputmode="numeric" aria-label="Quantity of {code}"></td></tr>')
    return "\n".join(rows)

# Blog posts: (source file, URL slug, last modified). Newest first; the blog index lists them by hand.
BLOG_POSTS = [
    ("blog-vettalks-antalya-2026.src.html", "vettalks-neurosurgery-workshop-antalya-2026", "2026-10-26"),
]

def footer(p):
    return f'''<footer class="alt" id="contact">
  <div class="kolon">
    <div style="display: grid; gap: var(--b4); align-content: start;">
      <a class="logo-link" href="{p}" aria-label="Vimics home">{logo}</a>
      <p class="ikincil kucuk">Vimics is a veterinary orthopaedic technology company developing patient-specific orthopaedic implants, surgical guides and digital surgical planning solutions for animals.</p>
    </div>
    <div>
      <h2>Contact</h2>
      <address>
        <a href="mailto:info@vimics.vet">info@vimics.vet</a>
        <a href="https://www.linkedin.com/company/vimics" rel="noopener">LinkedIn · Vimics</a>
        <a href="https://www.instagram.com/vimics.veterinary/" rel="noopener">Instagram · @vimics.veterinary</a>
        <a href="{p}dicom/">Send a case · vimics.vet/dicom</a>
      </address>
    </div>
    <div>
      <h2>Address</h2>
      <address>Mustafa Kemal Mah. Dumlupınar Bul. No:280/G İç Kapı No:1260<br>06510 Çankaya / Ankara, Türkiye</address>
    </div>
    <div class="kunye">
      <span>© 2026 Vimics</span>
      <span>VETERINARY INNOVATIVE ENGINEERING MÜHENDİSLİK VETERİNERLİK SANAYİ VE TİCARET ANONİM ŞİRKETİ</span>
      <span>MERSİS 0925123067800001</span>
      <span>Ankara Ticaret Sicili 508020</span>
    </div>
  </div>
</footer>'''

def render(src):
    s = open(os.path.join(SRC, src), encoding="utf-8").read()
    s = s.replace("{{LOGO}}", logo).replace("{{UPLOAD_URL}}", UPLOAD_URL or "#upload-pending")
    s = s.replace("{{VC_MATRIS}}", matrix_figure()).replace("{{VC_TABLO}}", size_rows()).replace("{{VC_SIPARIS}}", size_rows(order=True))
    s = s.replace("{{VC_ADET}}", str(len(VCAGE_SIZES)))
    s = s.replace("{{GSC}}\n", f'<meta name="google-site-verification" content="{GSC_TOKEN}">\n' if GSC_TOKEN else "")
    s = re.sub(r"\{\{FOOTER:([./]*)\}\}", lambda m: footer(m.group(1)), s)
    return re.sub(r"\{\{I:([a-z_]+)\}\}", lambda m: icon(m.group(1)), s)

pages = {
    "index.html": render("index.src.html"),
    "dicom/index.html": render("dicom.src.html"),
    "vcage/index.html": render("vcage.src.html"),
    "vicage/index.html": render("redirect.src.html").replace("{{HEDEF}}", "https://vimics.vet/vcage/"),
    "blog/index.html": render("blog.src.html"),
}
for src, slug, _ in BLOG_POSTS:
    pages[f"blog/{slug}/index.html"] = render(src)
for path, html in pages.items():
    os.makedirs(os.path.dirname(os.path.join(WEB, path)) or WEB, exist_ok=True)
    open(os.path.join(WEB, path), "w", encoding="utf-8").write(html)

mono = open(os.path.join(SRC, "parts", "monogram.svg"), encoding="utf-8").read().replace("var(--logo-monogram)", "#26497F")
open(os.path.join(WEB, "assets", "img", "favicon.svg"), "w", encoding="utf-8").write(mono)
open(os.path.join(WEB, "CNAME"), "w").write("vimics.vet\n")

urls = [("", "2026-10-26"), ("vcage/", "2026-10-26"), ("dicom/", "2026-10-26"), ("blog/", BLOG_POSTS[0][2])]
urls += [(f"blog/{slug}/", mod) for _, slug, mod in BLOG_POSTS]
open(os.path.join(WEB, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>https://vimics.vet/{u}</loc><lastmod>{m}</lastmod></url>\n" for u, m in urls) + "</urlset>\n")
open(os.path.join(WEB, "robots.txt"), "w").write("User-agent: *\nAllow: /\n\nSitemap: https://vimics.vet/sitemap.xml\n")
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
        # Folder links ("../", "vcage/", "blog/<slug>/") need an explicit index.html in the preview.
        def f(m):
            path = "" if m.group(1) == "./" else m.group(1)
            return f'href="{path}index.html{m.group(2) or ""}"'
        return re.sub(r'href="((?:\.\./|\./|[a-z0-9-]+/)+)(#[^"]*)?"', f, h)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(dirlinks(strip(pages["index.html"])))
    for path, html in pages.items():
        if path == "index.html":
            continue
        os.makedirs(os.path.dirname(os.path.join(out, path)), exist_ok=True)
        open(os.path.join(out, path), "w", encoding="utf-8").write(dirlinks(html))
    print("preview:", out)
