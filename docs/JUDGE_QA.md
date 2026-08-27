# Judge Q&A

### Is this a flood prediction system?
No. The current build is a decision-support prototype using a transparent scenario risk index. It is not an operational flood forecast.

### Why is the route not simply the shortest route?
Because the shortest route can contain higher modeled flood exposure or closed roads. The engine minimizes a risk-aware travel cost.

### What happens when rainfall increases?
The rainfall/duration indices increase the scenario risk component. This can raise edge risk, trigger closures and alter routes.

### What is technically difficult here?
The GIS/network integration: obtaining a real road graph, attaching scenario risk to individual edges, removing closed edges and recalculating routes dynamically.

### Why NetworkX?
It provides graph algorithms needed for shortest-path/risk-aware routing.

### Why OSMnx?
It provides Python tooling around OpenStreetMap street networks and works well with NetworkX for routing workflows.

### Why not use deep learning?
A three-day prototype needs an explainable and testable baseline first. ML should be added only when sufficient labelled historical flood data exists and can be validated.

### What is the current terrain limitation?
A relative spatial proxy is used when no DEM is available. It is not a measured elevation surface.

### What is needed for production?
Validated DEM and drainage data, authoritative rainfall/forecast feeds, historical flood observations, calibrated hydrologic/hydraulic modelling, expert-reviewed thresholds and operational validation.
