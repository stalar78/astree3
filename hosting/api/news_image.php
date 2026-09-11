<?php

declare(strict_types=1);

header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');

$filename = is_string($_GET['file'] ?? null) ? $_GET['file'] : '';
if (preg_match('/^[a-f0-9]{32}\.(?:jpg|png|webp)$/', $filename) !== 1) {
    http_response_code(404);
    exit;
}

$override = getenv('ASTREA_HOSTING_NEWS_UPLOAD_DIR');
$root = is_string($override) && trim($override) !== ''
    ? rtrim($override, DIRECTORY_SEPARATOR)
    : dirname(__DIR__, 2) . '/private/uploads/news';
$path = $root . DIRECTORY_SEPARATOR . $filename;
if (!is_file($path) || !is_readable($path)) {
    http_response_code(404);
    exit;
}

$finfo = new finfo(FILEINFO_MIME_TYPE);
$mime = $finfo->file($path);
$allowed = ['image/jpeg', 'image/png', 'image/webp'];
if (!is_string($mime) || !in_array($mime, $allowed, true)) {
    http_response_code(404);
    exit;
}

$size = filesize($path);
if (!is_int($size) || $size < 1) {
    http_response_code(404);
    exit;
}

header('Content-Type: ' . $mime);
header('Content-Length: ' . $size);
header('Cache-Control: public, max-age=86400');
header('Content-Disposition: inline; filename="' . $filename . '"');
readfile($path);
