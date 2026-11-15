from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

COMMUNES = ["Gombe", "Limete", "Ngaliema", "Bandalungwa", "Kintambo"]
motos = {}

# Initialisation de 500 motos-taxis en memoire (RAM)
for i in range(1, 501):
    moto_id = f"moto-{i}"
    motos[moto_id] = {
        "id": moto_id,
        "statut": "libre" if i % 2 == 0 else "en_course",
        "commune": COMMUNES[i % 5]
    }

class StatusUpdate(BaseModel):
    id: str
    statut: str
    commune: str

# 1. Mettre a jour le statut d'une moto
@app.post("/status", status_code=201)
def update_status(data: StatusUpdate):
    if not data.id or not data.statut or not data.commune:
        raise HTTPException(status_code=400, detail="Donnees incompletes")
    motos[data.id] = {
        "id": data.id,
        "statut": data.statut,
        "commune": data.commune
    }
    return {
        "status": "ok",
        "id": data.id,
        "statut": data.statut,
        "commune": data.commune
    }

# 2. Lister et filtrer les motos par commune
@app.get("/motos")
def list_motos(commune: Optional[str] = None):
    liste = [m for m in motos.values() if not commune or m["commune"] == commune]
    return {
        "commune": commune if commune else "Toutes",
        "count": len(liste),
        "motos": liste
    }

# 3. Calculer les statistiques globales de disponibilite de la flotte
@app.get("/stats")
def get_stats():
    libres = 0
    en_course = 0
    for m in motos.values():
        if m["statut"] == "libre":
            libres += 1
        else:
            en_course += 1
    total = len(motos)
    taux = round((libres / total) * 100, 2) if total > 0 else 0.0
    return {
        "total": total,
        "libres": libres,
        "en_course": en_course,
        "taux_disponibilite": taux
    }
