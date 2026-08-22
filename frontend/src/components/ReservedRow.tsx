type ReservedRowProps = {
  label: string;
  title?: string;
};

export function ReservedRow({ label, title = 'редакционная подготовка' }: ReservedRowProps) {
  return (
    <div className="grid gap-4 border-t border-brand-gray10/30 py-8 md:grid-cols-[180px_1fr]">
      <p className="text-sm font-semibold uppercase text-brand-gray10">{label}</p>
      <p className="font-display text-3xl text-brand-ink">{title}</p>
    </div>
  );
}
