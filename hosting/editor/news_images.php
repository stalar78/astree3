<?php

declare(strict_types=1);

const ASTREA_NEWS_IMAGE_MAX_BYTES = 5 * 1024 * 1024;
const ASTREA_NEWS_IMAGE_MAX_PIXELS = 40_000_000;
const ASTREA_NEWS_IMAGE_MAX_DIMENSION = 12_000;
const ASTREA_NEWS_IMAGE_URL_PREFIX = '/uploads/news/';
const ASTREA_NEWS_IMAGE_FILENAME_PATTERN = '/^[a-f0-9]{32}\.(?:jpg|png|webp)$/';

function astrea_editor_news_image_root(): string
{
    $override = getenv('ASTREA_HOSTING_NEWS_UPLOAD_DIR');
    if (is_string($override) && trim($override) !== '') {
        return rtrim($override, DIRECTORY_SEPARATOR);
    }

    return dirname(__DIR__, 2) . '/private/uploads/news';
}

function astrea_editor_news_image_filename(mixed $url): ?string
{
    if (!is_string($url) || !str_starts_with($url, ASTREA_NEWS_IMAGE_URL_PREFIX)) {
        return null;
    }

    $filename = substr($url, strlen(ASTREA_NEWS_IMAGE_URL_PREFIX));
    if (!is_string($filename) || preg_match(ASTREA_NEWS_IMAGE_FILENAME_PATTERN, $filename) !== 1) {
        return null;
    }

    return $filename;
}

function astrea_editor_news_image_url(mixed $value): ?string
{
    if (!is_string($value)) {
        return null;
    }

    $value = trim($value);
    if ($value === '') {
        return null;
    }

    if (astrea_editor_news_image_filename($value) !== null) {
        return $value;
    }

    if (strlen($value) > 500 || filter_var($value, FILTER_VALIDATE_URL) === false || parse_url($value, PHP_URL_SCHEME) !== 'https') {
        throw new InvalidArgumentException('Для изображения укажите HTTPS-ссылку или загрузите файл.');
    }

    return $value;
}

function astrea_editor_store_news_image(array $file, bool $requireUploadedFile = true): string
{
    $error = $file['error'] ?? null;
    if (!is_int($error)) {
        throw new InvalidArgumentException('Не удалось прочитать загруженное изображение.');
    }
    if ($error === UPLOAD_ERR_NO_FILE) {
        throw new InvalidArgumentException('Файл изображения не выбран.');
    }
    if ($error !== UPLOAD_ERR_OK) {
        if (in_array($error, [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true)) {
            throw new InvalidArgumentException('Изображение слишком большое. Максимальный размер — 5 МБ.');
        }
        throw new InvalidArgumentException('Не удалось загрузить изображение. Попробуйте другой файл.');
    }

    $tmpName = $file['tmp_name'] ?? null;
    $size = $file['size'] ?? null;
    if (!is_string($tmpName) || $tmpName === '' || !is_file($tmpName) || !is_int($size) || $size < 1) {
        throw new InvalidArgumentException('Загруженное изображение повреждено.');
    }
    if ($size > ASTREA_NEWS_IMAGE_MAX_BYTES) {
        throw new InvalidArgumentException('Изображение слишком большое. Максимальный размер — 5 МБ.');
    }
    if ($requireUploadedFile && !is_uploaded_file($tmpName)) {
        throw new InvalidArgumentException('Некорректный файл загрузки.');
    }

    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mime = $finfo->file($tmpName);
    $extensions = [
        'image/jpeg' => 'jpg',
        'image/png' => 'png',
        'image/webp' => 'webp',
    ];
    if (!is_string($mime) || !isset($extensions[$mime])) {
        throw new InvalidArgumentException('Разрешены только изображения JPG, PNG и WebP.');
    }

    $imageInfo = @getimagesize($tmpName);
    if (!is_array($imageInfo) || !isset($imageInfo[0], $imageInfo[1], $imageInfo['mime'])) {
        throw new InvalidArgumentException('Файл не является корректным изображением.');
    }
    $width = (int)$imageInfo[0];
    $height = (int)$imageInfo[1];
    if ($imageInfo['mime'] !== $mime || $width < 1 || $height < 1) {
        throw new InvalidArgumentException('Файл не является корректным изображением.');
    }
    if ($width > ASTREA_NEWS_IMAGE_MAX_DIMENSION || $height > ASTREA_NEWS_IMAGE_MAX_DIMENSION || ($width * $height) > ASTREA_NEWS_IMAGE_MAX_PIXELS) {
        throw new InvalidArgumentException('Разрешение изображения слишком большое.');
    }

    $root = astrea_editor_news_image_root();
    if (!is_dir($root) && !mkdir($root, 0750, true) && !is_dir($root)) {
        throw new RuntimeException('Не удалось подготовить каталог изображений.');
    }
    if (!is_writable($root)) {
        throw new RuntimeException('Каталог изображений недоступен для записи.');
    }

    $filename = bin2hex(random_bytes(16)) . '.' . $extensions[$mime];
    $target = $root . DIRECTORY_SEPARATOR . $filename;
    $stored = $requireUploadedFile ? move_uploaded_file($tmpName, $target) : rename($tmpName, $target);
    if (!$stored) {
        throw new RuntimeException('Не удалось сохранить загруженное изображение.');
    }
    @chmod($target, 0640);

    return ASTREA_NEWS_IMAGE_URL_PREFIX . $filename;
}

function astrea_editor_delete_news_image(mixed $url): void
{
    $filename = astrea_editor_news_image_filename($url);
    if ($filename === null) {
        return;
    }

    $path = astrea_editor_news_image_root() . DIRECTORY_SEPARATOR . $filename;
    if (is_file($path)) {
        @unlink($path);
    }
}
