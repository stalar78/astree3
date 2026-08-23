import type { ReactNode } from 'react';

type EditorialNoteProps = {
  title?: string;
  children: ReactNode;
};

export function EditorialNote({ title = 'Редакционное состояние', children }: EditorialNoteProps) {
  return (
    <div className="border-l-4 border-brand-red bg-white/55 px-6 py-5 text-brand-ink shadow-sm">
      <p className="font-display text-2xl">{title}</p>
      <p className="mt-3 max-w-3xl text-base leading-7 text-brand-ink/75">{children}</p>
    </div>
  );
}
