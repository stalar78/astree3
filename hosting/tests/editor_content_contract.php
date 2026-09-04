<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/api/bootstrap.php';
require_once dirname(__DIR__) . '/editor/content.php';

function expect_true(bool $condition, string $message): void
{
    if (!$condition) throw new RuntimeException($message);
}

$db = astrea_db();
$originalPage = astrea_editor_get_page($db, 'materials');
if (!is_array($originalPage)) throw new RuntimeException('Seeded materials page missing.');

$newsId = null;
$materialId = null;
$eventId = null;

try {
    $newsId = astrea_editor_save_news($db, [
        'slug' => 'ci-news-item',
        'title' => 'CI News',
        'excerpt' => 'Short text',
        'body' => 'Full text',
    ]);
    expect_true(astrea_public_news_post($db, 'ci-news-item') === null, 'Draft news leaked publicly.');

    astrea_editor_save_news($db, [
        'id' => $newsId,
        'slug' => 'ci-news-item',
        'title' => 'CI News Published',
        'excerpt' => 'Short text',
        'body' => 'Full text',
        'is_published' => '1',
    ]);
    $publicNews = astrea_public_news_post($db, 'ci-news-item');
    expect_true(is_array($publicNews) && $publicNews['title'] === 'CI News Published', 'Published news unavailable publicly.');

    $materialId = astrea_editor_save_material($db, [
        'material_type' => 'video',
        'slug' => 'ci-video-item',
        'title' => 'CI Video',
        'excerpt' => 'Video description',
        'source_url' => 'https://rutube.ru/video/0123456789abcdef0123456789abcdef/',
    ]);
    expect_true(astrea_public_material($db, 'ci-video-item') === null, 'Draft material leaked publicly.');

    astrea_editor_save_material($db, [
        'id' => $materialId,
        'material_type' => 'video',
        'slug' => 'ci-video-item',
        'title' => 'CI Video',
        'excerpt' => 'Video description',
        'source_url' => 'https://rutube.ru/video/0123456789abcdef0123456789abcdef/',
        'is_published' => '1',
    ]);
    expect_true(astrea_public_material($db, 'ci-video-item') !== null, 'Published material unavailable publicly.');

    $rejectedVideo = false;
    try {
        astrea_editor_save_material($db, [
            'material_type' => 'video',
            'slug' => 'ci-invalid-video',
            'title' => 'Bad Video',
            'excerpt' => 'Bad',
            'source_url' => 'https://example.com/video',
        ]);
    } catch (InvalidArgumentException) {
        $rejectedVideo = true;
    }
    expect_true($rejectedVideo, 'Non-RuTube video URL accepted.');

    $eventId = astrea_editor_save_event($db, [
        'title' => 'CI Event',
        'event_date' => '2026-09-30',
        'event_type' => 'work',
        'note' => 'Public note',
    ]);
    expect_true(astrea_public_events($db, 20, 0, '2026-09-30', '2026-09-30') === [], 'Draft event leaked publicly.');

    astrea_editor_save_event($db, [
        'id' => $eventId,
        'title' => 'CI Event',
        'event_date' => '2026-09-30',
        'event_type' => 'work',
        'note' => 'Public note',
        'is_published' => '1',
    ]);
    $events = astrea_public_events($db, 20, 0, '2026-09-30', '2026-09-30');
    expect_true(count($events) === 1 && $events[0]['title'] === 'CI Event', 'Published event unavailable publicly.');

    astrea_editor_save_page($db, [
        'key' => 'materials',
        'title' => 'CI Materials',
        'content' => 'CI materials content',
        'is_published' => '1',
    ]);
    $page = astrea_public_page($db, 'materials');
    expect_true(is_array($page) && $page['title'] === 'CI Materials', 'Published managed page unavailable publicly.');

    $badKeyRejected = false;
    try {
        astrea_editor_save_page($db, ['key'=>'invented','title'=>'X','content'=>'Y']);
    } catch (InvalidArgumentException) {
        $badKeyRejected = true;
    }
    expect_true($badKeyRejected, 'Arbitrary page key accepted.');

    astrea_editor_delete_news($db, $newsId);
    $newsId = null;
    astrea_editor_delete_material($db, $materialId);
    $materialId = null;
    astrea_editor_delete_event($db, $eventId);
    $eventId = null;

    echo "HOSTING editor content contract verified.\n";
} finally {
    if (is_int($newsId)) astrea_editor_delete_news($db, $newsId);
    if (is_int($materialId)) astrea_editor_delete_material($db, $materialId);
    if (is_int($eventId)) astrea_editor_delete_event($db, $eventId);
    $restore = $db->prepare('UPDATE pages SET title=:title, content=:content, is_published=:is_published WHERE `key`=:key');
    $restore->execute([
        'title'=>$originalPage['title'],
        'content'=>$originalPage['content'],
        'is_published'=>$originalPage['is_published'],
        'key'=>'materials',
    ]);
}
