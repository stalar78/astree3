import { Heraldry } from '../components/Heraldry';
import { MonumentHeading } from '../components/MonumentHeading';
import { Section } from '../components/Section';
import { PublicManagedPageFrame, PublicPageBody } from '../publicContent/PublicManagedPage';

export function AboutPage() {
  return (
    <>
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
      >
        {(page) => <PublicPageBody page={page} />}
      </PublicManagedPageFrame>
      <Section tone="dark">
        <div className="mx-auto max-w-3xl">
          <MonumentHeading title="Официальная символика" lead="На сайте используются только предоставленные клиентом официальные изображения." />
          <div className="mt-10">
            <Heraldry />
          </div>
        </div>
      </Section>
    </>
  );
}
