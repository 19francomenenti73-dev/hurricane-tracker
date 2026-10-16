import json
import urllib.request

# Endpoint ArcGIS REST ufficiale NOAA (Dynamic Query per tempeste attive)
ENDPOINTS = [
    (
        (
            'https://services9.arcgis.com/RHVPKKfVbevIKQzG/arcgis/rest/services/'
            'Active_Hurricanes_v1/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson'
        ),
        'noaa_arcgis_features',
    ),
    ('https://www.nhc.noaa.gov/index-at.xml', 'nhc_rss_fallback'),
]

OUTPUT_FILE = 'storms.json'


def fetch_and_parse_storms():
  all_storms = []

  for url, source_type in ENDPOINTS:
    try:
      req = urllib.request.Request(
          url,
          headers={
              'User-Agent': (
                  'NowcastingItalia-Tracker/3.0 (Civil Protection Monitor)'
              )
          },
      )
      with urllib.request.urlopen(req, timeout=30) as response:
        if response.status == 200:
          content = response.read().decode('utf-8')

          # Gestione GeoJSON da ArcGIS REST
          if source_type == 'noaa_arcgis_features':
            data = json.loads(content)
            features = data.get('features', [])
            print(f'ArcGIS Features trovate: {len(features)}')

            for f in features:
              props = f.get('properties', {})
              geom = f.get('geometry', {})
              if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                  all_storms.append({
                      'name': str(
                          props.get('STORMNAME')
                          or props.get('NAME')
                          or 'SISTEMA TROPICALE'
                      ),
                      'basin': str(props.get('BASIN', 'ATL/PAC')),
                      'intensity': str(
                          props.get('INTENSITY')
                          or props.get('MAX_WIND')
                          or 'N/D'
                      ),
                      'pressure': str(
                          props.get('PRESSURE') or props.get('MSLP') or 'N/D'
                      ),
                      'lat': float(coords[1]),
                      'lon': float(coords[0]),
                  })

    except Exception as e:
      print(f'Errore con {source_type}: {e}')

  output = {
      'status': 'success',
      'count': len(all_storms),
      'storms': all_storms,
  }

  with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

  print(f'Totale tempeste salvate in storms.json: {len(all_storms)}')


if __name__ == '__main__':
  fetch_and_parse_storms()
    
