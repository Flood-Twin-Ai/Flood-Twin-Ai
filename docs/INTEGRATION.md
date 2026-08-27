# GIS Integration

The teammate's GIS package and the ARC Reactors flood-routing engine are now in one repository.

## Connected now

- Ravet study-area boundary → dashboard map overlay
- Pavana River reference → dashboard map overlay
- Ravet study-center/extent → OSMnx road acquisition center
- Teammate QGIS project and source scripts → preserved under `gis/`

## Still separate by design

- The teammate's QGIS project remains an analysis/reference artifact.
- The Streamlit application owns scenario/risk/routing computation.
- The supplied GeoPackage is not treated as containing real road features unless those layers are populated.

## Next optional integration

If the OSM download scripts are run and the resulting GeoPackage contains verified road/building/drainage layers, those can be ingested as GIS features. The routing engine can continue using OSMnx for graph topology while the GeoPackage provides visualization/attribute layers.
