<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/api/candidate_mail.php';

function expect_candidate(bool $condition, string $message): void
{
    if (!$condition) throw new RuntimeException($message);
}

expect_candidate(ASTREA_CANDIDATE_MAIL_TO === 'freemasons@internet.ru', 'Unexpected candidate mail recipient.');
expect_candidate(ASTREA_CANDIDATE_MAX_PHOTO_BYTES === 8388608, 'Unexpected candidate photo limit.');
expect_candidate(astrea_candidate_text(['name'=>'  Test User  '], 'name', 50) === 'Test User', 'Candidate text normalization failed.');
expect_candidate(astrea_candidate_text([], 'optional', 50, false) === null, 'Optional candidate field must allow null.');
expect_candidate(astrea_candidate_date('2026-09-11') === '2026-09-11', 'Candidate date validation failed.');
expect_candidate(astrea_candidate_email('candidate@example.com') === 'candidate@example.com', 'Candidate email validation failed.');
expect_candidate(astrea_candidate_consent('true'), 'Expected consent value was rejected.');
expect_candidate(!astrea_candidate_consent('false'), 'False consent value was accepted.');

$badEmailRejected=false;
try { astrea_candidate_email("bad@example.com\r\nBcc: attacker@example.com"); }
catch(InvalidArgumentException){ $badEmailRejected=true; }
expect_candidate($badEmailRejected, 'Header-injection email value was accepted.');

$badDateRejected=false;
try { astrea_candidate_date('2026-02-31'); }
catch(InvalidArgumentException){ $badDateRejected=true; }
expect_candidate($badDateRejected, 'Impossible date was accepted.');

echo "HOSTING candidate mail contract verified.\n";
