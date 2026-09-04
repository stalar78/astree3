import { spawnSync } from 'node:child_process';
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { dirname, extname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const hostingDir = dirname(scriptDir);
const repoRoot = dirname(hostingDir);
const frontendDir = join(repoRoot, 'frontend');
const frontendDist = join(frontendDir, 'dist');
const releaseRoot = join(hostingDir, 'release', 'astrea-hosting');
const publicRoot = join(releaseRoot, 'public');
const privateRoot = join(releaseRoot, 'private');
const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';

const originArg = process.argv.find((argument) => argument.startsWith('--origin='));
const originInput = originArg?.slice('--origin='.length) || process.env.ASTREA_HOSTING_SITE_ORIGIN || '';
const skipBuild = process.argv.includes('--skip-build');
const publicIndexingEnabled = !process.argv.includes('--noindex');
const siteOrigin = validateOrigin(originInput);

if (!skipBuild) {
  console.log(`Building Astrea HOSTING frontend for ${siteOrigin}.`);
  if (!publicIndexingEnabled) {
    console.log('Transitional noindex mode enabled.');
  }
  const build = spawnSync(npmCommand, ['run', 'build:hosting'], {
    cwd: frontendDir,
    env: {
      ...process.env,
      VITE_PUBLIC_SITE_ORIGIN: siteOrigin,
      VITE_PUBLIC_INDEXING_ENABLED: publicIndexingEnabled ? 'true' : 'false',
    },
    stdio: 'inherit',
  });
  if (build.error) throw build.error;
  if (build.status !== 0) process.exit(build.status ?? 1);
}

if (!existsSync(join(frontendDist, 'index.html'))) {
  console.error('frontend/dist is missing. Run without --skip-build or build the HOSTING frontend first.');
  process.exit(2);
}

rmSync(releaseRoot, { recursive: true, force: true });
mkdirSync(publicRoot, { recursive: true });
mkdirSync(privateRoot, { recursive: true });

cpSync(frontendDist, publicRoot, { recursive: true });
cpSync(join(hostingDir, 'api'), join(publicRoot, 'api'), { recursive: true });
cpSync(join(hostingDir, 'editor'), join(publicRoot, 'editor'), { recursive: true });
cpSync(join(hostingDir, 'public', '.htaccess'), join(publicRoot, '.htaccess'));

mkdirSync(join(privateRoot, 'config'), { recursive: true });
cpSync(
  join(hostingDir, 'config', 'config.example.php'),
  join(privateRoot, 'config', 'config.local.php.example'),
);
cpSync(join(hostingDir, 'db'), join(privateRoot, 'db'), { recursive: true });
mkdirSync(join(privateRoot, 'scripts'), { recursive: true });
for (const filename of ['bootstrap-editor.php', 'preflight.php']) {
  cpSync(join(hostingDir, 'scripts', filename), join(privateRoot, 'scripts', filename));
}

const deploymentGuide = join(hostingDir, 'DEPLOY_TIMEWEB.md');
if (existsSync(deploymentGuide)) {
  cpSync(deploymentGuide, join(releaseRoot, 'DEPLOY_TIMEWEB.md'));
}

const manifest = {
  edition: 'hosting',
  site_origin: siteOrigin,
  public_indexing: publicIndexingEnabled,
  document_root: 'public',
  private_root: 'private',
  candidate_intake: false,
  schema: ['001_initial', '002_editor_auth'],
};
writeFileSync(join(releaseRoot, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');

validatePackage();

console.log('HOSTING package verified.');
console.log(`Package root: ${releaseRoot}`);
console.log('Deploy only the public directory as the web document root; keep private outside public_html.');

function validateOrigin(value) {
  if (!value) {
    console.error('Usage: node hosting/scripts/build-package.mjs --origin=https://example.com [--noindex]');
    console.error('Alternatively set ASTREA_HOSTING_SITE_ORIGIN.');
    process.exit(2);
  }

  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    console.error('HOSTING site origin must be a valid HTTPS origin.');
    process.exit(2);
  }

  if (
    parsed.protocol !== 'https:' ||
    parsed.username !== '' ||
    parsed.password !== '' ||
    parsed.pathname !== '/' ||
    parsed.search !== '' ||
    parsed.hash !== ''
  ) {
    console.error('HOSTING site origin must be a bare HTTPS origin such as https://example.com.');
    process.exit(2);
  }

  return parsed.origin;
}

function validatePackage() {
  const requiredPublicFiles = [
    'index.html',
    '.htaccess',
    'robots.txt',
    'api/index.php',
    'api/bootstrap.php',
    'editor/index.php',
    'editor/auth.php',
    'editor/content.php',
  ];
  if (publicIndexingEnabled) {
    requiredPublicFiles.push('sitemap.xml');
  }
  for (const path of requiredPublicFiles) {
    if (!existsSync(join(publicRoot, path))) {
      throw new Error(`HOSTING package missing public/${path}`);
    }
  }

  const requiredPrivateFiles = [
    'config/config.local.php.example',
    'db/001_initial.sql',
    'db/002_editor_auth.sql',
    'scripts/bootstrap-editor.php',
    'scripts/preflight.php',
  ];
  for (const path of requiredPrivateFiles) {
    if (!existsSync(join(privateRoot, path))) {
      throw new Error(`HOSTING package missing private/${path}`);
    }
  }

  if (existsSync(join(privateRoot, 'config', 'config.local.php'))) {
    throw new Error('Real HOSTING credentials must never be copied into the package.');
  }

  const forbiddenPublicExtensions = new Set(['.sql', '.env', '.bak']);
  const forbiddenPublicNames = new Set(['config.local.php', '.env']);
  for (const file of walkFiles(publicRoot)) {
    const relativePath = relative(publicRoot, file).replaceAll('\\', '/');
    const filename = relativePath.split('/').at(-1) ?? '';
    if (forbiddenPublicNames.has(filename) || forbiddenPublicExtensions.has(extname(filename).toLowerCase())) {
      throw new Error(`Private/operator artifact leaked into public package: ${relativePath}`);
    }
  }

  const runtimeFiles = walkFiles(join(publicRoot, 'api')).concat(walkFiles(join(publicRoot, 'editor')));
  for (const file of runtimeFiles) {
    const contents = readFileSync(file, 'utf8');
    if (contents.includes('candidate-applications') || contents.includes('candidate_applications')) {
      throw new Error(`Candidate runtime unexpectedly present in HOSTING package: ${relative(publicRoot, file)}`);
    }
  }

  const robots = readFileSync(join(publicRoot, 'robots.txt'), 'utf8');
  const sitemapPath = join(publicRoot, 'sitemap.xml');

  if (!publicIndexingEnabled) {
    if (existsSync(sitemapPath)) {
      throw new Error('Transitional noindex package must not contain sitemap.xml.');
    }
    if (!/^Disallow:\s*\/$/m.test(robots)) {
      throw new Error('Transitional noindex package must block crawling in robots.txt.');
    }
    if (/^Sitemap:/im.test(robots)) {
      throw new Error('Transitional noindex package must not advertise a sitemap.');
    }
    return;
  }

  const sitemap = readFileSync(sitemapPath, 'utf8');
  if (!sitemap.includes(`<loc>${siteOrigin}/</loc>`)) {
    throw new Error('Generated sitemap does not contain the configured HOSTING site origin.');
  }
  if (sitemap.includes('/admin') || sitemap.includes('/api/')) {
    throw new Error('Generated sitemap exposes a private/runtime route.');
  }
}

function walkFiles(root) {
  const output = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) output.push(...walkFiles(path));
    else if (entry.isFile()) output.push(path);
  }
  return output;
}
