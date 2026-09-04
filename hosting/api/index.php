<?php

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$requestUri = $_SERVER['REQUEST_URI'] ?? '/';
$path = parse_url($requestUri, PHP_URL_PATH);
$path = is_string($path) ? $path : '/';

if ($method === 'GET' && ($path === '/api/health' || $path === '/api/v1/health')) {
    http_response_code(200);
    echo json_encode(
        ['status' => 'ok', 'edition' => 'hosting'],
        JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
    );
    exit;
}

http_response_code(404);
echo json_encode(
    ['detail' => 'Not found'],
    JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
);
