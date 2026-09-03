import type { ReactNode } from 'react';

import { ReferenceLayout } from './ReferenceLayout';

type ReferenceInnerPageProps = {
  eyebrow?: string;
  title: string;
  lead?: string;
  children: ReactNode;
};

export function ReferenceInnerPage({ eyebrow, title, lead, children }: ReferenceInnerPageProps) {
  return (
    <ReferenceLayout>
      <div className="space-y-6 sm:space-y-8">
        <header className="rounded-[6px] border border-brand-reference-line/35 bg-brand-reference-panel px-5 py-6 shadow-referenceCard sm:px-6 sm:py-7 lg:px-8 lg:py-9">
          {eyebrow ? (
            <p className="text-xs uppercase tracking-[0.14em] text-brand-reference-muted/55">{eyebrow}</p>
          ) : null}
          <h1 className="mt-2 break-words font-referenceHeading text-[clamp(1.85rem,8vw,3.45rem)] font-normal leading-[1.04] text-brand-reference-text sm:text-[clamp(2rem,5.8vw,3.45rem)] lg:text-[clamp(2rem,3.2vw,3.45rem)]">
            {title}
          </h1>
          {lead ? (
            <>
              <div className="my-5 h-px bg-brand-reference-line/70" />
              <p className="max-w-4xl text-[15px] font-light leading-7 text-brand-reference-muted">{lead}</p>
            </>
          ) : null}
        </header>
        {children}
      </div>
    </ReferenceLayout>
  );
}

type ReferencePanelProps = {
  children: ReactNode;
  className?: string;
};

export function ReferencePanel({ children, className = '' }: ReferencePanelProps) {
  return (
    <section
      className={`rounded-[6px] border border-brand-reference-line/30 bg-brand-reference-panel px-5 py-6 shadow-referenceCard sm:px-6 sm:py-7 lg:px-8 lg:py-8 ${className}`}
    >
      {children}
    </section>
  );
}

type ReferenceNoticeProps = {
  title: string;
  children: ReactNode;
  action?: ReactNode;
};

export function ReferenceNotice({ title, children, action }: ReferenceNoticeProps) {
  return (
    <ReferencePanel>
      <div className="border-l-2 border-brand-reference-red pl-4 sm:pl-5">
        <h2 className="break-words font-referenceHeading text-[clamp(1.35rem,6vw,1.5rem)] font-normal text-brand-reference-text">{title}</h2>
        <div className="mt-3 max-w-3xl text-[15px] font-light leading-7 text-brand-reference-muted">{children}</div>
        {action ? <div className="mt-6">{action}</div> : null}
      </div>
    </ReferencePanel>
  );
}
