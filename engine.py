import json
import urllib.request

# Endpoint GeoJSON ufficiale diretto dell'NHC per tempeste attive
URL = "https://www.nhc.noaa.gov/gis/geojson/active_storms.geojson"
OUTPUT_FILE = "storms.json"


def fetch_and_parse_storms():
  all_storms = []

  try:
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                " AppleWebKit/537.36 (KHTML, like Gecko)"
                " Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
      if response.status == 200:
        data = json.loads(response.read().decode("utf-8"))
        features = data.get("features", [])
        print(f"Features totali lette dal feed NOAA: {len(features)}")

        for f in features:
          props = f.get("properties", {})
          geom = f.get("geometry", {})

          if geom.get("type") == "Point":
            coords = geom.get("coordinates", [])
            if len(coords) >= 2:
              all_storms.append({
                  "name": str(
                      props.get("stormName")
                      or props.get("NAME")
                      or props.get("name")
                      or "SISTEMA TROPICALE"
                  ),
                  "basin": str(props.get("basin", "ATL/PAC")),
                  "intensity": str(
                      props.get("intensity") or props.get("MAXWIND") or "N/D"
                  ),
                  "pressure": str(
                      props.get("pressure") or props.get("MSLP") or "N/D"
                  ),
                  "lat": float(coords[1]),
                  "lon": float(coords[0]),
              })

  except Exception as e:
    print(f"Errore durante il recupero dei dati NOAA: {e}")

  output = {
      "status": "success",
      "count": len(all_storms),
      "storms": all_storms,
  }

  with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

  print(f"Totale tempeste salvate in storms.json: {len(all_storms)}")


if __name__ == "__main__":
  fetch_and_parse_storms()
    
