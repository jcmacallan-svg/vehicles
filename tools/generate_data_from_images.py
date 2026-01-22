#!/usr/bin/env python3
"""Generate app/data.json from your existing app/images/*.jpg filenames.

Usage:
  python3 generate_data_from_images.py --images app/images --out app/data.json
"""
import argparse, os, json, re

VEHICLE_CLASSES = [
 "Battle Tank (BT)",
 "Armoured Infantry Fighting Vehicle (AIFV)",
 "Armoured Patrol Car (AP)",
 "Armoured Personnel Carrier (APC)",
 "Heavy Armament Combat Vehicle (HACV)",
 "(Armoured) Engineer Vehicle (A/EV)",
 "(Armoured) Vehicle Laying Bridge (A/VLB)",
 "(Armoured) Recovery Vehicle (A/RV)",
 "Artillery (Art)",
 "Air Defence (AD)",
 "Reconnaissance Vehicle (RV)",
 "Armoured Cars (AC)"
]

REPL = [
 (r"\\bgevechtstank\\b","main battle tank"),
 (r"\\bbergingstank\\b","armoured recovery vehicle"),
 (r"\\bbrugleggende-tank\\b","armoured vehicle launched bridge"),
 (r"\\bgeniedoorbraaksysteem\\b","armoured engineer vehicle"),
 (r"\\binfanteriegevechtsvoertuig\\b","infantry fighting vehicle"),
 (r"\\bverkenningsvoertuig\\b","reconnaissance vehicle"),
 (r"\\bpantserrupsvoertuig\\b","armoured tracked vehicle"),
 (r"\\bpantserwielvoertuig\\b","armoured wheeled vehicle"),
 (r"\\bpantservoertuig\\b","armoured vehicle"),
 (r"\\brupsvoertuig\\b","tracked vehicle"),
 (r"\\bterreinwagen\\b","all-terrain vehicle"),
 (r"\\bterreinvoertuig\\b","all-terrain vehicle"),
 (r"\\btransportvoertuig\\b","transport vehicle"),
 (r"\\bwissellaadsysteem\\b","hooklift system"),
 (r"\\btakelwagens?\\b","recovery truck"),
 (r"\\btrekker-opleggercombinatie\\b","tractor‑trailer combination"),
 (r"\\bde-4-tonner\\b","4‑ton truck"),
 (r"\\bcrashtender\\b","crash tender"),
 (r"\\bbrandweerwagen\\b","fire truck"),
 (r"\\bpick-uptruck\\b","pickup truck"),
 (r"\\bmotorfiets\\b","motorcycle"),
 (r"\\bmeldkamer-op-locatie\\b","mobile command post"),
 (r"\\bmobiele-drinkwaterinstallatie\\b","mobile drinking water unit"),
 (r"\\bwaterboorinstallatie\\b","water drilling unit"),
 (r"\\bwegenmatsysteem\\b","road mat system"),
 (r"\\bontsmettingssysteem\\b","decontamination system"),
 (r"\\bzware-uitvoering\\b","heavy variant"),
 (r"\\bluchtmobiel-speciaal-voertuig\\b","airmobile special operations vehicle"),
 (r"\\bgrondverzetmachines\\b","earthmoving machinery"),
]

def pretty(asset: str) -> str:
    s = asset.replace("2000nl","2000NL").replace("cbrn","CBRN").replace("mlc-70","MLC 70")
    for pat, rep in REPL:
        s = re.sub(pat, rep, s)
    s = s.replace("-"," ")
    s = re.sub(r"\\s+"," ", s).strip()
    small = {"and","or","of","the","a","an","for","to","in","on","with"}
    out=[]
    for w in s.split():
        if w.isupper(): out.append(w)
        elif re.fullmatch(r"\\d+[a-zA-Z]*", w): out.append(w.upper() if w.lower()=="nl" else w)
        elif w.lower() in small: out.append(w.lower())
        else:
            if re.fullmatch(r"\\d+[a-z]\\d*", w.lower()): out.append(w.upper())
            else: out.append(w.capitalize())
    txt=" ".join(out)
    txt = txt.replace("Leopard 2 A6","Leopard 2A6").replace("Mercedes Benz","Mercedes-Benz")
    if txt.startswith("Actros"): txt = "Mercedes-Benz " + txt
    if txt.startswith("E One"): txt = txt.replace("E One","E-One",1)
    return txt

def aliases(ans: str, asset: str):
    a=set([ans.lower(), asset.replace("-"," ").lower()])
    toks=re.sub(r"[^a-zA-Z0-9\\s-]","", ans).split()
    if toks: a.add(toks[0].lower())
    if len(toks)>=2: a.add((toks[0]+" "+toks[1]).lower())
    return sorted(x for x in a if x)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--images", default="app/images")
    ap.add_argument("--out", default="app/data.json")
    args=ap.parse_args()

    files=[f for f in os.listdir(args.images) if f.lower().endswith(".jpg") and f.lower()!="missing.jpg"]
    files=sorted(files)
    questions=[]
    for i,f in enumerate(files,1):
        asset=f[:-4]
        ans=pretty(asset)
        questions.append({
            "id": f"army_{asset}_{i}",
            "branch":"army",
            "asset": asset,
            "class":"",
            "answer": ans,
            "aliases": aliases(ans, asset),
            "source":"local-images"
        })

    data={
      "version":"7.1-images-to-data",
      "title":"NL Defensie Materieelherkenning – Speaking Trainer",
      "settings":{
        "quizLength":10,
        "showCorrectAfterNext": True,
        "avoidImmediateRepeats": True,
        "steps":{
          "classificationFirst": True,
          "requireName": True,
          "inputModeName":"type",
          "nameMcqOptions":5,
          "classMcqOptions":5
        }
      },
      "microTheory":[
        "Step 1: choose the classification (BT / APC / Art / …).",
        "Step 2: say and/or type the platform name in English.",
        "After Next: you briefly see the correct class + name with the same image."
      ],
      "branches":[{"id":"army","label":"Landmacht"}],
      "vehicleClasses": VEHICLE_CLASSES,
      "speakingFrames":[
        "Class: It looks like ___.",
        "Name: I think it is a ___.",
        "Because it has ___ (wheels/tracks/turret), it is ___.",
        "Role: It is used for ___."
      ],
      "questions":questions
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out,"w",encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
    print(f"Wrote {len(questions)} questions to {args.out}")

if __name__=="__main__":
    main()
