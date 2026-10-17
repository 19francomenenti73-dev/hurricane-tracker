
import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE_URL = (
    "https://mapservices.weather.noaa.gov/tropical/rest/services/"
    "tropical/NHC_tropical_weather_summary/MapServer"
)

OUTPUT_FILE = "storms.json"
TIMEOUT_SECONDS = 45

LAYERS = {
    "forecast_points": 5,
    "forecast_track": 6,
    "forecast_cone": 7,
}


def fetch_layer(layer_id):
    """Scarica un livello GeoJSON dal servizio ufficiale NOAA/NHC."""
    query_url = f"{BASE_URL}/{layer_id}/query"

    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }

    url = query_url + "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OpenSource-Hurricane-Tracker/1.0",
            "Accept": "application/geo+json, application/json",
        },
    )

    with urllib.request.urlopen(
        request, timeout=TIMEOUT_SECONDS
    ) as response:
        raw = response.read().decode("utf-8")

    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError(
            f"Risposta inattesa per il livello {layer_id}"
        )

    # Alcuni servizi ArcGIS restituiscono errori in formato JSON.
    if "error" in data:
        raise RuntimeError(
            f"Errore NOAA livello {layer_id}: "
            f"{json.dumps(data['error'], ensure_ascii=False)}"
        )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Il livello {layer_id} non ha restituito "
            "una FeatureCollection GeoJSON valida."
        )

    features = data.get("features")
    if not isinstance(features, list):
        raise ValueError(
            f"Elenco features mancante nel livello {layer_id}"
        )

    # Mantiene soltanto elementi con geometria e proprietà valide.
    valid_features = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        if not isinstance(feature.get("properties"), dict):
            feature["properties"] = {}
        if not isinstance(feature.get("geometry"), dict):
            continue
        if not feature["geometry"].get("type"):
            continue
        valid_features.append(feature)

    data["features"] = valid_features
    return data


def build_output():
    result = {
        "source": "NOAA / National Hurricane Center",
        "source_url": BASE_URL,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "notice": (
            "Dati ufficiali NOAA/NHC. Le previsioni possono cambiare. "
            "Il cono indica incertezza della traiettoria, non l'area "
            "esatta dei venti o dei danni."
        ),
        "layers": {},
        "counts": {},
    }

    # Se uno dei livelli fallisce, il processo si interrompe:
    # non pubblica silenziosamente un aggiornamento incompleto.
    for name, layer_id in LAYERS.items():
        print(f"Scaricamento livello {layer_id}: {name}")
        geojson = fetch_layer(layer_id)
        result["layers"][name] = geojson
        result["counts"][name] = len(geojson["features"])
        print(
            f"  Elementi validi: "
            f"{result['counts'][name]}"
        )

    result["count"] = sum(result["counts"].values())
    return result


def save_atomically(data):
    directory = os.path.dirname(os.path.abspath(OUTPUT_FILE))
    os.makedirs(directory, exist_ok=True)

    fd, temporary_path = tempfile.mkstemp(
        prefix="storms_",
        suffix=".tmp",
        dir=directory,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            file.write("\n")

        os.replace(temporary_path, OUTPUT_FILE)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def main():
    try:
        data = build_output()
        save_atomically(data)

        print(
            "Aggiornamento completato. Elementi totali: "
            f"{data['count']}"
        )
        print(f"Conteggi per livello: {data['counts']}")

        # Un risultato vuoto può significare che non ci sono
        # sistemi attivi nel feed; lo segnaliamo chiaramente.
        if data["count"] == 0:
            print(
                "AVVISO: NOAA ha restituito zero elementi "
                "in tutti e tre i livelli."
            )

    except Exception as error:
        print(f"ERRORE aggiornamento NOAA: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
    
