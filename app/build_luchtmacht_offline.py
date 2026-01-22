#!/usr/bin/env python3
import os, json, time, re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO

BASE = "https://www.defensie.nl"
TOPICS = [
    "/onderwerpen/materieel/vliegtuigen-en-helikopters"
]

OUT_IMG = "app/images/luchtmacht"
OUT_JSON = "app/data/luchtmacht.json"

os.makedirs(OUT_IMG, exist_ok=True)

HEADERS = {"User-Agent": "NL Defence Speaking Trainer"}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def extract_image(html):
    m = re.search(r'(/binaries/large/[^"\']+)', html)
    return urljoin(BASE, m.group(1)) if m else None

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

questions = []
seen = set()

for topic in TOPICS:
    soup = BeautifulSoup(fetch(BASE + topic), "html.parser")
    for a in soup.select("a[href^='/onderwerpen/materieel/']"):
        url = urljoin(BASE, a["href"].split("?")[0])
        if url in seen:
            continue
        seen.add(url)

        html = fetch(url)
        title = BeautifulSoup(html, "html.parser").find("h1")
        if not title:
            continue
        name = title.text.strip()
        asset = slug(name)

        img_url = extract_image(html)
        if img_url:
            img = Image.open(BytesIO(requests.get(img_url).content))
            img.thumbnail((1200, 800))
            img.save(f"{OUT_IMG}/{asset}.jpg", "JPEG", quality=85)

        questions.append({
            "id": f"af_{asset}",
            "asset": asset,
            "class": "Aircraft",
            "answer": name,
            "aliases": [name.lower()]
        })

        print("✔", name)
        time.sleep(0.6)

json.dump({
    "quizLength": 10,
    "mcqOptions": 6,
    "classes": [
        "Fighter Aircraft",
        "Transport Aircraft",
        "Helicopter",
        "Maritime Patrol Aircraft",
        "Trainer Aircraft"
    ],
    "questions": questions
}, open(OUT_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print("✅ Luchtmacht klaar:", len(questions), "items")