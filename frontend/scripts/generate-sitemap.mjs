import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const DIST_DIR = resolve(process.cwd(), 'dist');
const ROBOTS_PATH = resolve(DIST_DIR, 'robots.txt');
const SITEMAP_PATH = resolve(DIST_DIR, 'sitemap.xml');

const STATIC_INDEXABLE_PATHS = [
  '/',
  '/novosti',
  '/video',
  '/vstuplenie',
  '/privacy',
  '/consent',
];

function configuredPublicOrigin(rawValue) {
  const raw = rawValue?.trim();
  if (!raw) return null;

  try {
    const url = new URL(raw);
    const hostname = url.hostname.toLowerCase();
    const localHost =
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '::1' ||
      hostname.endsWith('.local');
    const bareOrigin =
      url.pathname === '/' &&
      !url.search &&
      !url.hash &&
      !url.username &&
      !url.password;

    if (url.protocol !== 'https:' || localHost || !bareOrigin) return null;
    return url.origin;
  } catch {
    return null;
  }
}

function xmlEscape(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

function sitemapXml(origin) {
  const urls = STATIC_INDEXABLE_PATHS.map((pathname) => {
    const location = new URL(pathname, `${origin}/`).toString();
    return `  <url><loc>${xmlEscape(location)}</loc></url>`;
  }).join('\n');

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    urls,
    '</urlset>',
    '',
  ].join('\n');
}

async function rewriteRobots(origin) {
  let robots = await readFile(ROBOTS_PATH, 'utf8');
  robots = robots
    .split(/\r?\n/)
    .filter((line) => !/^Sitemap:/i.test(line.trim()))
    .join('\n')
    .replace(/\n*$/, '\n');

  if (origin) {
    robots += `Sitemap: ${origin}/sitemap.xml\n`;
  }

  await writeFile(ROBOTS_PATH, robots, 'utf8');
}

const origin = configuredPublicOrigin(process.env.VITE_PUBLIC_SITE_ORIGIN);

await mkdir(DIST_DIR, { recursive: true });

if (!origin) {
  await rm(SITEMAP_PATH, { force: true });
  await rewriteRobots(null);
  console.log('Sitemap skipped: VITE_PUBLIC_SITE_ORIGIN is unset or not a valid public HTTPS origin.');
  process.exit(0);
}

await writeFile(SITEMAP_PATH, sitemapXml(origin), 'utf8');
await rewriteRobots(origin);
console.log(`Sitemap generated for ${origin}.`);
