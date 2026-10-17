# engine.py
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = (
    "https://mapservices.weather.noaa.gov/tropical/rest/services/"
    "tropical/NHC_tropical_weather_summary/MapServer/5/query"
)
OUTPUT = "storms.json"
TIMEOUT = 35


def fetch_data():
    params = urlencode({
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    })
    request = Request(
        f"{API_URL}?{params}",
        headers={
            "User-Agent": "OpenCycloneTracker/1.0 (educational non-profit project)",
            "Accept": "application/geo+json, application/json",
        },
    )

    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP inatteso: {response.status}")
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Errore NOAA HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Errore di rete NOAA: {exc.reason}") from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Risposta NOAA non valida o timeout: {exc}") from exc

    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise RuntimeError("NOAA non ha restituito una FeatureCollection GeoJSON.")

    features = data.get("features")
    if not isinstance(features, list):
        raise RuntimeError("Il campo features manca o non è una lista.")

    # Verifica che il feed sia interpretabile, senza inventare dati.
    for feature in features:
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Point":
            raise RuntimeError("Geometria inattesa nel feed dei punti NOAA.")
        coords = geometry.get("coordinates") or []
        if len(coords) < 2:
            raise RuntimeError("Coordinate mancanti in un punto NOAA.")
        lon, lat = coords[0], coords[1]
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise RuntimeError("Coordinate geografiche non valide.")

    return features


def atomic_write(data):
    folder = os.path.dirname(os.path.abspath(OUTPUT))
    fd, temp_path = tempfile.mkstemp(prefix="storms_", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, OUTPUT)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def main():
    print("Recupero dei punti ciclonici dal servizio NOAA/NHC...")
    features = fetch_data()

    result = {
        "source": "NOAA/NHC ArcGIS REST - Forecast Points",
        "source_url": API_URL,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(features),
        "status": "ok",
        "notice": (
            "Punti ufficiali del servizio NHC. Le proprietà originali sono "
            "conservate; interpretare i campi secondo i metadati NOAA."
        ),
        "features": features,
    }

    atomic_write(result)
    print(f"Acquisizione verificata. Punti salvati: {len(features)}")
    print(f"File aggiornato: {OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERRORE FATALE: {exc}", file=sys.stderr)
        sys.exit(1)
