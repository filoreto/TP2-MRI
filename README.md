# TP n° 2 — Méthode de Recherche en Informatique (MRI)
**Comparaison expérimentale de la performance de Node.js (Express), Python (FastAPI), PHP (Natif) et Go (Natif) sur une API REST de gestion de flotte de motos-taxis à Kinshasa**

---

## 👥 Membres du groupe

* **Christian TETO FILORETO** — `christianteto58@gmail.com`
* **Joel MBAYI TUDIAMBA** — `Mbayijoel11@gmail.com`
* **Bienvenu MASAMBA KAMBA** — `Bienvenumasamba27@gmail.com`
* **Guy BAMBALATIWE SOLOMO** — `bamsolguy@gmail.com`
* **Daniel NGASUEN KABEBO** — `kabebo@icloud.com`

---

## 📌 1. Présentation de l'application de référence

L'application de référence est une **API RESTful de gestion en temps réel d'une flotte de 500 motos-taxis (*wewa*) à Kinshasa**, fonctionnant exclusivement en **mémoire vive (RAM)** afin d'isoler la performance pure des environnements d'exécution sans biais lié au disque ou à un SGBD externe.

Au démarrage de chaque serveur, 500 motos (`moto-1` à `moto-500`) sont initialisées de manière déterministe :
* **Statut :** alternance stricte selon la parité de l'identifiant (`libre` pour les indices pairs, `en_course` pour les indices impairs, soit 250 libres et 250 en course).
* **Commune :** affectation cyclique modulo 5 parmi `Gombe`, `Limete`, `Ngaliema`, `Bandalungwa` et `Kintambo` (100 motos par commune).

### Les 3 routes exposées (Contrat d'interface REST)

| Fonctionnalité | Méthode & Route | Profil de sollicitation | Code HTTP & Réponse type |
| :--- | :--- | :--- | :--- |
| **`maj_statut`** | `POST /status` | Écriture unitaire en mémoire ($O(1)$) et décodage JSON | `201 Created` — `{"status": "ok", "id": "moto-500", "statut": "libre", "commune": "Gombe"}` |
| **`lister_motos`** | `GET /motos?commune=Gombe` | Parcours ($O(N)$), filtrage et sérialisation JSON de 100 objets | `200 OK` — `{"commune": "Gombe", "count": 100, "motos": [...]}` |
| **`compter_disponibles`** | `GET /stats` | Agrégation en boucle sur 500 motos ($O(N)$) et calcul de taux | `200 OK` — `{"total": 500, "libres": 250, "en_course": 250, "taux_disponibilite": 50.0}` |

---

## 🗂️ 2. Structure de l'archive de rendu

```text
TP2_MRI_Motos_Kinshasa_Rendu_Final/
├── README.md                                   # Documentation complète du projet
├── 01_Rapport/
│   ├── rapport_TP2_Motos_Kinshasa.pdf          # Article scientifique compilé (format IEEE 2 colonnes)
│   └── rapport_TP2_Motos_Kinshasa.tex          # Code source LaTeX complet (avec graphiques PGFPlots)
├── 02_Codes_Sources/
│   ├── benchmark.py                            # Script automatisé de test de charge (Python aiohttp)
│   ├── node_app/
│   │   ├── app.js                              # Serveur Node.js (Express) — Port 3000
│   │   └── package.json
│   ├── python_app/
│   │   └── main.py                             # Serveur Python (FastAPI / Uvicorn) — Port 3001
│   ├── php_app/
│   │   └── index.php                           # Serveur PHP (Natif CLI) — Port 3002
│   └── go_app/
│       └── main.go                             # Serveur Go (Natif net/http + sync.RWMutex) — Port 3003
└── 03_Donnees_CSV/
    ├── mesures_brutes.csv                      # Relevés bruts globaux (2 400 essais / 412 800 requêtes)
    ├── mesures_nodejs.csv                      # Relevés bruts Node.js (600 essais)
    ├── mesures_python.csv                      # Relevés bruts Python (600 essais)
    ├── mesures_php.csv                         # Relevés bruts PHP (600 essais)
    ├── mesures_go.csv                          # Relevés bruts Go (600 essais)
    └── synthese_moyennes.csv                   # Moyennes agrégées par palier (60 configurations)
