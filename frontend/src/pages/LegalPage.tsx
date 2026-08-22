import { LegalTemplate } from '../components/LegalTemplate';

export function LegalPage({ kind }: { kind: 'privacy' | 'consent' }) {
  if (kind === 'privacy') {
    return (
      <LegalTemplate
        title="Политика конфиденциальности"
        lead="Правовая страница для будущего утвержденного документа."
        sections={['Общие положения', 'Категории данных', 'Цели обработки', 'Права субъекта данных']}
      />
    );
  }

  return (
    <LegalTemplate
      title="Согласие на обработку данных"
      lead="Страница для будущего утвержденного текста согласия."
      sections={['Предмет согласия', 'Состав данных', 'Срок действия', 'Порядок отзыва']}
    />
  );
}
