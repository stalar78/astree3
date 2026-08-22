import type { RouteObject } from 'react-router-dom';
import { PageShell } from './components/PageShell';
import { HomePage } from './pages/HomePage';
import { AboutPage } from './pages/AboutPage';
import { LodgesPage } from './pages/LodgesPage';
import { PrinciplesPage } from './pages/PrinciplesPage';
import { FaqPage } from './pages/FaqPage';
import { LegalPage } from './pages/LegalPage';
import { CandidatePage } from './pages/CandidatePage';
import { NewsPage } from './pages/NewsPage';
import { NewsArticlePage } from './pages/NewsArticlePage';
import { VideoPage } from './pages/VideoPage';
import { ContactsPage } from './pages/ContactsPage';
import { AdminLoginPage } from './pages/admin/AdminLoginPage';
import { AdminCandidatesPage } from './pages/admin/AdminCandidatesPage';
import { AdminCandidateDetailPage } from './pages/admin/AdminCandidateDetailPage';
import { AdminProtectedLayout } from './admin/AdminShell';
import { Navigate } from 'react-router-dom';

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
        element: <AboutPage />,
        handle: { title: 'О ложе | Astrea', description: 'Информационная страница о Д.Л. «Астрея» № 3.' } satisfies SeoMeta,
      },
      {
        path: '/lozhi-sankt-peterburga',
        element: <LodgesPage />,
        handle: { title: 'Ложи Санкт-Петербурга | Astrea', description: 'Редакционный раздел о петербургском контексте.' } satisfies SeoMeta,
      },
      {
        path: '/celi-i-principy',
        element: <PrinciplesPage />,
        handle: { title: 'Цели и принципы | Astrea', description: 'Раздел для утвержденного текста о целях и принципах.' } satisfies SeoMeta,
      },
      {
        path: '/vstuplenie',
        element: <CandidatePage />,
        handle: { title: 'Вступление | Astrea', description: 'Статичная форма обращения кандидата без отправки данных.' } satisfies SeoMeta,
      },
      {
        path: '/faq',
        element: <FaqPage />,
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
        element: <LegalPage kind="privacy" />,
        handle: { title: 'Политика конфиденциальности | Astrea', description: 'Правовая страница, ожидающая утвержденного текста.' } satisfies SeoMeta,
      },
      {
        path: '/consent',
        element: <LegalPage kind="consent" />,
        handle: { title: 'Согласие на обработку данных | Astrea', description: 'Страница согласия, ожидающая утвержденного текста.' } satisfies SeoMeta,
      },
    ],
  },
  {
    path: '/admin/login',
    element: <AdminLoginPage />,
  },
  {
    path: '/admin',
    element: <AdminProtectedLayout />,
    children: [
      { index: true, element: <Navigate to="candidates" replace /> },
      { path: 'candidates', element: <AdminCandidatesPage /> },
      { path: 'candidates/:candidateId', element: <AdminCandidateDetailPage /> },
    ],
  },
];
