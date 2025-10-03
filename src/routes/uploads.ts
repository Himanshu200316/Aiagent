import { Router } from 'express';
import multer from 'multer';
import path from 'node:path';
import { paths } from '../lib/fs.js';
import { randomUUID } from 'node:crypto';

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, paths.UPLOADS_DIR),
  filename: (_req, file, cb) => {
    const ext = path.extname(file.originalname) || '.bin';
    cb(null, `${Date.now()}-${randomUUID()}${ext}`);
  },
});

const upload = multer({ storage });

export const uploadsRouter = Router();

uploadsRouter.post('/', upload.single('image'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });
  res.json({ path: req.file.path, filename: req.file.filename });
});
