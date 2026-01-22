# NL Defensie Materieelherkenning – Speaking Trainer (Landmacht)

Static (offline-friendly) speaking trainer for A2/B1 English:
- Step 1: choose **classification** (5 options)
- Step 2: say + type the **platform name**
- After Next: shows **correct class + name** with the same image
- Each round: **10 random vehicles** (new mix every restart)

## Repo structure (important)
```
.
├── app/                 # GitHub Pages site (static)
│   ├── index.html
│   ├── data.json
│   └── images/          # <-- put your 46 JPGs here (same filenames as assets)
├── tools/               # helper scripts
└── spreadsheets/        # Excel templates
```

## Quick start (local)
1) Put your images in `app/images/` (JPG).
2) Open `app/index.html` in a browser.

## Update / rebuild data.json from your images (optional)
From repo root:
```bash
python3 tools/generate_data_from_images.py --images app/images --out app/data.json
```

## Apply classifications from Excel (optional)
Fill `spreadsheets/vehicle_classification_template_filled.xlsx` (or your own), then:
```bash
python3 tools/apply_classifications.py --data app/data.json --in spreadsheets/vehicle_classification_template_filled.xlsx
```

## Publish online with GitHub Pages (recommended)
This repo includes a GitHub Actions workflow that publishes the `app/` folder to GitHub Pages.

Steps:
1. Create a new GitHub repo and push these files.
2. In GitHub: **Settings → Pages**
   - Source: **GitHub Actions**
3. Open the Pages URL GitHub shows.
