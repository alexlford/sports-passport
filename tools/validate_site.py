#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
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

def team_slug(value):
    value=value.lower().replace("&","and")
    value=re.sub(r"[^a-z0-9]+","-",value)
    return value.strip("-")

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
clean_urls=ROOT/"assets"/"clean-urls.js"
route_bootstrap=ROOT/"assets"/"route-bootstrap.js"
route_entry_paths=[
    "about/index.html","years/index.html","events/index.html","teams/index.html","venues/index.html",
    "geography/index.html","geography/map/index.html","journeys/index.html","chapters/index.html",
    "favorites/index.html","analytics/index.html","hall-of-fame/index.html",
]

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

if not clean_urls.is_file():
    errors.append("missing assets/clean-urls.js")
else:
    clean_text=clean_urls.read_text(encoding="utf-8")
    for token in ("/years/?year=", "/events/?event=", "/teams/?team=", "/venues/?venue=", "/journeys/?journey=", "/chapters/?chapter="):
        if token not in clean_text:
            errors.append(f"clean URL normalizer missing route pattern {token}")

if not route_bootstrap.is_file():
    errors.append("missing assets/route-bootstrap.js")
else:
    route_text=route_bootstrap.read_text(encoding="utf-8")
    for token in ("publicQuery.get('year')", "publicQuery.get('event')", "publicQuery.get('team')", "publicQuery.get('venue')", "publicQuery.get('journey')", "publicQuery.get('chapter')"):
        if token not in route_text:
            errors.append(f"route bootstrap missing clean query mapping: {token}")

for rel in route_entry_paths:
    path=ROOT/rel
    if not path.is_file():
        errors.append(f"missing clean public route entry: {rel}")
    elif "/assets/route-bootstrap.js" not in path.read_text(encoding="utf-8"):
        errors.append(f"clean public route entry does not load route bootstrap: {rel}")

home=ROOT/"index.html"
if home.is_file() and 'assets/clean-urls.js' not in home.read_text(encoding="utf-8"):
    errors.append("homepage must load clean URL normalizer")

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
        f"{PUBLIC_ORIGIN}/about/",
        f"{PUBLIC_ORIGIN}/years/",
        f"{PUBLIC_ORIGIN}/favorites/",
        f"{PUBLIC_ORIGIN}/geography/",
        f"{PUBLIC_ORIGIN}/geography/map/",
        f"{PUBLIC_ORIGIN}/hall-of-fame/",
        f"{PUBLIC_ORIGIN}/journeys/",
        f"{PUBLIC_ORIGIN}/analytics/",
        f"{PUBLIC_ORIGIN}/teams/",
        f"{PUBLIC_ORIGIN}/venues/",
    }

    # Every annual edition, life chapter, and recurring journey should be directly discoverable.
    try:
        config=json.loads((ROOT/"data"/"config.json").read_text(encoding="utf-8"))
        start=int(config["archive_start_year"])
        current=int(config["current_year"])
        required_urls.update(f"{PUBLIC_ORIGIN}/years/?year={year}" for year in range(start,current+1))
    except Exception as exc:
        errors.append(f"could not derive annual sitemap URLs: {exc}")
    try:
        phases=json.loads((ROOT/"data"/"phases.json").read_text(encoding="utf-8"))
        required_urls.update(f"{PUBLIC_ORIGIN}/chapters/?chapter={p['key']}" for p in phases if p.get("key"))
    except Exception as exc:
        errors.append(f"could not derive life-chapter sitemap URLs: {exc}")
    try:
        journeys=json.loads((ROOT/"data"/"journeys.json").read_text(encoding="utf-8"))
        required_urls.update(f"{PUBLIC_ORIGIN}/journeys/?journey={j['key']}" for j in journeys if j.get("key"))
    except Exception as exc:
        errors.append(f"could not derive journey sitemap URLs: {exc}")

    # Personal Canon content gets explicit sitemap priority: favorite teams, ranked events, and ranked venue identities.
    try:
        lore=json.loads((ROOT/"data"/"team-lore.json").read_text(encoding="utf-8"))
        favorite_teams=[team for team,data in lore.items() if isinstance(data,dict) and data.get("favorite")]
        required_urls.update(f"{PUBLIC_ORIGIN}/teams/?team={team_slug(team)}" for team in favorite_teams)
    except Exception as exc:
        errors.append(f"could not derive favorite-team sitemap URLs: {exc}")
    try:
        rankings=json.loads((ROOT/"data"/"curated-rankings.json").read_text(encoding="utf-8"))
        ranked_slugs={
            slug
            for list_name in ("favorite_venues","best_venues")
            for item in rankings.get(list_name,[])
            for slug in item.get("venue_slugs",[])
        }
        required_urls.update(f"{PUBLIC_ORIGIN}/venues/?venue={slug}" for slug in ranked_slugs)
        required_urls.update(f"{PUBLIC_ORIGIN}/events/?event={item['event_id']}" for item in rankings.get("sports_experiences",[]) if item.get("event_id"))
    except Exception as exc:
        errors.append(f"could not derive ranked sitemap URLs: {exc}")

    missing=sorted(required_urls-set(sitemap_urls))
    if missing:
        errors.append("sitemap.xml missing required public URLs: " + " | ".join(missing))

    allowed_query_keys={"year","event","team","venue","journey","chapter"}
    for url in sitemap_urls:
        parsed=urlsplit(url)
        if f"{parsed.scheme}://{parsed.netloc}" != PUBLIC_ORIGIN:
            errors.append(f"sitemap URL is off canonical origin: {url}")
            continue
        if ".html" in parsed.path:
            errors.append(f"sitemap URL exposes legacy .html route: {url}")
        query_keys=set(parse_qs(parsed.query).keys())
        if not query_keys.issubset(allowed_query_keys):
            errors.append(f"sitemap URL uses noncanonical query keys: {url}")
        if parsed.path == "/":
            local=ROOT/"index.html"
        else:
            local=ROOT/parsed.path.strip("/")/"index.html"
        if not local.is_file():
            errors.append(f"sitemap URL has no matching clean route entry: {url}")
    if len(sitemap_urls) != len(set(sitemap_urls)):
        errors.append("sitemap.xml contains duplicate URLs")

if errors:
    print("\n".join("ERROR: "+e for e in errors))
    sys.exit(1)
print(
    f"OK: {len(html_files)} legacy templates, {len(js_files)} shared JS files, clean route entries, local references, "
    f"data loads, JavaScript syntax, publication metadata, favicon/manifest, branded 404 recovery, robots.txt, "
    f"and {len(sitemap_urls)} clean canonical sitemap URLs validated against archive/editorial data."
)
