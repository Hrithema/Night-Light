import h5py, glob

files = sorted(glob.glob("data/raw/*.h5"))
print(len(files), "files found")

with h5py.File(files[-1], "r") as f:
    def show(name, obj):
        if hasattr(obj, "shape"):
            print(name, obj.shape, obj.dtype)
    f.visititems(show)