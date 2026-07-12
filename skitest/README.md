# Skitur Brukertest · NTNU 2026

## Setup on the NTNU server

1. Last opp hele mappen til serveren din (f.eks. via SCP eller git)
2. Installer avhengigheter:
   pip install -r requirements.txt --break-system-packages

3. Kjør lokalt for testing:
   python app.py

4. For produksjon på NTNU Apache-server:
   - Legg inn app.py som CGI eller bruk gunicorn
   - Sett SECRET_KEY som miljøvariabel

## Lenker

- Deltakerside: https://din-server/
- Adminside:    https://din-server/admin
  - Passord: ntnu2026odin (bytt dette i app.py linje 35)

## Data

Alle svar lagres i data/responses.json
Rutekart lagres som base64 PNG i samme fil
Eksporter til CSV fra adminsiden

## Passord

Standard adminpassord: ntnu2026odin
Bytt ved å endre linje 35 i app.py:
  if hashlib.sha256(pw.encode()).hexdigest() != hashlib.sha256(b"DITT_PASSORD").hexdigest():
