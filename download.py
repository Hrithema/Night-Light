from dotenv import load_dotenv
load_dotenv()

import os, time
import earthaccess

earthaccess.login(strategy="environment")

results = earthaccess.search_data(
    short_name="VNP46A4",
    bounding_box=(83.3, 21.9, 87.9, 25.4),
    temporal=("2013-01-01", "2024-12-31"),
)
print(len(results), "granules found")

os.makedirs("data/raw", exist_ok=True)

for i, r in enumerate(results):
    name = r.data_links()[0].split("/")[-1]
    path = f"data/raw/{name}"
    if os.path.exists(path) and os.path.getsize(path) > 10_000_000:
        print(f"[{i+1}/{len(results)}] already have {name}")
        continue
    for attempt in range(5):
        try:
            print(f"[{i+1}/{len(results)}] downloading {name} (try {attempt+1})", flush=True)
            earthaccess.download([r], "data/raw", threads=1)
            break
        except Exception as e:
            print("   failed:", e, flush=True)
            time.sleep(10)