#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

POSSIBLE_DATA_DIRS = [
    ROOT / "app" / "data",
    ROOT / "data",
]

FILES = {
    "landmacht": "landmacht.json",
    "luchtmacht": "luchtmacht.json",
    "marine": "marine.json",
}

OPTIONS_PATHS = [
    ROOT / "data" / "classification_options.json",
    ROOT / "app" / "data" / "classification_options.json",
]

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, obj: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def find_data_dir() -> Path:
    for d in POSSIBLE_DATA_DIRS:
        if d.exists():
            return d
    raise FileNotFoundError("Could not find data dir. Expected one of: app/data or data")

def find_options() -> Dict[str, List[str]]:
    for p in OPTIONS_PATHS:
        if p.exists():
            return load_json(p)
    raise FileNotFoundError("classification_options.json not found (looked in data/ and app/data/)")

def get_str_list(item: Dict[str, Any], keys: List[str]) -> List[str]:
    """Return list of strings for any of the keys found."""
    for k in keys:
        if k in item and item[k] is not None:
            v = item[k]
            if isinstance(v, list):
                return [str(x) for x in v]
            if isinstance(v, str):
                # allow "a, b, c" or single string
                return [s.strip() for s in v.split(",") if s.strip()]
    return []

def get_str(item: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        if k in item and isinstance(item[k], str):
            return item[k]
    return ""

# --- Heuristics -----------------------------------------------------------

LAND_ARMOURED = {"tank", "ifv", "afv", "armoured", "armored", "tracked", "mbt"}
LAND_TROOP = {"apc", "troop", "infantry", "carrier", "transport", "personnel"}
AIR_COMBAT = {"strike", "air superiority", "cas", "sead", "dead", "fighter", "bomber", "attack"}
AIR_TRANSPORT = {"airlift", "transport", "medevac", "utility", "cargo", "tanker"}
AIR_RECON = {"isr", "recon", "reconnaissance", "ew", "elint", "sigint", "aew", "awacs", "mpa", "maritime patrol"}

SEA_FIGHTING = {"asuw", "aaw", "asw", "strike", "frigate", "destroyer", "corvette", "submarine"}
SEA_PATROL = {"patrol", "mcm", "mine countermeasures", "security", "coast", "interdiction"}
SEA_SUPPORT = {"support", "auxiliary", "replenishment", "logistics", "amphib", "lpd", "jss", "tender", "survey", "salvage"}

def normalize_tokens(*parts: List[str]) -> List[str]:
    tokens = []
    for p in parts:
        for s in p:
            tokens.append(s.lower().strip())
    return tokens

def infer_land(item: Dict[str, Any]) -> Tuple[str, str]:
    """
    Returns (category, confidence) where confidence is 'high'|'medium'|'low'
    """
    type_str = get_str(item, ["type", "vehicleType", "platformType", "class"])
    roles = get_str_list(item, ["roles", "nato_roles", "natoRoles", "role"])
    tags  = get_str_list(item, ["tags", "keywords"])

    tokens = normalize_tokens([type_str], roles, tags)

    if any(t in " ".join(tokens) for t in LAND_ARMOURED):
        return ("Armoured vehicle", "high")
    if any(t in " ".join(tokens) for t in LAND_TROOP):
        return ("Infantry / Troop transport", "high")
    # fallback
    return ("Support vehicle", "low")

def infer_air(item: Dict[str, Any]) -> Tuple[str, str]:
    type_str = get_str(item, ["type", "aircraftType", "platformType", "class"])
    roles = get_str_list(item, ["roles", "nato_roles", "natoRoles", "role"])
    tags  = get_str_list(item, ["tags", "keywords"])

    tokens = normalize_tokens([type_str], roles, tags)
    blob = " ".join(tokens)

    if any(k in blob for k in AIR_COMBAT):
        return ("Combat", "high")
    if any(k in blob for k in AIR_TRANSPORT):
        return ("Transport", "high")
    if any(k in blob for k in AIR_RECON):
        return ("Reconnaissance", "high")

    # weaker type-based fallback
    if "fighter" in blob or "attack" in blob or "bomber" in blob:
        return ("Combat", "medium")
    if "helicopter" in blob and ("transport" in blob or "utility" in blob):
        return ("Transport", "medium")
    return ("Reconnaissance", "low")

def infer_sea(item: Dict[str, Any]) -> Tuple[str, str]:
    type_str = get_str(item, ["type", "shipType", "platformType", "class"])
    roles = get_str_list(item, ["roles", "nato_roles", "natoRoles", "role"])
    tags  = get_str_list(item, ["tags", "keywords"])

    tokens = normalize_tokens([type_str], roles, tags)
    blob = " ".join(tokens)

    if any(k in blob for k in SEA_FIGHTING):
        return ("Fighting ship", "high")
    if any(k in blob for k in SEA_PATROL):
        return ("Patrol ship", "high")
    if any(k in blob for k in SEA_SUPPORT):
        return ("Support ship", "high")

    # fallback
    return ("Support ship", "low")

INFER = {
    "landmacht": infer_land,
    "luchtmacht": infer_air,
    "marine": infer_sea,
}

def iter_items(data: Any) -> List[Dict[str, Any]]:
    """
    Support data as:
    - list[dict]
    - dict with 'items' list
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    raise ValueError("Unsupported JSON format: expected a list or {items:[...]}")

def main() -> None:
    data_dir = find_data_dir()
    options = find_options()

    report = {"updated": [], "already_ok": [], "invalid_fixed": [], "low_confidence": []}

    for domain, fname in FILES.items():
        path = data_dir / fname
        if not path.exists():
            print(f"[WARN] Missing file: {path}")
            continue

        data = load_json(path)
        items = iter_items(data)

        allowed = set(options[domain])

        changed = False
        for it in items:
            # existing category?
            cat = it.get("category")
            if isinstance(cat, str) and cat in allowed:
                report["already_ok"].append((domain, it.get("id", it.get("name", "unknown"))))
                continue

            if isinstance(cat, str) and cat not in allowed:
                # fix invalid existing category
                inferred, conf = INFER[domain](it)
                it["category"] = inferred
                changed = True
                report["invalid_fixed"].append((domain, it.get("id", it.get("name", "unknown")), cat, inferred, conf))
                if conf == "low":
                    report["low_confidence"].append((domain, it.get("id", it.get("name", "unknown")), inferred))
                continue

            # no category: infer
            inferred, conf = INFER[domain](it)
            it["category"] = inferred
            changed = True
            report["updated"].append((domain, it.get("id", it.get("name", "unknown")), inferred, conf))
            if conf == "low":
                report["low_confidence"].append((domain, it.get("id", it.get("name", "unknown")), inferred))

        if changed:
            save_json(path, data)
            print(f"[OK] Wrote updated categories to {path}")
        else:
            print(f"[OK] No changes needed for {path}")

    # write report
    report_path = ROOT / "tools" / "apply_step1_categories_report.json"
    save_json(report_path, report)
    print(f"[DONE] Report written to {report_path}")

if __name__ == "__main__":
    main()
