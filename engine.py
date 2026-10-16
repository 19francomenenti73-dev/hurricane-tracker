
import json
import urllib.request

# Endpoint ufficiale NOAA / ArcGIS per i cicloni tropicali attivi
DATA_URL = "https://services9.arcgis.com/RHVPKK2913V4675B/arcgis/rest/services/Active_Hurricanes_v1/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
OUTPUT_FILE = "storms.json"

def fetch_and_save_storms():
    print("Sincronizzazione dati globali uragani/tifoni in corso...")
    try:
        req = urllib.request.Request(
            DATA_URL,
            headers={'User-Agent': 'NowcastingItalia-StormTracker/2.0 (Independent Research)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                raw_data = response.read().decode('utf-8')
                data = json.loads(raw_data)
                
                # Salvataggio del file JSON pulito nel repository
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                features_count = len(data.get('features', []))
                print(f"Successo! Salvati {features_count} sistemi tropicali in {OUTPUT_FILE}.")
            else:
                print(f"Errore HTTP dal server ufficiale: {response.status}")
                save_empty_fallback()
    except Exception as e:
        print(f"Errore durante il recupero dei dati NOAA: {e}")
        save_empty_fallback()

def save_empty_fallback():
    # Fallback sicuro per evitare crash in assenza di rete o dati
    fallback_data = {"type": "FeatureCollection", "features": []}
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(fallback_data, f, ensure_ascii=False, indent=2)
    print("Salvato file di fallback vuoto valido.")

if __name__ == "__main__":
    fetch_and_save_storms()
  
