#!/usr/bin/env python3
import json
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
    for k in keys:
        if k in item and item[k] is not None:
            v = item[k]
            if isinstance(v, list):
                return [str(x) for x in v]
            if isinstance(v, str):
                return [s.strip() for s in v.split(",") if s.strip()]
    return []

def get_str(item: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        if k in item and isinstance(item[k], str):
            return item[k]
    return ""

# --- Heuristics -----------------------------------------------------------

LAND_ARMOURED = {"tank", "ifv", "afv", "armoured", "armored", "tracked", "mbt"}
LAND_TROOP    = {"apc", "troop", "infantry", "carrier", "transport", "personnel"}

AIR_COMBAT    = {"strike", "air superiority", "cas", "sead", "dead", "fighter", "bomber", "attack"}
AIR_TRANSPORT = {"airlift", "transport", "medevac", "utility", "cargo", "tanker"}
AIR_RECON     = {"isr", "recon", "reconnaissance", "ew", "elint", "sigint", "aew", "awacs", "mpa", "maritime patrol"}

SEA_FIGHTING  = {"asuw", "aaw", "asw", "strike", "frigate", "destroyer", "corvette", "submarine"}
SEA_PATROL    = {"patrol", "mcm", "mine countermeasures", "security", "coast", "interdiction"}
SEA_SUPPORT   = {"support", "auxiliary", "replenishment", "logistics", "amphib", "lpd", "jss", "tender", "survey", "salvage"}

def normalize_tokens(*parts: List[str]) -> List[str]:
    tokens: List[str] = []
    for p in parts:
        for s in p:
            tokens.append(str(s).lower().strip())
    return tokens

def infer_land(item: Dict[str, Any]) -> Tuple[str, str]:
    type_str = get_str(item, ["type", "vehicleType", "platformType", "class"])
    roles = get_str_list(item, ["roles", "nato_roles", "natoRoles", "role"])
    tags  = get_str_list(item, ["tags", "keywords"])

    blob = " ".join(normalize_tokens([type_str], roles, tags))

    if any(k in blob for k in LAND_ARMOURED):
        return ("Combat vehicle", "high")
    if any(k in blob for k in LAND_TROOP):
        return ("Infantry / Troop transport", "high")
    return ("Support vehicle", "low")

def infer_air(item: Dict[str, Any]) -> Tuple[str, str]:
    type_str = get_str(item, ["type", "aircraftType", "platformType", "class"])
    roles = get_str_list(item, ["roles", "nato_roles", "natoRoles", "role"])
    tags  = get_str_list(item, ["tags", "keywords"])

    blob = " ".join(normalize_tokens([type_str], roles, tags))

    if any(k in blob for k in AIR_COMBAT):
        return ("Combat", "high")
    if any(k in blob for k in AIR_TRANSPORT):
        return ("Transport", "high")
    if any(k in blob for k in AIR_RECON):
        return ("Reconnaissance", "high")

    if "fighter" in blob or "attack" in blob or "bomber" in blob:
        return ("Combat", "medium")
    if "helicopter" in blob and ("transport" in blob or "utility" in blob):
        return ("Transport", "medium")

    return ("Reconnaissance", "low")

def infer_sea(item: Dict[str, Any]) -> Tuple[str, str]:
    type_str = get_str(item, ["type", "shipType", "platformType", "class"])
    roles = get_str_list(item, ["roles", "nato_roles", "natoRoles", "role"])
    tags  = get_str_list(item, ["tags", "keywords"])

    blob = " ".join(normalize_tokens([type_str], roles, tags))

    if any(k in blob for k in SEA_FIGHTING):
        return ("Fighting ship", "high")
    if any(k in blob for k in SEA_PATROL):
        return ("Patrol ship", "high")
    if any(k in blob for k in SEA_SUPPORT):
        return ("Support ship", "high")

    return ("Support ship", "low")

INFER = {
    "landmacht": infer_land,
    "luchtmacht": infer_air,
    "marine": infer_sea,
}

def iter_items(data: Any) -> Tuple[List[Dict[str, Any]], Any, str]:
    """
    Returns (items, owner, key)
    - items: the list we will process
    - owner: the dict that owns the list (or the list itself)
    - key: the key in owner containing the list, or "" if data is already a list
    Special case:
    - if data contains {"categories": { ... }} then returns ([], data, "categories")
      and main() will iterate buckets.
    """
    if isinstance(data, list):
        return data, data, ""

    if isinstance(data, dict):
        for k in ["items", "vehicles", "data", "records", "entries"]:
            if isinstance(data.get(k), list):
                return data[k], data, k

        # domain-keyed list
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v, data, k

        if isinstance(data.get("categories"), dict):
            return [], data, "categories"

    raise ValueError(
        "Unsupported JSON format. Expected list, or dict containing a list under one of "
        "['items','vehicles','data','records','entries'] or a domain-keyed list."
    )

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
        items, owner, key = iter_items(data)

        allowed = set(options[domain])
        changed = False

        def process_items(items_list: List[Dict[str, Any]]) -> None:
            nonlocal changed
            for it in items_list:
                cat = it.get("category")
                ident = it.get("id", it.get("name", "unknown"))

                if isinstance(cat, str) and cat in allowed:
                    report["already_ok"].append((domain, ident))
                    continue

                inferred, conf = INFER[domain](it)
                it["category"] = inferred
                changed = True

                if isinstance(cat, str) and cat not in allowed:
                    report["invalid_fixed"].append((domain, ident, cat, inferred, conf))
                else:
                    report["updated"].append((domain, ident, inferred, conf))

                if conf == "low":
                    report["low_confidence"].append((domain, ident, inferred))

        # Special case: nested buckets under "categories"
        if key == "categories" and isinstance(owner.get("categories"), dict):
            for bucket_name, bucket_items in owner["categories"].items():
                if isinstance(bucket_items, list) and (not bucket_items or isinstance(bucket_items[0], dict)):
                    process_items(bucket_items)
        else:
            process_items(items)

        if changed:
            save_json(path, data)
            print(f"[OK] Wrote updated categories to {path}")
        else:
            print(f"[OK] No changes needed for {path}")

    report_path = ROOT / "tools" / "apply_step1_categories_report.json"
    save_json(report_path, report)
    print(f"[DONE] Report written to {report_path}")

if __name__ == "__main__":
    main()