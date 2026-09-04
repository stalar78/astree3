<?php

declare(strict_types=1);

require_once __DIR__ . '/auth.php';

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store, max-age=0');
header('Pragma: no-cache');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');
header('X-Robots-Tag: noindex, nofollow, noarchive');
header("Content-Security-Policy: default-src 'self'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'");

function astrea_editor_escape(mixed $value): string
{
    return htmlspecialchars((string) $value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function astrea_editor_redirect(string $location = '/editor/'): never
{
    header('Location: ' . $location, true, 303);
    exit;
}

function astrea_editor_overview_counts(PDO $db): array
{
    $queries = [
        'news' => 'SELECT COUNT(*) FROM news',
        'materials' => 'SELECT COUNT(*) FROM materials',
        'events' => 'SELECT COUNT(*) FROM events',
        'pages' => 'SELECT COUNT(*) FROM pages',
    ];
    $counts = [];
    foreach ($queries as $key => $sql) {
        $counts[$key] = (int) $db->query($sql)->fetchColumn();
    }
    return $counts;
}

$error = null;
$statusMessage = null;

try {
    astrea_editor_start_session();
    $db = astrea_db();

    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
        $action = $_POST['action'] ?? '';

        if ($action === 'login' && !astrea_editor_is_authenticated()) {
            $username = is_string($_POST['username'] ?? null) ? $_POST['username'] : '';
            $password = is_string($_POST['password'] ?? null) ? $_POST['password'] : '';
            $clientKey = astrea_editor_client_key($_SERVER['REMOTE_ADDR'] ?? null);
            $result = astrea_editor_authenticate($db, $username, $password, $clientKey);

            if ($result['ok'] === true && is_array($result['user'])) {
                astrea_editor_login_session($result['user']);
                astrea_editor_redirect();
            }
            $error = $result['blocked'] === true
                ? 'Слишком много неудачных попыток. Попробуйте позже.'
                : 'Неверное имя пользователя или пароль.';
        } elseif ($action === 'logout' && astrea_editor_is_authenticated()) {
            if (!astrea_editor_verify_csrf($_POST['csrf_token'] ?? null)) {
                http_response_code(403);
                $error = 'Сессия формы устарела. Обновите страницу и повторите действие.';
            } else {
                astrea_editor_logout_session();
                astrea_editor_redirect();
            }
        } else {
            http_response_code(400);
            $error = 'Некорректный запрос.';
        }
    }
} catch (Throwable) {
    http_response_code(503);
    $db = null;
    $error = 'Редактор временно недоступен. Проверьте конфигурацию хостинга.';
}

$authenticated = astrea_editor_is_authenticated();
$counts = $authenticated && $db instanceof PDO ? astrea_editor_overview_counts($db) : [];
$csrfToken = $authenticated ? astrea_editor_csrf_token() : null;
$username = $authenticated ? astrea_editor_username() : null;
?>
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <title>Astrea Lite Editor</title>
  <style>
    :root { color-scheme: dark; --bg:#071019; --panel:#0d1822; --line:#29404f; --text:#eef2f4; --muted:#9aa8b2; --red:#9b1c2f; --red2:#ba2740; --gold:#b9a471; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; background:linear-gradient(180deg,#050c12,#09141d); color:var(--text); font-family:Arial,Helvetica,sans-serif; }
    a { color:inherit; }
    .wrap { width:min(1120px,calc(100% - 32px)); margin:0 auto; }
    .top { border-bottom:1px solid var(--line); background:#050b10; }
    .topin { min-height:76px; display:flex; align-items:center; justify-content:space-between; gap:20px; }
    .brand small { display:block; color:var(--gold); letter-spacing:.18em; text-transform:uppercase; font-size:11px; }
    .brand strong { display:block; margin-top:5px; font:400 27px/1.1 "Times New Roman",Times,serif; }
    .user { display:flex; align-items:center; gap:12px; color:var(--muted); font-size:14px; }
    main { padding:38px 0 60px; }
    .login { width:min(470px,100%); margin:8vh auto 0; padding:30px; border:1px solid var(--line); background:var(--panel); box-shadow:0 20px 60px rgba(0,0,0,.28); }
    h1,h2 { margin:0; font-family:"Times New Roman",Times,serif; font-weight:400; }
    h1 { font-size:34px; } h2 { font-size:24px; }
    .lead { color:var(--muted); line-height:1.6; margin:10px 0 24px; }
    label { display:block; margin:15px 0 7px; color:#dbe2e6; font-size:14px; }
    input { width:100%; border:1px solid var(--line); background:#071019; color:var(--text); padding:12px 13px; font-size:16px; outline:none; }
    input:focus { border-color:#d8dee2; box-shadow:0 0 0 2px rgba(255,255,255,.07); }
    button,.button { display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--red2); background:var(--red); color:white; padding:11px 16px; cursor:pointer; font-weight:700; letter-spacing:.04em; text-decoration:none; }
    button:hover,.button:hover { background:var(--red2); }
    .ghost { background:transparent; border-color:var(--line); color:var(--text); }
    .error { margin:0 0 18px; padding:12px 14px; border:1px solid #74303a; background:#291017; color:#ffd9df; line-height:1.45; }
    .notice { margin:0 0 18px; padding:12px 14px; border:1px solid #395949; background:#10251b; color:#d9f5e4; }
    .toolbar { display:flex; align-items:flex-start; justify-content:space-between; gap:20px; margin-bottom:28px; }
    .toolbar p { color:var(--muted); margin:8px 0 0; }
    .nav { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 24px; }
    .nav a,.nav span { padding:10px 13px; border:1px solid var(--line); text-decoration:none; font-size:14px; }
    .nav a.active { border-color:var(--red2); background:#261018; }
    .nav span { color:#687986; cursor:not-allowed; }
    .grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
    .card { border:1px solid var(--line); background:var(--panel); padding:20px; min-height:142px; }
    .card .num { font:400 40px/1 "Times New Roman",Times,serif; margin-top:24px; }
    .card p { margin:7px 0 0; color:var(--muted); font-size:13px; }
    .coming { margin-top:24px; border:1px solid var(--line); background:rgba(13,24,34,.72); padding:22px; }
    .coming p { color:var(--muted); line-height:1.6; margin:8px 0 0; }
    .actions { margin-top:22px; display:flex; gap:10px; }
    @media (max-width:800px) { .grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .topin,.toolbar { align-items:flex-start; flex-direction:column; padding:18px 0; } .user { width:100%; justify-content:space-between; } }
    @media (max-width:480px) { .grid { grid-template-columns:1fr; } .wrap { width:min(100% - 22px,1120px); } .login { padding:22px; } }
  </style>
</head>
<body>
<header class="top">
  <div class="wrap topin">
    <div class="brand"><small>Astrea</small><strong>Lite Editor</strong></div>
    <?php if ($authenticated): ?>
      <div class="user">
        <span><?= astrea_editor_escape($username) ?></span>
        <form method="post" action="/editor/">
          <input type="hidden" name="action" value="logout">
          <input type="hidden" name="csrf_token" value="<?= astrea_editor_escape($csrfToken) ?>">
          <button class="ghost" type="submit">Выйти</button>
        </form>
      </div>
    <?php endif; ?>
  </div>
</header>
<main class="wrap">
  <?php if (!$authenticated): ?>
    <section class="login">
      <h1>Вход в редактор</h1>
      <p class="lead">Управление новостями, материалами, календарём и страницами ложи.</p>
      <?php if ($error): ?><div class="error"><?= astrea_editor_escape($error) ?></div><?php endif; ?>
      <form method="post" action="/editor/" autocomplete="on">
        <input type="hidden" name="action" value="login">
        <label for="username">Имя пользователя</label>
        <input id="username" name="username" type="text" maxlength="120" autocomplete="username" required>
        <label for="password">Пароль</label>
        <input id="password" name="password" type="password" autocomplete="current-password" required>
        <div class="actions"><button type="submit">Войти</button></div>
      </form>
    </section>
  <?php else: ?>
    <div class="toolbar">
      <div><h1>Панель управления</h1><p>Короткий редактор для повседневного обновления сайта.</p></div>
    </div>
    <?php if ($error): ?><div class="error"><?= astrea_editor_escape($error) ?></div><?php endif; ?>
    <?php if ($statusMessage): ?><div class="notice"><?= astrea_editor_escape($statusMessage) ?></div><?php endif; ?>
    <nav class="nav" aria-label="Разделы редактора">
      <a class="active" href="/editor/">Обзор</a>
      <span title="Следующий этап">Новости</span>
      <span title="Следующий этап">Материалы</span>
      <span title="Следующий этап">События</span>
      <span title="Следующий этап">Страницы</span>
    </nav>
    <section class="grid" aria-label="Сводка контента">
      <article class="card"><h2>Новости</h2><div class="num"><?= (int) ($counts['news'] ?? 0) ?></div><p>Всего записей</p></article>
      <article class="card"><h2>Материалы</h2><div class="num"><?= (int) ($counts['materials'] ?? 0) ?></div><p>Книги, видео, аудио, статьи</p></article>
      <article class="card"><h2>События</h2><div class="num"><?= (int) ($counts['events'] ?? 0) ?></div><p>Даты работ и мероприятий</p></article>
      <article class="card"><h2>Страницы</h2><div class="num"><?= (int) ($counts['pages'] ?? 0) ?></div><p>Предопределённые страницы</p></article>
    </section>
    <section class="coming">
      <h2>Редактор подключён</h2>
      <p>Авторизация, защищённая сессия, CSRF и ограничение попыток входа работают. Формы редактирования контента подключаются следующим H3-срезом.</p>
    </section>
  <?php endif; ?>
</main>
</body>
</html>
