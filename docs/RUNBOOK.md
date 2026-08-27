# Runbook

## Windows / VS Code

Open the project folder in VS Code.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

If `python` is unavailable but the Windows launcher is available:

```powershell
py -m venv venv
py -m pip install -r requirements.txt
```

## Offline mode

If OpenStreetMap cannot be reached, switch off **Use OpenStreetMap road/infrastructure data** in the sidebar. The application then uses a synthetic demonstration road graph.

## Troubleshooting

### OSM download is slow/fails
Use offline mode for the demo. Do not repeatedly redownload the same network.

### Map is slow
Leave **Show all road segments** unchecked.

### No route
The current rainfall/closure threshold may close too many edges. Increase the closure threshold or use a lower scenario for demonstration.

### Infrastructure is empty
OSM tagging is incomplete and the network query may fail. The routing module does not depend on this layer.
