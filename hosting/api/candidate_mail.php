<?php

declare(strict_types=1);

const ASTREA_CANDIDATE_MAIL_TO = 'freemasons@internet.ru';
const ASTREA_CANDIDATE_MAIL_FROM = 'noreply@mason-astrea.ru';
const ASTREA_CANDIDATE_MAX_PHOTO_BYTES = 8388608;

function astrea_candidate_submit(array $form, array $files): void
{
    $honeypot = is_string($form['website'] ?? null) ? trim($form['website']) : '';
    if ($honeypot !== '') {
        return;
    }

    $data = [
        'full_name' => astrea_candidate_text($form, 'full_name', 255),
        'date_of_birth' => astrea_candidate_date($form['date_of_birth'] ?? null),
        'city' => astrea_candidate_text($form, 'city', 120),
        'phone' => astrea_candidate_text($form, 'phone', 80),
        'email' => astrea_candidate_email($form['email'] ?? null),
        'education' => astrea_candidate_text($form, 'education', 4000),
        'occupation' => astrea_candidate_text($form, 'occupation', 4000),
        'marital_status' => astrea_candidate_text($form, 'marital_status', 120),
        'other_organizations' => astrea_candidate_text($form, 'other_organizations', 4000, false),
        'social_links' => astrea_candidate_text($form, 'social_links', 4000, false),
        'motivation' => astrea_candidate_text($form, 'motivation', 4000),
    ];

    foreach (['personal_data_processing', 'privacy_policy_acknowledgement', 'saint_petersburg_acknowledgement'] as $consent) {
        if (!astrea_candidate_consent($form[$consent] ?? null)) {
            throw new InvalidArgumentException('Required consent is missing.');
        }
    }

    $photo = astrea_candidate_photo($files['photo'] ?? null);
    if (!astrea_candidate_send_mail($data, $photo)) {
        throw new RuntimeException('Candidate mail delivery failed.');
    }
}

function astrea_candidate_text(array $form, string $key, int $max, bool $required = true): ?string
{
    $value = $form[$key] ?? null;
    if (!is_string($value)) {
        if ($required) {
            throw new InvalidArgumentException('Required field is missing.');
        }
        return null;
    }

    $value = trim($value);
    if ($value === '') {
        if ($required) {
            throw new InvalidArgumentException('Required field is empty.');
        }
        return null;
    }
    if (strlen($value) > $max) {
        throw new InvalidArgumentException('Field is too long.');
    }
    return $value;
}

function astrea_candidate_date(mixed $value): string
{
    if (!is_string($value) || preg_match('/^(\d{4})-(\d{2})-(\d{2})$/D', $value, $matches) !== 1) {
        throw new InvalidArgumentException('Invalid date.');
    }
    if (!checkdate((int)$matches[2], (int)$matches[3], (int)$matches[1])) {
        throw new InvalidArgumentException('Invalid date.');
    }
    return $value;
}

function astrea_candidate_email(mixed $value): string
{
    if (!is_string($value)) {
        throw new InvalidArgumentException('Invalid email.');
    }
    $value = trim($value);
    if ($value === '' || strlen($value) > 255 || preg_match('/[\r\n]/', $value) === 1 || filter_var($value, FILTER_VALIDATE_EMAIL) === false) {
        throw new InvalidArgumentException('Invalid email.');
    }
    return $value;
}

function astrea_candidate_consent(mixed $value): bool
{
    return $value === 'true' || $value === '1' || $value === 1 || $value === true || $value === 'on';
}

function astrea_candidate_photo(mixed $upload): array
{
    if (!is_array($upload)) {
        throw new InvalidArgumentException('Photo is required.');
    }

    $error = (int)($upload['error'] ?? UPLOAD_ERR_NO_FILE);
    if ($error === UPLOAD_ERR_INI_SIZE || $error === UPLOAD_ERR_FORM_SIZE) {
        throw new LengthException('Photo is too large.');
    }
    if ($error !== UPLOAD_ERR_OK) {
        throw new InvalidArgumentException('Photo upload failed.');
    }

    $tmpName = $upload['tmp_name'] ?? null;
    $size = (int)($upload['size'] ?? 0);
    if (!is_string($tmpName) || $tmpName === '' || !is_uploaded_file($tmpName) || $size < 1) {
        throw new InvalidArgumentException('Invalid photo upload.');
    }
    if ($size > ASTREA_CANDIDATE_MAX_PHOTO_BYTES) {
        throw new LengthException('Photo is too large.');
    }

    if (!function_exists('finfo_open')) {
        throw new RuntimeException('File validation is unavailable.');
    }
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    if ($finfo === false) {
        throw new RuntimeException('File validation is unavailable.');
    }
    try {
        $mime = finfo_file($finfo, $tmpName);
    } finally {
        finfo_close($finfo);
    }

    $allowed = [
        'image/jpeg' => 'jpg',
        'image/png' => 'png',
        'image/webp' => 'webp',
    ];
    if (!is_string($mime) || !isset($allowed[$mime])) {
        throw new InvalidArgumentException('Unsupported photo type.');
    }
    if (@getimagesize($tmpName) === false) {
        throw new InvalidArgumentException('Invalid image file.');
    }

    $contents = file_get_contents($tmpName);
    if (!is_string($contents) || $contents === '') {
        throw new RuntimeException('Photo could not be read.');
    }

    return [
        'mime' => $mime,
        'filename' => 'candidate-photo.' . $allowed[$mime],
        'contents' => $contents,
    ];
}

function astrea_candidate_send_mail(array $data, array $photo): bool
{
    $subject = 'Новая анкета кандидата — ДЛ «Астрея» №3';
    $encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $boundary = '=_Astrea_' . bin2hex(random_bytes(18));

    $headers = [
        'MIME-Version: 1.0',
        'From: Astrea Website <' . ASTREA_CANDIDATE_MAIL_FROM . '>',
        'Reply-To: ' . $data['email'],
        'Content-Type: multipart/mixed; boundary="' . $boundary . '"',
    ];

    $lines = [
        'Новая анкета кандидата с сайта ДЛ «Астрея» №3.',
        '',
        'ФИО: ' . $data['full_name'],
        'Дата рождения: ' . $data['date_of_birth'],
        'Город проживания: ' . $data['city'],
        'Телефон: ' . $data['phone'],
        'Email: ' . $data['email'],
        '',
        'Образование:',
        (string)$data['education'],
        '',
        'Работа / род занятий:',
        (string)$data['occupation'],
        '',
        'Семейное положение: ' . $data['marital_status'],
        '',
        'Членство в иных организациях:',
        $data['other_organizations'] ?? '—',
        '',
        'VK / публичные социальные ссылки:',
        $data['social_links'] ?? '—',
        '',
        'О себе / мотивация:',
        (string)$data['motivation'],
        '',
        'Согласие на обработку персональных данных: да',
        'Ознакомление с политикой конфиденциальности: да',
        'Подтверждение подачи заявки в Санкт-Петербург: да',
        '',
        'Фотография кандидата приложена к письму.',
    ];

    $text = implode("\r\n", $lines);
    $attachment = chunk_split(base64_encode((string)$photo['contents']));
    $filename = (string)$photo['filename'];
    $mime = (string)$photo['mime'];

    $body = '--' . $boundary . "\r\n"
        . "Content-Type: text/plain; charset=UTF-8\r\n"
        . "Content-Transfer-Encoding: 8bit\r\n\r\n"
        . $text . "\r\n\r\n"
        . '--' . $boundary . "\r\n"
        . 'Content-Type: ' . $mime . '; name="' . $filename . "\"\r\n"
        . "Content-Transfer-Encoding: base64\r\n"
        . 'Content-Disposition: attachment; filename="' . $filename . "\"\r\n\r\n"
        . $attachment . "\r\n"
        . '--' . $boundary . "--\r\n";

    return @mail(ASTREA_CANDIDATE_MAIL_TO, $encodedSubject, $body, implode("\r\n", $headers));
}
