<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/api/bootstrap.php';

const ASTREA_EDITOR_MAX_FAILURES = 5;
const ASTREA_EDITOR_FAILURE_WINDOW_SECONDS = 900;
const ASTREA_EDITOR_BLOCK_SECONDS = 900;
const ASTREA_EDITOR_IDLE_SECONDS = 28800;
const ASTREA_EDITOR_USERNAME_PATTERN = '/^[A-Za-z0-9._-]{3,120}$/D';

function astrea_editor_start_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }

    $config = astrea_config();
    $session = $config['session'] ?? [];
    if (!is_array($session)) {
        $session = [];
    }

    $name = $session['name'] ?? 'astrea_lite';
    $secure = $session['secure'] ?? true;
    $sameSite = $session['same_site'] ?? 'Strict';

    if (!is_string($name) || preg_match('/^[A-Za-z0-9_-]{1,64}$/D', $name) !== 1) {
        throw new RuntimeException('Invalid editor session configuration.');
    }
    if (!is_bool($secure) || !in_array($sameSite, ['Strict', 'Lax'], true)) {
        throw new RuntimeException('Invalid editor session configuration.');
    }

    session_name($name);
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => '/editor',
        'secure' => $secure,
        'httponly' => true,
        'samesite' => $sameSite,
    ]);
    if (!session_start()) {
        throw new RuntimeException('Unable to start editor session.');
    }

    $now = time();
    $lastSeen = $_SESSION['last_seen'] ?? null;
    if (is_int($lastSeen) && ($now - $lastSeen) > ASTREA_EDITOR_IDLE_SECONDS) {
        astrea_editor_clear_session();
        session_regenerate_id(true);
    }
    $_SESSION['last_seen'] = $now;
}

function astrea_editor_clear_session(): void
{
    $_SESSION = [];
}

function astrea_editor_is_authenticated(): bool
{
    return isset($_SESSION['editor_user_id'], $_SESSION['editor_username'])
        && is_int($_SESSION['editor_user_id'])
        && is_string($_SESSION['editor_username']);
}

function astrea_editor_username(): ?string
{
    return astrea_editor_is_authenticated() ? $_SESSION['editor_username'] : null;
}

function astrea_editor_csrf_token(): string
{
    $token = $_SESSION['csrf_token'] ?? null;
    if (!is_string($token) || strlen($token) < 32) {
        $token = bin2hex(random_bytes(32));
        $_SESSION['csrf_token'] = $token;
    }
    return $token;
}

function astrea_editor_verify_csrf(mixed $value): bool
{
    $expected = $_SESSION['csrf_token'] ?? null;
    return is_string($value) && is_string($expected) && hash_equals($expected, $value);
}

function astrea_editor_client_key(?string $remoteAddress): string
{
    $address = is_string($remoteAddress) ? trim($remoteAddress) : '';
    if ($address === '' || filter_var($address, FILTER_VALIDATE_IP) === false) {
        $address = 'unknown';
    }
    return hash('sha256', $address);
}

function astrea_editor_authenticate(PDO $db, string $username, string $password, string $clientKey): array
{
    $username = trim($username);
    if (preg_match(ASTREA_EDITOR_USERNAME_PATTERN, $username) !== 1 || $password === '') {
        astrea_editor_record_failure($db, $clientKey);
        return ['ok' => false, 'blocked' => astrea_editor_is_blocked($db, $clientKey), 'user' => null];
    }

    if (astrea_editor_is_blocked($db, $clientKey)) {
        return ['ok' => false, 'blocked' => true, 'user' => null];
    }

    $statement = $db->prepare(
        'SELECT id, username, password_hash FROM editor_users '
        . 'WHERE username = :username AND is_active = 1 LIMIT 1'
    );
    $statement->execute(['username' => $username]);
    $row = $statement->fetch();

    static $dummyHash = null;
    if (!is_string($dummyHash)) {
        $dummyHash = password_hash('astrea-invalid-password', PASSWORD_DEFAULT);
    }
    $hash = is_array($row) && is_string($row['password_hash'] ?? null) ? $row['password_hash'] : $dummyHash;
    $valid = password_verify($password, $hash);

    if (!$valid || !is_array($row)) {
        astrea_editor_record_failure($db, $clientKey);
        return ['ok' => false, 'blocked' => astrea_editor_is_blocked($db, $clientKey), 'user' => null];
    }

    astrea_editor_clear_failures($db, $clientKey);
    return [
        'ok' => true,
        'blocked' => false,
        'user' => ['id' => (int) $row['id'], 'username' => (string) $row['username']],
    ];
}

function astrea_editor_login_session(array $user): void
{
    $id = $user['id'] ?? null;
    $username = $user['username'] ?? null;
    if (!is_int($id) || $id < 1 || !is_string($username)) {
        throw new InvalidArgumentException('Invalid editor user.');
    }
    session_regenerate_id(true);
    $_SESSION['editor_user_id'] = $id;
    $_SESSION['editor_username'] = $username;
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    $_SESSION['last_seen'] = time();
}

function astrea_editor_logout_session(): void
{
    astrea_editor_clear_session();
    if (session_status() === PHP_SESSION_ACTIVE) {
        session_regenerate_id(true);
    }
}

function astrea_editor_is_blocked(PDO $db, string $clientKey): bool
{
    astrea_editor_validate_client_key($clientKey);
    $statement = $db->prepare('SELECT blocked_until FROM editor_login_attempts WHERE client_key = :client_key LIMIT 1');
    $statement->execute(['client_key' => $clientKey]);
    $value = $statement->fetchColumn();
    if (!is_string($value) || $value === '') {
        return false;
    }
    $blockedUntil = DateTimeImmutable::createFromFormat('!Y-m-d H:i:s.u', $value, new DateTimeZone('UTC'));
    if ($blockedUntil === false) {
        $blockedUntil = DateTimeImmutable::createFromFormat('!Y-m-d H:i:s', $value, new DateTimeZone('UTC'));
    }
    return $blockedUntil instanceof DateTimeImmutable && $blockedUntil > new DateTimeImmutable('now', new DateTimeZone('UTC'));
}

function astrea_editor_record_failure(PDO $db, string $clientKey): void
{
    astrea_editor_validate_client_key($clientKey);
    $now = new DateTimeImmutable('now', new DateTimeZone('UTC'));

    $db->beginTransaction();
    try {
        $statement = $db->prepare(
            'SELECT failed_count, window_started_at, blocked_until '
            . 'FROM editor_login_attempts WHERE client_key = :client_key FOR UPDATE'
        );
        $statement->execute(['client_key' => $clientKey]);
        $row = $statement->fetch();

        $count = 1;
        $windowStarted = $now;
        if (is_array($row)) {
            $storedStart = astrea_editor_parse_utc($row['window_started_at'] ?? null);
            if ($storedStart !== null && ($now->getTimestamp() - $storedStart->getTimestamp()) <= ASTREA_EDITOR_FAILURE_WINDOW_SECONDS) {
                $count = ((int) $row['failed_count']) + 1;
                $windowStarted = $storedStart;
            }
        }

        $blockedUntil = $count >= ASTREA_EDITOR_MAX_FAILURES
            ? $now->modify('+' . ASTREA_EDITOR_BLOCK_SECONDS . ' seconds')
            : null;

        $upsert = $db->prepare(
            'INSERT INTO editor_login_attempts (client_key, failed_count, window_started_at, blocked_until) '
            . 'VALUES (:client_key, :failed_count, :window_started_at, :blocked_until) '
            . 'ON DUPLICATE KEY UPDATE failed_count = VALUES(failed_count), '
            . 'window_started_at = VALUES(window_started_at), blocked_until = VALUES(blocked_until)'
        );
        $upsert->execute([
            'client_key' => $clientKey,
            'failed_count' => $count,
            'window_started_at' => $windowStarted->format('Y-m-d H:i:s.u'),
            'blocked_until' => $blockedUntil?->format('Y-m-d H:i:s.u'),
        ]);
        $db->commit();
    } catch (Throwable $error) {
        if ($db->inTransaction()) {
            $db->rollBack();
        }
        throw $error;
    }
}

function astrea_editor_clear_failures(PDO $db, string $clientKey): void
{
    astrea_editor_validate_client_key($clientKey);
    $statement = $db->prepare('DELETE FROM editor_login_attempts WHERE client_key = :client_key');
    $statement->execute(['client_key' => $clientKey]);
}

function astrea_editor_parse_utc(mixed $value): ?DateTimeImmutable
{
    if (!is_string($value) || $value === '') {
        return null;
    }
    $timezone = new DateTimeZone('UTC');
    $date = DateTimeImmutable::createFromFormat('!Y-m-d H:i:s.u', $value, $timezone);
    if ($date === false) {
        $date = DateTimeImmutable::createFromFormat('!Y-m-d H:i:s', $value, $timezone);
    }
    return $date === false ? null : $date;
}

function astrea_editor_validate_client_key(string $clientKey): void
{
    if (preg_match('/^[a-f0-9]{64}$/D', $clientKey) !== 1) {
        throw new InvalidArgumentException('Invalid editor client key.');
    }
}
