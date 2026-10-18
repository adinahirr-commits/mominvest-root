#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה את mominvest.co.il מתוך content/*.md (מאמרים) + build/home.html (דף הבית).

  python3 build/build.py

כל קובץ ב-content/ = מאמר אחד: frontmatter (---) עם slug/title/description/question/date/updated,
ואחריו גוף ב-HTML (h2/p/ul/table...). המנוע עוטף בכרום משותף, מוסיף JSON-LD, sitemap ו-blog/index.html.
"""
import os, re, json, datetime, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://mominvest.co.il"
LIVUI = "https://livui.mominvest.co.il/"
TODAY = datetime.date.today().isoformat()

# המדריכים החינמיים והמוצרים (כותרות = הכותרות של הדפים עצמם)
GUIDES = {
    "guide1": {"url": "https://adinahirr-commits.github.io/mominvest-guides/guide1/",
               "title": "איך למצוא בין 300 ל-700 ש\"ח כל חודש להשקעה",
               "text": "המדריך החינמי לכספים האבודים: 7 תחנות, תסריט מוכן לכל שיחה, ובסוף את יודעת בדיוק כמה כסף מצאת.",
               "btn": "לקבל את המדריך בחינם »"},
    "guide2": {"url": "https://adinahirr-commits.github.io/mominvest-guides/guide2/",
               "title": "איך לסדר לילד שלך 50-70 אלף ש\"ח מתנה מהמדינה",
               "text": "המדריך החינמי לחיסכון לכל ילד: מה לבדוק, איזה מסלול לבחור ואיך מוציאים מהחיסכון את המקסימום.",
               "btn": "לקבל את המדריך בחינם »"},
}
COURSE500K = "https://500k.mominvest.co.il/"
# לכל מאמר: איזה מדריך מופיע באמצעו, והאם מופיע גם הקורס (מנגנון החצי מיליון)
ARTICLE_GUIDE = {
    "kesef-avud": "guide1", "kesef-baovesh": "guide1", "marvichim-yafe-lo-nishar": "guide1",
    "hachnasa-nosefet": "guide1", "keren-kaspit": "guide1", "pensia-gil-40": "guide1",
    "hisachon-lekol-yeled": "guide2", "lachsoch-leyeladim": "guide2", "snp-500": "guide2",
    "kupat-gemel-keren-hishtalmut-polisa": "guide2",
}
ARTICLE_500K = {"hisachon-lekol-yeled", "lachsoch-leyeladim", "snp-500"}

def utm(url, medium, campaign):
    return "%s?utm_source=site&utm_medium=%s&utm_campaign=%s" % (url, medium, campaign)

def guide_box(key, campaign):
    g = GUIDES[key]
    return """
<div class="box guide-box">
  <span class="eyebrow">מדריך חינמי</span>
  <h3>%s</h3>
  <p>%s</p>
  <a class="btn" href="%s">%s</a>
</div>
""" % (html.escape(g["title"]), html.escape(g["text"]), utm(g["url"], "article-guide", campaign), g["btn"])

def course_box(campaign):
    return """
<div class="box guide-box">
  <span class="eyebrow">מנגנון החצי מיליון</span>
  <h3>ההדרכה המלאה: איך לתת חצי מיליון לכל ילד</h3>
  <p>מנגנון החצי מיליון של עדי סומך: בני עתיד כלכלי לילדים שלך.</p>
  <a class="btn" href="%s">לפרטים על ההדרכה »</a>
</div>
""" % utm(COURSE500K, "article-500k", campaign)

def insert_mid(body, block):
    # לפני ה-h2 השלישי (אמצע המאמר); אם אין, לפני האחרון
    idx = [m.start() for m in re.finditer(r"<h2", body)]
    if len(idx) >= 3: at = idx[2]
    elif idx: at = idx[-1]
    else: return body + block
    return body[:at] + block + body[at:]

def read(p):
    with open(p, encoding="utf-8") as f: return f.read()

def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(s)

def parse(md):
    m = re.match(r"---\n(.*?)\n---\n(.*)$", md, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()

HEAD = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}">
<link rel="icon" href="/assets/logo.png">
<meta property="og:type" content="{ogtype}">
<meta property="og:locale" content="he_IL">
<meta property="og:site_name" content="אמא משקיעה">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<script type="application/ld+json">{ld}</script>
<!-- Meta Pixel (כמו בדף הליווי) -->
<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','1820166155346211');fbq('track','PageView');
</script>
<!-- מדידה משלנו דרך הפורטל (הדף סטטי ואין לו לוגים) -->
<script>
(function(){{
  var TRACK="https://academy.mominvest.co.il/guide-hit", q=new URLSearchParams(location.search), vid;
  var KEYS=['ref','utm_source','utm_medium','utm_campaign','utm_content'];
  try{{ vid=localStorage.getItem('mi_vid'); if(!vid){{ vid=Date.now().toString(36)+Math.random().toString(36).slice(2,10); localStorage.setItem('mi_vid',vid); }}
    KEYS.forEach(function(k){{ if(q.get(k)) localStorage.setItem('mi_'+k,q.get(k)); }}); }}catch(e){{ vid='nostore'; }}
  function attrib(){{ var o={{vid:vid||''}}; KEYS.forEach(function(k){{ var v=q.get(k)||(function(){{ try{{ return localStorage.getItem('mi_'+k); }}catch(e){{ return ''; }} }})(); if(v) o[k]=v; }});
    if(!o.ref && document.referrer && document.referrer.indexOf(location.host)<0) o.ref=document.referrer.slice(0,120); return o; }}
  window.miHit=function(page){{ try{{ if(sessionStorage.getItem('mi_hit_'+page)) return; sessionStorage.setItem('mi_hit_'+page,'1'); }}catch(e){{}}
    var p=new URLSearchParams(attrib()); p.set('page',page); var b=p.toString();
    try{{ if(!navigator.sendBeacon||!navigator.sendBeacon(TRACK,new Blob([b],{{type:'application/x-www-form-urlencoded'}}))){{ fetch(TRACK,{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:b,keepalive:true}}).catch(function(){{}}); }} }}catch(e){{}} }};
  miHit('{page}');
}})();
</script>
</head>
<body>
<a class="skip" href="#main">דילוג לתוכן</a>
<header class="site">
  <div class="bar">
    <a href="/" aria-label="אמא משקיעה, דף הבית"><img src="/assets/logo.png" alt="אמא משקיעה"></a>
    <nav aria-label="ניווט ראשי">
      <a href="/adi-somech/">עדי סומך</a>
      <a class="hide-m" href="/#method">השיטה</a>
      <a class="hide-m" href="/#testimonials">מהשטח</a>
      <a href="/blog/">מאמרים</a>
      <a href="/madrichim/">מדריכים חינמיים</a>
      <a class="cta" href="{livui}?utm_source=site&utm_medium=nav">הליווי »</a>
    </nav>
  </div>
</header>
<main id="main">
"""

FOOT = """
</main>
<footer>
  <div class="wrap wide">
    <div class="fgrid">
      <div>
        <img src="/assets/logo.png" alt="אמא משקיעה" style="height:40px;width:auto;margin-bottom:10px">
        <p style="margin:0;max-width:40ch">עדי סומך, מייסדת אמא משקיעה. מלווה אמהות לבנות רשת ביטחון למשפחה מהכסף שכבר יש להן.</p>
      </div>
      <div><h4>ניווט</h4><ul><li><a href="/adi-somech/">עדי סומך</a></li><li><a href="/#story">הסיפור שלי</a></li><li><a href="/#method">השיטה</a></li><li><a href="/#testimonials">מהשטח</a></li><li><a href="/blog/">מאמרים</a></li><li><a href="/madrichim/">מדריכים חינמיים</a></li><li><a href="{livui}?utm_source=site&utm_medium=footer">תכנית הליווי</a></li></ul></div>
      <div><h4>עוד</h4><ul><li><a href="https://academy.mominvest.co.il/calculator" target="_blank" rel="noopener">מחשבון ריבית דריבית</a></li><li><a href="https://500k.mominvest.co.il/?utm_source=site&utm_medium=footer" target="_blank" rel="noopener">מנגנון החצי מיליון</a></li><li><a href="https://podcasts.apple.com/il/podcast/id1809721347" target="_blank" rel="noopener">הפודקאסט</a></li><li><a href="https://www.instagram.com/adi_somech_" target="_blank" rel="noopener">אינסטגרם</a></li><li><a href="https://www.tiktok.com/@adi_somech_" target="_blank" rel="noopener">טיקטוק</a></li><li><a href="mailto:mominvest10x@gmail.com">צרי קשר</a></li></ul></div>
    </div>
    <div><strong style="color:var(--ink)">אמא משקיעה · עדי סומך</strong> · עוסק מורשה 204151658 · <a href="mailto:mominvest10x@gmail.com">mominvest10x@gmail.com</a></div>
    <div class="social">
      <a href="https://www.instagram.com/adi_somech_" rel="me noopener" target="_blank">אינסטגרם</a>
      <a href="https://www.tiktok.com/@adi_somech_" rel="me noopener" target="_blank">טיקטוק</a>
      <a href="https://www.facebook.com/profile.php?id=61579848634547" rel="me noopener" target="_blank">פייסבוק</a>
      <a href="https://podcasts.apple.com/il/podcast/id1809721347" rel="me noopener" target="_blank">הפודקאסט</a>
      <a href="https://www.linkedin.com/in/adi-somech-6471a318a/" rel="me noopener" target="_blank">לינקדאין</a>
    </div>
    <p style="margin:12px 0 0">האתר משתמש בקובצי מדידה כדי שנדע מה באמת עוזר לך. הכל מפורט כאן:</p>
    <div class="links">
      <a href="/terms.html">תנאי שימוש</a>
      <a href="/privacy.html">מדיניות פרטיות</a>
      <a href="/accessibility.html">הצהרת נגישות</a>
    </div>
    <div class="legal">
      <p>התכנים באתר הם לידע כללי בלבד ואינם ייעוץ השקעות, שיווק השקעות, ייעוץ פנסיוני או ייעוץ מס. עדי סומך ואמא משקיעה אינן בעלות רישיון בתחומים אלה ואינן ממליצות על נייר ערך, קרן, מסלול או גוף ספציפי. נתונים רגולטוריים מצוטטים מהמקורות הרשמיים ונכונים למועד הכתיבה; לפני כל החלטה כדאי לבדוק מול המקור ומול בעל רישיון.</p>
      <p style="margin:0">© 2026 אמא משקיעה · עדי סומך. כל הזכויות שמורות. אין להעתיק תכנים מהאתר ללא אישור בכתב.</p>
    </div>
  </div>
</footer>
<div class="cookie" id="cookieBar" role="region" aria-label="הודעת עוגיות" hidden>
  <span>האתר משתמש בקובצי מדידה (Meta Pixel ומדידה אנונימית) כדי להבין מה עוזר לך. <a href="/privacy.html">מדיניות פרטיות</a></span>
  <button type="button" id="cookieOk">הבנתי</button>
</div>
<button class="a11y-btn" id="a11yBtn" type="button" aria-expanded="false" aria-controls="a11yPanel" aria-label="הגדרות נגישות">
  <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><circle cx="12" cy="4.5" r="2.2" fill="currentColor"/><path d="M4.5 8.5c5 1.2 10 1.2 15 0l.5 1.9c-2 .5-3.9.8-5.5 1v3.1l2.6 6.4-2 .8-2.6-6.1h-1l-2.6 6.1-2-.8L9.5 14.5v-3.1c-1.6-.2-3.5-.5-5.5-1z" fill="currentColor"/></svg>
</button>
<div class="a11y-panel" id="a11yPanel" role="dialog" aria-label="הגדרות נגישות" hidden>
  <div class="a11y-title">נגישות</div>
  <div class="a11y-row"><span>טקסט גדול</span><button type="button" data-a11y="bigtext" aria-pressed="false">הפעלה</button></div>
  <div class="a11y-row"><span>ניגודיות גבוהה</span><button type="button" data-a11y="contrast" aria-pressed="false">הפעלה</button></div>
  <div class="a11y-row"><span>הדגשת קישורים</span><button type="button" data-a11y="links" aria-pressed="false">הפעלה</button></div>
  <div class="a11y-row"><span>עצירת תנועה</span><button type="button" data-a11y="noanim" aria-pressed="false">הפעלה</button></div>
  <div class="a11y-row"><span></span><button type="button" data-a11y="reset">איפוס</button></div>
  <a class="a11y-link" href="/accessibility.html">הצהרת נגישות</a>
</div>
<script>
(function(){
  var KEY='mm_a11y', root=document.documentElement, btn=document.getElementById('a11yBtn'), panel=document.getElementById('a11yPanel');
  var state={}; try{ state=JSON.parse(localStorage.getItem(KEY)||'{}')||{}; }catch(e){}
  function apply(){ ['bigtext','contrast','links','noanim'].forEach(function(k){ root.classList.toggle('a11y-'+k,!!state[k]); var b=panel.querySelector('[data-a11y="'+k+'"]'); if(b){ b.setAttribute('aria-pressed',state[k]?'true':'false'); b.textContent=state[k]?'כיבוי':'הפעלה'; } }); try{ localStorage.setItem(KEY,JSON.stringify(state)); }catch(e){} }
  btn.addEventListener('click',function(){ var open=panel.hidden; panel.hidden=!open; btn.setAttribute('aria-expanded',open?'true':'false'); });
  panel.addEventListener('click',function(e){ var b=e.target.closest('[data-a11y]'); if(!b) return; var k=b.getAttribute('data-a11y'); if(k==='reset'){ state={}; } else { state[k]=!state[k]; } apply(); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&!panel.hidden){ panel.hidden=true; btn.setAttribute('aria-expanded','false'); btn.focus(); } });
  (function(){ var b=document.getElementById('cookieBar'), ok=document.getElementById('cookieOk'); if(!b) return; var seen=false; try{ seen=localStorage.getItem('mi_cookie_ok')==='1'; }catch(e){} if(!seen){ b.hidden=false; } ok.addEventListener('click',function(){ b.hidden=true; try{ localStorage.setItem('mi_cookie_ok','1'); }catch(e){} }); })();
  apply();
  document.querySelectorAll('a[href^="https://livui."]').forEach(function(a){ a.addEventListener('click',function(){ try{ window.miHit && miHit(document.body.dataset.page+'-to-livui'); }catch(e){} }); });
})();
</script>
</body>
</html>
"""

ORG = {"@type":"Organization","@id":SITE+"/#org","name":"אמא משקיעה",
       "alternateName":["Mama Investor","MomInvest","Mom Invest","עדי סומך אמא משקיעה","אמא משקיעה עדי סומך","משקיעה בעצמי","Adi Somech Mama Investor"],
       "url":SITE+"/","logo":SITE+"/assets/logo.png","email":"mominvest10x@gmail.com",
       "founder":{"@id":SITE+"/#adi"},
       "sameAs":["https://www.instagram.com/adi_somech_","https://www.tiktok.com/@adi_somech_",
                 "https://www.facebook.com/profile.php?id=61579848634547","https://podcasts.apple.com/il/podcast/id1809721347",
                 "https://www.linkedin.com/in/adi-somech-6471a318a/",LIVUI]}
ADI = {"@type":"Person","@id":SITE+"/#adi","name":"עדי סומך","alternateName":["Adi Somech","עדי סומך אמא משקיעה","עדי סומך משקיעה בעצמי","עדי סומך מאפרת","Adi Somech Nahir","עדי סומך נהיר"],
       "jobTitle":"מייסדת אמא משקיעה","knowsAbout":["השקעות לאמהות","חיסכון לכל ילד","תקציב משפחתי","קופת גמל להשקעה","קרן השתלמות","כספים אבודים","פנסיה"],
       "homeLocation":{"@type":"Country","name":"Israel"},"nationality":"IL",
       "mainEntityOfPage":SITE+"/adi-somech/","image":SITE+"/assets/adi.webp","url":SITE+"/",
       "description":"עדי סומך, מייסדת אמא משקיעה, מלווה אמהות לבנות הון משפחתי מכמה מאות שקלים בחודש.",
       "worksFor":{"@id":SITE+"/#org"},
       "sameAs":["https://www.instagram.com/adi_somech_","https://www.tiktok.com/@adi_somech_",
                 "https://podcasts.apple.com/il/podcast/id1809721347","https://www.linkedin.com/in/adi-somech-6471a318a/",
                 "https://www.facebook.com/profile.php?id=61579848634547","https://www.facebook.com/AdiSomechnahir","https://www.instagram.com/glam_team_il"]}
WEBSITE = {"@type":"WebSite","@id":SITE+"/#site","url":SITE+"/","name":"אמא משקיעה","inLanguage":"he","publisher":{"@id":SITE+"/#org"}}

def heb_date(iso):
    y,m,d = iso.split("-"); return "%d.%d.%s" % (int(d), int(m), y)

def ld(graph): return json.dumps({"@context":"https://schema.org","@graph":graph}, ensure_ascii=False)

def page(title, desc, url, body, pagekey, ldgraph, ogtype="website"):
    h = HEAD.format(title=html.escape(title), desc=html.escape(desc), url=url, site=SITE, ld=ld(ldgraph),
                    page=pagekey, livui=LIVUI, ogtype=ogtype)
    h = h.replace("<body>", '<body data-page="%s">' % pagekey)
    return h + body + FOOT.replace("{livui}", LIVUI)

def faq_ld(body):
    """שאלות ותשובות מתוך <details> בגוף המאמר → FAQPage."""
    qs = re.findall(r"<summary>(.*?)</summary>\s*<p>(.*?)</p>", body, re.S)
    if not qs: return None
    strip = lambda s: re.sub(r"<[^>]+>", "", s).strip()
    return {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":strip(q),
            "acceptedAnswer":{"@type":"Answer","text":strip(a)}} for q,a in qs]}

def build():
    posts = []
    for fn in sorted(os.listdir(os.path.join(ROOT,"content"))):
        if not fn.endswith(".md"): continue
        meta, body = parse(read(os.path.join(ROOT,"content",fn)))
        posts.append((meta, body))
    posts.sort(key=lambda x: int(x[0].get("order","99")))

    cta = lambda: ("""
<div class="cta-block">
  <h2>רוצה שמישהי תעשה איתך את זה, צעד אחרי צעד?</h2>
  <p>הליווי של אמא משקיעה: 28 יום שבסופם הכסף שלך מסודר ועובד בשבילך. עם עדי, בקבוצה קטנה.</p>
  <a class="btn" href="%s?utm_source=site&utm_medium=article">לכל הפרטים על הליווי »</a>
</div>""" % LIVUI)

    author = """
<div class="author">
  <img src="/assets/adi.webp" alt="עדי סומך">
  <p><strong>עדי סומך, אמא משקיעה</strong>אמא לשתי בנות, בעלת עסק, ומלווה אמהות בישראל להפוך כמה מאות שקלים בחודש להון משפחתי. בלי ז'רגון, בלי פחד, צעד אחרי צעד. <a class="textlink" href="/">עוד עליי »</a></p>
</div>"""

    # מאמרים
    for i,(meta, body) in enumerate(posts):
        url = "%s/blog/%s/" % (SITE, meta["slug"])
        others = [p for j,p in enumerate(posts) if j != i][:3]
        slug = meta["slug"]
        if slug in ARTICLE_GUIDE:
            body = insert_mid(body, guide_box(ARTICLE_GUIDE[slug], slug))
        extra = course_box(slug) if slug in ARTICLE_500K else ""
        rel = "".join('<a class="post" href="/blog/%s/"><span class="q">%s</span><h3>%s</h3><span class="more">לקריאה »</span></a>' %
                      (m["slug"], html.escape(m["question"]), html.escape(m["title"])) for m,_ in others)
        page_body = """
<div class="article-head"><div class="wrap">
  <span class="eyebrow">%s</span>
  <h1>%s</h1>
  <p class="lead">%s</p>
  <p class="meta">מאת <a href="/">עדי סומך</a> · עודכן %s</p>
</div></div>
<article class="article"><div class="wrap">
%s
%s
%s
%s
<div class="related"><h2>עוד שאלות שאמהות שואלות</h2><div class="posts">%s</div></div>
</div></article>""" % (html.escape(meta["question"]), html.escape(meta["title"]), html.escape(meta.get("lead") or meta["description"]),
                       heb_date(meta.get("updated", TODAY)), body, extra, cta(), author, rel)
        graph = [ORG, ADI, WEBSITE,
                 {"@type":"Article","@id":url+"#article","headline":meta["title"],"description":meta["description"],
                  "inLanguage":"he","datePublished":meta.get("date",TODAY),"dateModified":meta.get("updated",TODAY),
                  "author":{"@id":SITE+"/#adi"},"publisher":{"@id":SITE+"/#org"},"mainEntityOfPage":url,
                  "image":SITE+"/assets/og.jpg","isPartOf":{"@id":SITE+"/#site"}},
                 {"@type":"BreadcrumbList","itemListElement":[
                    {"@type":"ListItem","position":1,"name":"אמא משקיעה","item":SITE+"/"},
                    {"@type":"ListItem","position":2,"name":"מאמרים","item":SITE+"/blog/"},
                    {"@type":"ListItem","position":3,"name":meta["title"],"item":url}]}]
        f = faq_ld(body)
        if f: graph.append(f)
        write(os.path.join(ROOT,"blog",meta["slug"],"index.html"),
              page(meta["title"]+" | אמא משקיעה", meta["description"], url, page_body, "blog-"+meta["slug"], graph, "article"))

    # אינדקס המאמרים
    cards = "".join('<a class="post" href="/blog/%s/"><span class="q">%s</span><h3>%s</h3><p>%s</p><span class="more">לקריאה »</span></a>' %
                    (m["slug"], html.escape(m["question"]), html.escape(m["title"]), html.escape(m["description"])) for m,_ in posts)
    idx = """
<section><div class="wrap wide">
  <span class="eyebrow">מאמרים</span>
  <h1>השאלות שאמהות מקלידות בגוגל בשתיים בלילה</h1>
  <p class="lead">תשובות פשוטות, במילים של עדי, עם המספרים מהמקורות הרשמיים. בלי ז'רגון ובלי פחד.</p>
  <div class="posts">%s</div>
</div></section>""" % cards
    write(os.path.join(ROOT,"blog","index.html"),
          page("מאמרים על כסף לאמהות | אמא משקיעה", "תשובות פשוטות לשאלות שאמהות שואלות על חיסכון לילדים, פנסיה, קרן כספית, S&P 500, כסף אבוד ותקציב משפחתי. מאת עדי סומך, אמא משקיעה.",
               SITE+"/blog/", idx, "blog-index", [ORG, ADI, WEBSITE,
               {"@type":"CollectionPage","@id":SITE+"/blog/#page","url":SITE+"/blog/","name":"מאמרים","isPartOf":{"@id":SITE+"/#site"},"inLanguage":"he"}]))

    # דף הבית
    home = read(os.path.join(ROOT,"build","home.html"))
    latest = "".join('<a class="post" href="/blog/%s/"><span class="q">%s</span><h3>%s</h3><span class="more">לקריאה »</span></a>' %
                     (m["slug"], html.escape(m["question"]), html.escape(m["title"])) for m,_ in posts[:6])
    home = home.replace("{{POSTS}}", latest).replace("{{LIVUI}}", LIVUI)
    write(os.path.join(ROOT,"index.html"),
          page("עדי סומך | אמא משקיעה · כסף שעובד בשביל המשפחה שלך",
               "עדי סומך, אמא משקיעה: השיטה שבה אלפי אמהות בישראל הופכות כמה מאות שקלים בחודש להון משפחתי ומסדרות את העתיד של הילדים. מאמרים, כלים ותכנית הליווי.",
               SITE+"/", home, "home", [ORG, ADI, WEBSITE,
               {"@type":"WebPage","@id":SITE+"/#page","url":SITE+"/","name":"עדי סומך | אמא משקיעה","isPartOf":{"@id":SITE+"/#site"},"about":{"@id":SITE+"/#adi"},"inLanguage":"he"}]))

    # עמוד "עדי סומך" (שם + כל הווריאציות)
    adi = read(os.path.join(ROOT,"build","adi.html")).replace("{{LIVUI}}", LIVUI)
    write(os.path.join(ROOT,"adi-somech","index.html"),
          page("עדי סומך | Adi Somech · מייסדת אמא משקיעה",
               "עדי סומך (Adi Somech): מייסדת אמא משקיעה ו\"משקיעה בעצמי\", לשעבר מאפרת ומעצבת שיער לכלות. מי היא, מה השיטה, הפודקאסט, הרשתות ותכנית הליווי לאמהות.",
               SITE+"/adi-somech/", adi, "adi-page", [ORG, ADI, WEBSITE,
               {"@type":"ProfilePage","@id":SITE+"/adi-somech/#page","url":SITE+"/adi-somech/","name":"עדי סומך","mainEntity":{"@id":SITE+"/#adi"},"isPartOf":{"@id":SITE+"/#site"},"inLanguage":"he"},
               faq_ld(adi) or {"@type":"Thing","name":"עדי סומך"}], "profile"))

    # עמוד המדריכים החינמיים
    gcards = "".join('<div class="box guide-box"><span class="eyebrow">מדריך חינמי</span><h2>%s</h2><p>%s</p><a class="btn" href="%s">%s</a></div>' %
                     (html.escape(g["title"]), html.escape(g["text"]), utm(g["url"], "guides-page", k), g["btn"]) for k,g in GUIDES.items())
    gpage = """
<div class="article-head"><div class="wrap">
  <span class="eyebrow">מדריכים חינמיים</span>
  <h1>המדריכים החינמיים של אמא משקיעה</h1>
  <p class="lead">כלים מעשיים שאפשר להתחיל איתם כבר היום: למצוא כסף שמחכה לך, ולבנות לילדים עתיד כלכלי. בחינם, ישר למייל.</p>
</div></div>
<article class="article"><div class="wrap">
%s
<div class="box guide-box"><span class="eyebrow">כלי חינמי</span><h2>מחשבון ריבית דריבית</h2><p>כמה יהיה שווה הסכום שלך בעוד 10, 20 ו-30 שנה? מכניסות סכום ורואות את התמונה.</p><a class="btn" href="https://academy.mominvest.co.il/calculator?utm_source=site&utm_medium=guides-page">למחשבון »</a></div>
%s
%s
<div class="related"><h2>מאמרים שכדאי לקרוא</h2><div class="posts">%s</div></div>
</div></article>""" % (gcards, course_box("guides-page"), cta(), "".join(
        '<a class="post" href="/blog/%s/"><span class="q">%s</span><h3>%s</h3><span class="more">לקריאה »</span></a>' %
        (m["slug"], html.escape(m["question"]), html.escape(m["title"])) for m,_ in posts[:6]))
    write(os.path.join(ROOT,"madrichim","index.html"),
          page("מדריכים חינמיים לאמהות על כסף | אמא משקיעה",
               "המדריכים החינמיים של עדי סומך, אמא משקיעה: איך למצוא 300-700 ש\"ח כל חודש, איך לסדר לילד 50-70 אלף ש\"ח מחיסכון לכל ילד, ומחשבון ריבית דריבית.",
               SITE+"/madrichim/", gpage, "guides", [ORG, ADI, WEBSITE,
               {"@type":"CollectionPage","@id":SITE+"/madrichim/#page","url":SITE+"/madrichim/","name":"מדריכים חינמיים","isPartOf":{"@id":SITE+"/#site"},"inLanguage":"he"}]))

    # sitemap + robots
    urls = [(SITE+"/", TODAY, "1.0"), (SITE+"/adi-somech/", TODAY, "0.9"), (SITE+"/blog/", TODAY, "0.8"), (SITE+"/madrichim/", TODAY, "0.8")] + \
           [("%s/blog/%s/" % (SITE, m["slug"]), m.get("updated",TODAY), "0.8") for m,_ in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
         "".join("  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n" % u for u in urls) + "</urlset>\n"
    write(os.path.join(ROOT,"sitemap.xml"), sm)
    write(os.path.join(ROOT,"robots.txt"), "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE)
    print("built: home, blog index, %d posts" % len(posts))

if __name__ == "__main__":
    build()
