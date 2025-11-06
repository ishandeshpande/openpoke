import axios from 'axios';
import { config } from './config';
import type { Message } from '@photon-ai/imessage-kit';
import Database from 'better-sqlite3';

export interface BackendResponse {
  ok: boolean;
  response?: string;
  error?: string;
}

/**
 * Extract text content from iMessage attributedBody field
 * NSAttributedString format: ...NSString...+[LENGTH_BYTE][TEXT_CONTENT]...
 */
function extractTextFromAttributedBody(attributedBody: Buffer): string | null {
  if (!attributedBody || attributedBody.length === 0) {
    return null;
  }

  try {
    // Find the '+' character which marks the start of the text section
    const plusIndex = attributedBody.indexOf('+');
    if (plusIndex === -1 || plusIndex >= attributedBody.length - 2) {
      return null;
    }

    // The byte immediately after '+' is the length of the text
    const textLength = attributedBody[plusIndex + 1];
    if (textLength === 0 || plusIndex + 1 + textLength >= attributedBody.length) {
      return null;
    }

    // Extract exactly that many bytes as UTF-8 text
    const textBytes = attributedBody.slice(plusIndex + 2, plusIndex + 2 + textLength);
    const text = textBytes.toString('utf8');

    // Basic validation: should have at least one letter and be reasonable length
    if (text.length > 0 && text.length <= 1000 && /[a-zA-Z0-9]/.test(text)) {
      return text.trim();
    }

    return null;
  } catch (error) {
    console.error('[MessageHandler] Error extracting text from attributedBody:', error);
    return null;
  }
}

/**
 * Get the most current text for a message from the database
 * Always queries the database since SDK may have stale/cached data
 */
async function getMessageTextFromDB(messageId: string): Promise<string | null> {
  try {
    const db = new Database('/Users/ishan/Library/Messages/chat.db', { readonly: true });

    const result = db.prepare(`
      SELECT text, attributedBody
      FROM message
      WHERE ROWID = ?
    `).get(messageId) as { text?: string; attributedBody?: Buffer } | undefined;

    db.close();

    if (result) {
      // Try text field first (sometimes populated)
      if (result.text && result.text.trim().length > 0) {
        return result.text.trim();
      }

      // Try attributedBody parsing (always contains the data)
      if (result.attributedBody) {
        const extractedText = extractTextFromAttributedBody(result.attributedBody);
        if (extractedText) {
          return extractedText;
        }
      }
    }
  } catch (error) {
    console.error('[MessageHandler] Error querying database for text:', error);
  }

  return null;
}

/**
 * Process an incoming iMessage and get a response from the backend
 */
export async function handleIncomingMessage(message: Message): Promise<string | null> {
  try {
    // Always get the most current text from database (SDK may have stale data)
    const messageText = await getMessageTextFromDB(message.id);

    if (config.debug) {
      console.log(`[MessageHandler] Processing message from ${message.sender}`);
      console.log(`[MessageHandler] Message details:`, {
        sdkText: message.text,
        dbText: messageText,
        hasAttachments: message.attachments?.length > 0,
        attachmentCount: message.attachments?.length || 0,
        service: message.service,
        chatId: message.chatId,
        messageId: message.id,
      });
    }

    // Use text from database if available, otherwise use SDK text
    const finalText = messageText || message.text;

    // Don't respond to group chats in Phase 1
    if (message.isGroupChat) {
      if (config.debug) {
        console.log('[MessageHandler] Skipping group chat message');
      }
      return null;
    }

    // Handle messages with no text
    if (!finalText || finalText.trim().length === 0) {
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
    const response = await callBackend(finalText);

    if (config.debug) {
      console.log(`[MessageHandler] Backend response: ${response}`);
    }

    return response;
  } catch (error) {
    console.error('[MessageHandler] Error processing message:', error);
    
    // Return a friendly error message to the user
    return "Sorry, I encountered an error processing your message. Please try again.";
  }
}

/**
 * Call the FastAPI backend with sync_mode enabled
 */
async function callBackend(messageText: string): Promise<string> {
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
    };

    if (config.debug) {
      console.log(`[MessageHandler] Calling backend at ${url}`);
    }

    const response = await axios.post<BackendResponse>(url, payload, {
      timeout: 120000, // 2 minute timeout for LLM responses
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.data.ok && response.data.response) {
      return response.data.response;
    } else if (response.data.error) {
      throw new Error(`Backend error: ${response.data.error}`);
    } else {
      throw new Error('Invalid backend response format');
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNREFUSED') {
        throw new Error('Cannot connect to backend server. Is it running?');
      } else if (error.response) {
        throw new Error(`Backend returned ${error.response.status}: ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        throw new Error('No response from backend server');
      }
    }
    throw error;
  }
}

