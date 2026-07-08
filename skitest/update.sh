#!/bin/bash
cd ~/public_html/skitest

mkdir -p static/js static/maps

# Kjernefiler
wget -q -O static/index.html https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/index.html
wget -q -O static/admin.html https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/admin.html
wget -q -O app.py https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/app.py
wget -q -O requirements.txt https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/requirements.txt

# Kartmodul (Leaflet-basert zoombart kart)
wget -q -O static/js/topomap.js https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/js/topomap.js
wget -q -O static/maps/map_metadata.json https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/maps/map_metadata.json
wget -q -O static/maps/01_zoom_base.png https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/maps/01_zoom_base.png
wget -q -O static/maps/01_zoom_steepness.png https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/maps/01_zoom_steepness.png
wget -q -O static/maps/02_zoom_base.png https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/maps/02_zoom_base.png
wget -q -O static/maps/02_zoom_steepness.png https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/maps/02_zoom_steepness.png
wget -q -O static/maps/03_zoom_base.png https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/maps/03_zoom_base.png
wget -q -O static/maps/03_zoom_steepness.png https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/maps/03_zoom_steepness.png

# Sikkerhetsnett i tilfelle eldre filversjoner med relative API-stier dukker opp igjen
sed -i "s|fetch('/api/|fetch('/skitest/app.cgi/api/|g" static/index.html static/admin.html
sed -i "s|const MAP_URL = '/kart.png'|const MAP_URL = '/skitest/app.cgi/kart.png'|g" static/index.html

rm -rf __pycache__
echo "Ferdig! Alle filer (inkludert kartmodul) oppdatert og cache ryddet."
