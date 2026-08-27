#!/usr/bin/env bash
set -euo pipefail

# Ravet FloodTwin - Member 2 real-data downloader
# Study bbox: south=18.615 west=73.705 north=18.675 east=73.785
# Requires: curl, ogr2ogr (GDAL), gzip, QGIS recommended.
# Source: OpenStreetMap contributors (ODbL).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/GIS_Data"
TMP="$ROOT/.download_tmp"
mkdir -p "$TMP" "$DATA"

OVERPASS="https://overpass-api.de/api/interpreter"

cat > "$TMP/roads_query.txt" <<'EOF'
[out:xml][timeout:180];
(
  way["highway"](18.615,73.705,18.675,73.785);
);
(._;>;);
out body;
EOF

cat > "$TMP/buildings_query.txt" <<'EOF'
[out:xml][timeout:180];
(
  way["building"](18.615,73.705,18.675,73.785);
);
(._;>;);
out body;
EOF

cat > "$TMP/drainage_query.txt" <<'EOF'
[out:xml][timeout:180];
(
  way["waterway"](18.615,73.705,18.675,73.785);
  way["drain"](18.615,73.705,18.675,73.785);
);
(._;>;);
out body;
EOF

echo "[1/4] Downloading OSM roads..."
curl -L --fail --retry 3 --data-urlencode "data@=$TMP/roads_query.txt" "$OVERPASS" -o "$TMP/roads.osm"

echo "[2/4] Downloading OSM building footprints..."
curl -L --fail --retry 3 --data-urlencode "data@=$TMP/buildings_query.txt" "$OVERPASS" -o "$TMP/buildings.osm"

echo "[3/4] Downloading OSM drainage/waterway lines..."
curl -L --fail --retry 3 --data-urlencode "data@=$TMP/drainage_query.txt" "$OVERPASS" -o "$TMP/drainage.osm"

echo "[4/4] Converting to GeoPackage layers..."
rm -f "$DATA/osm_member2.gpkg"
ogr2ogr -f GPKG "$DATA/osm_member2.gpkg" "$TMP/roads.osm" lines -where "highway IS NOT NULL" -nln roads -t_srs EPSG:4326
ogr2ogr -f GPKG "$DATA/osm_member2.gpkg" "$TMP/buildings.osm" multipolygons -where "building IS NOT NULL" -nln buildings -t_srs EPSG:4326 -update
ogr2ogr -f GPKG "$DATA/osm_member2.gpkg" "$TMP/drainage.osm" lines -where "waterway IS NOT NULL" -nln drainage -t_srs EPSG:4326 -update

echo "Done. Open $DATA/osm_member2.gpkg in QGIS."
echo "Keep OpenStreetMap attribution: © OpenStreetMap contributors, ODbL."
