<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/router.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$requestUri = $_SERVER['REQUEST_URI'] ?? '/';
$path = parse_url($requestUri, PHP_URL_PATH);
$path = is_string($path) ? $path : '/';

function astrea_emit_json(int $status, array $payload): never
{
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

if ($method === 'GET' && ($path === '/api/health' || $path === '/api/v1/health')) {
    astrea_emit_json(200, ['status' => 'ok', 'edition' => 'hosting']);
}

try {
    [$status, $payload] = astrea_dispatch(astrea_db(), $method, $path, $_GET);
    astrea_emit_json($status, $payload);
} catch (Throwable) {
    astrea_emit_json(503, ['detail' => 'Service unavailable']);
}
