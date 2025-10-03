import { appendJsonl, paths, readJsonl } from '../lib/fs.js';
import { randomUUID } from 'node:crypto';
import { generateCaption, generateImage } from './generation.js';
import { postToInstagram, postToTwitter, postToLinkedIn } from './posters/index.js';

export type AdRequirements = {
  description: string;
  tone: string;
  audience: string;
  useUploadedImagePath?: string;
  requestAIGeneratedImage?: boolean;
};

export async function generateAd(req: AdRequirements) {
  const caption = await generateCaption(req);
  const imagePath = req.useUploadedImagePath || (req.requestAIGeneratedImage ? await generateImage(req) : undefined);
  const promptId = randomUUID();
  const ad = { id: promptId, caption, imagePath, requirements: req, createdAt: new Date().toISOString() };
  // dedupe: if same description+tone+audience+caption already exists, skip logging
  const history = readJsonl<{ requirements: AdRequirements; caption: string }>(paths.PROMPTS_FILE);
  const exists = history.some(h => h.caption === caption && JSON.stringify(h.requirements) === JSON.stringify(req));
  if (!exists) appendJsonl(paths.PROMPTS_FILE, ad);
  return ad;
}

export async function planAndPostNext() {
  // generate fresh ad with default prompt to avoid repeats
  const ad = await generateAd({ description: 'Daily promotion', tone: 'engaging', audience: 'broad', requestAIGeneratedImage: true });
  const results = await Promise.allSettled([
    postToInstagram(ad),
    postToTwitter(ad),
    postToLinkedIn(ad),
  ]);
  const outcome = results.map((r) => (r.status === 'fulfilled' ? r.value : { error: String(r.reason) }));
  appendJsonl(paths.POSTS_FILE, { adId: ad.id, at: new Date().toISOString(), outcome });
  return { ad, outcome };
}
