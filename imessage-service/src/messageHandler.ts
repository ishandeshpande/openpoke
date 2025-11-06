import axios from 'axios';
import { config } from './config';
import type { Message } from '@photon-ai/imessage-kit';

export interface BackendResponse {
  ok: boolean;
  response?: string;
  error?: string;
}

/**
 * Process an incoming iMessage and get a response from the backend
 */
export async function handleIncomingMessage(message: Message): Promise<string | null> {
  try {
    // Use the message text (now potentially refreshed via retry mechanism)
    const messageText = message.text;

    // Don't respond to group chats in Phase 1
    if (message.isGroupChat) {
      if (config.debug) {
        console.log('[MessageHandler] Skipping group chat message');
      }
      return null;
    }

    // Handle messages with no text
    if (!messageText || messageText.trim().length === 0) {
      // Check if it's an attachment-only message
      const hasAttachments = message.attachments && message.attachments.length > 0;
      if (hasAttachments) {
        if (config.debug) {
          console.log(`[MessageHandler] Message has ${message.attachments?.length || 0} attachment(s) but no text`);
        }
        // You could handle attachments here in the future
        // For now, we'll skip it
        return null;
      }

      if (config.debug) {
        console.log('[MessageHandler] Skipping empty message (no text, no attachments)');
      }
      return null;
    }

    // Only respond to whitelisted numbers (if configured)
    if (config.allowedNumbers.length > 0) {
      const isAllowed = config.allowedNumbers.some(allowed => {
        // Match if sender contains the allowed number
        // This handles different formats: +1234567890, (123) 456-7890, etc.
        const normalizedSender = message.sender.replace(/\D/g, '');
        const normalizedAllowed = allowed.replace(/\D/g, '');
        return normalizedSender.includes(normalizedAllowed) || 
               normalizedAllowed.includes(normalizedSender);
      });

      if (!isAllowed) {
        if (config.debug) {
          console.log(`[MessageHandler] Ignoring message from non-whitelisted number: ${message.sender}`);
        }
        return null;
      }
    }

    // Call the backend API
    const response = await callBackend(messageText, message.sender);

    if (config.debug) {
      console.log(`[MessageHandler] Backend response: ${response}`);
    }

    return response;
  } catch (error) {
    console.error('[MessageHandler] Error processing message:', error);
    
    // Check if it's a rate limit error
    const errorMessage = error instanceof Error ? error.message : String(error);
    if (errorMessage.includes('rate_limit') || errorMessage.includes('429')) {
      return "I'm getting a lot of messages right now! Give me a moment and try again in a few seconds. 😊";
    }
    
    // Return a friendly error message to the user
    return "Sorry, I encountered an error processing your message. Please try again.";
  }
}

/**
 * Call the FastAPI backend with sync_mode enabled
 */
async function callBackend(messageText: string, senderPhone: string): Promise<string> {
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  try {
    const url = `${config.backendUrl}/api/v1/chat/send`;

    const payload = {
      messages: [
        {
          role: 'user',
          content: messageText,
        },
      ],
      sync_mode: true,
      source: 'imessage',
      sender_phone: senderPhone,
      request_id: requestId, // Add unique ID for tracking
    };

    if (config.debug) {
      console.log(`[MessageHandler] [${requestId}] Calling backend at ${url} for "${messageText.substring(0, 50)}${messageText.length > 50 ? '...' : ''}"`);
    }

    const response = await axios.post<BackendResponse>(url, payload, {
      timeout: 120000, // 2 minute timeout for LLM responses
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.data.ok && response.data.response) {
      console.log(`[MessageHandler] [${requestId}] Backend returned response: "${response.data.response}"`);
      return response.data.response;
    } else if (response.data.error) {
      console.log(`[MessageHandler] [${requestId}] Backend returned error: ${response.data.error}`);
      throw new Error(`Backend error: ${response.data.error}`);
    } else {
      console.log(`[MessageHandler] [${requestId}] Invalid backend response format:`, response.data);
      throw new Error('Invalid backend response format');
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNREFUSED') {
        console.log(`[MessageHandler] [${requestId}] Cannot connect to backend server`);
        throw new Error('Cannot connect to backend server. Is it running?');
      } else if (error.response) {
        console.log(`[MessageHandler] [${requestId}] Backend returned ${error.response.status}: ${JSON.stringify(error.response.data)}`);
        throw new Error(`Backend returned ${error.response.status}: ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        console.log(`[MessageHandler] [${requestId}] No response from backend server`);
        throw new Error('No response from backend server');
      }
    }
    console.log(`[MessageHandler] [${requestId}] Unexpected error:`, error);
    throw error;
  }
}

