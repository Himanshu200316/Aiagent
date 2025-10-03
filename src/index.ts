import 'dotenv/config';
import express from 'express';
import multer from 'multer';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ensureDataDirs } from './lib/fs.js';
import { cerebrusRouter } from './routes/cerebrus.js';
import { uploadsRouter } from './routes/uploads.js';
import { scheduler } from './lib/scheduler.js';

const app = express();
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Ensure data directories exist
ensureDataDirs();

// Static serving of generated ads
const __dirname = path.dirname(fileURLToPath(import.meta.url));
app.use('/public', express.static(path.join(__dirname, '..', 'data', 'public')));

// Routers
app.use('/api/cerebrus', cerebrusRouter);
app.use('/api/uploads', uploadsRouter);

// Health
app.get('/health', (_req, res) => res.json({ ok: true }));

const port = Number(process.env.PORT || 8080);
app.listen(port, () => {
  console.log(`[server] listening on :${port}`);
});

// Start scheduler
scheduler.start();
