import json
import urllib.request

# Fonti ufficiali multiple per evitare endpoint vuoti o bloccati
ENDPOINTS = [
    (
        'https://www.nhc.noaa.gov/gis/geojson/active_storms.geojson',
        'noaa_nhc',
    ),
    ('https://www.gdacs.org/xml/rss_to_geojson.geojson', 'gdacs'),
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
                  'NowcastingItalia StormTracker/2.5 (Independent Civil'
                  ' Protection Monitor)'
              )
          },
      )
      with urllib.request.urlopen(req, timeout=30) as response:
        if response.status == 200:
          data = json.loads(response.read().decode('utf-8'))
          features = data.get('features', [])
          print(f'Fonte {source_type}: trovate {len(features)} features.')

          for f in features:
            props = f.get('properties', {})
            geom = f.get('geometry', {})
            geom_type = geom.get('type')

            coords = []
            if geom_type == 'Point':
              coords = geom.get('coordinates', [])
            elif geom_type in ['Polygon', 'MultiPolygon', 'LineString']:
              # Estrazione sicura della prima coordinata disponibile per geometrie complesse
              flat = geom.get('coordinates', [])
              try:
                while isinstance(flat, list) and len(flat) > 0:
                  if isinstance(flat[0], (int, float)) and len(coords) < 2:
                    coords = flat
                    break
                  flat = flat[0]
              except Exception:
                pass

            if len(coords) >= 2:
              lon, lat = coords[0], coords[1]
              if -90 <= lat <= 90 and -180 <= lon <= 180:
                all_storms.append({
                    'name': str(
                        props.get('stormName')
                        or props.get('NAME')
                        or props.get('name')
                        or props.get('title')
                        or 'SISTEMA TROPICALE'
                    ),
                    'basin': str(props.get('basin', source_type.upper())),
                    'intensity': str(
                        props.get('intensity')
                        or props.get('MAXWIND')
                        or 'N/D'
                    ),
                    'pressure': str(
                        props.get('pressure') or props.get('MSLP') or 'N/D'
                    ),
                    'lat': float(lat),
                    'lon': float(lon),
                })
    except Exception as e:
      print(f'Errore con endpoint {url}: {e}')

  output = {
      'status': 'success',
      'count': len(all_storms),
      'storms': all_storms,
  }

  with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

  print(f'Totale tempeste/eventi salvati in storms.json: {len(all_storms)}')


if __name__ == '__main__':
  fetch_and_parse_storms()
    
