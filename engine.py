import json
import urllib.request

# Fonti ufficiali multiple aperte (GDACS globale + NOAA ArcGIS)
ENDPOINTS = [
    "https://www.gdacs.org/xml/rss_tc_georss.geojson",
    "https://services9.arcgis.com/RHVPKK2913V4675B/arcgis/rest/services/Active_Hurricanes_v1/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
]
OUTPUT_FILE = "storms.json"

def fetch_and_merge_storms():
    all_features = []
    
    for url in ENDPOINTS:
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'NowcastingItalia-StormTracker/2.5 (Independent Civil Protection Monitor)'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    features = data.get('features', [])
                    if features:
                        all_features.extend(features)
        except Exception as e:
            print(f"Avviso su endpoint {url}: {e}")
            
    # Creazione del FeatureCollection unificato
    combined_data = {
        "type": "FeatureCollection",
        "features": all_features
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)
        
    print(f"Sincronizzazione completata: inclusi {len(all_features)} sistemi attivi in {OUTPUT_FILE}.")

if __name__ == "__main__":
    fetch_and_merge_storms()
    
