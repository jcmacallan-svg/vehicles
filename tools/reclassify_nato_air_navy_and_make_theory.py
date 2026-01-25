#!/usr/bin/env python3
"""
Reclassify Luchtmacht + Marine datasets to NATO role-based classes
and generate optional Theory JSON files for the Speaking Trainer.

Assumptions:
- Your repo has:
    app/data/luchtmacht.json
    app/data/marine.json
- Each question has at least:
    { "asset": "...", "answer": "Title ..." }
  Optionally: "source_page"

What it does:
- Updates "classes" list to NATO role-based set (full names).
- Auto-classifies each question based on keywords in the "answer" (and "source_page" if present).
- Writes backups:
    app/data/luchtmacht.json.bak
    app/data/marine.json.bak
- Creates:
    app/theory/luchtmacht.json
    app/theory/marine.json

Run (from repo root):
    source .venv/bin/activate   # if you use venv
    python3 tools/reclassify_nato_air_navy_and_make_theory.py
"""

import json, re
from pathlib import Path

AIR_PATH = Path("app/data/luchtmacht.json")
NAVY_PATH = Path("app/data/marine.json")

AIR_CLASSES = [
  "Fighter Aircraft",
  "Transport Aircraft",
  "Helicopter",
  "Trainer Aircraft",
  "Uncrewed Aerial System (UAS)",
  "Other"
]

NAVY_CLASSES = [
  "Submarine",
  "Frigate",
  "Patrol Vessel",
  "Amphibious Ship",
  "Mine Countermeasures Vessel",
  "Support Vessel",
  "Other"
]

def load(p: Path):
  with p.open("r", encoding="utf-8") as f:
    return json.load(f)

def save(p: Path, obj):
  with p.open("w", encoding="utf-8") as f:
    json.dump(obj, f, indent=2, ensure_ascii=False)

def backup(p: Path):
  b = p.with_suffix(p.suffix + ".bak")
  if not b.exists():
    b.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
  return b

def norm(s: str) -> str:
  return re.sub(r"\s+", " ", (s or "")).strip().lower()

def classify_air(answer: str, source_page: str = "") -> str:
  t = norm(answer)
  u = norm(source_page)

  if any(k in t for k in ["drone", "onbemand", "onbemande", "uav", "uas", "mq-9", "mq9", "reaper"]):
    return "Uncrewed Aerial System (UAS)"
  if any(k in t for k in ["helikopter", "helicopter", "apache", "chinook", "nh90", "cougar"]):
    return "Helicopter"
  if any(k in t for k in ["lesvliegtuig", "trainer", "training", "pc-7", "pc7", "pilatus"]):
    return "Trainer Aircraft"
  if any(k in t for k in ["jachtvliegtuig", "fighter", "f-35", "f35", "f-16", "f16"]):
    return "Fighter Aircraft"
  if any(k in t for k in ["transport", "transportvliegtuig", "tanker", "tankvliegtuig", "kdc-10", "kdc10", "a330", "mrt", "mrt t", "c-130", "c130", "hercules", "gulfstream"]):
    return "Transport Aircraft"

  if any(k in u for k in ["f-35", "f-16"]):
    return "Fighter Aircraft"
  if any(k in u for k in ["apache", "chinook", "nh90", "helikopter"]):
    return "Helicopter"

  return "Other"

def classify_ship(answer: str, source_page: str = "") -> str:
  t = norm(answer)
  u = norm(source_page)

  if any(k in t for k in ["onderzeeboot", "submarine", "walrusklasse", "walrus-klasse", "walrus"]):
    return "Submarine"
  if any(k in t for k in ["fregat", "frigate", "zeven provinci", "zevenprovincien", "zeven provinciën", "lcf", "luchtverdedigings- en commandofregat", "m-fregat", "multipurpose fregat"]):
    return "Frigate"
  if any(k in t for k in ["patrouille", "patrol", "opv", "hollandklasse", "holland-klasse", "offshore patrol"]):
    return "Patrol Vessel"
  if any(k in t for k in ["amfib", "amphib", "landingsschip", "landing platform", "rotterdam", "johan de witt", "johan-de-witt"]):
    return "Amphibious Ship"
  if any(k in t for k in ["mijnenjager", "mijnenbestr", "mine counter", "mcm", "alkmaar", "alkmaarklasse", "alkmaar-klasse"]):
    return "Mine Countermeasures Vessel"
  if any(k in t for k in ["bevoorrad", "support", "ondersteun", "tanker", "logistiek", "karel doorman", "doorman", "combat support", "hydrograf", "sleepboot", "hulpvaartuig"]):
    return "Support Vessel"

  if "onderzeeboot" in u:
    return "Submarine"
  if "fregat" in u or "lcf" in u:
    return "Frigate"
  if "opv" in u or "patrouille" in u:
    return "Patrol Vessel"
  if "mijnen" in u:
    return "Mine Countermeasures Vessel"

  return "Other"

def make_theory_air():
  return {
    "title": "Royal Netherlands Air Force – NATO role classification",
    "intro": [
      "In NATO recognition, classify by role first (what it is used for).",
      "Use simple English: 'This is a … It is used for …'."
    ],
    "items": {
      "Fighter Aircraft": {
        "bullets": [
          "Used for air combat and precision strike missions.",
          "Fast aircraft with advanced sensors.",
          "Often armed and built for high performance."
        ],
        "why_not": "Not a transport aircraft because it is not designed to carry cargo or many passengers."
      },
      "Transport Aircraft": {
        "bullets": [
          "Used to move people and cargo over distance.",
          "Large internal space for cargo or passengers.",
          "Often used for logistics and humanitarian support."
        ],
        "why_not": "Not a fighter aircraft because it is not built for air-to-air combat."
      },
      "Helicopter": {
        "bullets": [
          "Can take off and land vertically.",
          "Can hover and fly at low speed.",
          "Used for transport, attack, and rescue."
        ],
        "why_not": "Not a fixed-wing aircraft because it uses rotors, not wings, for lift."
      },
      "Trainer Aircraft": {
        "bullets": [
          "Used for pilot training.",
          "Usually lighter and simpler than combat aircraft.",
          "Often unarmed or lightly equipped."
        ],
        "why_not": "Not a fighter aircraft because its main role is training, not combat."
      },
      "Uncrewed Aerial System (UAS)": {
        "bullets": [
          "No pilot onboard (remotely piloted or autonomous).",
          "Often used for surveillance and reconnaissance.",
          "Can stay airborne for long periods."
        ],
        "why_not": "Not a helicopter because it is uncrewed and operates differently."
      },
      "Other": {
        "bullets": [
          "Special-purpose aircraft or items that do not fit the main roles.",
          "Classify by best match; if unsure, use Other.",
          "Teacher can discuss the closest NATO role."
        ],
        "why_not": "Used when the primary role is unclear or unique."
      }
    }
  }

def make_theory_navy():
  return {
    "title": "Royal Netherlands Navy – NATO role classification",
    "intro": [
      "In NATO recognition, classify ships by role and capability.",
      "Use simple English: 'This is a … It is used for …'."
    ],
    "items": {
      "Submarine": {
        "bullets": [
          "Operates underwater for stealth.",
          "Used for intelligence and sea denial.",
          "Carries torpedoes and sensors."
        ],
        "why_not": "Not a surface ship because it operates mainly underwater."
      },
      "Frigate": {
        "bullets": [
          "Multi-role warship for escort and task groups.",
          "Often used for air defence and anti-submarine warfare.",
          "Has advanced sensors and weapons."
        ],
        "why_not": "Not a patrol vessel because it has heavier combat capability."
      },
      "Patrol Vessel": {
        "bullets": [
          "Used for maritime security and patrol tasks.",
          "Usually lighter weapons than major warships.",
          "Long endurance for presence at sea."
        ],
        "why_not": "Not a frigate because it has fewer sensors and lighter weapons."
      },
      "Amphibious Ship": {
        "bullets": [
          "Used to transport troops and vehicles.",
          "Can support landings with landing craft and helicopters.",
          "Acts as a command and support platform."
        ],
        "why_not": "Not a frigate because its main role is transport and landing support."
      },
      "Mine Countermeasures Vessel": {
        "bullets": [
          "Used to detect and neutralize sea mines.",
          "Specialized sonar and mine disposal systems.",
          "Often supports safe routes for other ships."
        ],
        "why_not": "Not a patrol vessel because its primary mission is mine warfare."
      },
      "Support Vessel": {
        "bullets": [
          "Provides fuel, food, ammunition, or repairs at sea.",
          "Keeps task groups operational for longer.",
          "Usually not designed for front-line combat."
        ],
        "why_not": "Not a frigate because its main role is logistics, not combat."
      },
      "Other": {
        "bullets": [
          "Special-purpose vessels that do not fit the main roles.",
          "Classify by best match; if unsure, use Other.",
          "Teacher can discuss the closest NATO role."
        ],
        "why_not": "Used when the primary role is unclear or unique."
      }
    }
  }

def attach_examples(theory: dict, questions: list):
  by_class = {}
  for q in questions:
    by_class.setdefault(q.get("class", "Other"), []).append(q)
  for cls, item in theory["items"].items():
    ex = by_class.get(cls, [])[:1]
    item["example_asset"] = ex[0]["asset"] if ex else None
    item["example_answer"] = ex[0].get("answer") if ex else None

def main():
  updated = 0

  # Air
  if AIR_PATH.exists():
    air = load(AIR_PATH)
    backup(AIR_PATH)
    air["classes"] = AIR_CLASSES
    for q in air.get("questions", []):
      q["class"] = classify_air(q.get("answer",""), q.get("source_page",""))
      updated += 1
    save(AIR_PATH, air)

    Path("app/theory").mkdir(parents=True, exist_ok=True)
    th = make_theory_air()
    attach_examples(th, air.get("questions", []))
    save(Path("app/theory/luchtmacht.json"), th)
    print("✅ Updated:", AIR_PATH, "questions:", len(air.get("questions", [])))
  else:
    print("⚠️ Missing:", AIR_PATH)

  # Navy
  if NAVY_PATH.exists():
    nav = load(NAVY_PATH)
    backup(NAVY_PATH)
    nav["classes"] = NAVY_CLASSES
    for q in nav.get("questions", []):
      q["class"] = classify_ship(q.get("answer",""), q.get("source_page",""))
      updated += 1
    save(NAVY_PATH, nav)

    Path("app/theory").mkdir(parents=True, exist_ok=True)
    th = make_theory_navy()
    attach_examples(th, nav.get("questions", []))
    save(Path("app/theory/marine.json"), th)
    print("✅ Updated:", NAVY_PATH, "questions:", len(nav.get("questions", [])))
  else:
    print("⚠️ Missing:", NAVY_PATH)

  print("DONE. Updated question records:", updated)
  print("Theory files created in: app/theory/")

if __name__ == "__main__":
  main()
