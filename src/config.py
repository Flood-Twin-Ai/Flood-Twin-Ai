from dataclasses import dataclass

# Friend's GIS package defines the MVP study extent as Ravet / Pimpri-Chinchwad.
PUNE_CENTER = (18.64327, 73.74506)
PUNE_RADIUS_M = 5500
STUDY_AREA = {"south": 18.615, "west": 73.705, "north": 18.675, "east": 73.785}

# Approximate demonstration waypoints inside/near the supplied study extent.
# These are routing demo points, not official shelters.
PUNE_WAYPOINTS = {
    "Ravet": (18.64327, 73.74506),
    "Tathawade": (18.6298, 73.7480),
    "Akurdi": (18.6487, 73.7750),
    "Nigdi": (18.6506, 73.7797),
    "Punawale": (18.6160, 73.7420),
    "Kiwale": (18.6380, 73.7180),
    "Mamurdi": (18.6550, 73.7055),
}

@dataclass(frozen=True)
class Scenario:
    rainfall_mm_h: float
    duration_h: float
    closure_threshold: float

    @property
    def severity(self) -> float:
        intensity = min(1.0, max(0.0, self.rainfall_mm_h / 200.0))
        duration = min(1.0, max(0.0, self.duration_h / 6.0))
        return 0.7 * intensity + 0.3 * duration

SCENARIOS = {
    "Moderate": Scenario(50.0, 1.0, 0.82),
    "Heavy": Scenario(100.0, 2.0, 0.78),
    "Extreme": Scenario(150.0, 3.0, 0.72),
}
