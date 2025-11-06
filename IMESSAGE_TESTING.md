# iMessage Bot Testing Guide

This guide helps you test the iMessage integration end-to-end.

## Pre-Testing Checklist

### 1. System Requirements
- [ ] Running macOS (iMessage integration only works on macOS)
- [ ] iMessage is configured and working on your Mac
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Anthropic API key configured in `.env`

### 2. Permissions
- [ ] Full Disk Access granted to Terminal/IDE
  - System Settings → Privacy & Security → Full Disk Access
  - Added your Terminal or IDE to the list
  - Restarted terminal/IDE after granting

### 3. Installation
- [ ] Python dependencies installed: `pip install -r server/requirements.txt`
- [ ] Node dependencies installed: `cd imessage-service && npm install`
- [ ] TypeScript compiled: `cd imessage-service && npm run build`

## Testing Procedure

### Test 1: Backend Only

Start just the backend to verify it works independently:

```bash
cd server
python -m uvicorn server:app --host 0.0.0.0 --port 8001
```

**Expected Result:**
- Server starts without errors
- Log shows: `INFO: Application startup complete.`
- API docs accessible at http://localhost:8001/docs

**Test the API:**
```bash
curl -X POST http://localhost:8001/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "sync_mode": false
  }'
```

**Expected:** `202 Accepted` response (async mode)

**Test sync mode:**
```bash
curl -X POST http://localhost:8001/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "sync_mode": true,
    "source": "imessage"
  }'
```

**Expected:** `200 OK` with JSON response containing the agent's reply

Stop the backend with Ctrl+C before proceeding.

### Test 2: iMessage Service Only

With backend running in another terminal, start the iMessage service:

```bash
cd imessage-service
npm start
```

**Expected Output:**
```
=================================================
  OpenPoke iMessage Service
=================================================
Backend URL: http://localhost:8001
Poll Interval: 2000ms
Debug Mode: true
=================================================

✓ iMessage SDK initialized
✓ Starting message watcher...

✓ Watching for messages...
Press Ctrl+C to stop
```

**If you see permission errors:**
- Grant Full Disk Access to your terminal
- Restart terminal and try again

### Test 3: End-to-End Message Flow

With both services running:

1. **Send a test message** to your phone number from another device
   - Use another iPhone, iPad, or Mac signed into a different Apple ID
   - Or use a friend's phone temporarily

2. **Watch the console logs:**

   **iMessage Service Console:**
   ```
   [2025-01-06T10:30:00.000Z] New message from +1234567890
   [MessageHandler] Processing message from +1234567890
   [MessageHandler] Content: Hello
   [MessageHandler] Calling backend at http://localhost:8001/chat/send
   [MessageHandler] Backend response: Hi! How can I help you today?
   [2025-01-06T10:30:05.000Z] Sending response...
   [2025-01-06T10:30:06.000Z] ✓ Response sent
   ```

   **Backend Console:**
   ```
   INFO: chat request {"message_length": 5, "source": "imessage", "sync_mode": true}
   INFO: Processing user message through interaction agent
   INFO: Tool 'send_message_to_agent' completed
   ```

3. **Verify the response:**
   - You should receive a reply via iMessage
   - The response should be from Poke (the interaction agent)

### Test 4: Habit Tracking via iMessage

Send habit-related messages:

```
You: "I went to the gym today"
Expected: Poke acknowledges and logs the habit

You: "What are my habits?"
Expected: Poke lists your current habits

You: "I want to start meditating daily"
Expected: Poke helps you set up a new habit
```

### Test 5: Web Interface Compatibility

While iMessage bot is running, test the web interface:

1. Open http://localhost:3000
2. Send a message: "What habits am I tracking?"
3. **Expected:** Web interface works normally, shows same habits

**Verify:**
- [ ] Web chat works
- [ ] Conversation history includes messages from both web and iMessage
- [ ] Habit data is consistent across both channels

### Test 6: Error Handling

Test error scenarios:

1. **Backend Down:**
   - Stop backend server
   - Send iMessage
   - **Expected:** Bot responds with friendly error message

2. **Empty Messages:**
   - Send just spaces or emoji
   - **Expected:** Bot ignores or handles gracefully

3. **Group Chat (should ignore):**
   - Send message in a group chat
   - **Expected:** Bot logs but doesn't respond (Phase 1 limitation)

## Troubleshooting

### "Cannot connect to backend server"
**Solution:**
```bash
# Check if backend is running
curl http://localhost:8001/health

# If not, start it:
cd server && python -m uvicorn server:app --port 8001
```

### "Permission denied accessing iMessage database"
**Solution:**
1. System Settings → Privacy & Security → Full Disk Access
2. Add Terminal/IDE
3. Restart terminal/IDE
4. Try again

### "Module not found" errors (Node)
**Solution:**
```bash
cd imessage-service
rm -rf node_modules package-lock.json
npm install
npm run build
```

### "No module named 'server'" (Python)
**Solution:**
```bash
# Make sure you're in the server directory or use module syntax
cd server
python -m uvicorn server:app --port 8001

# OR from project root:
python -m server.server
```

### Bot not responding to messages
**Debug steps:**
1. Check console logs for errors
2. Verify `DEBUG=true` in `imessage-service/.env`
3. Test backend directly with curl
4. Ensure iMessage is working (send message to yourself)
5. Check that message is being received (look for log entry)

### Messages sending slowly
- Normal: Polling-based system checks every 2 seconds
- Adjust `POLL_INTERVAL` in `.env` to check more frequently (minimum: 1000ms)
- Note: Too frequent polling may impact performance

## Success Criteria

All tests pass if:
- ✅ Backend starts and responds to API calls
- ✅ iMessage service connects to backend
- ✅ Messages sent via iMessage receive responses
- ✅ Habit tracking works via iMessage
- ✅ Web interface continues to work normally
- ✅ Conversation history unified across channels
- ✅ Error handling works gracefully

## Performance Baseline

Expected response times:
- **Message detection:** 0-2 seconds (polling interval)
- **Backend processing:** 2-15 seconds (depends on LLM)
- **Message sending:** 1-2 seconds (AppleScript)
- **Total round-trip:** 3-20 seconds

If response times are significantly longer:
1. Check network connection
2. Verify Anthropic API is responding
3. Check system resources (CPU, memory)
4. Review logs for bottlenecks

## Next Steps After Testing

Once all tests pass:

1. **Regular Usage:**
   - Use `./start-imessage.sh` to start both services
   - Leave running in the background
   - Interact via iMessage or web as needed

2. **Production Considerations (Phase 2):**
   - Add multi-user support
   - Implement phone verification
   - Deploy to cloud
   - Add monitoring and logging
   - Implement rate limiting

3. **Feedback:**
   - Report issues on GitHub
   - Share feature requests
   - Contribute improvements

## Cleanup After Testing

To stop services:
```bash
# In terminals running services, press:
Ctrl+C

# Or if running via start-imessage.sh:
Ctrl+C  (stops both services)
```

To reset state for fresh testing:
```bash
# Clear conversation history
curl -X DELETE http://localhost:8001/chat/history

# Reset habits (delete database)
rm server/data/goals.db
rm server/data/triggers.db

# Clear logs
rm server/data/conversation/*.log
```

