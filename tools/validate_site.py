#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
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

if errors:
    print("\n".join("ERROR: "+e for e in errors))
    sys.exit(1)
print(f"OK: {len(html_files)} HTML pages, {len(js_files)} shared JS files, local references, data loads, and inline JavaScript syntax validated.")
