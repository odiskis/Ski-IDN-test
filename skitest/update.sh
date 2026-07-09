#!/bin/bash
cd ~/public_html/skitest
wget -q -O static/index.html https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/index.html
wget -q -O static/admin.html https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/static/admin.html
wget -q -O app.py https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/app.py
wget -q -O requirements.txt https://raw.githubusercontent.com/odiskis/Ski-IDN-test/main/skitest/requirements.txt
sed -i "s|fetch('/api/|fetch('/skitest/app.cgi/api/|g" static/index.html static/admin.html
sed -i "s|const MAP_URL = '/kart.png'|const MAP_URL = '/skitest/app.cgi/kart.png'|g" static/index.html
rm -rf __pycache__
echo "Ferdig! Alle fire filer oppdatert og cache ryddet."
