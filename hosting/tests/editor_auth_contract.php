<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/editor/auth.php';

function expect_true(bool $condition, string $message): void
{
    if (!$condition) {
        throw new RuntimeException($message);
    }
}

$db = astrea_db();
$db->beginTransaction();

try {
    $db->exec('DELETE FROM editor_login_attempts');
    $db->exec('DELETE FROM editor_users');

    $password = 'correct-horse-battery-staple';
    $hash = password_hash($password, PASSWORD_DEFAULT);
    expect_true(is_string($hash), 'Unable to create test password hash.');

    $insert = $db->prepare(
        'INSERT INTO editor_users (username, password_hash, is_active) VALUES (:username, :password_hash, 1)'
    );
    $insert->execute(['username' => 'ciadmin', 'password_hash' => $hash]);

    $clientA = astrea_editor_client_key('192.0.2.10');
    $clientB = astrea_editor_client_key('192.0.2.11');
    expect_true(strlen($clientA) === 64 && $clientA !== '192.0.2.10', 'Client address must be hashed.');

    $success = astrea_editor_authenticate($db, 'ciadmin', $password, $clientA);
    expect_true($success['ok'] === true, 'Valid editor credentials were rejected.');
    expect_true($success['user']['username'] === 'ciadmin', 'Authenticated user mismatch.');

    for ($attempt = 0; $attempt < ASTREA_EDITOR_MAX_FAILURES; $attempt++) {
        astrea_editor_authenticate($db, 'ciadmin', 'wrong-password', $clientA);
    }
    expect_true(astrea_editor_is_blocked($db, $clientA), 'Repeated failures did not trigger throttling.');

    $blockedCorrect = astrea_editor_authenticate($db, 'ciadmin', $password, $clientA);
    expect_true($blockedCorrect['ok'] === false && $blockedCorrect['blocked'] === true, 'Blocked client bypassed throttle.');

    $otherClient = astrea_editor_authenticate($db, 'ciadmin', $password, $clientB);
    expect_true($otherClient['ok'] === true, 'Throttle leaked across independent client keys.');

    $missingUser = astrea_editor_authenticate($db, 'missing-user', 'some-password', $clientB);
    expect_true($missingUser['ok'] === false, 'Unknown editor user authenticated.');

    $_SESSION = [];
    $token = astrea_editor_csrf_token();
    expect_true(strlen($token) === 64, 'CSRF token has unexpected length.');
    expect_true(astrea_editor_verify_csrf($token), 'Valid CSRF token rejected.');
    expect_true(!astrea_editor_verify_csrf('invalid'), 'Invalid CSRF token accepted.');

    $storedKey = $db->query('SELECT client_key FROM editor_login_attempts LIMIT 1')->fetchColumn();
    expect_true(!is_string($storedKey) || filter_var($storedKey, FILTER_VALIDATE_IP) === false, 'Plain client IP leaked to throttle table.');

    echo "HOSTING editor auth contract verified.\n";
} finally {
    $db->rollBack();
}
