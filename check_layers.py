import h5py, glob, numpy as np

path = sorted(glob.glob("data/raw/*.h5"))[-1]
base = "HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/"
with h5py.File(path, "r") as f:
    rad = f[base + "AllAngle_Composite_Snow_Free"]
    print("radiance attrs:", dict(rad.attrs))

    q = f[base + "AllAngle_Composite_Snow_Free_Quality"][:]
    vals, counts = np.unique(q, return_counts=True)
    print("quality values:", dict(zip(vals.tolist(), counts.tolist())))

    lat = f[base + "lat"][:]
    lon = f[base + "lon"][:]
    print("lat:", lat[0], "->", lat[-1])
    print("lon:", lon[0], "->", lon[-1])

    r = rad[:]
    print("radiance min/max:", np.nanmin(r), np.nanmax(r))