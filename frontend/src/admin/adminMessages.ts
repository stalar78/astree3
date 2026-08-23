import { AdminApiError } from './adminApi';

type AdminErrorScope =
  | 'session'
  | 'login'
  | 'list'
  | 'detail'
  | 'photo'
  | 'update'
  | 'logout'
  | 'contentList'
  | 'contentDetail'
  | 'contentCreate'
  | 'contentUpdate'
  | 'contentDelete';

export const SESSION_SECURITY_MESSAGE = 'Не удалось подтвердить безопасность сессии. Обновите страницу и повторите действие.';

const genericAuth = {
  401: 'Сессия администратора недействительна.',
  403: 'Сессия администратора недействительна.',
  503: 'Сервис авторизации временно недоступен.',
};

const contentRead = {
  ...genericAuth,
  404: 'Материал не найден.',
  422: 'Проверьте заполнение формы.',
  503: 'Раздел временно недоступен.',
};

const contentWrite = {
  401: 'Сессия администратора недействительна.',
  403: SESSION_SECURITY_MESSAGE,
  404: 'Материал не найден.',
  409: 'Новость с таким slug уже существует.',
  422: 'Проверьте заполнение формы.',
  503: 'Раздел временно недоступен.',
};

const contentDelete = {
  401: 'Сессия администратора недействительна.',
  403: SESSION_SECURITY_MESSAGE,
  404: 'Материал не найден.',
  503: 'Раздел временно недоступен.',
};

const SCOPE_MESSAGES: Record<AdminErrorScope, Record<number, string>> = {
  session: genericAuth,
  login: {
    401: 'Неверные учетные данные.',
    429: 'Слишком много попыток входа. Попробуйте позже.',
    503: 'Сервис авторизации временно недоступен.',
  },
  list: {
    ...genericAuth,
    404: 'Заявки не найдены.',
    422: 'Запрос не прошел проверку.',
    503: 'Список заявок временно недоступен.',
  },
  detail: {
    ...genericAuth,
    404: 'Кандидат не найден.',
    422: 'Запрос не прошел проверку.',
    503: 'Карточка кандидата временно недоступна.',
  },
  photo: {
    ...genericAuth,
    404: 'Фотография не найдена.',
    422: 'Запрос не прошел проверку.',
    503: 'Фотография временно недоступна.',
  },
  update: {
    ...genericAuth,
    403: SESSION_SECURITY_MESSAGE,
    404: 'Кандидат не найден.',
    422: 'Запрос не прошел проверку.',
    503: 'Сохранение временно недоступно.',
  },
  logout: {
    ...genericAuth,
    403: SESSION_SECURITY_MESSAGE,
    503: 'Сервис авторизации временно недоступен.',
  },
  contentList: contentRead,
  contentDetail: contentRead,
  contentCreate: contentWrite,
  contentUpdate: contentWrite,
  contentDelete,
};

const DEFAULT_MESSAGES: Record<AdminErrorScope, string> = {
  session: 'Сессия администратора недоступна.',
  login: 'Вход временно недоступен.',
  list: 'Список заявок временно недоступен.',
  detail: 'Карточка кандидата временно недоступна.',
  photo: 'Фотография временно недоступна.',
  update: 'Сохранение временно недоступно.',
  logout: 'Выход временно недоступен.',
  contentList: 'Раздел временно недоступен.',
  contentDetail: 'Материал временно недоступен.',
  contentCreate: 'Создание временно недоступно.',
  contentUpdate: 'Сохранение временно недоступно.',
  contentDelete: 'Удаление временно недоступно.',
};

export function formatAdminError(error: unknown, scope: AdminErrorScope): string {
  if (error instanceof AdminApiError) {
    return SCOPE_MESSAGES[scope][error.status] ?? DEFAULT_MESSAGES[scope];
  }
  return DEFAULT_MESSAGES[scope];
}
