import fs from 'node:fs';
import path from 'node:path';

const DATA_DIR = path.resolve(process.cwd(), 'data');
const ADS_DIR = path.join(DATA_DIR, 'public', 'ads');
const UPLOADS_DIR = path.join(DATA_DIR, 'uploads');
const PROMPTS_FILE = path.join(DATA_DIR, 'prompts.jsonl');
const POSTS_FILE = path.join(DATA_DIR, 'posts.jsonl');
const SECRETS_FILE = path.join(DATA_DIR, 'secrets.json');
const PREFS_FILE = path.join(DATA_DIR, 'prefs.json');

export function ensureDataDirs(): void {
  fs.mkdirSync(ADS_DIR, { recursive: true });
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
  if (!fs.existsSync(PROMPTS_FILE)) fs.writeFileSync(PROMPTS_FILE, '');
  if (!fs.existsSync(POSTS_FILE)) fs.writeFileSync(POSTS_FILE, '');
  if (!fs.existsSync(SECRETS_FILE)) fs.writeFileSync(SECRETS_FILE, '{}');
  if (!fs.existsSync(PREFS_FILE)) fs.writeFileSync(PREFS_FILE, '{}');
}

export const paths = {
  DATA_DIR,
  ADS_DIR,
  UPLOADS_DIR,
  PROMPTS_FILE,
  POSTS_FILE,
  SECRETS_FILE,
  PREFS_FILE,
};

export function appendJsonl(filePath: string, obj: unknown): void {
  fs.appendFileSync(filePath, JSON.stringify(obj) + '\n');
}

export function readJsonl<T = unknown>(filePath: string): T[] {
  if (!fs.existsSync(filePath)) return [];
  const content = fs.readFileSync(filePath, 'utf8');
  return content
    .split('\n')
    .filter(Boolean)
    .map((line) => JSON.parse(line) as T);
}

export function readJson<T = unknown>(filePath: string, fallback: T): T {
  if (!fs.existsSync(filePath)) return fallback;
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8')) as T;
  } catch {
    return fallback;
  }
}

export function writeJson(filePath: string, obj: unknown): void {
  fs.writeFileSync(filePath, JSON.stringify(obj, null, 2));
}
