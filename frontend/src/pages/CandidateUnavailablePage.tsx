import { ReferenceInnerPage, ReferenceNotice } from '../components/ReferenceInnerPage';

const INACTIVE_COPY = 'Приём заявок через сайт временно недоступен.';

export function CandidateUnavailablePage() {
  return (
    <ReferenceInnerPage eyebrow="Кандидату" title="Вступление" lead={INACTIVE_COPY}>
      <div className="mx-auto w-full max-w-5xl">
        <ReferenceNotice title="Приём заявок">{INACTIVE_COPY}</ReferenceNotice>
      </div>
    </ReferenceInnerPage>
  );
}
