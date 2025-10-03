import cron from 'node-cron';
import { planAndPostNext } from '../services/agent.js';

export const scheduler = cron.schedule('0 0 * * *', async () => {
  try {
    await planAndPostNext();
  } catch (error) {
    console.error('[scheduler] error during daily post', error);
  }
}, { scheduled: false, timezone: 'UTC' });
