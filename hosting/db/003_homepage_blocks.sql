SET NAMES utf8mb4;
SET time_zone = '+00:00';

INSERT IGNORE INTO pages (`key`, title, content, is_published) VALUES
    (
        'home_1',
        'Добро пожаловать в достопочтенную ложу «Астрея» № 3 на Востоке Санкт-Петербурга',
        '{"eyebrow":"Астрея №3","text":"Единственная регулярная Великая Ложа, действующая на территории России, признанная регулярными Великими Ложами стран мира. Вновь учрежденная в 1995 году, Великая Ложа России неукоснительно хранит древние традиции Ордена и содействует распространению масонского света на территории России и СНГ.","image_url":"/media/home/home-welcome.webp","href":null}',
        1
    ),
    (
        'home_2',
        'Новости ложи',
        '{"eyebrow":"События","text":"Официальные сообщения появятся здесь после публикации через административную панель.","image_url":"/media/home/home-events.webp","href":"/novosti"}',
        1
    ),
    (
        'home_3',
        'Публикации и медиа',
        '{"eyebrow":"Материалы","text":"Разделы сайта подготовлены для утвержденных материалов, фотографий и видеопубликаций.","image_url":"/media/home/home-media.webp","href":"/materialy"}',
        1
    );

INSERT IGNORE INTO hosting_schema_migrations (version) VALUES ('003_homepage_blocks');
