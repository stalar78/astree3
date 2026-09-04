<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/api/bootstrap.php';
require_once dirname(__DIR__) . '/api/router.php';

function expect_status(array $result, int $status): array
{
    if ($result[0] !== $status) {
        throw new RuntimeException("Expected status {$status}, got {$result[0]}");
    }
    return $result[1];
}

function expect_true(bool $condition, string $message): void
{
    if (!$condition) {
        throw new RuntimeException($message);
    }
}

$db = astrea_db();
$db->beginTransaction();

try {
    $db->exec("UPDATE pages SET is_published = 0");
    $db->exec("UPDATE pages SET is_published = 1, title = 'О ложе тест', content = 'Публичный текст' WHERE `key` = 'about'");

    $db->exec("INSERT INTO news (slug, title, excerpt, body, is_published, published_at) VALUES
        ('public-news', 'Публичная новость', 'Кратко', 'Полный текст', 1, '2026-09-04 06:00:00'),
        ('draft-news', 'Черновик', 'Не показывать', 'Скрыто', 0, NULL)");

    $db->exec("INSERT INTO materials
        (material_type, slug, title, excerpt, body, author, source_url, sort_order, is_published, published_at)
        VALUES
        ('book', 'public-book', 'Книга', 'Рекомендуем', NULL, 'Автор', 'https://example.com/book', 1, 1, '2026-09-04 06:00:00'),
        ('video', 'public-video', 'Видео', 'Описание видео', NULL, NULL, 'https://rutube.ru/video/0123456789abcdef0123456789abcdef/', 2, 1, '2026-09-04 07:00:00'),
        ('audio', 'draft-audio', 'Черновой подкаст', 'Не показывать', NULL, NULL, 'https://example.com/audio', 3, 0, NULL)");

    $db->exec("INSERT INTO events (title, event_date, event_type, note, is_published) VALUES
        ('Работа ложи', '2026-09-20', 'lodge_work', 'Санкт-Петербург', 1),
        ('Скрытое событие', '2026-09-21', 'other', NULL, 0)");

    $page = expect_status(astrea_dispatch($db, 'GET', '/api/v1/pages/about', []), 200);
    expect_true($page['title'] === 'О ложе тест', 'Published page was not returned.');
    expect_status(astrea_dispatch($db, 'GET', '/api/v1/pages/contacts', []), 404);

    $news = expect_status(astrea_dispatch($db, 'GET', '/api/v1/news', []), 200);
    expect_true(count($news) === 1 && $news[0]['slug'] === 'public-news', 'Draft news leaked into public list.');
    $newsDetail = expect_status(astrea_dispatch($db, 'GET', '/api/v1/news/public-news', []), 200);
    expect_true($newsDetail['body'] === 'Полный текст', 'Published news detail is incomplete.');
    expect_status(astrea_dispatch($db, 'GET', '/api/v1/news/draft-news', []), 404);

    $materials = expect_status(astrea_dispatch($db, 'GET', '/api/v1/materials', []), 200);
    expect_true(count($materials) === 2, 'Unexpected published material count.');
    $books = expect_status(astrea_dispatch($db, 'GET', '/api/v1/materials', ['type' => 'book']), 200);
    expect_true(count($books) === 1 && $books[0]['slug'] === 'public-book', 'Material type filter failed.');
    expect_status(astrea_dispatch($db, 'GET', '/api/v1/materials/draft-audio', []), 404);

    $videos = expect_status(astrea_dispatch($db, 'GET', '/api/v1/videos', []), 200);
    expect_true(count($videos) === 1, 'Published video mapping failed.');
    expect_true($videos[0]['provider'] === 'rutube', 'Unexpected video provider.');
    expect_true($videos[0]['embed_url'] === 'https://rutube.ru/play/embed/0123456789abcdef0123456789abcdef/', 'RuTube embed URL was not derived safely.');

    $events = expect_status(
        astrea_dispatch($db, 'GET', '/api/v1/events', ['from' => '2026-09-01', 'to' => '2026-09-30']),
        200
    );
    expect_true(count($events) === 1 && $events[0]['title'] === 'Работа ложи', 'Draft event leaked or date filter failed.');

    expect_status(astrea_dispatch($db, 'GET', '/api/v1/news', ['limit' => '101']), 422);
    expect_status(astrea_dispatch($db, 'GET', '/api/v1/events', ['from' => '2026-10-01', 'to' => '2026-09-01']), 422);
    expect_status(astrea_dispatch($db, 'POST', '/api/v1/news', []), 404);
    expect_status(astrea_dispatch($db, 'POST', '/api/v1/candidate-applications', []), 404);

    $editorUsers = (int) $db->query('SELECT COUNT(*) FROM editor_users')->fetchColumn();
    expect_true($editorUsers === 0, 'H2 must not seed editor credentials.');

    echo "HOSTING public content contract verified.\n";
} finally {
    $db->rollBack();
}
