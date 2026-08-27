# Data Provenance

## Integrated GIS package

The teammate-supplied GIS package defines a working Ravet / Pimpri-Chinchwad MVP study extent:

- 18.615 to 18.675 latitude
- 73.705 to 73.785 longitude
- EPSG:4326

It includes a study-area polygon and a Pavana River reference geometry. The package explicitly states that roads/buildings/drainage/elevation were not fabricated when source data was unavailable.

## OpenStreetMap

The application can acquire the driving road network and tagged infrastructure using OSMnx/OpenStreetMap when online access is available.

Attribution: © OpenStreetMap contributors, ODbL.

## SRTM

The teammate's GIS package provides a reproducible script for a public SRTM ~30 m elevation tile. Download and verify it before using it as analytical elevation input.

## Rainfall

The current dashboard uses scenario rainfall inputs. It is not a live IMD feed.

## Simulated events

Emergency incidents and response units in the dashboard are simulated demonstration records.

## Critical honesty rule

Do not claim that the current risk score is a calibrated flood probability or flood depth. A production model requires validated DEM, drainage, rainfall and historical event data plus calibration/validation.
