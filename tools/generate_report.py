#!/usr/bin/env python3
"""
Northern Sauce — Website Audit Report Generator
Usage: python3 tools/generate_report.py <data.json> <output/report.html>

The skill writes a compact JSON data file; this script generates the full HTML.
Keeps token cost low — Claude writes ~100 lines of JSON, not 700 lines of HTML.
"""

import json
import sys
import os
from html import escape

SECTION_META = {
    "getting_in_touch": ("Why aren't visitors getting in touch?",          "b-journey",   "This checks every point of friction between a visitor who's interested and one who's actually made contact. One unclear button, one extra step, one 'we'll get back to you' without a timeframe — and they're gone."),
    "stand_out":        ("Why would anyone pick you over everyone else?",   "b-strategy",  "If a visitor could read your site and three competitors' sites without seeing any names, could they tell which is yours? This checks whether your site gives someone a real reason to choose you — not just 'we're passionate and dedicated', but something specific and honest that only you could say."),
    "right_person":     ("Does your site speak to the right person?",       "b-messaging", "People don't buy services. They buy solutions to problems they feel. This checks whether your site opens in the client's world — names the problem they actually lose sleep over, speaks to the frustration underneath it, and shows them what life looks like once it's solved."),
    "copy_works":       ("Would your ideal client keep reading — or click away?", "b-copy", "Every line on your site is either moving a visitor toward picking up the phone or giving them a reason to leave. This checks whether your words are actually doing that job — or just filling space."),
    "trust":            ("Do people trust you enough to call?",             "b-trust",     "A visitor who's almost ready to get in touch will do one last check: is there proof this person is the real deal? This checks whether your site gives them enough evidence — from enough sources — that the answer is an easy yes."),
    "pre_sold":         ("Are visitors arriving at a first call already convinced?", "b-hub", "The best enquiries come from people who've already read your content, seen your prices, and decided you're the one. This checks whether your site is doing that pre-selling work — or leaving it all to a first phone call."),
}

VERDICT_CLASS = {"pass": "v-pass", "partial": "v-partial", "fail": "v-fail", "na": "v-na"}
VERDICT_LABEL = {"pass": "PASS", "partial": "PARTIAL", "fail": "FAIL", "na": "N/A"}
RAG_LABELS = {"red": "Red", "amber": "Amber", "green": "Green"}


def e(s):
    return escape(str(s), quote=False)


def depth(audit_dir):
    """Return relative path from audit dir back to repo root."""
    parts = audit_dir.replace("\\", "/").split("/")
    # Find 'audits' in the path to count depth
    try:
        idx = parts.index("audits")
        depth_from_root = len(parts) - idx  # audits + slug
        return "../" * depth_from_root
    except ValueError:
        return "../../"


def render_fix(i, fix):
    tag = fix.get("type", "")
    tag_html = ""
    if tag == "quick":
        tag_html = '<span class="fix-tag quick">Quick win</span>'
    elif tag == "project":
        tag_html = '<span class="fix-tag project">Bigger project</span>'

    return f"""  <div class="fix-item">
    <div class="fix-num">{i}</div>
    <div class="fix-body">
      <div class="fix-title">{e(fix['title'])}{tag_html}</div>
      <div class="fix-detail">{e(fix['detail'])}</div>
      <div class="fix-action"><strong>Do this:</strong> {e(fix['action'])}</div>
    </div>
  </div>"""


def render_finding(f):
    v = f.get("v", "na")
    vc = VERDICT_CLASS.get(v, "v-na")
    vl = VERDICT_LABEL.get(v, "N/A")
    rec = ""
    if f.get("rec"):
        rec = f'\n      <div class="finding-rec"><strong>Fix:</strong> {e(f["rec"])}</div>'
    return f"""    <div class="finding">
      <div class="verdict-dot"><span class="verdict-tag {vc}">{vl}</span></div>
      <div class="finding-body">
        <div class="finding-check">{e(f['check'])}</div>
        <div class="finding-note">{e(f['note'])}</div>{rec}
      </div>
    </div>"""


def render_section(sec, idx):
    sid = sec["id"]
    meta = SECTION_META.get(sid, (sid.title(), "b-tech", ""))
    name, badge, desc = meta
    findings = sec.get("findings", [])
    passed = sum(1 for f in findings if f.get("v") == "pass")
    applicable = sum(1 for f in findings if f.get("v") != "na")
    pct = round(passed / applicable * 100) if applicable else 0
    score_label = f"{passed} / {applicable} &nbsp;·&nbsp; {pct}%"
    findings_html = "\n".join(render_finding(f) for f in findings)
    desc_html = f'\n  <div class="sec-desc">{e(desc)}</div>' if desc else ""
    n = idx + 1
    return f"""<div class="audit-section">
  <div class="audit-sec-head" onclick="toggleSec('s{n}')">
    <span class="sec-badge {badge}">{name}</span>
    <h2>{name}</h2>
    <span class="sec-score">{score_label}</span>
    <span class="chev" id="chev-s{n}">▼</span>
  </div>
  <div class="sec-prog-wrap"><div class="sec-prog-bar {badge}" style="width:{pct}%"></div></div>
  <div class="findings-list" id="body-s{n}" style="display:none">{desc_html}
{findings_html}
  </div>
</div>"""


def generate(data, output_path):
    root = depth(os.path.dirname(output_path))
    css_path = root + "assets/report.css"

    rag = data.get("rag", "red")
    rag_label = RAG_LABELS.get(rag, rag.title())
    passed = data.get("passed", 0)
    failed = data.get("failed", 0)
    partial = data.get("partial", 0)
    na = data.get("na", 0)
    score = data.get("score", 0)
    total_applicable = passed + failed + partial

    fixes_html = "\n".join(render_fix(i + 1, f) for i, f in enumerate(data.get("fixes", [])))
    sections_html = "\n\n".join(render_section(s, i) for i, s in enumerate(data.get("sections", [])))
    positives_html = "\n".join(
        f'  <div class="positive-item"><span class="positive-dot">✓</span> {e(p)}</div>'
        for p in data.get("positives", [])
    )

    scope = e(data.get("scope_note", ""))
    verdict = e(data.get("verdict", ""))
    business = e(data.get("business", ""))
    url = e(data.get("url", ""))
    date_str = e(data.get("date", ""))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Website audit — {business}</title>
<link rel="stylesheet" href="{css_path}">
</head>
<body>

<div class="report-header">
  <div class="report-meta">
    <div class="report-title-block">
      <h1>Website audit — {business}</h1>
      <div class="report-url"><a href="https://{url}" target="_blank">{url}</a></div>
      <div class="report-date">Audit date: {date_str} &nbsp;·&nbsp; Prepared by Northern Sauce</div>
    </div>
    <div class="rag-block">
      <span class="rag-pill rag-{rag}">{rag_label}</span>
    </div>
  </div>
  <div class="score-row">
    <div class="score-card">
      <div class="score-label">Checks passed</div>
      <div class="score-val">{passed}</div>
      <div class="score-sub">out of {total_applicable} applicable</div>
    </div>
    <div class="score-card">
      <div class="score-label">Failed</div>
      <div class="score-val">{failed}</div>
      <div class="score-sub">need attention</div>
    </div>
    <div class="score-card">
      <div class="score-label">Partial</div>
      <div class="score-val">{partial}</div>
      <div class="score-sub">could be stronger</div>
    </div>
    <div class="score-card">
      <div class="score-label">Overall score</div>
      <div class="score-val">{score}%</div>
      <div class="score-sub">{'green — strong foundations' if rag == 'green' else 'amber — good foundations' if rag == 'amber' else 'red — significant gaps'}</div>
    </div>
  </div>
  <div class="verdict-block {rag}">
    {verdict}
  </div>
  <div class="scope-note">
    {scope}
  </div>
</div>

<div class="section-heading">Top 5 fixes</div>
<div class="fix-list">
{fixes_html}
</div>

<div class="section-heading">Detailed findings</div>

{sections_html}

<div class="section-heading">What's working</div>
<div class="positives-list">
{positives_html}
</div>

<div class="report-footer">
  <div class="footer-brand">Confidential &mdash; prepared for <strong>{business}</strong></div>
  <img src="https://northernsauce.uk/wp-content/uploads/2026/04/Ns-EmblemDark.png" alt="Northern Sauce" height="28">
</div>

<script>
function toggleSec(id) {{
  const body = document.getElementById('body-'+id);
  const chev = document.getElementById('chev-'+id);
  const isOpen = body.style.display !== 'none';
  body.style.display = isOpen ? 'none' : 'block';
  chev.classList.toggle('open', !isOpen);
}}
</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report written: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 tools/generate_report.py <data.json> <output/report.html>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    generate(data, sys.argv[2])
