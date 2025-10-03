import { Router } from 'express';
import { z } from 'zod';
import { writeJson, readJson, paths } from '../lib/fs.js';
import { planAndPostNext, generateAd } from '../services/agent.js';

export const cerebrusRouter = Router();

const CredentialsSchema = z.object({
  instagram: z.object({ accessToken: z.string().min(1) }).optional(),
  twitter: z.object({ apiKey: z.string(), apiSecret: z.string(), accessToken: z.string(), accessSecret: z.string() }).optional(),
  linkedin: z.object({ accessToken: z.string().min(1) }).optional(),
});

cerebrusRouter.post('/credentials', (req, res) => {
  const parsed = CredentialsSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const existing = readJson(paths.SECRETS_FILE, {} as any);
  const merged = { ...existing, ...parsed.data };
  writeJson(paths.SECRETS_FILE, merged);
  res.json({ ok: true });
});

const PrefsSchema = z.object({
  scheduleCron: z.string().default('0 0 * * *'),
  postTargets: z.array(z.enum(['instagram_feed', 'instagram_story', 'twitter', 'linkedin'])).default(['instagram_feed','twitter','linkedin']),
});

cerebrusRouter.post('/preferences', (req, res) => {
  const parsed = PrefsSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const merged = { ...readJson(paths.PREFS_FILE, {} as any), ...parsed.data };
  writeJson(paths.PREFS_FILE, merged);
  res.json({ ok: true });
});

const RequirementsSchema = z.object({
  description: z.string().min(1),
  tone: z.string().default('friendly'),
  audience: z.string().default('general'),
  useUploadedImagePath: z.string().optional(),
  requestAIGeneratedImage: z.boolean().default(true),
});

cerebrusRouter.post('/generate', async (req, res) => {
  const parsed = RequirementsSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  try {
    const ad = await generateAd(parsed.data);
    res.json(ad);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to generate ad' });
  }
});

cerebrusRouter.post('/post-now', async (_req, res) => {
  try {
    const result = await planAndPostNext();
    res.json(result);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to post' });
  }
});
