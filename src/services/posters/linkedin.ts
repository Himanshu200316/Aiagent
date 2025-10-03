import { readJson, paths } from '../../lib/fs.js';
import { Ad } from './index.js';
import axios from 'axios';
import fs from 'node:fs';
import path from 'node:path';

export async function postToLinkedIn(ad: Ad) {
  try {
    const secrets = readJson<any>(paths.SECRETS_FILE, {} as any);
    const token: string | undefined = secrets.linkedin?.accessToken || process.env.LI_ACCESS_TOKEN;
    if (!token) return { platform: 'linkedin', skipped: true, reason: 'missing_token' };

    // Stub: save artifact representing the LinkedIn post
    const artifact = path.join(path.dirname(ad.imagePath || ''), `${ad.id}-linkedin.json`);
    fs.writeFileSync(artifact, JSON.stringify({ caption: ad.caption, imagePath: ad.imagePath }, null, 2));
    return { platform: 'linkedin', ok: true, artifact };
  } catch (error) {
    return { platform: 'linkedin', error: String(error) };
  }
}
