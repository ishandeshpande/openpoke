# OpenPoke iMessage Service

This service integrates OpenPoke with iMessage using [@photon-ai/imessage-kit](https://github.com/photon-hq/imessage-kit), allowing you to interact with your habit tracking system through text messages.

## Prerequisites

### System Requirements
- **macOS only** (iMessage integration requires access to local iMessage database)
- **Node.js 18+** or Bun 1.0+
- **iMessage** configured and active on your Mac
- **Python backend** running on port 8001

### Permissions Required

Before running the service, you **must** grant Full Disk Access to your terminal or IDE:

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the **"+"** button
3. Add your Terminal application (Terminal.app, iTerm2, etc.) or IDE (Cursor, VS Code, etc.)
4. Restart your terminal/IDE after granting permissions

This permission is required for imessage-kit to read your iMessage database at `~/Library/Messages/chat.db`.

## Installation

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build
```

## Configuration

Create a `.env` file in this directory (or copy from `.env.example`):

```bash
# Backend API Configuration
BACKEND_URL=http://localhost:8001

# iMessage Watcher Configuration
POLL_INTERVAL=2000

# Debug Mode
DEBUG=true

# Allowed Phone Numbers (comma-separated)
# IMPORTANT: Only these numbers will receive bot responses!
# Leave empty to respond to ALL (not recommended)
ALLOWED_NUMBERS=+11234567890
```

### Configuration Options

- `BACKEND_URL`: URL of the OpenPoke FastAPI backend (default: `http://localhost:8001`)
- `POLL_INTERVAL`: How often to check for new messages in milliseconds (default: `2000`)
- `DEBUG`: Enable detailed logging (default: `true`)
- `ALLOWED_NUMBERS`: **Comma-separated list of phone numbers that can use the bot** (default: empty = ALL)
  - **⚠️ IMPORTANT:** If left empty, bot will respond to EVERYONE who texts you!
  - Supports any format: `+11234567890`, `(123) 456-7890`, `123-456-7890`
  - Example: `ALLOWED_NUMBERS=+11234567890,+10987654321`
  - **Recommended:** Set to your own number for personal use

## Usage

### Start the Service

From the project root:

```bash
# Start both backend and iMessage service
./start-imessage.sh
```

Or start just the iMessage service (requires backend to be already running):

```bash
cd imessage-service

# Production mode
npm start

# Development mode (auto-restart on changes)
npm run dev
```

### Sending Messages

Once running, the bot will automatically:
1. Monitor your iMessage conversations for new messages
2. Send messages to the backend for processing
3. Reply with Poke's response

Just send a text message to your phone number from another device, and the bot will respond!

## How It Works

```
User → iMessage App
         ↓ (SDK polls every 2s)
    Node.js Service
         ↓ POST /chat/send
    FastAPI Backend
         ↓ Interaction Agent
    FastAPI Backend
         ↓ Response
    Node.js Service
         ↓ sdk.send()
    iMessage App → User
```

The service uses imessage-kit's `startWatching()` feature to monitor incoming messages, sends them to the backend with `sync_mode: true`, waits for the response, and sends it back via iMessage.

## Development

```bash
# Build TypeScript
npm run build

# Watch mode (rebuild on changes)
npm run watch

# Development mode with ts-node
npm run dev
```

## Project Structure

```
imessage-service/
├── src/
│   ├── index.ts           # Main entry point, SDK initialization
│   ├── messageHandler.ts  # Message processing logic
│   └── config.ts          # Environment configuration
├── dist/                  # Compiled JavaScript (generated)
├── package.json
├── tsconfig.json
└── .env                   # Local configuration
```

## Troubleshooting

### "Cannot connect to backend server"
- Ensure the Python backend is running on port 8001
- Check `BACKEND_URL` in `.env`

### "Permission denied" errors
- Grant Full Disk Access to your terminal/IDE in System Settings
- Restart your terminal after granting permissions

### Bot not receiving messages
- Check that iMessage is active and working on your Mac
- Verify `DEBUG=true` in `.env` to see detailed logs
- Try sending a message from another device to yourself

### Messages not sending
- Check AppleScript permissions (imessage-kit uses AppleScript to send messages)
- Ensure iMessage is the default messaging app
- Check console logs for specific errors

## Limitations (Phase 1)

- **Single-user only**: No phone verification or multi-tenant support
- **No group chats**: Group messages are ignored
- **Local only**: Must run on a Mac with iMessage configured
- **Polling-based**: Checks for messages every 2 seconds (configurable)

## Future Enhancements (Phase 2)

- Multi-tenant support with phone verification
- Supabase/PostgreSQL backend
- Cloud deployment
- Group chat support
- Real-time webhooks instead of polling
- Rate limiting per user

## License

Same as OpenPoke main project

