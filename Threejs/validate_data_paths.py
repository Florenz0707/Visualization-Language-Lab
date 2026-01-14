# validate_data_paths.py
import os, sys, json, argparse, subprocess
from pathlib import Path

REQUIRED = [
    "cities_major.geojson",
    "contours.geojson",
    "countries_eastern_europe.geojson",
    "provinces.geojson",
    "rivers.geojson",
    "merged_dem_cropped.tif",
    "index.html",
    "main.js"
]

def human(n):
    for u in ['B','KB','MB','GB','TB']:
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def check_files(folder):
    print("Checking files in:", folder)
    p = Path(folder)
    missing = []
    for fn in REQUIRED:
        fp = p / fn
        if fp.exists():
            sz = fp.stat().st_size
            print(f"  OK: {fn}  ({human(sz)})")
        else:
            print(f"  MISSING: {fn}")
            missing.append(fn)
    return missing

def inspect_geojson(path):
    print(f"\nInspect GeoJSON: {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            obj = json.load(f)
    except Exception as e:
        print("  ERROR reading JSON:", e)
        return
    t = obj.get('type')
    print("  top-level type:", t)
    features = obj.get('features')
    if not isinstance(features, list):
        print("  WARNING: 'features' missing or not a list")
        return
    print("  #features:", len(features))
    if len(features) > 0:
        f0 = features[0]
        geom = f0.get('geometry')
        props = f0.get('properties')
        if geom:
            print("  first feature geometry.type:", geom.get('type'))
            coords = geom.get('coordinates')
            if coords is not None:
                print("  first geometry sample (truncated):", str(coords)[:200])
        else:
            print("  first feature has no geometry")
        if props:
            print("  first feature properties keys:", list(props.keys())[:10])
    else:
        print("  NOTE: feature collection is empty")

def run_gdalinfo(tifpath):
    print(f"\nTry gdalinfo on: {tifpath}")
    try:
        out = subprocess.check_output(["gdalinfo", str(tifpath)], stderr=subprocess.STDOUT, universal_newlines=True, timeout=20)
        # print selected lines
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Size is") or line.startswith("Origin =") or line.startswith("Pixel Size") or line.startswith("Corner Coordinates") or line.startswith("Band"):
                print("  " + line)
        return True
    except FileNotFoundError:
        print("  gdalinfo not found on PATH.")
        return False
    except subprocess.TimeoutExpired:
        print("  gdalinfo timed out.")
        return True
    except subprocess.CalledProcessError as e:
        print("  gdalinfo failed:", e)
        return True

def try_rasterio(tifpath):
    print("\nTry rasterio fallback (if installed)")
    try:
        import rasterio
        with rasterio.open(str(tifpath)) as ds:
            print("  rasterio reports:")
            print(f"    width x height: {ds.width} x {ds.height}")
            print(f"    crs: {ds.crs}")
            print(f"    bounds: {ds.bounds}")
            print(f"    count (bands): {ds.count}")
            nodata = ds.nodata
            print(f"    nodata: {nodata}")
        return True
    except Exception as e:
        print("  rasterio not available or failed:", e)
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", "-d", help="Folder containing data (default = current dir)", default=".")
    args = ap.parse_args()
    folder = Path(args.dir)
    if not folder.exists():
        print("Folder does not exist:", folder)
        sys.exit(2)
    missing = check_files(folder)
    # Inspect geojsons that exist
    for name in REQUIRED:
        fp = folder / name
        if fp.exists() and fp.suffix.lower() == ".geojson":
            inspect_geojson(fp)
    # gdalinfo for tif
    tif = folder / "merged_dem_cropped.tif"
    if tif.exists():
        ok = run_gdalinfo(tif)
        if not ok:
            try_rasterio(tif)
    else:
        print("\nNo TIFF to inspect.")
    print("\nValidation complete.")
    if missing:
        print("Missing files (please place them in the folder):")
        for m in missing:
            print("  -", m)

if __name__ == "__main__":
    main()
