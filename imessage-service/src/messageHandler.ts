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
 * iMessage stores message text in attributedBody as NSAttributedString archive
 * Format: NSKeyedArchiver with NSString objects containing length-prefixed UTF-8 text
 */
function extractTextFromAttributedBody(attributedBody: Buffer): string | null {
  if (!attributedBody || attributedBody.length === 0) {
    return null;
  }

  try {
    const candidates: { text: string; score: number }[] = [];

    const isMetadata = (text: string): boolean => {
      const lowerText = text.toLowerCase();
      // Check for known iMessage metadata patterns
      return lowerText.includes('__kim') || // iMessage internal attributes
             lowerText.includes('__k') ||    // Other iMessage attributes
             lowerText.startsWith('ns') ||   // NSFoundation classes
             lowerText === 'streamtyped' ||  // Archive header
             lowerText.includes('attributename') || // Attribute names
             text.includes('_'); // Any string with underscores is likely metadata
    };

    // Look for NSString markers followed by length-prefixed text
    let searchPos = 0;
    while (searchPos < attributedBody.length - 20) {
      const nsstringIndex = attributedBody.indexOf(Buffer.from('NSString'), searchPos);
      if (nsstringIndex === -1) break;

      let pos = nsstringIndex + 8; // Skip "NSString"

      while (pos < attributedBody.length - 10) {
        const lengthByte = attributedBody[pos];

        if (lengthByte > 0 && lengthByte <= 200 && pos + 1 + lengthByte < attributedBody.length) {
          const potentialText = attributedBody.slice(pos + 1, pos + 1 + lengthByte).toString('utf8');

          if (potentialText.length === lengthByte &&
              /^[\w\s\.,!?\-\'\"]+$/.test(potentialText) &&
              !potentialText.includes('\x00') &&
              !isMetadata(potentialText)) {

            // Calculate a score based on length and content quality
            const printableRatio = potentialText.split('').filter(c =>
              (c >= ' ' && c <= '~') || c === '\n' || c === '\r' || c === '\t'
            ).length / potentialText.length;

            const wordCount = potentialText.split(/\s+/).filter(w => w.length > 0).length;
            const hasRealWords = wordCount > 0 && potentialText.length > 2;

            // Penalize strings that look like identifiers (contain underscores)
            const identifierPenalty = potentialText.includes('_') ? 0.5 : 1;

            if (printableRatio >= 0.8 && hasRealWords) {
              const score = (potentialText.length * 10 + wordCount * 5 + (printableRatio * 100)) * identifierPenalty;
              candidates.push({ text: potentialText, score });
            }
          }
        }

        pos++;
        if (pos > nsstringIndex + 50) break;
      }

      searchPos = nsstringIndex + 1;
    }

    // Also search globally for length-prefixed strings
    for (let i = 0; i < attributedBody.length - 10; i++) {
      const lengthByte = attributedBody[i];
      if (lengthByte > 0 && lengthByte <= 200 && i + 1 + lengthByte < attributedBody.length) {
        const potentialText = attributedBody.slice(i + 1, i + 1 + lengthByte).toString('utf8');

        if (potentialText.length === lengthByte &&
            /^[\w\s\.,!?\-\'\"]+$/.test(potentialText) &&
            !potentialText.includes('\x00') &&
            !isMetadata(potentialText) &&
            potentialText.length > 1) { // Skip single characters

          const printableRatio = potentialText.split('').filter(c =>
            (c >= ' ' && c <= '~') || c === '\n' || c === '\r' || c === '\t'
          ).length / potentialText.length;

          const wordCount = potentialText.split(/\s+/).filter(w => w.length > 0).length;

          // Penalize strings that look like identifiers
          const identifierPenalty = potentialText.includes('_') ? 0.5 : 1;

          if (printableRatio >= 0.9 && wordCount > 0) {
            const score = (potentialText.length * 10 + wordCount * 5 + (printableRatio * 100)) * identifierPenalty;
            candidates.push({ text: potentialText, score });
          }
        }
      }
    }

    // Return the highest-scoring candidate
    if (candidates.length > 0) {
      candidates.sort((a, b) => b.score - a.score);
      return candidates[0].text;
    }

    return null;
  } catch (error) {
    console.error('[MessageHandler] Error extracting text from attributedBody:', error);
    return null;
  }
}

/**
 * Enhanced message with text extracted from database if needed
 */
async function getMessageWithText(message: Message): Promise<Message> {
  // If message already has text, return as-is
  if (message.text && message.text.trim().length > 0) {
    return message;
  }

  // Try to get text from database directly
  try {
    const db = new Database('/Users/ishan/Library/Messages/chat.db', { readonly: true });

    const result = db.prepare(`
      SELECT text, attributedBody
      FROM message
      WHERE ROWID = ?
    `).get(message.id) as { text?: string; attributedBody?: Buffer } | undefined;

    db.close();

    if (result) {
      // Try text field first
      if (result.text && result.text.trim().length > 0) {
        return { ...message, text: result.text };
      }

      // Try attributedBody if available
      if (result.attributedBody) {
        const extractedText = extractTextFromAttributedBody(result.attributedBody);
        if (extractedText) {
          return { ...message, text: extractedText };
        }
      }
    }
  } catch (error) {
    console.error('[MessageHandler] Error querying database directly:', error);
  }

  return message;
}

/**
 * Process an incoming iMessage and get a response from the backend
 */
export async function handleIncomingMessage(message: Message): Promise<string | null> {
  try {
    // First, ensure we have the message text by querying database directly if needed
    const messageWithText = await getMessageWithText(message);

    if (config.debug) {
      console.log(`[MessageHandler] Processing message from ${message.sender}`);
      console.log(`[MessageHandler] Message details:`, {
        originalText: message.text,
        extractedText: messageWithText.text,
        hasAttachments: message.attachments?.length > 0,
        attachmentCount: message.attachments?.length || 0,
        service: message.service,
        chatId: message.chatId,
        messageId: message.id,
      });
    }

    // Use the enhanced message
    message = messageWithText;

    // Don't respond to group chats in Phase 1
    if (message.isGroupChat) {
      if (config.debug) {
        console.log('[MessageHandler] Skipping group chat message');
      }
      return null;
    }

    // Handle messages with no text
    if (!message.text || message.text.trim().length === 0) {
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
    const response = await callBackend(message.text);

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

