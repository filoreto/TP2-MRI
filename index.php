<?php
header('Content-Type: application/json');

$communes = ["Gombe", "Limete", "Ngaliema", "Bandalungwa", "Kintambo"];
$motos = [];

// Initialisation de 500 motos-taxis en memoire (RAM)
for ($i = 1; $i <= 500; $i++) {
    $id = "moto-" . $i;
    $motos[$id] = [
        "id" => $id,
        "statut" => ($i % 2 === 0) ? "libre" : "en_course",
        "commune" => $communes[$i % 5]
    ];
}

$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];

// 1. Mettre a jour le statut d'une moto
if ($method === 'POST' && $uri === '/status') {
    $data = json_decode(file_get_contents('php://input'), true);
    if (!isset($data['id'], $data['statut'], $data['commune'])) {
        http_response_code(400);
        echo json_encode(["error" => "Donnees incompletes"]);
        exit;
    }
    $id = $data['id'];
    $motos[$id] = [
        "id" => $id,
        "statut" => $data['statut'],
        "commune" => $data['commune']
    ];
    http_response_code(201);
    echo json_encode([
        "status" => "ok",
        "id" => $id,
        "statut" => $data['statut'],
        "commune" => $data['commune']
    ]);
    exit;
}

// 2. Lister et filtrer les motos par commune
if ($method === 'GET' && $uri === '/motos') {
    $commune = $_GET['commune'] ?? null;
    $liste = [];
    foreach ($motos as $m) {
        if (!$commune || $m['commune'] === $commune) {
            $liste[] = $m;
        }
    }
    echo json_encode([
        "commune" => $commune ? $commune : "Toutes",
        "count" => count($liste),
        "motos" => $liste
    ]);
    exit;
}

// 3. Calculer les statistiques globales de disponibilite de la flotte
if ($method === 'GET' && $uri === '/stats') {
    $libres = 0;
    $en_course = 0;
    foreach ($motos as $m) {
        if ($m['statut'] === 'libre') {
            $libres++;
        } else {
            $en_course++;
        }
    }
    $total = count($motos);
    $taux = $total > 0 ? round(($libres / $total) * 100, 2) : 0;
    echo json_encode([
        "total" => $total,
        "libres" => $libres,
        "en_course" => $en_course,
        "taux_disponibilite" => $taux
    ]);
    exit;
}

http_response_code(404);
echo json_encode(["error" => "Route introuvable"]);
