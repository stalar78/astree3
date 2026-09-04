<?php

declare(strict_types=1);

function astrea_config(): array
{
    static $config = null;
    if (is_array($config)) {
        return $config;
    }

    $localPath = dirname(__DIR__) . '/config/config.local.php';
    if (is_file($localPath)) {
        $loaded = require $localPath;
        if (!is_array($loaded)) {
            throw new RuntimeException('Invalid HOSTING configuration.');
        }
        $config = $loaded;
        return $config;
    }

    $dsn = getenv('ASTREA_HOSTING_DB_DSN');
    $username = getenv('ASTREA_HOSTING_DB_USER');
    $password = getenv('ASTREA_HOSTING_DB_PASSWORD');

    if (!is_string($dsn) || $dsn === '' || !is_string($username) || $username === '' || !is_string($password)) {
        throw new RuntimeException('HOSTING configuration is not installed.');
    }

    $config = [
        'db' => [
            'dsn' => $dsn,
            'username' => $username,
            'password' => $password,
        ],
    ];
    return $config;
}

function astrea_db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }

    $config = astrea_config();
    $db = $config['db'] ?? null;
    if (!is_array($db)) {
        throw new RuntimeException('Invalid HOSTING database configuration.');
    }

    $dsn = $db['dsn'] ?? null;
    $username = $db['username'] ?? null;
    $password = $db['password'] ?? null;
    if (!is_string($dsn) || !is_string($username) || !is_string($password)) {
        throw new RuntimeException('Invalid HOSTING database configuration.');
    }

    $pdo = new PDO($dsn, $username, $password, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);
    $pdo->exec("SET time_zone = '+00:00'");
    return $pdo;
}
