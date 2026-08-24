import { PublicManagedPageFrame, PublicPageBody } from '../publicContent/PublicManagedPage';

export function ContactsPage() {
  return (
    <>
      <PublicManagedPageFrame
        eyebrow="Связь"
        fallbackTitle="Контакты"
        pageKey="contacts"
        loadingTitle="Загрузка материала"
        loadingMessage="Материал страницы загружается."
        notFoundTitle="Материал пока не опубликован"
        notFoundMessage="Материал пока не опубликован."
        errorTitle="Не удалось загрузить материал"
        errorMessage="Не удалось загрузить материал. Повторить позже."
        retryLabel="Повторить"
        bodyWidthClassName="max-w-3xl"
      >
        {(page) => <PublicPageBody page={page} />}
      </PublicManagedPageFrame>
    </>
  );
}
