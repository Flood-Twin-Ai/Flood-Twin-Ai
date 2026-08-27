#!/usr/bin/env bash
set -euo pipefail

# Ravet FloodTwin - Member 2 DEM downloader
# SRTM 1 arc-second (~30 m) tile covering the study area.
# Requires: curl, gzip, GDAL (gdal_translate).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/GIS_Data"
TMP="$ROOT/.download_tmp"
mkdir -p "$TMP" "$DATA"

URL="https://s3.amazonaws.com/elevation-tiles-prod/skadi/N18/N18E073.hgt.gz"
FILE="$TMP/N18E073.hgt.gz"

echo "Downloading SRTM tile..."
curl -L --fail --retry 3 "$URL" -o "$FILE"
gunzip -f "$FILE"

# Crop to the project extent and save as GeoTIFF.
gdal_translate -projwin 73.705 18.675 73.785 18.615   -a_srs EPSG:4326 "$TMP/N18E073.hgt" "$DATA/Ravet_SRTM_DEM_30m.tif"

echo "Created: $DATA/Ravet_SRTM_DEM_30m.tif"
echo "Source: NASA SRTM / USGS-hosted elevation tile."
