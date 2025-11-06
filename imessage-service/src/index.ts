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
const processedMessages = new Map<string, number>(); // key: sender+text, value: timestamp
const inFlightRequests = new Map<string, number>(); // key: sender+text, value: start time
const processedContent = new Set<string>(); // key: sender+text, for aggressive deduplication
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
      const messageKey = `${msg.sender}:${msg.text?.trim() || ''}`;
      const contentSignature = `${msg.sender}:${msg.text?.trim() || ''}`; // exact content match
      const now = Date.now();

      // Atomic check: prevent processing if already processed by ID or content, or in-flight, or exact content signature
      const shouldSkip = processedIds.has(msg.id) ||
                        processedContent.has(contentSignature) ||
                        (processedMessages.get(messageKey) && (now - processedMessages.get(messageKey)!) < 10000) ||
                        (inFlightRequests.has(messageKey) && (now - (inFlightRequests.get(messageKey) || 0)) < 30000); // 30s timeout

      if (shouldSkip) {
        if (config.debug) {
          if (processedIds.has(msg.id)) {
            log(`⏭️  Skipping duplicate message ID: ${msg.id}`);
          } else if (processedContent.has(contentSignature)) {
            log(`⏭️  Skipping duplicate content signature: ${contentSignature}`);
          } else if (processedMessages.get(messageKey) && (now - processedMessages.get(messageKey)!) < 10000) {
            log(`⏭️  Skipping duplicate message content from ${msg.sender} (within 10s window)`);
          } else if (inFlightRequests.has(messageKey) && (now - (inFlightRequests.get(messageKey) || 0)) < 30000) {
            log(`⏭️  Skipping duplicate in-flight request for message from ${msg.sender}`);
          }
        }
        return;
      }

      // Atomically mark as processed and in-flight
      processedIds.add(msg.id);
      processedContent.add(contentSignature);
      processedMessages.set(messageKey, now);
      inFlightRequests.set(messageKey, now);

      if (config.debug) {
        log(`🆔 Processing message ID: ${msg.id}`);
      }

      // Memory leak prevention
      if (processedIds.size > 1000) {
        const ids = Array.from(processedIds);
        processedIds.clear();
        ids.slice(-500).forEach(id => processedIds.add(id));
      }

      // Clean old message keys (older than 30 seconds)
      if (processedMessages.size > 100) {
        for (const [key, timestamp] of processedMessages.entries()) {
          if (now - timestamp > 30000) {
            processedMessages.delete(key);
          }
        }
      }

      // Safety cleanup for in-flight requests (remove old/stuck requests)
      if (inFlightRequests.size > 10) {
        const now = Date.now();
        const toRemove: string[] = [];
        for (const [key, startTime] of inFlightRequests.entries()) {
          if (now - startTime > 60000) { // 1 minute timeout
            toRemove.push(key);
          }
        }
        toRemove.forEach(key => inFlightRequests.delete(key));
        if (toRemove.length > 0 && config.debug) {
          log(`⚠️  Cleaned up ${toRemove.length} stuck in-flight requests`);
        }
      }

      // Safety cleanup for content signatures
      if (processedContent.size > 1000) {
        if (config.debug) {
          log(`⚠️  Clearing old content signatures (${processedContent.size} > 1000)`);
        }
        // Clear half of the content signatures to prevent memory issues
        const signatures = Array.from(processedContent);
        const toKeep = signatures.slice(signatures.length / 2);
        processedContent.clear();
        toKeep.forEach(sig => processedContent.add(sig));
      }


      try {
        log(`\n📨 New message from ${msg.sender}`);

        // Small delay to allow database sync (iMessage timing issue)
        await new Promise(resolve => setTimeout(resolve, 500));

        // Handle text messages (like imessage-kit examples)
        if (msg.text?.trim()) {
          try {
            log(`✅ Message text: "${msg.text}"`);
            const response = await handleIncomingMessage(msg);

            if (response && sdk) {
              // NOTE: Don't send response directly - it's queued by backend and will be sent by poller
              // This prevents double-sending messages
              log(`✅ Response queued (will be sent by poller)`);
            } else if (response === null) {
              log(`ℹ️  No response needed (filtered message)`);
            }
          } finally {
            // Always remove from in-flight set when done
            const messageKey = `${msg.sender}:${msg.text.trim()}`;
            inFlightRequests.delete(messageKey);
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

  // Start polling for outgoing messages
  startOutgoingMessagePoller();
}

interface OutgoingMessage {
  id: number;
  recipient: string;
  message: string;
  created_at: string;
}

interface PendingMessagesResponse {
  ok: boolean;
  messages: OutgoingMessage[];
}

/**
 * Poll for outgoing messages and send them via iMessage
 */
function startOutgoingMessagePoller() {
  const POLL_INTERVAL = 5000; // Poll every 5 seconds

  const pollMessages = async () => {
    try {
      const response = await fetch(`${config.backendUrl}/api/v1/messages/pending?limit=10`);

      if (!response.ok) {
        log(`❌ Failed to fetch pending messages: ${response.status}`);
        return;
      }

      const data = await response.json() as PendingMessagesResponse;
      const messages = data.messages || [];

      for (const msg of messages) {
        try {
          log(`📤 Sending queued message to ${msg.recipient}`);

          if (sdk) {
            await sdk.send(msg.recipient, msg.message);
            log(`✅ Sent message ${msg.id}`);

            // Mark as sent
            await fetch(`${config.backendUrl}/api/v1/messages/status`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message_id: msg.id,
                success: true
              })
            });
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          log(`❌ Failed to send message ${msg.id}: ${errorMessage}`);

          // Mark as failed
          await fetch(`${config.backendUrl}/api/v1/messages/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message_id: msg.id,
              success: false,
              error: errorMessage
            })
          });
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (config.debug) {
        log(`Error polling for outgoing messages: ${errorMessage}`);
      }
    }
  };

  // Initial poll
  pollMessages();

  // Set up interval
  setInterval(pollMessages, POLL_INTERVAL);
  log(`✓ Started outgoing message poller (interval: ${POLL_INTERVAL}ms)`);
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

