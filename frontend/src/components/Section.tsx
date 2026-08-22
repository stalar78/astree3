import type { ReactNode } from 'react';

type SectionProps = {
  children: ReactNode;
  tone?: 'paper' | 'alternate' | 'dark';
  className?: string;
};

export function Section({ children, tone = 'paper', className = '' }: SectionProps) {
  const toneClass = {
    paper: 'bg-brand-paper text-brand-ink',
    alternate: 'bg-brand-paperAlt text-brand-ink',
    dark: 'bg-brand-black text-white',
  }[tone];

  return (
    <section className={`${toneClass} ${className}`}>
      <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-24">{children}</div>
    </section>
  );
}
