import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

type ActionProps = {
  children: ReactNode;
  to: string;
  variant?: 'primary' | 'secondary';
  onClick?: () => void;
};

export function Action({ children, to, variant = 'primary', onClick }: ActionProps) {
  const className =
    variant === 'primary'
      ? 'inline-flex items-center justify-center border border-brand-red bg-brand-red px-6 py-3 text-sm font-semibold uppercase text-white transition hover:bg-transparent focus:outline focus:outline-2 focus:outline-offset-4 focus:outline-brand-red'
      : 'inline-flex items-center justify-center border border-current/30 px-6 py-3 text-sm font-semibold uppercase transition hover:border-brand-red focus:outline focus:outline-2 focus:outline-offset-4 focus:outline-brand-red';

  return (
    <Link to={to} onClick={onClick} className={className}>
      {children}
    </Link>
  );
}
