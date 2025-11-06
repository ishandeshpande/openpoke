import { IMessageSDK } from '@photon-ai/imessage-kit';
import type { Message } from '@photon-ai/imessage-kit';
import { config } from './config';
import { handleIncomingMessage } from './messageHandler';

let sdk: IMessageSDK | null = null;

/**
 * Initialize and start the iMessage bot service
 */
async function main() {
  console.log('=================================================');
  console.log('  OpenPoke iMessage Service');
  console.log('=================================================');
  console.log(`Backend URL: ${config.backendUrl}`);
  console.log(`Poll Interval: ${config.pollInterval}ms`);
  console.log(`Debug Mode: ${config.debug}`);
  
  if (config.allowedNumbers.length > 0) {
    console.log(`Allowed Numbers: ${config.allowedNumbers.join(', ')}`);
    console.log(`⚠️  Will ONLY respond to whitelisted numbers`);
  } else {
    console.log(`Allowed Numbers: ALL (not restricted)`);
    console.log(`⚠️  WARNING: Bot will respond to ALL incoming messages!`);
  }
  
  console.log('=================================================\n');

  // Initialize the iMessage SDK
  sdk = new IMessageSDK({
    debug: config.debug,
    maxConcurrent: 5,
    watcher: {
      pollInterval: config.pollInterval,
      excludeOwnMessages: true,
      unreadOnly: false, // Process all new messages, not just unread ones
    },
  });

  console.log('✓ iMessage SDK initialized');
  console.log('✓ Starting message watcher...\n');

  // Start watching for new messages
  await sdk.startWatching({
    onNewMessage: async (message: Message) => {
      try {
        console.log(`\n[${new Date().toISOString()}] New message from ${message.sender}`);

        // Process the message and get response
        // The message handler now handles text extraction from attributedBody
        const response = await handleIncomingMessage(message);

        // Send the response back if we have one
        if (response && sdk) {
          console.log(`[${new Date().toISOString()}] Sending response...`);
          await sdk.send(message.sender, response);
          console.log(`[${new Date().toISOString()}] ✓ Response sent`);
        }
      } catch (error) {
        console.error('[Error] Failed to handle message:', error);
      }
    },

    onGroupMessage: async (message: Message) => {
      // Log group messages but don't respond (Phase 1)
      if (config.debug) {
        console.log(`[${new Date().toISOString()}] Group message in ${message.chatId} (ignored)`);
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
  console.log('\n\nShutting down...');
  
  if (sdk) {
    try {
      sdk.stopWatching();
      await sdk.close();
      console.log('✓ iMessage SDK closed');
    } catch (error) {
      console.error('Error during shutdown:', error);
    }
  }
  
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

