import type { RouteObject } from 'react-router-dom';
import { PageShell } from './components/PageShell';
import { HomePage } from './pages/HomePage';
import { EditorialPage } from './pages/EditorialPage';
import { CandidatePage } from './pages/CandidatePage';
import { NewsPage } from './pages/NewsPage';
import { NewsArticlePage } from './pages/NewsArticlePage';
import { VideoPage } from './pages/VideoPage';
import { ContactsPage } from './pages/ContactsPage';

export type SeoMeta = {
  title: string;
  description: string;
};

const commonDescription = 'Официальный сайт Достопочтенной Ложи «Астрея» № 3 на Востоке Санкт-Петербурга.';

export const routes: RouteObject[] = [
  {
    element: <PageShell />,
    children: [
      { path: '/', element: <HomePage />, handle: { title: 'Astrea', description: commonDescription } satisfies SeoMeta },
      {
        path: '/o-lozhe',
        element: <EditorialPage kind="about" />,
        handle: { title: 'О ложе | Astrea', description: 'Информационная страница о Д.Л. «Астрея» № 3.' } satisfies SeoMeta,
      },
      {
        path: '/lozhi-sankt-peterburga',
        element: <EditorialPage kind="lodges" />,
        handle: { title: 'Ложи Санкт-Петербурга | Astrea', description: 'Редакционный раздел о петербургском контексте.' } satisfies SeoMeta,
      },
      {
        path: '/celi-i-principy',
        element: <EditorialPage kind="principles" />,
        handle: { title: 'Цели и принципы | Astrea', description: 'Раздел для утвержденного текста о целях и принципах.' } satisfies SeoMeta,
      },
      {
        path: '/vstuplenie',
        element: <CandidatePage />,
        handle: { title: 'Вступление | Astrea', description: 'Статичная форма обращения кандидата без отправки данных.' } satisfies SeoMeta,
      },
      {
        path: '/faq',
        element: <EditorialPage kind="faq" />,
        handle: { title: 'FAQ | Astrea', description: 'Раздел ответов на вопросы, ожидающий утвержденного содержания.' } satisfies SeoMeta,
      },
      {
        path: '/novosti',
        element: <NewsPage />,
        handle: { title: 'Новости | Astrea', description: 'Архив новостей Д.Л. «Астрея» № 3.' } satisfies SeoMeta,
      },
      {
        path: '/novosti/:slug',
        element: <NewsArticlePage />,
        handle: { title: 'Материал не опубликован | Astrea', description: 'Материал пока не опубликован.' } satisfies SeoMeta,
      },
      {
        path: '/video',
        element: <VideoPage />,
        handle: { title: 'Видео | Astrea', description: 'Раздел внешних видеоматериалов, ожидающий утвержденных ссылок.' } satisfies SeoMeta,
      },
      {
        path: '/kontakty',
        element: <ContactsPage />,
        handle: { title: 'Контакты | Astrea', description: 'Контактный раздел, ожидающий утвержденной информации.' } satisfies SeoMeta,
      },
      {
        path: '/privacy',
        element: <EditorialPage kind="privacy" />,
        handle: { title: 'Политика конфиденциальности | Astrea', description: 'Правовая страница, ожидающая утвержденного текста.' } satisfies SeoMeta,
      },
      {
        path: '/consent',
        element: <EditorialPage kind="consent" />,
        handle: { title: 'Согласие на обработку данных | Astrea', description: 'Страница согласия, ожидающая утвержденного текста.' } satisfies SeoMeta,
      },
    ],
  },
];
