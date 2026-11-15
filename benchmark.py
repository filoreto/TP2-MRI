import asyncio
import aiohttp
import time
import csv
import statistics

# Configuration des 4 serveurs a tester
TECHNOLOGIES = [
    {"nom": "Node.js (Express)", "fichier": "mesures_nodejs.csv", "base_url": "http://127.0.0.1:3000"},
    {"nom": "Python (FastAPI)",  "fichier": "mesures_python.csv", "base_url": "http://127.0.0.1:3001"},
    {"nom": "PHP (Natif)",       "fichier": "mesures_php.csv",    "base_url": "http://127.0.0.1:3002"},
    {"nom": "Go (Natif)",        "fichier": "mesures_go.csv",     "base_url": "http://127.0.0.1:3003"},
]

# Les 3 fonctionnalites du cahier des charges (Gestion de flotte de motos-taxis)
FONCTIONS = [
    {
        "nom": "maj_statut",
        "methode": "POST",
        "chemin": "/status",
        "payload": {"id": "moto-500", "statut": "libre", "commune": "Gombe"}
    },
    {
        "nom": "lister_motos",
        "methode": "GET",
        "chemin": "/motos?commune=Gombe",
        "payload": None
    },
    {
        "nom": "compter_disponibles",
        "methode": "GET",
        "chemin": "/stats",
        "payload": None
    }
]

NIVEAUX_CHARGE = [10, 50, 100, 200, 500]  # Utilisateurs simultanes
NOMBRE_ESSAIS = 40                        # 40 repetitions par niveau de charge

ENTETES_BRUTES = [
    "Technologie", "Fonction", "Utilisateurs", "Essai",
    "Temps_reponse_ms", "P95_ms", "Debit_rps", "Erreurs"
]

ENTETES_SYNTHESE = [
    "Technologie", "Fonction", "Utilisateurs",
    "Temps_moyen_ms", "P95_moyen_ms", "Debit_moyen_rps", "Total_erreurs"
]

async def envoyer_requete(session, methode, url, payload):
    debut = time.perf_counter()
    try:
        if methode == "POST":
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                await response.read()
                duree_ms = (time.perf_counter() - debut) * 1000.0
                return duree_ms, (response.status in (200, 201))
        else:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                await response.read()
                duree_ms = (time.perf_counter() - debut) * 1000.0
                return duree_ms, (response.status == 200)
    except Exception:
        duree_ms = (time.perf_counter() - debut) * 1000.0
        return duree_ms, False

async def executer_essai(methode, url, payload, nb_utilisateurs):
    connector = aiohttp.TCPConnector(limit=0, force_close=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        debut_lot = time.perf_counter()
        taches = [envoyer_requete(session, methode, url, payload) for _ in range(nb_utilisateurs)]
        resultats = await asyncio.gather(*taches)
        duree_totale_s = time.perf_counter() - debut_lot

    temps_reponses = [r[0] for r in resultats if r[1]]
    nb_erreurs = sum(1 for r in resultats if not r[1])

    if not temps_reponses:
        return 0.0, 0.0, 0.0, nb_erreurs

    temps_moyen = statistics.mean(temps_reponses)
    temps_tries = sorted(temps_reponses)
    index_p95 = min(int(len(temps_tries) * 0.95), len(temps_tries) - 1)
    p95 = temps_tries[index_p95]
    debit_rps = len(temps_reponses) / duree_totale_s if duree_totale_s > 0 else 0.0

    return round(temps_moyen, 2), round(p95, 2), round(debit_rps, 2), nb_erreurs

async def main():
    lignes_globales = []
    lignes_synthese = []

    print("=== DEMARRAGE DU BENCHMARK : FLOTTE MOTOS-TAXIS KINSHASA ===")

    for tech in TECHNOLOGIES:
        nom_tech = tech["nom"]
        fichier_tech = tech["fichier"]
        base_url = tech["base_url"]
        lignes_tech = []

        print(f"\n==========================================")
        print(f" TECHNOLOGIE : {nom_tech}")
        print(f"==========================================")

        for fonc in FONCTIONS:
            nom_fonc = fonc["nom"]
            methode = fonc["methode"]
            url = base_url + fonc["chemin"]
            payload = fonc["payload"]

            print(f"\n  ---> Fonction : {nom_fonc} ({methode} {fonc['chemin']})")
            await executer_essai(methode, url, payload, 5)  # Echauffement

            for utilisateurs in NIVEAUX_CHARGE:
                moyennes_essais, p95_essais, debits_essais = [], [], []
                erreurs_totales = 0

                for essai in range(1, NOMBRE_ESSAIS + 1):
                    t_moy, p95, debit, erreurs = await executer_essai(methode, url, payload, utilisateurs)
                    ligne = [nom_tech, nom_fonc, utilisateurs, essai, t_moy, p95, debit, erreurs]
                    lignes_tech.append(ligne)
                    lignes_globales.append(ligne)

                    if t_moy > 0:
                        moyennes_essais.append(t_moy)
                        p95_essais.append(p95)
                        debits_essais.append(debit)
                    erreurs_totales += erreurs

                moy_globale = round(statistics.mean(moyennes_essais), 2) if moyennes_essais else 0.0
                p95_global = round(statistics.mean(p95_essais), 2) if p95_essais else 0.0
                debit_global = round(statistics.mean(debits_essais), 2) if debits_essais else 0.0

                lignes_synthese.append([
                    nom_tech, nom_fonc, utilisateurs,
                    moy_globale, p95_global, debit_global, erreurs_totales
                ])
                print(f"    Charge {utilisateurs:3d} u. -> Moy: {moy_globale:7.2f} ms | "
                      f"P95: {p95_global:7.2f} ms | Debit: {debit_global:7.2f} req/s | Err: {erreurs_totales}")

        # Sauvegarde du fichier CSV propre a chaque technologie
        with open(fichier_tech, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(ENTETES_BRUTES)
            writer.writerows(lignes_tech)
        print(f"\n  [OK] Fichier sauvegarde : {fichier_tech} ({len(lignes_tech)} lignes)")

    # Sauvegarde du fichier CSV brut global (2400 lignes)
    with open("mesures_brutes.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(ENTETES_BRUTES)
        writer.writerows(lignes_globales)

    # Sauvegarde du fichier CSV de synthese (60 lignes) pour le rapport LaTeX
    with open("synthese_moyennes.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(ENTETES_SYNTHESE)
        writer.writerows(lignes_synthese)

    print("\n=== TERMINE ! ===")
    print("Fichiers crees : mesures_nodejs.csv, mesures_python.csv, mesures_php.csv, mesures_go.csv, mesures_brutes.csv et synthese_moyennes.csv")

if __name__ == "__main__":
    asyncio.run(main())
