<?php

declare(strict_types=1);

const ASTREA_DEFAULT_LIMIT = 20;
const ASTREA_MAX_LIMIT = 100;
const ASTREA_SLUG_PATTERN = '/^[a-z0-9]+(?:-[a-z0-9]+)*$/D';
const ASTREA_PAGE_KEY_PATTERN = '/^[a-z0-9]+(?:_[a-z0-9]+)*$/D';
const ASTREA_MATERIAL_TYPES = ['book', 'video', 'audio', 'article'];

function astrea_public_page(PDO $db, string $key): ?array
{
    astrea_validate_identifier($key, ASTREA_PAGE_KEY_PATTERN, 80);
    $statement = $db->prepare(
        'SELECT `key`, title, content FROM pages WHERE `key` = :key AND is_published = 1 LIMIT 1'
    );
    $statement->execute(['key' => $key]);
    $row = $statement->fetch();
    return is_array($row) ? $row : null;
}

function astrea_public_news(PDO $db, int $limit, int $offset): array
{
    $sql = sprintf(
        'SELECT slug, title, excerpt, image_url, published_at FROM news '
        . 'WHERE is_published = 1 '
        . 'ORDER BY published_at IS NULL ASC, published_at DESC, id DESC LIMIT %d OFFSET %d',
        $limit,
        $offset
    );
    $rows = $db->query($sql)->fetchAll();
    return array_map('astrea_news_list_item', $rows);
}

function astrea_public_news_post(PDO $db, string $slug): ?array
{
    astrea_validate_identifier($slug, ASTREA_SLUG_PATTERN, 160);
    $statement = $db->prepare(
        'SELECT slug, title, excerpt, body, image_url, published_at '
        . 'FROM news WHERE slug = :slug AND is_published = 1 LIMIT 1'
    );
    $statement->execute(['slug' => $slug]);
    $row = $statement->fetch();
    if (!is_array($row)) {
        return null;
    }
    $row['published_at'] = astrea_public_timestamp($row['published_at'] ?? null);
    return $row;
}

function astrea_public_materials(PDO $db, int $limit, int $offset, ?string $type): array
{
    $params = [];
    $where = 'is_published = 1';
    if ($type !== null) {
        astrea_validate_material_type($type);
        $where .= ' AND material_type = :material_type';
        $params['material_type'] = $type;
    }

    $sql = sprintf(
        'SELECT id, material_type, slug, title, excerpt, body, author, source_url, media_url, sort_order, published_at '
        . 'FROM materials WHERE %s '
        . 'ORDER BY sort_order ASC, published_at IS NULL ASC, published_at DESC, id DESC LIMIT %d OFFSET %d',
        $where,
        $limit,
        $offset
    );
    $statement = $db->prepare($sql);
    $statement->execute($params);
    return array_map('astrea_material_item', $statement->fetchAll());
}

function astrea_public_material(PDO $db, string $slug): ?array
{
    astrea_validate_identifier($slug, ASTREA_SLUG_PATTERN, 160);
    $statement = $db->prepare(
        'SELECT id, material_type, slug, title, excerpt, body, author, source_url, media_url, sort_order, published_at '
        . 'FROM materials WHERE slug = :slug AND is_published = 1 LIMIT 1'
    );
    $statement->execute(['slug' => $slug]);
    $row = $statement->fetch();
    return is_array($row) ? astrea_material_item($row) : null;
}

function astrea_public_videos(PDO $db, int $limit, int $offset): array
{
    $materials = astrea_public_materials($db, $limit, $offset, 'video');
    $videos = [];
    foreach ($materials as $material) {
        $sourceUrl = $material['source_url'];
        if (!is_string($sourceUrl)) {
            continue;
        }
        $video = astrea_rutube_video($sourceUrl);
        if ($video === null) {
            continue;
        }
        $videos[] = [
            'id' => $material['id'],
            'title' => $material['title'],
            'description' => $material['excerpt'],
            'source_url' => $video['source_url'],
            'provider' => 'rutube',
            'embed_url' => $video['embed_url'],
            'published_at' => $material['published_at'],
        ];
    }
    return $videos;
}

function astrea_public_video(PDO $db, int $id): ?array
{
    if ($id < 1) {
        throw new InvalidArgumentException('Invalid video id.');
    }
    $statement = $db->prepare(
        "SELECT id, title, excerpt, source_url, published_at FROM materials "
        . "WHERE id = :id AND material_type = 'video' AND is_published = 1 LIMIT 1"
    );
    $statement->execute(['id' => $id]);
    $row = $statement->fetch();
    if (!is_array($row) || !is_string($row['source_url'] ?? null)) {
        return null;
    }
    $video = astrea_rutube_video($row['source_url']);
    if ($video === null) {
        return null;
    }
    return [
        'id' => (int) $row['id'],
        'title' => (string) $row['title'],
        'description' => (string) $row['excerpt'],
        'source_url' => $video['source_url'],
        'provider' => 'rutube',
        'embed_url' => $video['embed_url'],
        'published_at' => astrea_public_timestamp($row['published_at'] ?? null),
    ];
}

function astrea_public_events(PDO $db, int $limit, int $offset, ?string $from, ?string $to): array
{
    $where = ['is_published = 1'];
    $params = [];
    if ($from !== null) {
        astrea_validate_date($from);
        $where[] = 'event_date >= :date_from';
        $params['date_from'] = $from;
    }
    if ($to !== null) {
        astrea_validate_date($to);
        $where[] = 'event_date <= :date_to';
        $params['date_to'] = $to;
    }
    if ($from !== null && $to !== null && $from > $to) {
        throw new InvalidArgumentException('Invalid event date range.');
    }

    $sql = sprintf(
        'SELECT id, title, event_date, event_type, note FROM events WHERE %s '
        . 'ORDER BY event_date ASC, id ASC LIMIT %d OFFSET %d',
        implode(' AND ', $where),
        $limit,
        $offset
    );
    $statement = $db->prepare($sql);
    $statement->execute($params);
    return array_map(
        static fn(array $row): array => [
            'id' => (int) $row['id'],
            'title' => (string) $row['title'],
            'event_date' => (string) $row['event_date'],
            'event_type' => (string) $row['event_type'],
            'note' => $row['note'] === null ? null : (string) $row['note'],
        ],
        $statement->fetchAll()
    );
}

function astrea_news_list_item(array $row): array
{
    return [
        'slug' => (string) $row['slug'],
        'title' => (string) $row['title'],
        'excerpt' => (string) $row['excerpt'],
        'image_url' => $row['image_url'] === null ? null : (string) $row['image_url'],
        'published_at' => astrea_public_timestamp($row['published_at'] ?? null),
    ];
}

function astrea_material_item(array $row): array
{
    return [
        'id' => (int) $row['id'],
        'type' => (string) $row['material_type'],
        'slug' => (string) $row['slug'],
        'title' => (string) $row['title'],
        'excerpt' => (string) $row['excerpt'],
        'body' => $row['body'] === null ? null : (string) $row['body'],
        'author' => $row['author'] === null ? null : (string) $row['author'],
        'source_url' => $row['source_url'] === null ? null : (string) $row['source_url'],
        'media_url' => $row['media_url'] === null ? null : (string) $row['media_url'],
        'sort_order' => (int) $row['sort_order'],
        'published_at' => astrea_public_timestamp($row['published_at'] ?? null),
    ];
}

function astrea_parse_limit(array $query, int $default = ASTREA_DEFAULT_LIMIT): int
{
    return astrea_parse_bounded_integer($query['limit'] ?? null, $default, 1, ASTREA_MAX_LIMIT);
}

function astrea_parse_offset(array $query): int
{
    return astrea_parse_bounded_integer($query['offset'] ?? null, 0, 0, PHP_INT_MAX);
}

function astrea_optional_query_string(array $query, string $key): ?string
{
    if (!array_key_exists($key, $query)) {
        return null;
    }
    $value = $query[$key];
    if (!is_string($value) || $value === '') {
        throw new InvalidArgumentException('Invalid query value.');
    }
    return $value;
}

function astrea_parse_bounded_integer(mixed $value, int $default, int $minimum, int $maximum): int
{
    if ($value === null) {
        return $default;
    }
    if (!is_string($value) || preg_match('/^\d+$/D', $value) !== 1) {
        throw new InvalidArgumentException('Invalid integer query value.');
    }
    $parsed = filter_var($value, FILTER_VALIDATE_INT);
    if (!is_int($parsed) || $parsed < $minimum || $parsed > $maximum) {
        throw new InvalidArgumentException('Integer query value is out of bounds.');
    }
    return $parsed;
}

function astrea_validate_identifier(string $value, string $pattern, int $maxLength): void
{
    if ($value === '' || strlen($value) > $maxLength || preg_match($pattern, $value) !== 1) {
        throw new InvalidArgumentException('Invalid identifier.');
    }
}

function astrea_validate_material_type(string $type): void
{
    if (!in_array($type, ASTREA_MATERIAL_TYPES, true)) {
        throw new InvalidArgumentException('Invalid material type.');
    }
}

function astrea_validate_date(string $value): void
{
    $date = DateTimeImmutable::createFromFormat('!Y-m-d', $value);
    $errors = DateTimeImmutable::getLastErrors();
    if ($date === false || ($errors !== false && ($errors['warning_count'] > 0 || $errors['error_count'] > 0)) || $date->format('Y-m-d') !== $value) {
        throw new InvalidArgumentException('Invalid date.');
    }
}

function astrea_public_timestamp(mixed $value): ?string
{
    if ($value === null) {
        return null;
    }
    $text = (string) $value;
    return str_replace(' ', 'T', preg_replace('/\.0+$/', '', $text) ?? $text);
}

function astrea_rutube_video(string $value): ?array
{
    if (str_contains(strtolower($value), '<iframe') || str_contains($value, '<') || str_contains($value, '>')) {
        return null;
    }
    $parts = parse_url($value);
    if (!is_array($parts) || ($parts['scheme'] ?? null) !== 'https') {
        return null;
    }
    if (isset($parts['user']) || isset($parts['pass']) || isset($parts['port']) || isset($parts['query']) || isset($parts['fragment'])) {
        return null;
    }
    $host = strtolower((string) ($parts['host'] ?? ''));
    if (str_starts_with($host, 'www.')) {
        $host = substr($host, 4);
    }
    if ($host !== 'rutube.ru') {
        return null;
    }
    $pathParts = array_values(array_filter(explode('/', (string) ($parts['path'] ?? '')), static fn(string $part): bool => $part !== ''));
    $videoId = null;
    if (count($pathParts) === 2 && $pathParts[0] === 'video' && preg_match('/^[0-9a-fA-F]{32}$/D', $pathParts[1]) === 1) {
        $videoId = $pathParts[1];
    } elseif (count($pathParts) === 3 && $pathParts[0] === 'play' && $pathParts[1] === 'embed' && preg_match('/^[0-9a-fA-F]{32}$/D', $pathParts[2]) === 1) {
        $videoId = $pathParts[2];
    }
    if ($videoId === null) {
        return null;
    }
    $normalizedId = strtolower($videoId);
    return [
        'source_url' => "https://rutube.ru/video/{$normalizedId}/",
        'embed_url' => "https://rutube.ru/play/embed/{$normalizedId}/",
    ];
}
