<?php

declare(strict_types=1);

function astrea_bootstrap_public_root(): string
{
    // Source tree: <repo>/hosting/scripts/bootstrap-editor.php -> <repo>/hosting
    $sourceRoot = dirname(__DIR__);
    if (is_file($sourceRoot . '/api/bootstrap.php') && is_file($sourceRoot . '/editor/auth.php')) {
        return $sourceRoot;
    }

    // Deployment package: <site>/private/scripts/bootstrap-editor.php -> <site>/public
    $packagedRoot = dirname(__DIR__, 2) . '/public';
    if (is_file($packagedRoot . '/api/bootstrap.php') && is_file($packagedRoot . '/editor/auth.php')) {
        return $packagedRoot;
    }

    fwrite(STDERR, "Unable to locate the HOSTING public runtime.\n");
    exit(2);
}

$publicRoot = astrea_bootstrap_public_root();
require_once $publicRoot . '/api/bootstrap.php';
require_once $publicRoot . '/editor/auth.php';

if (PHP_SAPI !== 'cli') {
    fwrite(STDERR, "CLI only.\n");
    exit(2);
}

$username = $argv[1] ?? null;
if (!is_string($username) || preg_match(ASTREA_EDITOR_USERNAME_PATTERN, $username) !== 1) {
    fwrite(STDERR, "Usage: php bootstrap-editor.php <username>\n");
    fwrite(STDERR, "Password is read from standard input and is never accepted as a command-line argument.\n");
    exit(2);
}

fwrite(STDOUT, "Enter editor password via stdin: ");
$password = stream_get_contents(STDIN);
if (!is_string($password)) {
    fwrite(STDERR, "Unable to read password.\n");
    exit(2);
}
$password = rtrim($password, "\r\n");

if (strlen($password) < 14 || strlen($password) > 200) {
    fwrite(STDERR, "Password must be between 14 and 200 characters.\n");
    exit(2);
}

$db = astrea_db();
$existing = (int) $db->query('SELECT COUNT(*) FROM editor_users')->fetchColumn();
if ($existing !== 0) {
    fwrite(STDERR, "Editor account already exists. Bootstrap is one-time only.\n");
    exit(1);
}

$hash = password_hash($password, PASSWORD_DEFAULT);
if (!is_string($hash) || $hash === '') {
    fwrite(STDERR, "Unable to hash password.\n");
    exit(1);
}

$statement = $db->prepare(
    'INSERT INTO editor_users (username, password_hash, is_active) VALUES (:username, :password_hash, 1)'
);
$statement->execute(['username' => $username, 'password_hash' => $hash]);

fwrite(STDOUT, "Lite Editor account created for {$username}.\n");
