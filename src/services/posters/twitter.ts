import { readJson, paths } from '../../lib/fs.js';
import { Ad } from './index.js';
import { TwitterApi } from 'twitter-api-v2';
import fs from 'node:fs';

export async function postToTwitter(ad: Ad) {
  try {
    const secrets = readJson<any>(paths.SECRETS_FILE, {} as any);
    const creds = secrets.twitter || {};
    const client = (creds.apiKey && creds.apiSecret && creds.accessToken && creds.accessSecret)
      ? new TwitterApi({ appKey: creds.apiKey, appSecret: creds.apiSecret, accessToken: creds.accessToken, accessSecret: creds.accessSecret })
      : null;
    if (!client) return { platform: 'twitter', skipped: true, reason: 'missing_creds' };

    // Upload media if present
    let mediaId: string | undefined;
    if (ad.imagePath && fs.existsSync(ad.imagePath)) {
      const data = await client.v1.uploadMedia(ad.imagePath);
      mediaId = data;
    }
    const tweet = await client.v2.tweet(ad.caption, mediaId ? { media: { media_ids: [mediaId] } as any } : {} as any);
    return { platform: 'twitter', ok: true, id: tweet.data.id };
  } catch (error) {
    return { platform: 'twitter', error: String(error) };
  }
}
