# Night-Light: Land-Change Detection from Night-Time Satellite Imagery (Jharkhand, v1)

Finds places in Jharkhand, India, where night-time lights rose strongly between 2013 and 2024 (a signal linked to industrialisation, rapid urban development and possibly mining), groups them into sites, and scores them with a small classifier. Results are served through a Flask API for a web front end.

> **Status: working prototype (Version 1).** Trained on 85 hand-labelled locations from one state. See [Limitations](#limitations) before relying on any output.

## How it works

1. **Data:** NASA Black Marble `VNP46A4` annual composites (tile `h26v06`, ~500 m pixels), 2013-2024, downloaded with `earthaccess`.
2. **Preprocessing:** crop to Jharkhand, mask bad pixels and everything outside the state border.
3. **Detection:** rule-based flags for *growth* (already lit, got much brighter) and *emergence* (dark, now lit).
4. **Sites:** neighbouring flagged pixels are merged into sites (271 found) with area, radiance before/after and total gain.
5. **Classifier:** Random Forest on local brightness-change features, trained on hand-labelled sites, evaluated with spatial cross-validation.
6. **API:** `api.py` exposes sites, per-point analysis and time series.

## Results (v1)

| | Value |
|---|---|
| Sites detected | 271 |
| Labelled locations | 85 (45 no change, 30 urban growth, 6 mining, 4 industrial) |
| Rule alone: flagged sites that are real change | 65% |
| Binary model (change vs no change), spatial CV | accuracy 0.73, macro F1 0.73 |
| Change class | precision 0.68, recall 0.80 |
| Four-class model | macro F1 0.35 (industrial and mining not learnable with this data) |

Among flagged sites only, the model improves on the rule only slightly (precision 0.65 to 0.68). The shipped model is the **binary** one.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root (never commit it):

```
EARTHDATA_TOKEN=your_nasa_earthdata_token
```

Get a token from your NASA Earthdata profile (tokens last 60 days).

You also need a district-level India boundary GeoJSON saved as `data/india.geojson` (it should have a state-name column, here `st_nm`). This project used the one from [udit-001/india-maps-data](https://github.com/udit-001/india-maps-data).

## Run the pipeline

```bash
# 1. Download the annual tiles into data/raw/
python download.py

# 2. Detect changes and extract sites
python run_pipeline.py --real --boundary data/india.geojson --state-name Jharkhand --state-key st_nm

# 3. Label sites: open label_tool.html in a browser, load data/processed/label_sheet.csv,
#    label the sites, export, and replace data/processed/label_sheet.csv

# 4. Train (binary: change vs no change)
python train.py --merge industrial,mining,urban_growth=change

# 5. Start the API
python api.py          # http://localhost:5001
```

`run_pipeline.py --fake` runs the whole pipeline on synthetic data, which is useful for testing without downloads.

## API

| Endpoint | Returns |
|---|---|
| `GET /api/health` | status, `model_loaded` flag |
| `GET /api/sites?type=growth\|emergence&min_area=&limit=` | GeoJSON of detected sites |
| `GET /api/analyze?lat=&lon=` | change score, label, probabilities, features, yearly radiance |
| `GET /api/timeseries?lat=&lon=` | yearly radiance for a point |
| `GET /api/images/<name>.png` | PNG maps written by the pipeline |

Points outside the Jharkhand crop return a 400 error. Without a trained model, `/api/analyze` returns a rule-based score only.

### Files the API needs

These are not stored in git (they are large or generated), so share them separately:

- `data/processed/features.npz`, `stack.npy`, `years.json`
- `outputs/sites.geojson`
- `models/site_classifier.joblib` (optional)

## Project structure

```
api.py                  Flask API
run_pipeline.py         preprocessing, detection, site extraction
train.py                classifier training and evaluation
download.py             Earthdata download
label_tool.html         browser tool for labelling sites
src/                    config, loading, features, sites, plotting, geo helpers
data/                   raw and processed data (git-ignored)
outputs/                maps and sites.geojson (git-ignored)
models/                 trained model (git-ignored)
```

## Limitations

- Small training set (85 labels), one region, one annotator.
- ~500 m pixels: small sites are not resolved, and many mines have little night lighting.
- The model separates changing from stable areas moderately well, but cannot reliably tell real land change from lights that grew without construction (road lighting, electrification).
- Industrial and mining could not be distinguished from other change.
- Thresholds were tuned by eye on Jharkhand; the model has not been tested elsewhere.
- Light change does not show whether an activity is legal or illegal.

## Roadmap (Version 2)

- More labels (especially emergence sites) and a second annotator.
- Sentinel-2 daytime features to identify mining and industrial land cover.
- Shape features to separate road lighting from new buildings.
- Validate on a second region; support multi-tile regions.
- Production setup: precomputed results, caching, deployment.

## Data and references

- NASA Black Marble VNP46A4, via NASA Earthdata / LAADS DAAC.
- Roman, M. O., et al. (2018). NASA's Black Marble nighttime lights product suite. *Remote Sensing of Environment*, 210, 113-143.
- District boundary data: udit-001/india-maps-data (github.com/udit-001/india-maps-data), district-level GeoJSON of India.