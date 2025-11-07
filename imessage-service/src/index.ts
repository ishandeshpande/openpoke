import { IMessageSDK } from '@photon-ai/imessage-kit';
import type { Message } from '@photon-ai/imessage-kit';
import { config } from './config';
import { handleIncomingMessage } from './messageHandler';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

let sdk: IMessageSDK | null = null;
const processedIds = new Set<string>();
const execAsync = promisify(exec);


/**
 * Check if Messages app is running
 */
async function isMessagesAppRunning(): Promise<boolean> {
  try {
    const { stdout } = await execAsync('ps aux | grep -i "Messages.app" | grep -v grep');
    return stdout.trim().length > 0;
  } catch (error) {
    return false;
  }
}

/**
 * Start Messages app if not running
 */
async function ensureMessagesAppRunning(): Promise<void> {
  const isRunning = await isMessagesAppRunning();
  if (!isRunning) {
    log('📱 Messages app not running, starting it...');
    try {
      await execAsync('open -a Messages');
      // Wait a bit for the app to start
      await new Promise(resolve => setTimeout(resolve, 3000));
      log('✅ Messages app started');
    } catch (error) {
      log('❌ Failed to start Messages app');
      throw new Error('Cannot start Messages app. Please start it manually.');
    }
  } else {
    log('✅ Messages app is running');
  }
}

// Setup logging
const logDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

const logFile = path.join(logDir, `imessage-service-${new Date().toISOString().split('T')[0]}.log`);
const logStream = fs.createWriteStream(logFile, { flags: 'a' });

function log(message: string) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  console.log(message);
  logStream.write(logMessage);
}

process.on('exit', () => {
  logStream.end();
});

/**
 * Initialize and start the iMessage bot service
 */
async function main() {
  log('=================================================');
  log('  OpenPoke iMessage Service');
  log('=================================================');
  log(`Backend URL: ${config.backendUrl}`);
  log(`Poll Interval: ${config.pollInterval}ms`);
  log(`Debug Mode: ${config.debug}`);
  log(`Log File: ${logFile}`);
  
  if (config.allowedNumbers.length > 0) {
    log(`Allowed Numbers: ${config.allowedNumbers.join(', ')}`);
    log(`⚠️  Will ONLY respond to whitelisted numbers`);
  } else {
    log(`Allowed Numbers: ALL (not restricted)`);
    log(`⚠️  WARNING: Bot will respond to ALL incoming messages!`);
  }
  
  log('=================================================\n');

  // Ensure Messages app is running before initializing SDK
  await ensureMessagesAppRunning();

  // Initialize SDK (works in both Node.js and Bun)
  sdk = new IMessageSDK({
    debug: config.debug,
    maxConcurrent: 5
  });

  console.log('✓ iMessage SDK initialized');
  console.log('✓ Starting message watcher...\n');

  // Start watching for new messages
  await sdk.startWatching({
    onNewMessage: async (msg: Message) => {
      // Prevent duplicate processing
      if (processedIds.has(msg.id)) {
        return;
      }
      processedIds.add(msg.id);

      // Memory leak prevention
      if (processedIds.size > 1000) {
        const ids = Array.from(processedIds);
        processedIds.clear();
        ids.slice(-500).forEach(id => processedIds.add(id));
      }

      try {
        log(`\n📨 New message from ${msg.sender}`);

        // Small delay to allow database sync (iMessage timing issue)
        await new Promise(resolve => setTimeout(resolve, 500));

        // Handle text messages (like imessage-kit examples)
        if (msg.text?.trim()) {
          log(`✅ Message text: "${msg.text}"`);
          const response = await handleIncomingMessage(msg);

          if (response && sdk) {
            await sdk.send(msg.sender, response);
            log(`✅ Response sent`);
          } else if (response === null) {
            log(`ℹ️  No response needed (filtered message)`);
          }
        } else {
          // Check if it's an attachment-only message
          const hasAttachments = msg.attachments && msg.attachments.length > 0;
          if (hasAttachments) {
            log(`ℹ️  Message has ${msg.attachments.length} attachment(s) but no text`);
          } else {
            log(`ℹ️  Message has no text content (empty message)`);
          }
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);

        // Check for Messages app related errors
        if (errorMessage.includes('Messages app is not running') ||
            errorMessage.includes('osascript') ||
            errorMessage.includes('AppleScript')) {
          log(`❌ Messages app error: ${errorMessage}`);
          log(`💡 Make sure Messages app is running and you have granted Full Disk Access`);
        } else {
          log(`❌ Error: ${errorMessage}`);
        }
      }
    },

    onError: (error: Error) => {
      console.error('[Error] Watcher error:', error);
    },
  });

  console.log('✓ Watching for messages...');
  console.log('Press Ctrl+C to stop\n');
}

/**
 * Graceful shutdown handler
 */
async function shutdown() {
  log('\n\nShutting down...');
  
  if (sdk) {
    try {
      sdk.stopWatching();
      await sdk.close();
      log('✓ iMessage SDK closed');
    } catch (error) {
      log(`Error during shutdown: ${error}`);
    }
  }
  
  logStream.end();
  process.exit(0);
}

// Handle shutdown signals
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  shutdown();
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
  shutdown();
});

// Start the service
main().catch((error) => {
  console.error('Failed to start service:', error);
  process.exit(1);
});

