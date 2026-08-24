import { PublicManagedPageFrame, PublicPageBody } from '../publicContent/PublicManagedPage';

export function LodgesPage() {
  return (
    <>
      <PublicManagedPageFrame
        eyebrow="Справочный раздел"
        fallbackTitle="Ложи Санкт-Петербурга"
        pageKey="lodges_spb"
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
