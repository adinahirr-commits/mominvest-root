#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הופך את פלט ג'מיני ([TITLE]/[DESCRIPTION]/[LEAD]/[BODY]) לקובץ content/<slug>.md,
ומריץ בדיקות: מקפים, תגים מותרים, קישורים רק למקורות מאושרים, ורשימת כל המספרים לביקורת.
  python3 build/ingest.py <scratch-dir>
"""
import os, re, sys, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "build", "research")
SRC = sys.argv[1]
TODAY = datetime.date.today().isoformat()

ORDER = {"hisachon-lekol-yeled":1,"kesef-baovesh":2,"kupat-gemel-keren-hishtalmut-polisa":3,"keren-kaspit":4,"snp-500":5,
         "kesef-avud":6,"lachsoch-leyeladim":7,"pensia-gil-40":8,"marvichim-yafe-lo-nishar":9,"hachnasa-nosefet":10}
QUESTION = {"hisachon-lekol-yeled":"חיסכון לכל ילד","kesef-baovesh":"כסף בעובר ושב","kupat-gemel-keren-hishtalmut-polisa":"גמל להשקעה, השתלמות או פוליסה",
            "keren-kaspit":"קרן כספית","snp-500":"S&P 500","kesef-avud":"כסף אבוד","lachsoch-leyeladim":"חיסכון לילדים",
            "pensia-gil-40":"פנסיה בגיל 40","marvichim-yafe-lo-nishar":"תקציב משפחתי","hachnasa-nosefet":"הכנסה נוספת"}

allowed_urls = set()
for f in glob.glob(os.path.join(R, "facts-*.md")):
    allowed_urls |= set(re.findall(r"https?://[^\s)\]>,;\"']+", open(f, encoding="utf-8").read()))
ALLOWED_TAGS = {"h2","h3","p","br","ul","ol","li","strong","a","blockquote","table","thead","tbody","tr","th","td","div","section","details","summary","em"}

def sec(txt, name, nxt):
    m = re.search(r"\[%s\]\s*(.*?)(?=\[%s\]|\Z)" % (name, nxt), txt, re.S)
    return m.group(1).strip() if m else ""

problems = 0
for path in sorted(glob.glob(os.path.join(SRC, "seo-*.txt"))):
    slug = re.sub(r"^seo-\d+-", "", os.path.basename(path)[:-4])
    txt = open(path, encoding="utf-8").read()
    title, desc, lead = sec(txt,"TITLE","DESCRIPTION"), sec(txt,"DESCRIPTION","LEAD"), sec(txt,"LEAD","BODY")
    body = sec(txt, "BODY", "NEVER")
    body = re.sub(r"^```html\s*|```\s*$", "", body.strip(), flags=re.M).strip()
    issues = []
    if not (title and desc and lead and body): issues.append("חסר סקשן")
    if re.search(r"[—–]", txt): issues.append("מקפים")
    tags = set(t.lower() for t in re.findall(r"</?([a-zA-Z0-9]+)", body))
    bad = tags - ALLOWED_TAGS
    if bad: issues.append("תגים לא מותרים: " + ",".join(sorted(bad)))
    hrefs = re.findall(r'href="([^"]+)"', body)
    ext = [h for h in hrefs if h.startswith("http") and not any(h.rstrip("/").startswith(a.rstrip("/")) for a in allowed_urls) and "mominvest.co.il" not in h]
    if ext: issues.append("קישורים לא מאושרים: " + " | ".join(ext))
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    if len(title) > 70: issues.append("כותרת ארוכה %d" % len(title))
    if not (100 <= len(desc) <= 165): issues.append("תיאור %d תווים" % len(desc))
    nums = sorted(set(re.findall(r"\d[\d,\.]*\s?(?:%|₪|ש\"ח|שקל|אלף|מיליון|מיליארד)", re.sub(r"<[^>]+>", " ", body))))
    print("== %s | %d מילים | %s" % (slug, words, "OK" if not issues else "; ".join(issues)))
    print("   מספרים:", ", ".join(nums)[:600])
    if issues: problems += 1
    md = "---\nslug: %s\norder: %d\nquestion: %s\ntitle: %s\ndescription: %s\ndate: %s\nupdated: %s\n---\n%s\n" % (
        slug, ORDER[slug], QUESTION[slug], title, desc, TODAY, TODAY, body)
    # ה-lead נכנס כ-description בדף (build.py משתמש ב-description), שומרים את ה-lead בנפרד
    md = md.replace("description: %s\n" % desc, "description: %s\nlead: %s\n" % (desc, lead))
    open(os.path.join(ROOT, "content", slug + ".md"), "w", encoding="utf-8").write(md)
print("problems:", problems)
