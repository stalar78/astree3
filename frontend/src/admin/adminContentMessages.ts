import { AdminApiError } from './adminApi';
import { SESSION_SECURITY_MESSAGE, formatAdminError } from './adminMessages';

export type ContentEntity = 'news' | 'video' | 'page';
export type ContentAction = 'list' | 'detail' | 'create' | 'update' | 'delete';

const CONTENT_NOT_FOUND: Record<ContentEntity, string> = {
  news: 'Материал не найден.',
  video: 'Материал не найден.',
  page: 'Страница не найдена.',
};

const CONTENT_TITLES: Record<ContentEntity, string> = {
  news: 'Новости',
  video: 'Видео',
  page: 'Страницы',
};

const CONTENT_NEW_TITLES: Record<ContentEntity, string> = {
  news: 'Новая новость',
  video: 'Новое видео',
  page: 'Редактирование страницы',
};

const CONTENT_EDIT_TITLES: Record<ContentEntity, string> = {
  news: 'Редактирование новости',
  video: 'Редактирование видео',
  page: 'Редактирование страницы',
};

export function getContentListTitle(entity: ContentEntity) {
  return CONTENT_TITLES[entity];
}

export function getContentNewTitle(entity: ContentEntity) {
  return CONTENT_NEW_TITLES[entity];
}

export function getContentEditTitle(entity: ContentEntity) {
  return CONTENT_EDIT_TITLES[entity];
}

export function getContentNotFoundMessage(entity: ContentEntity) {
  return CONTENT_NOT_FOUND[entity];
}

export function formatContentLoadError(error: unknown, action: 'list' | 'detail') {
  return formatAdminError(error, action === 'list' ? 'contentList' : 'contentDetail');
}

export function formatContentMutationError(
  error: unknown,
  entity: ContentEntity,
  action: Exclude<ContentAction, 'list' | 'detail'>,
) {
  if (error instanceof AdminApiError) {
    if (error.status === 401) {
      return formatAdminError(error, action === 'create' ? 'contentCreate' : action === 'delete' ? 'contentDelete' : 'contentUpdate');
    }
    if (error.status === 403) {
      return SESSION_SECURITY_MESSAGE;
    }
    if (error.status === 422) {
      return 'Проверьте заполнение формы.';
    }
    if (error.status === 409 && entity === 'news') {
      return 'Новость с таким slug уже существует.';
    }
    if (error.status === 503) {
      return 'Раздел временно недоступен.';
    }
  }
  return entity === 'news' && action !== 'delete' ? 'Раздел временно недоступен.' : 'Раздел временно недоступен.';
}
