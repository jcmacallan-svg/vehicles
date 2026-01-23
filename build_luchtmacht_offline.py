#!/usr/bin/env python3
import argparse, os, re, time, json
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
from io import BytesIO

BASE = "https://www.defensie.nl"
TOPIC = f"{BASE}/onderwerpen/materieel/vliegtuigen-en-helikopters"
UA = {"User-Agent":"Mozilla/5.0 (speaking trainer scraper)"}

def fetch(url:str)->str:
    r = requests.get(url, timeout=60, headers=UA)
    r.raise_for_status()
    return r.text

def extract_title(html:str):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I|re.S)
    if not m: return None
    t = re.sub(r"<[^>]+>", "", m.group(1))
    return re.sub(r"\s+"," ",t).strip()

def extract_large_image_url(html:str):
    m = re.search(r'(/binaries/large/[^"\'>\s]+)', html)
    if not m: return None
    return urljoin(BASE, m.group(1))

def slug(s:str)->str:
    s = s.lower()
    s = re.sub(r"[’'\"`]", "", s)
    s = re.sub(r"[^a-z0-9]+","-", s).strip("-")
    return (s[:70] or "item")

def resize_to(jpg_bytes:bytes, size):
    im = Image.open(BytesIO(jpg_bytes)).convert("RGB")
    im = ImageOps.exif_transpose(im)
    im = ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(0.5,0.5))
    out = BytesIO()
    im.save(out, "JPEG", quality=88, optimize=True, progressive=True)
    return out.getvalue()

def aliases(title:str):
    t = re.sub(r"\s+"," ", title.lower()).strip()
    a = {t}
    # korte alias: alles vóór haakjes
    a.add(re.sub(r"\s*$begin:math:text$.*?$end:math:text$\s*", "", t).strip())
    return sorted(x for x in a if x)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="app", help="App folder")
    ap.add_argument("--size", default="900x600", help="e.g. 900x600")
    ap.add_argument("--delay", type=float, default=0.6)
    args = ap.parse_args()
    w,h = map(int, args.size.lower().split("x"))

    out_dir = args.out
    img_dir = os.path.join(out_dir, "images", "luchtmacht")
    os.makedirs(img_dir, exist_ok=True)
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    print("Fetching:", TOPIC)
    topic_html = fetch(TOPIC)
    soup = BeautifulSoup(topic_html, "html.parser")

    # Alleen links binnen dit onderwerp
    item_pages = []
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#")[0].split("?")[0]
        if href.startswith("/onderwerpen/materieel/vliegtuigen-en-helikopters/"):
            item_pages.append(urljoin(BASE, href))

    # dedupe
    seen=set(); pages=[]
    for u in item_pages:
        if u not in seen:
            seen.add(u); pages.append(u)

    print("Items found:", len(pages))

    questions=[]
    for i, page in enumerate(pages, 1):
        try:
            html = fetch(page)
            title = extract_title(html) or f"Luchtmacht item {i}"
            img_url = extract_large_image_url(html)
            asset = slug(title)

            if img_url:
                img_bytes = requests.get(img_url, timeout=90, headers=UA).content
                jpg = resize_to(img_bytes, (w,h))
                with open(os.path.join(img_dir, asset+".jpg"), "wb") as f:
                    f.write(jpg)

            questions.append({
                "id": f"af_{asset}_{i}",
                "asset": asset,
                "class": "UNKNOWN",          # later classificeren (Fighter/Transport/Helicopter/UAS/etc.)
                "answer": title,
                "aliases": aliases(title),
                "source_page": page
            })
            print(f"[{i}/{len(pages)}] OK:", title)
            time.sleep(args.delay)
        except Exception as e:
            print(f"[{i}/{len(pages)}] SKIP:", page, e)

    luchtmacht_json = {
        "quizLength": 10,
        "mcqOptions": 6,
        "classes": [
            "Fighter Aircraft",
            "Transport Aircraft",
            "Helicopter",
            "Trainer Aircraft",
            "Uncrewed Aerial System (UAS)",
            "Other"
        ],
        "questions": questions
    }

    out_json = os.path.join(out_dir, "data", "luchtmacht.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(luchtmacht_json, f, indent=2, ensure_ascii=False)

    print("DONE:", out_json, "questions:", len(questions))
    print("Images in:", img_dir)

if __name__ == "__main__":
    main()