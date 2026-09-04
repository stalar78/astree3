export type AstreaEdition = 'full' | 'hosting';

const configuredEdition = import.meta.env.VITE_ASTREA_EDITION ?? 'full';

if (configuredEdition !== 'full' && configuredEdition !== 'hosting') {
  throw new Error('Invalid VITE_ASTREA_EDITION. Expected "full" or "hosting".');
}

export const astreaEdition: AstreaEdition = configuredEdition;
export const isHostingEdition = astreaEdition === 'hosting';
export const isFullEdition = astreaEdition === 'full';
