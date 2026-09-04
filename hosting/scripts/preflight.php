<?php

declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    fwrite(STDERR, "CLI only.\n");
    exit(2);
}

$checkDb = in_array('--check-db', $argv, true);
$failed = false;

function astrea_preflight_line(string $status, string $label, string $detail): void
{
    fwrite(STDOUT, sprintf("[%s] %s: %s\n", $status, $label, $detail));
}

function astrea_preflight_fail(string $label, string $detail): void
{
    global $failed;
    $failed = true;
    astrea_preflight_line('FAIL', $label, $detail);
}

function astrea_preflight_public_root(): ?string
{
    $sourceRoot = dirname(__DIR__);
    if (is_file($sourceRoot . '/api/bootstrap.php')) {
        return $sourceRoot;
    }

    $packagedRoot = dirname(__DIR__, 2) . '/public';
    if (is_file($packagedRoot . '/api/bootstrap.php')) {
        return $packagedRoot;
    }

    return null;
}

function astrea_preflight_config_path(string $publicRoot): ?string
{
    $paths = [
        dirname($publicRoot) . '/private/config/config.local.php',
        $publicRoot . '/config/config.local.php',
    ];
    foreach ($paths as $path) {
        if (is_file($path)) {
            return $path;
        }
    }
    return null;
}

astrea_preflight_line('INFO', 'PHP', PHP_VERSION . ' (' . PHP_SAPI . ')');
if (version_compare(PHP_VERSION, '8.2.0', '<')) {
    astrea_preflight_fail('PHP version', 'PHP 8.2+ is required for the supported HOSTING deployment baseline.');
} else {
    astrea_preflight_line('OK', 'PHP version', 'supported');
}

$requiredExtensions = ['pdo', 'pdo_mysql', 'json', 'session', 'filter', 'hash'];
foreach ($requiredExtensions as $extension) {
    if (!extension_loaded($extension)) {
        astrea_preflight_fail('Extension ' . $extension, 'missing');
    } else {
        astrea_preflight_line('OK', 'Extension ' . $extension, 'loaded');
    }
}

foreach (['fileinfo', 'gd', 'imagick'] as $extension) {
    astrea_preflight_line(
        extension_loaded($extension) ? 'OK' : 'INFO',
        'Optional extension ' . $extension,
        extension_loaded($extension) ? 'loaded' : 'not loaded'
    );
}

foreach (['upload_max_filesize', 'post_max_size', 'memory_limit', 'max_execution_time', 'max_input_vars'] as $setting) {
    $value = ini_get($setting);
    astrea_preflight_line('INFO', 'PHP ' . $setting, is_string($value) && $value !== '' ? $value : '(not reported)');
}

$sessionPath = ini_get('session.save_path');
astrea_preflight_line('INFO', 'Session save path', is_string($sessionPath) && $sessionPath !== '' ? $sessionPath : '(default)');

$publicRoot = astrea_preflight_public_root();
if ($publicRoot === null) {
    astrea_preflight_fail('HOSTING runtime', 'public/api/bootstrap.php could not be located.');
} else {
    astrea_preflight_line('OK', 'HOSTING runtime', $publicRoot);
    $configPath = astrea_preflight_config_path($publicRoot);
    if ($configPath === null) {
        if ($checkDb) {
            astrea_preflight_fail('Configuration', 'config.local.php is missing; database check cannot run.');
        } else {
            astrea_preflight_line('INFO', 'Configuration', 'not installed yet; run again with --check-db after configuration.');
        }
    } else {
        astrea_preflight_line('OK', 'Configuration', 'config.local.php found outside output details.');

        if ($checkDb) {
            try {
                require_once $publicRoot . '/api/bootstrap.php';
                $db = astrea_db();
                $databaseVersion = (string) $db->query('SELECT VERSION()')->fetchColumn();
                astrea_preflight_line('OK', 'MySQL connection', $databaseVersion !== '' ? $databaseVersion : 'connected');

                $expectedTables = [
                    'editor_login_attempts',
                    'editor_users',
                    'events',
                    'hosting_schema_migrations',
                    'materials',
                    'news',
                    'pages',
                ];
                $actualTables = $db->query('SHOW TABLES')->fetchAll(PDO::FETCH_COLUMN);
                $actualTables = array_values(array_filter($actualTables, 'is_string'));
                sort($actualTables);
                $missingTables = array_values(array_diff($expectedTables, $actualTables));
                if ($missingTables !== []) {
                    astrea_preflight_fail('Schema tables', 'missing: ' . implode(', ', $missingTables));
                } else {
                    astrea_preflight_line('OK', 'Schema tables', 'all required tables present');
                }

                $versions = $db->query('SELECT version FROM hosting_schema_migrations ORDER BY version')->fetchAll(PDO::FETCH_COLUMN);
                $expectedVersions = ['001_initial', '002_editor_auth'];
                $missingVersions = array_values(array_diff($expectedVersions, $versions));
                if ($missingVersions !== []) {
                    astrea_preflight_fail('Schema migrations', 'missing: ' . implode(', ', $missingVersions));
                } else {
                    astrea_preflight_line('OK', 'Schema migrations', implode(', ', $expectedVersions));
                }
            } catch (Throwable $error) {
                astrea_preflight_fail('Database check', 'failed; verify credentials, schema and account database availability.');
            }
        }
    }
}

if ($failed) {
    fwrite(STDERR, "HOSTING preflight failed.\n");
    exit(1);
}

fwrite(STDOUT, $checkDb ? "HOSTING preflight and database check passed.\n" : "HOSTING capability preflight passed.\n");
