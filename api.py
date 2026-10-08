"""Flask API for the night-lights change detector.

Run:   python api.py          (serves http://localhost:5001)
Needs: run_pipeline.py has been run (so data/processed/ and outputs/ exist).
The classifier is optional: until models/site_classifier.joblib exists,
/api/analyze returns the rule-based result only.
"""
import json
import numpy as np
from flask import Flask, jsonify, request, send_from_directory, abort
from src import config
from src.site_features import FEATURE_NAMES, load_feature_maps, location_features, to_rowcol

app = Flask(__name__)
_cache = {}


@app.after_request
def add_cors(resp):                       # dev-only: lets the React dev server call us
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


def _maps():
    if "maps" not in _cache:
        _cache["maps"] = load_feature_maps()
    return _cache["maps"]


def _stack():
    if "stack" not in _cache:
        _cache["stack"] = np.load(config.PROCESSED_DIR / "stack.npy", mmap_mode="r")
        _cache["years"] = json.load(open(config.PROCESSED_DIR / "years.json"))
    return _cache["stack"], _cache["years"]


def _model():
    if "model" not in _cache:
        path = config.ROOT / "models" / "site_classifier.joblib"
        if path.exists():
            import joblib
            _cache["model"] = joblib.load(path)
        else:
            _cache["model"] = None
    return _cache["model"]


def _latlon():
    try:
        lat, lon = float(request.args["lat"]), float(request.args["lon"])
    except (KeyError, ValueError):
        abort(400, "lat and lon are required numbers")
    r, c = to_rowcol(lat, lon)
    H, W = _maps()["last_mean"].shape
    if not (0 <= r < H and 0 <= c < W):
        abort(400, "that point is outside the Jharkhand study area")
    return lat, lon, r, c


def _timeseries(r, c, half=1):
    stack, years = _stack()
    win = np.asarray(stack[:, max(r - half, 0):r + half + 1, max(c - half, 0):c + half + 1], dtype=np.float32)
    vals = np.nanmean(win.reshape(len(years), -1), axis=1)
    return [{"year": y, "radiance": None if np.isnan(v) else round(float(v), 2)}
            for y, v in zip(years, vals)]


@app.get("/api/health")
def health():
    return jsonify(status="ok", model_loaded=_model() is not None)


@app.get("/api/sites")
def sites():
    """GeoJSON of detected sites. Optional: ?type=growth|emergence &min_area=km2 &limit=n"""
    path = config.OUTPUT_DIR / "sites.geojson"
    if not path.exists():
        abort(404, "sites.geojson not found - run run_pipeline.py first")
    gj = json.load(open(path, encoding="utf-8"))
    feats = gj["features"]
    t, min_area = request.args.get("type"), float(request.args.get("min_area", 0))
    feats = [f for f in feats
             if (not t or f["properties"]["type"] == t)
             and f["properties"]["area_km2"] >= min_area]
    feats.sort(key=lambda f: f["properties"]["total_gain"], reverse=True)
    if "limit" in request.args:
        feats = feats[: int(request.args["limit"])]
    return jsonify(type="FeatureCollection", features=feats)


@app.get("/api/timeseries")
def timeseries():
    _, _, r, c = _latlon()
    return jsonify(timeseries=_timeseries(r, c))


@app.get("/api/analyze")
def analyze():
    """Everything the frontend needs for one clicked point."""
    lat, lon, r, c = _latlon()
    x = location_features(_maps(), lat, lon)
    f = dict(zip(FEATURE_NAMES, x))

    # rule-based signal (0..1): how strongly the lights rose, on a log scale
    rule_score = float(np.clip(f["log_ratio_w"] / 2.0, 0, 1))
    out = {
        "lat": lat, "lon": lon,
        "change_score": round(rule_score, 3),
        "label": "unclassified",
        "label_source": "rule",
        "features": {k: round(v, 3) for k, v in f.items()},
        "timeseries": _timeseries(r, c),
    }
    bundle = _model()
    if bundle is not None:
        proba = bundle["model"].predict_proba([x])[0]
        classes = bundle["classes"]
        best = int(np.argmax(proba))
        out["label"] = classes[best]
        out["label_source"] = "model"
        out["probabilities"] = {k: round(float(p), 3) for k, p in zip(classes, proba)}
        if "no_change" in classes:
            out["change_score"] = round(1 - float(proba[classes.index("no_change")]), 3)
    elif rule_score >= 0.5:
        out["label"] = "likely_change"
    else:
        out["label"] = "no_clear_change"
    return jsonify(out)


@app.get("/api/images/<path:name>")
def images(name):
    """Serves the PNG maps the pipeline writes (change_maps.png, sites_map.png)."""
    if not name.lower().endswith(".png"):
        abort(404)
    return send_from_directory(config.OUTPUT_DIR, name)


@app.errorhandler(400)
@app.errorhandler(404)
def err(e):
    return jsonify(error=e.description), e.code


if __name__ == "__main__":
    app.run(port=5001, debug=True)
