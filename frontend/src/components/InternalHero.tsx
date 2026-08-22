import { MonumentHeading } from './MonumentHeading';
import { OrnamentDivider } from './OrnamentDivider';

type InternalHeroProps = {
  eyebrow?: string;
  title: string;
  lead?: string;
};

export function InternalHero({ eyebrow, title, lead }: InternalHeroProps) {
  return (
    <section className="bg-brand-black text-white">
      <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-20">
        <MonumentHeading as="h1" eyebrow={eyebrow} title={title} lead={lead} />
        <div className="mt-12">
          <OrnamentDivider tone="dark" />
        </div>
      </div>
    </section>
  );
}
