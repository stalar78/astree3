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
$originalHome = astrea_editor_get_home_block($db, 'home_1');
if (!is_array($originalPage)) throw new RuntimeException('Seeded materials page missing.');
if (!is_array($originalHome)) throw new RuntimeException('Seeded homepage block missing.');

$uploadRoot = sys_get_temp_dir() . '/astrea-news-upload-' . bin2hex(random_bytes(8));
putenv('ASTREA_HOSTING_NEWS_UPLOAD_DIR=' . $uploadRoot);

$newsId = null;
$materialId = null;
$eventId = null;
$temporaryFiles = [];

try {
    $visiblePages = astrea_editor_list_pages($db);
    expect_true(count($visiblePages) === 3, 'Lite Editor page list must match the current frontend.');
    $visibleKeys = array_map(static fn(array $row): string => (string)$row['key'], $visiblePages);
    expect_true($visibleKeys === ['about', 'contacts', 'materials'], 'Unexpected Lite Editor page keys.');
    expect_true(astrea_editor_get_page($db, 'faq') === null, 'FAQ must not be exposed in Lite Editor.');
    expect_true(astrea_editor_get_page($db, 'lodges_spb') === null, 'Lodges page must not be exposed in Lite Editor.');
    expect_true(astrea_editor_get_page($db, 'principles') === null, 'Principles page must not be exposed in Lite Editor.');

    $homeBlocks = astrea_editor_list_home_blocks($db);
    expect_true(count($homeBlocks) === 3, 'Expected three editable homepage blocks.');
    astrea_editor_save_home_block($db, [
        'key' => 'home_1',
        'eyebrow' => 'CI Home',
        'title' => 'CI Homepage Title',
        'text' => 'CI homepage text',
        'image_url' => '/media/home/home-welcome.webp',
        'href' => '/materialy',
    ]);
    $publicHome = astrea_public_page($db, 'home_1');
    expect_true(is_array($publicHome) && $publicHome['title'] === 'CI Homepage Title', 'Homepage block did not publish.');
    $homePayload = json_decode((string)$publicHome['content'], true);
    expect_true(is_array($homePayload) && $homePayload['eyebrow'] === 'CI Home', 'Homepage block payload is invalid.');

    $pngBytes = base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', true);
    if (!is_string($pngBytes)) throw new RuntimeException('Unable to build test image.');
    $tmpImage = tempnam(sys_get_temp_dir(), 'astrea-news-');
    if (!is_string($tmpImage)) throw new RuntimeException('Unable to create test image.');
    $temporaryFiles[] = $tmpImage;
    file_put_contents($tmpImage, $pngBytes);
    $imageFile = [
        'name' => 'news.png',
        'type' => 'image/png',
        'tmp_name' => $tmpImage,
        'error' => UPLOAD_ERR_OK,
        'size' => filesize($tmpImage),
    ];
    $testImageStore = static fn(array $file): string => astrea_editor_store_news_image($file, false);

    $newsId = astrea_editor_save_news($db, [
        'slug' => 'ci-news-item',
        'title' => 'CI News',
        'excerpt' => 'Short text',
        'body' => 'Full text',
    ], ['image_file' => $imageFile], $testImageStore);
    expect_true(astrea_public_news_post($db, 'ci-news-item') === null, 'Draft news leaked publicly.');

    $storedNews = astrea_editor_get_news($db, $newsId);
    $storedImageUrl = is_array($storedNews) ? ($storedNews['image_url'] ?? null) : null;
    $storedFilename = astrea_editor_news_image_filename($storedImageUrl);
    expect_true(is_string($storedFilename), 'Uploaded news image URL was not stored.');
    expect_true(is_file($uploadRoot . DIRECTORY_SEPARATOR . $storedFilename), 'Uploaded news image file is missing.');

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
    expect_true(($publicNews['image_url'] ?? null) === $storedImageUrl, 'Published news lost uploaded image URL.');

    astrea_editor_save_news($db, [
        'id' => $newsId,
        'slug' => 'ci-news-item',
        'title' => 'CI News Published',
        'excerpt' => 'Short text',
        'body' => 'Full text',
        'image_url' => $storedImageUrl,
        'remove_image' => '1',
        'is_published' => '1',
    ]);
    $withoutImage = astrea_editor_get_news($db, $newsId);
    expect_true(is_array($withoutImage) && $withoutImage['image_url'] === null, 'News image removal did not persist.');
    expect_true(!is_file($uploadRoot . DIRECTORY_SEPARATOR . $storedFilename), 'Removed news image file still exists.');

    $badFile = tempnam(sys_get_temp_dir(), 'astrea-bad-image-');
    if (!is_string($badFile)) throw new RuntimeException('Unable to create invalid image fixture.');
    $temporaryFiles[] = $badFile;
    file_put_contents($badFile, 'not an image');
    $badRejected = false;
    try {
        astrea_editor_store_news_image([
            'name' => 'fake.png',
            'type' => 'image/png',
            'tmp_name' => $badFile,
            'error' => UPLOAD_ERR_OK,
            'size' => filesize($badFile),
        ], false);
    } catch (InvalidArgumentException) {
        $badRejected = true;
    }
    expect_true($badRejected, 'Non-image upload accepted as a news image.');

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
    foreach ($temporaryFiles as $temporaryFile) {
        if (is_string($temporaryFile) && is_file($temporaryFile)) @unlink($temporaryFile);
    }
    if (is_dir($uploadRoot)) {
        foreach (glob($uploadRoot . DIRECTORY_SEPARATOR . '*') ?: [] as $file) {
            if (is_file($file)) @unlink($file);
        }
        @rmdir($uploadRoot);
    }
    putenv('ASTREA_HOSTING_NEWS_UPLOAD_DIR');
    $restore = $db->prepare('UPDATE pages SET title=:title, content=:content, is_published=:is_published WHERE `key`=:key');
    $restore->execute([
        'title'=>$originalPage['title'],
        'content'=>$originalPage['content'],
        'is_published'=>$originalPage['is_published'],
        'key'=>'materials',
    ]);
    $originalHomeContent = json_encode([
        'eyebrow'=>$originalHome['eyebrow'],
        'text'=>$originalHome['text'],
        'image_url'=>$originalHome['image_url'] !== '' ? $originalHome['image_url'] : null,
        'href'=>$originalHome['href'] !== '' ? $originalHome['href'] : null,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $restore->execute([
        'title'=>$originalHome['title'],
        'content'=>$originalHomeContent,
        'is_published'=>1,
        'key'=>'home_1',
    ]);
}
