import dotenv from 'dotenv';
import path from 'path';

// Load environment variables from .env file
dotenv.config({ path: path.join(__dirname, '../.env') });

export interface Config {
  backendUrl: string;
  pollInterval: number;
  debug: boolean;
  allowedNumbers: string[];
}

export function loadConfig(): Config {
  // Parse allowed numbers from comma-separated list
  const allowedNumbersRaw = process.env.ALLOWED_NUMBERS || '';
  const allowedNumbers = allowedNumbersRaw
    .split(',')
    .map(num => num.trim())
    .filter(num => num.length > 0);

  return {
    backendUrl: process.env.BACKEND_URL || 'http://localhost:8001',
    pollInterval: parseInt(process.env.POLL_INTERVAL || '2000', 10),
    debug: process.env.DEBUG === 'true',
    allowedNumbers,
  };
}

export const config = loadConfig();

