import fs from 'node:fs';
import path from 'node:path';
import axios from 'axios';
import { Ad } from './index.js';
import { readJson, paths } from '../../lib/fs.js';

// Placeholder for MCP Instagram tool. For now, use Graph API if configured.
export async function postToInstagram(ad: Ad) {
  try {
    const secrets = readJson<any>(paths.SECRETS_FILE, {} as any);
    const token: string | undefined = secrets.instagram?.accessToken || process.env.IG_ACCESS_TOKEN;
    if (!token) return { platform: 'instagram', skipped: true, reason: 'missing_token' };

    // This is a stub. Proper Instagram posting requires Business Account via Graph API.
    // Here we just simulate success and save a sidecar JSON.
    const artifact = path.join(path.dirname(ad.imagePath || ''), `${ad.id}-instagram.json`);
    fs.writeFileSync(artifact, JSON.stringify({ caption: ad.caption, imagePath: ad.imagePath }, null, 2));
    return { platform: 'instagram', ok: true, artifact };
  } catch (error) {
    return { platform: 'instagram', error: String(error) };
  }
}
