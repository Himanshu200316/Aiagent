import OpenAI from 'openai';
import path from 'node:path';
import fs from 'node:fs';
import { paths } from '../lib/fs.js';
import { AdRequirements } from './agent.js';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function generateCaption(req: AdRequirements): Promise<string> {
  const prompt = `Write a concise social ad caption. Description: ${req.description}. Tone: ${req.tone}. Audience: ${req.audience}. Include 3-5 relevant hashtags.`;
  const response = await openai.chat.completions.create({
    model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
    messages: [
      { role: 'system', content: 'You write engaging, brand-safe, platform-agnostic ad captions.' },
      { role: 'user', content: prompt },
    ],
    temperature: 0.7,
  });
  return response.choices[0]?.message?.content?.trim() || 'Check out our latest offer!';
}

export async function generateImage(req: AdRequirements): Promise<string> {
  // Use OpenAI image generation (DALL·E) as default
  const prompt = `Product/Service: ${req.description}. Tone: ${req.tone}. Audience: ${req.audience}. Create an eye-catching ad visual.`;
  const img = await openai.images.generate({
    model: process.env.OPENAI_IMAGE_MODEL || 'gpt-image-1',
    prompt,
    size: '1024x1024'
  });
  const b64 = img.data[0].b64_json!;
  const buffer = Buffer.from(b64, 'base64');
  const filename = `${Date.now()}-ad.png`;
  const fullPath = path.join(paths.ADS_DIR, filename);
  fs.writeFileSync(fullPath, buffer);
  return fullPath;
}
