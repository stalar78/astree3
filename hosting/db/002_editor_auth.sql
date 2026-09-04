SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE IF NOT EXISTS editor_login_attempts (
    client_key CHAR(64) NOT NULL PRIMARY KEY,
    failed_count INT UNSIGNED NOT NULL DEFAULT 0,
    window_started_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    blocked_until DATETIME(6) NULL,
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY ix_editor_login_blocked_until (blocked_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO hosting_schema_migrations (version) VALUES ('002_editor_auth');
