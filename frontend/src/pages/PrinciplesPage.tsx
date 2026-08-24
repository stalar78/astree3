import { PublicManagedPageFrame, PublicPageBody } from '../publicContent/PublicManagedPage';

export function PrinciplesPage() {
  return (
    <>
      <PublicManagedPageFrame
        eyebrow="Материалы"
        fallbackTitle="Цели и принципы"
        pageKey="principles"
        loadingTitle="Загрузка материала"
        loadingMessage="Материал страницы загружается."
        notFoundTitle="Материал пока не опубликован"
        notFoundMessage="Материал пока не опубликован."
        errorTitle="Не удалось загрузить материал"
        errorMessage="Не удалось загрузить материал. Повторить позже."
        retryLabel="Повторить"
        bodyWidthClassName="max-w-4xl"
      >
        {(page) => <PublicPageBody page={page} />}
      </PublicManagedPageFrame>
    </>
  );
}
