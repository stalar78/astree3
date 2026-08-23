import { LegalTemplate } from '../components/LegalTemplate';
import { legalDocuments } from '../legal/legalDocuments';

export function LegalPage({ kind }: { kind: 'privacy' | 'consent' }) {
  return <LegalTemplate document={legalDocuments[kind]} />;
}
