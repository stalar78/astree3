<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/api/public_content.php';

const ASTREA_EDITOR_PAGE_KEYS = ['about', 'contacts', 'faq', 'lodges_spb', 'materials', 'principles'];
const ASTREA_EDITOR_EVENT_TYPES = ['work', 'feast', 'other'];

function astrea_editor_text(mixed $value, int $max, bool $required = true): ?string
{
    if (!is_string($value)) {
        if ($required) throw new InvalidArgumentException('Поле обязательно.');
        return null;
    }
    $value = trim($value);
    if ($value === '') {
        if ($required) throw new InvalidArgumentException('Поле обязательно.');
        return null;
    }
    if (strlen($value) > $max) throw new InvalidArgumentException('Поле слишком длинное.');
    return $value;
}

function astrea_editor_slug(mixed $value): string
{
    $slug = astrea_editor_text($value, 160, true);
    if (!is_string($slug) || preg_match(ASTREA_SLUG_PATTERN, $slug) !== 1) {
        throw new InvalidArgumentException('Slug должен содержать только строчные латинские буквы, цифры и дефисы.');
    }
    return $slug;
}

function astrea_editor_bool(mixed $value): int
{
    return $value === '1' || $value === 1 || $value === true || $value === 'on' ? 1 : 0;
}

function astrea_editor_https_url(mixed $value, int $max = 1000): ?string
{
    $url = astrea_editor_text($value, $max, false);
    if ($url === null) return null;
    if (filter_var($url, FILTER_VALIDATE_URL) === false || parse_url($url, PHP_URL_SCHEME) !== 'https') {
        throw new InvalidArgumentException('Разрешены только корректные HTTPS-ссылки.');
    }
    return $url;
}

function astrea_editor_publish_timestamp(int $published, mixed $existing = null): ?string
{
    if ($published !== 1) return null;
    if (is_string($existing) && $existing !== '') return $existing;
    return (new DateTimeImmutable('now', new DateTimeZone('UTC')))->format('Y-m-d H:i:s.u');
}

function astrea_editor_list_news(PDO $db): array
{
    return $db->query('SELECT id, slug, title, is_published, published_at, updated_at FROM news ORDER BY updated_at DESC, id DESC')->fetchAll();
}

function astrea_editor_get_news(PDO $db, int $id): ?array
{
    $st = $db->prepare('SELECT * FROM news WHERE id = :id LIMIT 1');
    $st->execute(['id' => $id]);
    $row = $st->fetch();
    return is_array($row) ? $row : null;
}

function astrea_editor_save_news(PDO $db, array $input): int
{
    $id = max(0, (int)($input['id'] ?? 0));
    $slug = astrea_editor_slug($input['slug'] ?? null);
    $title = astrea_editor_text($input['title'] ?? null, 255, true);
    $excerpt = astrea_editor_text($input['excerpt'] ?? null, 5000, true);
    $body = astrea_editor_text($input['body'] ?? null, 200000, true);
    $imageUrl = astrea_editor_https_url($input['image_url'] ?? null, 500);
    $published = astrea_editor_bool($input['is_published'] ?? null);
    $existing = $id > 0 ? astrea_editor_get_news($db, $id) : null;
    if ($id > 0 && $existing === null) throw new InvalidArgumentException('Новость не найдена.');
    $publishedAt = astrea_editor_publish_timestamp($published, $existing['published_at'] ?? null);

    try {
        $params = ['slug'=>$slug,'title'=>$title,'excerpt'=>$excerpt,'body'=>$body,'image_url'=>$imageUrl,'is_published'=>$published,'published_at'=>$publishedAt];
        if ($id > 0) {
            $st = $db->prepare('UPDATE news SET slug=:slug,title=:title,excerpt=:excerpt,body=:body,image_url=:image_url,is_published=:is_published,published_at=:published_at WHERE id=:id');
            $st->execute($params + ['id'=>$id]);
            return $id;
        }
        $st = $db->prepare('INSERT INTO news (slug,title,excerpt,body,image_url,is_published,published_at) VALUES (:slug,:title,:excerpt,:body,:image_url,:is_published,:published_at)');
        $st->execute($params);
        return (int)$db->lastInsertId();
    } catch (PDOException $error) {
        if ((string)$error->getCode() === '23000') throw new InvalidArgumentException('Такой slug уже используется.');
        throw $error;
    }
}

function astrea_editor_delete_news(PDO $db, int $id): void
{
    $st = $db->prepare('DELETE FROM news WHERE id=:id');
    $st->execute(['id'=>$id]);
}

function astrea_editor_list_materials(PDO $db): array
{
    return $db->query('SELECT id, material_type, slug, title, is_published, sort_order, updated_at FROM materials ORDER BY sort_order ASC, updated_at DESC, id DESC')->fetchAll();
}

function astrea_editor_get_material(PDO $db, int $id): ?array
{
    $st=$db->prepare('SELECT * FROM materials WHERE id=:id LIMIT 1');
    $st->execute(['id'=>$id]);
    $row=$st->fetch();
    return is_array($row)?$row:null;
}

function astrea_editor_save_material(PDO $db, array $input): int
{
    $id=max(0,(int)($input['id']??0));
    $type=astrea_editor_text($input['material_type']??null,20,true);
    if (!is_string($type) || !in_array($type, ASTREA_MATERIAL_TYPES, true)) throw new InvalidArgumentException('Недопустимый тип материала.');
    $slug=astrea_editor_slug($input['slug']??null);
    $title=astrea_editor_text($input['title']??null,255,true);
    $excerpt=astrea_editor_text($input['excerpt']??null,5000,true);
    $body=astrea_editor_text($input['body']??null,200000,false);
    $author=astrea_editor_text($input['author']??null,255,false);
    $sourceUrl=astrea_editor_https_url($input['source_url']??null,1000);
    if ($type === 'video' && ($sourceUrl === null || astrea_rutube_video($sourceUrl) === null)) throw new InvalidArgumentException('Для видео нужна корректная HTTPS-ссылка RuTube.');
    $sortOrder=max(-100000,min(100000,(int)($input['sort_order']??0)));
    $published=astrea_editor_bool($input['is_published']??null);
    $existing=$id>0?astrea_editor_get_material($db,$id):null;
    if($id>0&&$existing===null) throw new InvalidArgumentException('Материал не найден.');
    $publishedAt=astrea_editor_publish_timestamp($published,$existing['published_at']??null);

    try {
        $params=['material_type'=>$type,'slug'=>$slug,'title'=>$title,'excerpt'=>$excerpt,'body'=>$body,'author'=>$author,'source_url'=>$sourceUrl,'sort_order'=>$sortOrder,'is_published'=>$published,'published_at'=>$publishedAt];
        if($id>0){
            $st=$db->prepare('UPDATE materials SET material_type=:material_type,slug=:slug,title=:title,excerpt=:excerpt,body=:body,author=:author,source_url=:source_url,sort_order=:sort_order,is_published=:is_published,published_at=:published_at WHERE id=:id');
            $st->execute($params+['id'=>$id]); return $id;
        }
        $st=$db->prepare('INSERT INTO materials (material_type,slug,title,excerpt,body,author,source_url,sort_order,is_published,published_at) VALUES (:material_type,:slug,:title,:excerpt,:body,:author,:source_url,:sort_order,:is_published,:published_at)');
        $st->execute($params); return (int)$db->lastInsertId();
    } catch(PDOException $error){
        if((string)$error->getCode()==='23000') throw new InvalidArgumentException('Такой slug уже используется.');
        throw $error;
    }
}

function astrea_editor_delete_material(PDO $db,int $id):void
{
    $st=$db->prepare('DELETE FROM materials WHERE id=:id'); $st->execute(['id'=>$id]);
}

function astrea_editor_list_events(PDO $db): array
{
    return $db->query('SELECT id,title,event_date,event_type,is_published,updated_at FROM events ORDER BY event_date ASC,id ASC')->fetchAll();
}

function astrea_editor_get_event(PDO $db,int $id):?array
{
    $st=$db->prepare('SELECT * FROM events WHERE id=:id LIMIT 1'); $st->execute(['id'=>$id]); $row=$st->fetch();
    return is_array($row)?$row:null;
}

function astrea_editor_save_event(PDO $db,array $input):int
{
    $id=max(0,(int)($input['id']??0));
    $title=astrea_editor_text($input['title']??null,255,true);
    $date=astrea_editor_text($input['event_date']??null,10,true);
    astrea_validate_date((string)$date);
    $type=astrea_editor_text($input['event_type']??null,32,true);
    if(!is_string($type)||!in_array($type,ASTREA_EDITOR_EVENT_TYPES,true)) throw new InvalidArgumentException('Недопустимый тип события.');
    $note=astrea_editor_text($input['note']??null,10000,false);
    $published=astrea_editor_bool($input['is_published']??null);
    if($id>0&&astrea_editor_get_event($db,$id)===null) throw new InvalidArgumentException('Событие не найдено.');
    $params=['title'=>$title,'event_date'=>$date,'event_type'=>$type,'note'=>$note,'is_published'=>$published];
    if($id>0){
        $st=$db->prepare('UPDATE events SET title=:title,event_date=:event_date,event_type=:event_type,note=:note,is_published=:is_published WHERE id=:id');
        $st->execute($params+['id'=>$id]); return $id;
    }
    $st=$db->prepare('INSERT INTO events (title,event_date,event_type,note,is_published) VALUES (:title,:event_date,:event_type,:note,:is_published)');
    $st->execute($params); return(int)$db->lastInsertId();
}

function astrea_editor_delete_event(PDO $db,int $id):void
{
    $st=$db->prepare('DELETE FROM events WHERE id=:id'); $st->execute(['id'=>$id]);
}

function astrea_editor_list_pages(PDO $db):array
{
    return $db->query('SELECT `key`,title,is_published,updated_at FROM pages ORDER BY `key` ASC')->fetchAll();
}

function astrea_editor_get_page(PDO $db,string $key):?array
{
    if(!in_array($key,ASTREA_EDITOR_PAGE_KEYS,true)) return null;
    $st=$db->prepare('SELECT * FROM pages WHERE `key`=:key LIMIT 1'); $st->execute(['key'=>$key]); $row=$st->fetch();
    return is_array($row)?$row:null;
}

function astrea_editor_save_page(PDO $db,array $input):string
{
    $key=is_string($input['key']??null)?$input['key']:'';
    if(!in_array($key,ASTREA_EDITOR_PAGE_KEYS,true)||astrea_editor_get_page($db,$key)===null) throw new InvalidArgumentException('Страница не найдена.');
    $title=astrea_editor_text($input['title']??null,255,true);
    $content=astrea_editor_text($input['content']??null,200000,true);
    $published=astrea_editor_bool($input['is_published']??null);
    $st=$db->prepare('UPDATE pages SET title=:title,content=:content,is_published=:is_published WHERE `key`=:key');
    $st->execute(['title'=>$title,'content'=>$content,'is_published'=>$published,'key'=>$key]);
    return $key;
}
