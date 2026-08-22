type MonumentHeadingProps = {
  eyebrow?: string;
  title: string;
  lead?: string;
  as?: 'h1' | 'h2';
};

export function MonumentHeading({ eyebrow, title, lead, as = 'h2' }: MonumentHeadingProps) {
  const Heading = as;

  return (
    <div className="max-w-3xl">
      {eyebrow ? <p className="mb-4 text-xs font-semibold uppercase text-brand-red">{eyebrow}</p> : null}
      <Heading className="font-display text-4xl leading-tight text-current md:text-5xl lg:text-6xl">{title}</Heading>
      {lead ? <p className="mt-6 max-w-2xl text-lg leading-8 text-current/75">{lead}</p> : null}
    </div>
  );
}
