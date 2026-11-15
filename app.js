const express = require('express');
const app = express();
app.use(express.json());

const COMMUNES = ["Gombe", "Limete", "Ngaliema", "Bandalungwa", "Kintambo"];
const motos = {};

// Initialisation de 500 motos-taxis en memoire (RAM)
for (let i = 1; i <= 500; i++) {
    motos[`moto-${i}`] = {
        id: `moto-${i}`,
        statut: (i % 2 === 0) ? "libre" : "en_course",
        commune: COMMUNES[i % 5]
    };
}

// 1. Mettre a jour le statut d'une moto
app.post('/status', (req, res) => {
    const { id, statut, commune } = req.body;
    if (!id || !statut || !commune) {
        return res.status(400).json({ error: "Donnees incompletes" });
    }
    motos[id] = { id, statut, commune };
    res.status(201).json({ status: "ok", id, statut, commune });
});

// 2. Lister et filtrer les motos par commune
app.get('/motos', (req, res) => {
    const commune = req.query.commune;
    const liste = Object.values(motos).filter(m => !commune || m.commune === commune);
    res.json({
        commune: commune || "Toutes",
        count: liste.length,
        motos: liste
    });
});

// 3. Calculer les statistiques globales de disponibilite de la flotte
app.get('/stats', (req, res) => {
    let libres = 0;
    let en_course = 0;
    const valeurs = Object.values(motos);
    for (let i = 0; i < valeurs.length; i++) {
        if (valeurs[i].statut === "libre") {
            libres++;
        } else {
            en_course++;
        }
    }
    const total = valeurs.length;
    const taux = total > 0 ? Number(((libres / total) * 100).toFixed(2)) : 0;
    res.json({
        total: total,
        libres: libres,
        en_course: en_course,
        taux_disponibilite: taux
    });
});

app.listen(3000, '127.0.0.1', () => {
    console.log('Serveur Node.js (Express) demarre sur http://127.0.0.1:3000');
});
