"""Resolve a supported preset without evaluating configuration as shell code."""
import json
from pathlib import Path
import sys


def resolve(root, preset, genre, network):
    if preset not in ("2d-android", "3d-fps-windows"):
        raise ValueError("Unsupported preset: " + preset)
    data = json.loads((Path(root) / "profiles/presets" / (preset + ".json")).read_text())
    genre = genre or data["genre"]
    if genre not in data["genres"]:
        raise ValueError("Genre is incompatible with preset: " + genre)
    if network not in data["network_modes"]:
        raise ValueError("Network mode is incompatible with preset: " + network)
    return {"DIMENSION": data["dimension"], "PLATFORM": data["platform"],
            "ART_PIPELINE": data["art_pipeline"], "GENRE": genre, "NETWORK": network,
            "DEFAULT_STYLE": data["style"], "DEFAULT_PROJECTION": data["projection"],
            "EXPORT_PRESET": data["export_preset"], "EXPORT_EXT": data["export_extension"]}


if __name__ == "__main__":
    try:
        for key, value in resolve(*sys.argv[1:]).items():
            print(key + "=" + value)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
