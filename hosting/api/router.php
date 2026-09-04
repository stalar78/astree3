<?php

declare(strict_types=1);

require_once __DIR__ . '/public_content.php';

function astrea_dispatch(PDO $db, string $method, string $path, array $query): array
{
    if ($method !== 'GET') {
        return [404, ['detail' => 'Not found']];
    }

    try {
        if (preg_match('#^/api/v1/pages/([^/]+)$#D', $path, $matches) === 1) {
            $page = astrea_public_page($db, rawurldecode($matches[1]));
            return $page === null ? [404, ['detail' => 'Page not found']] : [200, $page];
        }

        if ($path === '/api/v1/news') {
            return [200, astrea_public_news($db, astrea_parse_limit($query), astrea_parse_offset($query))];
        }
        if (preg_match('#^/api/v1/news/([^/]+)$#D', $path, $matches) === 1) {
            $post = astrea_public_news_post($db, rawurldecode($matches[1]));
            return $post === null ? [404, ['detail' => 'News post not found']] : [200, $post];
        }

        if ($path === '/api/v1/materials') {
            $type = astrea_optional_query_string($query, 'type');
            return [200, astrea_public_materials($db, astrea_parse_limit($query), astrea_parse_offset($query), $type)];
        }
        if (preg_match('#^/api/v1/materials/([^/]+)$#D', $path, $matches) === 1) {
            $material = astrea_public_material($db, rawurldecode($matches[1]));
            return $material === null ? [404, ['detail' => 'Material not found']] : [200, $material];
        }

        if ($path === '/api/v1/videos') {
            return [200, astrea_public_videos($db, astrea_parse_limit($query), astrea_parse_offset($query))];
        }
        if (preg_match('#^/api/v1/videos/(\d+)$#D', $path, $matches) === 1) {
            $video = astrea_public_video($db, (int) $matches[1]);
            return $video === null ? [404, ['detail' => 'Video not found']] : [200, $video];
        }

        if ($path === '/api/v1/events') {
            $from = astrea_optional_query_string($query, 'from');
            $to = astrea_optional_query_string($query, 'to');
            return [
                200,
                astrea_public_events(
                    $db,
                    astrea_parse_limit($query, ASTREA_MAX_LIMIT),
                    astrea_parse_offset($query),
                    $from,
                    $to
                ),
            ];
        }
    } catch (InvalidArgumentException) {
        return [422, ['detail' => 'Invalid request']];
    }

    return [404, ['detail' => 'Not found']];
}
