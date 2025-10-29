# 1. Használj egy alap Python 3.10-es "slim" (kicsi) lemezképet
FROM python:3.10-slim

# 2. Állítsd be a munkakönyvtárat a konténeren belül
WORKDIR /app

# 3. Másold be a függőségek listáját
COPY requirements.txt .

# 4. Telepítsd a függőségeket
# A --no-cache-dir kisebb méretű Docker image-et eredményez
RUN pip install --no-cache-dir -r requirements.txt

# 5. Másold be az összes többi fájlt (az app.py-t)
COPY . .

# 6. Ez a parancs fog elindulni, amikor a Render elindítja a szervert
# Az app.py-ban lévő kód automatikusan figyeli a PORT változót.
CMD ["python", "app.py"]
