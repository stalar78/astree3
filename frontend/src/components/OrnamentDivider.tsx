type OrnamentDividerProps = {
  tone?: 'paper' | 'dark';
};

export function OrnamentDivider({ tone = 'paper' }: OrnamentDividerProps) {
  const color = tone === 'dark' ? 'border-white/20 text-brand-gray6' : 'border-brand-gray10/30 text-brand-gray10';
  return (
    <div className={`flex items-center gap-4 ${color}`} aria-hidden="true">
      <span className="h-px flex-1 border-t" />
      <span className="font-display text-xl">A</span>
      <span className="h-px flex-1 border-t" />
    </div>
  );
}
