#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ORIGIN = "https://sports.alexlford.com"
errors=[]
html_files=sorted(ROOT.glob("*.html"))

class RefParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source=source
    def handle_starttag(self, tag, attrs):
        values=dict(attrs)
        for attr in ("href","src"):
            value=values.get(attr)
            if value:
                check_ref(self.source, value)

def check_ref(source, value):
    value=value.strip()
    if not value or value.startswith(("#","http://","https://","mailto:","tel:","data:","javascript:","//")):
        return
    if "${" in value or "{{" in value:
        return
    path=urlsplit(value).path
    if not path or path.startswith("/"):
        return
    target=(source.parent/path).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"{source.name}: local reference escapes repository: {value}")
        return
    if not target.exists():
        errors.append(f"{source.name}: missing local reference {value}")

# Validate static local href/src targets and data loader references.
load_re=re.compile(r"\bD\.load\(\s*['\"]([^'\"]+)['\"]\s*\)")
for html in html_files:
    text=html.read_text(encoding="utf-8")
    parser=RefParser(html)
    try:
        parser.feed(text)
    except Exception as exc:
        errors.append(f"{html.name}: HTML parse error: {exc}")
    for name in load_re.findall(text):
        target=ROOT/"data"/f"{name}.json"
        if not target.is_file():
            errors.append(f"{html.name}: D.load('{name}') has no data/{name}.json")

# Syntax-check shared JS and every inline script without executing browser code.
js_files=sorted((ROOT/"assets").glob("*.js"))
script_re=re.compile(r"<script(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script>",re.IGNORECASE|re.DOTALL)
with tempfile.TemporaryDirectory() as tmp:
    tmpdir=Path(tmp)
    checks=[]
    for js in js_files:
        checks.append((str(js.relative_to(ROOT)),js.read_text(encoding="utf-8")))
    for html in html_files:
        text=html.read_text(encoding="utf-8")
        for i,script in enumerate(script_re.findall(text),1):
            if script.strip():
                checks.append((f"{html.name} inline script #{i}",script))
    for i,(label,code) in enumerate(checks):
        temp=tmpdir/f"check-{i}.js"
        temp.write_text(code,encoding="utf-8")
        proc=subprocess.run(["node","--check",str(temp)],capture_output=True,text=True)
        if proc.returncode:
            detail=(proc.stderr or proc.stdout).strip().splitlines()
            errors.append(f"{label}: JavaScript syntax check failed: {' | '.join(detail[-3:])}")

# Publication/discovery files are part of the public-site contract.
robots=ROOT/"robots.txt"
sitemap=ROOT/"sitemap.xml"
not_found=ROOT/"404.html"
favicon=ROOT/"favicon.svg"
manifest=ROOT/"site.webmanifest"
if not robots.is_file():
    errors.append("missing robots.txt")
else:
    robots_text=robots.read_text(encoding="utf-8")
    if f"Sitemap: {PUBLIC_ORIGIN}/sitemap.xml" not in robots_text:
        errors.append("robots.txt must advertise the canonical sitemap URL")
    if "Allow: /" not in robots_text:
        errors.append("robots.txt should allow the public archive to be crawled")
if not not_found.is_file():
    errors.append("missing branded 404.html")
else:
    not_found_text=not_found.read_text(encoding="utf-8")
    if 'name="robots" content="noindex"' not in not_found_text:
        errors.append("404.html must be noindex")
    if 'href="index.html"' not in not_found_text:
        errors.append("404.html must provide a path back to the archive home")
    if 'href="favicon.svg"' not in not_found_text:
        errors.append("404.html must use the Sports Passport favicon")

if not favicon.is_file():
    errors.append("missing favicon.svg")
else:
    try:
        ET.parse(favicon)
    except Exception as exc:
        errors.append(f"favicon.svg parse error: {exc}")

if not manifest.is_file():
    errors.append("missing site.webmanifest")
else:
    try:
        manifest_data=json.loads(manifest.read_text(encoding="utf-8"))
        for field in ("name","short_name","start_url","display","background_color","theme_color"):
            if not manifest_data.get(field):
                errors.append(f"site.webmanifest missing {field}")
    except Exception as exc:
        errors.append(f"site.webmanifest parse error: {exc}")

shared_js=ROOT/"assets"/"sports-passport-data.js"
if not shared_js.is_file():
    errors.append("missing shared Sports Passport data/runtime script")
else:
    shared_text=shared_js.read_text(encoding="utf-8")
    for token,label in (
        ("favicon.svg","shared favicon injection"),
        ("og:title","Open Graph title metadata"),
        ("og:description","Open Graph description metadata"),
        ("og:url","Open Graph canonical URL metadata"),
        ("twitter:card","Twitter card metadata"),
        ("upsertLink('canonical'","canonical-link metadata"),
    ):
        if token not in shared_text:
            errors.append(f"shared runtime missing {label}")

sitemap_urls=[]
if not sitemap.is_file():
    errors.append("missing sitemap.xml")
else:
    try:
        tree=ET.parse(sitemap)
        ns={"sm":"http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls=[node.text.strip() for node in tree.findall("sm:url/sm:loc",ns) if node.text and node.text.strip()]
    except Exception as exc:
        errors.append(f"sitemap.xml parse error: {exc}")
    required_urls={
        f"{PUBLIC_ORIGIN}/",
        f"{PUBLIC_ORIGIN}/annuals.html",
        f"{PUBLIC_ORIGIN}/favorites.html",
        f"{PUBLIC_ORIGIN}/geography.html",
        f"{PUBLIC_ORIGIN}/hall-of-fame.html",
        f"{PUBLIC_ORIGIN}/journeys.html",
        f"{PUBLIC_ORIGIN}/lifetime-analytics.html",
        f"{PUBLIC_ORIGIN}/teams.html",
        f"{PUBLIC_ORIGIN}/venue-map.html",
        f"{PUBLIC_ORIGIN}/venues.html",
    }
    missing=sorted(required_urls-set(sitemap_urls))
    if missing:
        errors.append("sitemap.xml missing core public URLs: " + " | ".join(missing))
    for url in sitemap_urls:
        parsed=urlsplit(url)
        if f"{parsed.scheme}://{parsed.netloc}" != PUBLIC_ORIGIN:
            errors.append(f"sitemap URL is off canonical origin: {url}")
            continue
        local_path=parsed.path.lstrip("/") or "index.html"
        if not (ROOT/local_path).is_file():
            errors.append(f"sitemap URL has no matching public template: {url}")
    if len(sitemap_urls) != len(set(sitemap_urls)):
        errors.append("sitemap.xml contains duplicate URLs")

if errors:
    print("\n".join("ERROR: "+e for e in errors))
    sys.exit(1)
print(
    f"OK: {len(html_files)} HTML pages, {len(js_files)} shared JS files, local references, data loads, "
    f"inline JavaScript syntax, publication metadata, favicon/manifest, branded 404 recovery, robots.txt, "
    f"and {len(sitemap_urls)} sitemap URLs validated."
)
