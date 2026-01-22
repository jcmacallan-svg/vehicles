# NL Defence Speaking Trainer (GitHub Pages package)

This zip is meant to be uploaded into your existing `vehicles` repo.

## What’s inside
- `app/` (the web app)
- `spreadsheets/vehicle_classification_template_filled.xlsx` (your filled classifications)
- `tools/` helper scripts

## IMPORTANT about images
Your repo must contain the JPGs in:
`app/images/*.jpg`

This package does NOT include the JPGs (to keep the zip small). Do **not** delete your existing `app/images/` folder on GitHub.

## Fast upload (no terminal)
1. Open your repo on GitHub → go to `vehicles/app/`
2. Upload/replace these files from this zip:
   - `app/index.html`
   - `app/app.js`
   - `app/styles.css`
   - `app/data.json`
3. (Optional) Upload the `spreadsheets/` and `tools/` folders too.

## If classes ever “all become APC” again
That happens when `data.json` is regenerated without preserving classes.
Use the safe sync script:
`python3 tools/sync_datajson_from_images.py --images app/images --data app/data.json`
