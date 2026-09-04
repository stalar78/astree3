import { Heraldry } from '../components/Heraldry';
import { ReferencePanel } from '../components/ReferenceInnerPage';
import { PublicManagedPageFrame, PublicPageBody } from '../publicContent/PublicManagedPage';

export function AboutPage() {
  return (
    <PublicManagedPageFrame
      eyebrow="Astrea"
      fallbackTitle="О ложе"
      pageKey="about"
      loadingTitle="Загрузка материала"
      loadingMessage="Материал страницы загружается."
      notFoundTitle="Материал пока не опубликован"
      notFoundMessage="Материал пока не опубликован."
      errorTitle="Не удалось загрузить материал"
      errorMessage="Не удалось загрузить материал. Повторить позже."
      retryLabel="Повторить"
      bodyWidthClassName="max-w-3xl"
      afterContent={
        <ReferencePanel className="mx-auto w-full max-w-3xl">
          <h2 className="font-referenceHeading text-3xl font-medium text-brand-reference-text">Официальная символика</h2>
          <div className="my-5 h-px bg-brand-reference-line/70" />
          <p className="text-[15px] font-light leading-7 text-brand-reference-muted">
            На сайте используются только предоставленные клиентом официальные изображения.
          </p>
          <div className="mt-7">
            <Heraldry />
          </div>
        </ReferencePanel>
      }
    >
      {(page) => <PublicPageBody page={page} />}
    </PublicManagedPageFrame>
  );
}
