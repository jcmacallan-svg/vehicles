#!/usr/bin/env python3
"""
Sync app/data.json questions to whatever is in app/images/*.jpg

- Keeps existing class/answer if an entry already exists for that asset.
- Creates new entries for new images.
- Removes entries for deleted images.

Run from repo root:
  python3 tools/sync_datajson_from_images.py --images app/images --data app/data.json
"""
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--data", required=True)
    args = ap.parse_args()

    img_dir = Path(args.images)
    data_path = Path(args.data)

    data = json.loads(data_path.read_text(encoding="utf-8"))
    existing = {q.get("asset"): q for q in data.get("questions", []) if q.get("asset")}

    assets = sorted([p.stem for p in img_dir.glob("*.jpg")])
    questions = []
    for i, asset in enumerate(assets, 1):
        base = existing.get(asset, {})
        answer = base.get("answer") or asset.replace("-", " ").title()
        klass = base.get("class") or "Unarmoured Vehicle"
        q = {
            "id": base.get("id") or f"lm_{asset}_{i}",
            "asset": asset,
            "class": klass,
            "answer": answer,
            "aliases": sorted({answer.lower(), asset.replace("-", " ").lower()}),
        }
        questions.append(q)

    data["questions"] = questions
    data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("✅ Synced data.json to images/")
    print("Images found (jpg):", len(assets))
    print("Questions written:", len(questions))

if __name__ == "__main__":
    main()
