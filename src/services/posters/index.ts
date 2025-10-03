import { AdRequirements } from '../agent.js';
import { postToInstagram as ig } from './instagram.js';
import { postToTwitter as tw } from './twitter.js';
import { postToLinkedIn as li } from './linkedin.js';

export type Ad = { id: string; caption: string; imagePath?: string; requirements: AdRequirements };

export const postToInstagram = (ad: Ad) => ig(ad);
export const postToTwitter = (ad: Ad) => tw(ad);
export const postToLinkedIn = (ad: Ad) => li(ad);
