import type { RouteObject } from 'react-router-dom';

import { AdminProtectedLayout } from './admin/AdminShell';
import { CandidatePage } from './pages/CandidatePage';
import { ContactsPage } from './pages/ContactsPage';
import { FaqPage } from './pages/FaqPage';
import { HomePage } from './pages/HomePage';
import { LegalPage } from './pages/LegalPage';
import { LodgesPage } from './pages/LodgesPage';
import { NewsArticlePage } from './pages/NewsArticlePage';
import { NewsPage } from './pages/NewsPage';
import { PageShell } from './components/PageShell';
import { PrinciplesPage } from './pages/PrinciplesPage';
import { VideoPage } from './pages/VideoPage';
import { AboutPage } from './pages/AboutPage';
import { AdminCandidatesPage } from './pages/admin/AdminCandidatesPage';
import { AdminCandidateDetailPage } from './pages/admin/AdminCandidateDetailPage';
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { AdminLoginPage } from './pages/admin/AdminLoginPage';
import { AdminNewsEditorPage, AdminPageEditorPage, AdminVideoEditorPage } from './pages/admin/AdminContentEditorPage';
import { AdminNewsPage, AdminVideosPage } from './pages/admin/AdminNewsPage';
import { AdminPagesPage } from './pages/admin/AdminPagesPage';

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
        handle: { title: 'Вступление | Astrea', description: 'Анкета кандидата для обращения в ДЛ «Астрея» №3 в Санкт-Петербурге.' } satisfies SeoMeta,
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
        handle: {
          title: 'Политика в отношении обработки персональных данных | Astrea',
          description: 'Политика в отношении обработки персональных данных сайта ДЛ «Астрея» №3.',
        } satisfies SeoMeta,
      },
      {
        path: '/consent',
        element: <LegalPage kind="consent" />,
        handle: {
          title: 'Согласие на обработку персональных данных | Astrea',
          description: 'Согласие на обработку персональных данных для анкеты кандидата ДЛ «Астрея» №3.',
        } satisfies SeoMeta,
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
      { index: true, element: <AdminDashboardPage /> },
      { path: 'candidates', element: <AdminCandidatesPage /> },
      { path: 'candidates/:candidateId', element: <AdminCandidateDetailPage /> },
      { path: 'news', element: <AdminNewsPage /> },
      { path: 'news/new', element: <AdminNewsEditorPage create /> },
      { path: 'news/:newsId', element: <AdminNewsEditorPage /> },
      { path: 'videos', element: <AdminVideosPage /> },
      { path: 'videos/new', element: <AdminVideoEditorPage create /> },
      { path: 'videos/:videoId', element: <AdminVideoEditorPage /> },
      { path: 'pages', element: <AdminPagesPage /> },
      { path: 'pages/:pageKey', element: <AdminPageEditorPage /> },
    ],
  },
];
