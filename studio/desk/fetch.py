"""Downloads the scanned materials and the studio HDRI the renders use. All of it is CC0.

    python3 studio/fetch.py

Files go to studio/assets, which is not in the repository. Each archive is unpacked into a folder of its own.
"""

import json
import os
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

# ambientCG material scans, 1K JPG sets: colour, normal, roughness, displacement.
MATERIALS = (
    "Leather037",
    "Leather030",
    "Paper001",
    "Paper002",
    "Paper006",
    "Plastic010",
    "Metal009",
    "Scratches003",
    "SurfaceImperfections003",
    "Fingerprints009",
    "Rubber004",
    "Clay003",
    "Wood067",
    # Tolex's pebbled grain, for the PRS tab (studio/tabs.py).
    "Leather025",
)
# ambientCG scans whose relief is built as real geometry, 2K PNG sets for their 16-bit displacement: creased paper,
# for the folds of a squeezed tube.
RELIEFS = ("Paper003",)
# Poly Haven HDRI: a small studio with softboxes.
HDRI = "studio_small_08"


def get(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-studio/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, open(path, "wb") as out:
        out.write(response.read())


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for material, kind in [(name, "1K-JPG") for name in MATERIALS] + [(name, "2K-PNG") for name in RELIEFS]:
        folder = os.path.join(ASSETS, material)
        if os.path.isdir(folder):
            continue
        archive = os.path.join(ASSETS, f"{material}.zip")
        get(f"https://ambientcg.com/get?file={material}_{kind}.zip", archive)
        os.makedirs(folder)
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.namelist():
                # Images only, flat into the folder.
                if member.lower().endswith((".jpg", ".png")) and "/" not in member and "\\" not in member:
                    bundle.extract(member, folder)
        os.remove(archive)
        print("fetched", material)

    hdri = os.path.join(ASSETS, f"{HDRI}.hdr")
    if not os.path.exists(hdri):
        request = urllib.request.Request(f"https://api.polyhaven.com/files/{HDRI}", headers={"User-Agent": "portfolio-studio/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            files = json.load(response)
        get(files["hdri"]["2k"]["hdr"]["url"], hdri)
        print("fetched", HDRI)


main()
