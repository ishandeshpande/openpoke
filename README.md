# OpenPoke 🌴

OpenPoke is an open-source, multi-agent AI assistant inspired by [Interaction Company's](https://interaction.co/about) [Poke](https://poke.com/). It demonstrates how a sophisticated AI orchestration stack can feel genuinely useful through conversational interfaces, persistent execution agents, intelligent reminders, and progressive goal tracking.

## ✨ Features

### 🤖 Multi-Agent Architecture
- **Interaction Agent**: Your friendly conversational interface powered by Claude Sonnet 4, with direct habit tracking capabilities
- **Execution Agents**: Persistent background agents that handle scheduled tasks, reminders, and proactive habit check-ins

### 📅 Smart Scheduling & Reminders
- Time-based triggers with iCalendar RRULE support
- Follow-up reminders when you don't respond
- Timezone-aware scheduling
- Persistent agent roster that survives server restarts

### 🎯 Progressive Goal Tracking System
- **Smart Starting Points**: Habits begin at 40-50% of target frequency
- **Automatic Initialization**: Default habits loaded from JSON on first interaction
- **Proactive Check-ins**: Daily reminders at habit-specific times
- **Context Awareness**: Tracks life situations (sick, exams, travel) and adjusts expectations
- **Consistency Scoring**: Gamified 0-100 score rewarding consistency and growth
- **Automatic Progression**: Weekly evaluations adjust difficulty based on performance
- **Empathetic Support**: AI that understands excuses and celebrates wins
- **Fuzzy Matching**: Natural language habit tracking ("went to gym" matches "Go to gym")

### 💬 Natural Conversation Flow
- Message summarization to maintain context over long conversations
- Working memory system for recent interactions
- Conversational history maintained across sessions

### 🌐 Modern Web Interface
- Clean, responsive Next.js UI
- Real-time chat experience
- Timezone configuration
- Settings management

## 📋 Table of Contents

- [Requirements](#-requirements)
- [Quick Setup](#-quick-setup)
- [How to Use](#-how-to-use)
- [Architecture](#-architecture)
- [Goals & Habits System](#-goals--habits-system)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Development Guide](#-development-guide)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

## 🔧 Requirements

- **Python 3.10+** (Required for backend)
- **Node.js 18+** (Required for frontend)
- **npm 9+** (Package management)
- **Anthropic API Key** (For Claude AI - [Get one here](https://console.anthropic.com/))

## 🚀 Quick Setup

### 1. Clone the Repository
```bash
git clone https://github.com/shlokkhemani/OpenPoke
cd OpenPoke
```

### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Open .env and add your API key
# Replace 'your_anthropic_api_key_here' with your actual Anthropic API key
```

**Required `.env` variables:**
```env
ANTHROPIC_API_KEY=your_actual_key_here
```

**Optional configuration:**
```env
OPENPOKE_HOST=0.0.0.0
OPENPOKE_PORT=8001
OPENPOKE_CORS_ALLOW_ORIGINS=*
```

### 3. Set Up Python Backend

**Create and activate virtual environment:**
```bash
# macOS/Linux
python3.10 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Verify Python version
python --version  # Should show 3.10+
```

**Install dependencies:**
```bash
pip install -r server/requirements.txt
```

### 4. Set Up Frontend

```bash
npm install --prefix web
```

### 5. Start the Application

**Terminal 1 - Backend Server:**
```bash
python -m server.server --reload
# Server runs at http://localhost:8001
```

**Terminal 2 - Frontend (new terminal):**
```bash
npm run dev --prefix web
# Web app runs at http://localhost:3000
```

### 6. Open the App

Navigate to **[http://localhost:3000](http://localhost:3000)** in your browser and start chatting!

## 📖 How to Use

### Basic Chat Interaction

Once the app is running, you can interact naturally:

```
You: Hey, can you remind me to call mom tomorrow at 3pm?
OpenPoke: Got it! I'll remind you tomorrow at 3 PM to call mom.

You: What's the weather like in San Francisco?
OpenPoke: Let me check that for you...
```

### Automatic Habit Initialization

When you send your **first message**, OpenPoke automatically creates default habits for you:

```
You: Hey there!
OpenPoke: [Automatically creates 3 starter habits in the background]
- Cook dinner (7x/week target, starting at 3x/week)
- Go to gym (5x/week target, starting at 2x/week)  
- Get 8 hours of sleep (7x/week target, starting at 3x/week)
```

You can customize these defaults by editing `server/data/default_habits.json`.

### Setting Goals & Building Habits

OpenPoke includes a powerful goal tracking system. Simply start a conversation about habits:

```
You: I want to start going to the gym regularly
OpenPoke: That's awesome! How many times per week are you aiming for?

You: 5 times a week
OpenPoke: Great goal! I'll start you off with 2 times per week to build 
the habit gradually. I'll check in with you daily at 8 PM. Sound good?

You: Perfect!
OpenPoke: You got this! 💪
```

### Logging Progress Naturally

Just mention what you did - OpenPoke understands:

```
You: I went to the gym today!
OpenPoke: That's awesome! Great job crushing your workout! 💪 
That's 2 out of 2 this week. You're on fire!

You: Cooked dinner tonight
OpenPoke: Awesome! That's 3 nights this week. You're doing great! 🍝
```

The system uses **fuzzy matching** so "gym" matches "Go to gym", "cooked" matches "Cook dinner", etc.

### Creating Scheduled Reminders

```
You: Remind me every Monday at 9am to submit my timesheet
OpenPoke: Done! I'll remind you every Monday at 9 AM to submit your timesheet.

You: Remind me to take out the trash every Tuesday and Friday at 7pm
OpenPoke: Set! You'll get reminders on Tuesdays and Fridays at 7 PM.
```

### Managing Context for Goals

When life gets in the way, just tell OpenPoke:

```
You: I have the flu and feeling terrible
OpenPoke: Oh no! Hope you feel better soon. I'll check in on you daily to 
see how you're doing. Don't worry about your habits while you're recovering.

[A few days later]
You: Feeling much better now!
OpenPoke: That's great to hear! Ready to get back on track with your goals?
```

**Context types the system understands:**
- **Sick**: Daily check-ins, no pressure on habits
- **Exam Period**: Reduced expectations, study-time awareness
- **Travel**: Flexible check-ins, location-aware
- **Injury**: Rest-focused, alternative suggestions

### Checking Your Progress

```
You: How am I doing with my goals?
OpenPoke: You're crushing it! 🌟

Your consistency score: 76/100

Cook dinner: 3/3 this week (100%)
Go to gym: 4/5 this week (80%)
Read before bed: 5/7 this week (71%)

Keep up the momentum!
```

## 🏗 Architecture

OpenPoke uses a sophisticated multi-agent architecture where specialized AI agents handle different responsibilities:

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User (Web UI)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Server                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 Interaction Agent                     │  │
│  │  • Handles user conversations                         │  │
│  │  • Direct habit tracking (log, query, score)          │  │
│  │  • Routes tasks to execution agents                   │  │
│  │  • Manages conversation flow                          │  │
│  └─────────────┬─────────────────────────────────────────┘  │
│                │                                              │
│       ┌────────▼────────┐                                    │
│       │ Execution Agents│                                    │
│       │ • Task execution│                                    │
│       │ • Scheduled     │ (e.g., "habit-tracker" for daily   │
│       │   reminders     │       check-ins)                   │
│       │ • Habit check-  │                                    │
│       │   ins via       │                                    │
│       │   triggers      │                                    │
│       └────────┬────────┘                                    │
│                │                                              │
│  ┌─────────────▼─────────────────────────────────────────┐  │
│  │           Services & Data Layer                        │  │
│  │  • Conversation Log & Summarization                    │  │
│  │  • Trigger Scheduler                                   │  │
│  │  • Goal Database (SQLite)                              │  │
│  │  • Execution Agent Roster                              │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Agent Descriptions

#### Interaction Agent (Your Main Interface)
- **Purpose**: Conversational interface and habit tracking
- **Personality**: Witty, warm, concise (like a smart friend)
- **Responsibilities**:
  - Handle user conversations naturally
  - **Direct habit tracking** - log progress, check status, view scores
  - Route complex tasks to execution agents
  - Summarize agent results back to user
  - Maintain conversation context
- **Habit Tools** (used directly by interaction agent):
  - `log_habit_progress` - Mark habits complete/incomplete with fuzzy matching
  - `get_todays_habits` - Query today's habits and status
  - `get_consistency_score` - Get detailed score breakdown
- **Model**: Claude Sonnet 4

#### Execution Agents (Background Workers)
- **Purpose**: Handle scheduled tasks, reminders, and proactive check-ins
- **Lifecycle**: Created on-demand, persist in roster
- **Capabilities**:
  - Create/manage triggers (scheduled reminders)
  - Execute time-based tasks
  - Proactive habit check-ins (via "habit-tracker" agent)
  - Report results back to interaction agent
- **Example Agents**:
  - "habit-tracker" - Daily habit check-ins and follow-ups
  - "dish-reminder" - Reminds user about dishes
  - "workout-tracker" - Manages workout reminders
- **Habit Tools** (for scheduled check-ins):
  - `getHabitsOverview` - Fetch current habits and status
  - `logHabitProgressByName` - Log progress by habit name (fuzzy matching)
  - `logHabitProgress` - Log progress by habit ID
- **Model**: Claude Sonnet 4

### Data Flow Examples

#### Daily Check-in Flow

```
1. User: "Remind me to call mom tomorrow at 3pm"
   ↓
2. Interaction Agent receives message
   ↓
3. Interaction Agent routes to new Execution Agent "call-mom-reminder"
   ↓
4. Execution Agent creates trigger:
   - start_time: Tomorrow at 3pm
   - payload: "Remind user to call mom"
   ↓
5. Execution Agent confirms back to Interaction Agent
   ↓
6. Interaction Agent tells user: "Got it! I'll remind you..."
   ↓
7. [Tomorrow at 3pm]
   ↓
8. Trigger fires → Execution Agent wakes up
   ↓
9. Execution Agent sends message to Interaction Agent
   ↓
10. User receives: "Time to call mom!"
```

#### Habit Progress Logging Flow

```
1. User: "I went to the gym today"
   ↓
2. Interaction Agent receives message
   ↓
3. Interaction Agent calls: log_habit_progress(habit_name="gym", completed=True)
   ↓
4. Tool fuzzy-matches "gym" → "Go to gym" habit
   ↓
5. Progress logged to database
   ↓
6. Consistency score updated
   ↓
7. Agent responds: "That's awesome! Great job crushing your workout! 💪"
```

#### Scheduled Habit Check-in Flow

```
1. 8 PM: Habit check-in trigger fires
   ↓
2. Trigger Scheduler calls: execute_agent("habit-tracker", "Check gym habit...")
   ↓
3. Execution Agent ("habit-tracker") wakes up
   ↓
4. Agent calls: getHabitsOverview() to check status
   ↓
5. Agent sends result to Interaction Agent
   ↓
6. Interaction Agent relays to user: "Hey! Did you go to the gym today?"
   ↓
7. User responds: "Yes!"
   ↓
8. Interaction Agent logs: log_habit_progress(habit_name="gym", completed=True)
   ↓
9. Interaction Agent: "Awesome! That's 4 out of 5 this week!"
```

#### Weekly Progression Flow

```
1. Sunday 11 PM: Weekly progression trigger fires
   ↓
2. Execution Agent ("habit-tracker") wakes up for evaluation
   ↓
3. Progression engine queries each habit's performance:
   - Last 2 weeks of data
   - Filters out contextual days (sick, exams)
   ↓
4. For "cook dinner" habit (currently 3x/week):
   - Week 1: 3/3 completed (100%)
   - Week 2: 3/3 completed (100%)
   - Decision: Increase to 5x/week
   ↓
5. Habit updated with new frequency
   ↓
6. Execution Agent sends result to Interaction Agent
   ↓
7. Interaction Agent tells user: "You've been crushing cooking! Let's step it up to 5 nights!"
```

### Core Services

#### Conversation Service
- **Log Management**: Stores all chat messages (`server/data/conversation/`)
- **Summarization**: Compresses long histories (threshold: 100 messages)
- **Working Memory**: Maintains recent context (last 10 messages)
- **Chat Handler**: Routes messages to appropriate agents based on keywords

#### Trigger Scheduler
- **Scheduling**: Time-based trigger execution using APScheduler
- **Recurrence**: iCalendar RRULE support (daily, weekly, custom patterns)
- **Persistence**: SQLite storage (`server/data/triggers.db`), survives restarts
- **Status Management**: Active, paused, completed triggers
- **Background Execution**: Runs as async background task

#### Goals Service
- **Database**: `server/data/goals.db` with 4 tables:
  - `habits` - Habit definitions, current/target frequencies
  - `progress_log` - Daily completion records with excuses
  - `context_memory` - Life situations (sick, exams, travel)
  - `consistency_score` - User scores and history
- **Habit Manager**: CRUD operations for habits
- **Habit Loader**: Loads default habits from JSON
- **Auto-Init**: Automatically creates habits on first interaction
- **Progress Tracker**: Daily completion logging, statistics
- **Context Manager**: Life situation tracking (sick, exams, travel)
- **Progression Engine**: Weekly evaluation and difficulty adjustment
- **Consistency Scorer**: Multi-factor scoring algorithm (0-100)
- **Trigger Manager**: Habit check-ins, follow-ups, weekly evaluations

#### Execution Service
- **Roster Management**: Tracks active execution agents
- **Agent Lifecycle**: Creates, persists, and resurrects agents
- **Log Store**: Stores execution logs for debugging
- **Batch Manager**: Handles triggered agent executions

## 🎯 Goals & Habits System

OpenPoke includes a sophisticated goal tracking system designed to help users build lasting habits through progressive difficulty and intelligent support.

### Key Concepts

#### 1. Progressive Difficulty

Habits don't start at full target frequency. Instead, they begin at **40-50% of your goal**:

| Target | Starting Frequency | Percentage |
|--------|-------------------|------------|
| 7x/week | 3x/week | 43% |
| 5x/week | 2x/week | 40% |
| 3x/week | 1x/week | 33% |

This "ramp-up" approach makes habits feel achievable and builds momentum.

**Formula:**
```python
starting_frequency = max(1, int(target_frequency * 0.45))
```

#### 2. Weekly Progression

Every **2 weeks**, the system evaluates your performance:

| Success Rate | Action | Example |
|-------------|--------|---------|
| ≥80% | Increase by 2 | 3x/week → 5x/week |
| 50-80% | Maintain | 3x/week → 3x/week |
| <50% | Decrease by 1 | 3x/week → 2x/week |

**Important**: Days with active contexts (sick, exams) are excluded from evaluation.

#### 3. Context Awareness

The system understands when life gets in the way:

- **Sick**: Daily wellness check-ins, habits don't count against you
- **Exam Period**: Reduced check-in frequency, grace on missed habits
- **Travel**: Flexible expectations, location-aware suggestions
- **Injury**: Alternative habit recommendations

Each context type has:
- Dynamic check-in frequency
- Expected end date (or open-ended)
- Related habits
- Auto-resolution capability

#### 4. Consistency Score (0-100)

Your score is calculated from multiple factors:

```
Base Score: 50 points
+ Completion Rate: 0-40 points (weighted by difficulty)
+ Streak Bonus: 0-20 points (maxes at 30-day streak)
+ Progression Bonus: 0-15 points (current vs target)
+ Excuse Grace: 0-10 points (legitimate excuses)
+ Trend Modifier: -15 to +15 points (week-over-week change)
= Final Score (clamped 0-100)
```

**Detailed Formula:**
- **Base**: 50 points (everyone starts here)
- **Completion**: `(completed / current_target) * difficulty_multiplier * 40`
- **Streak**: `min(current_streak / 30 * 20, 20)`
- **Progression**: `(avg_current_freq / avg_target_freq) * 15`
- **Excuse Grace**: `(legitimate_excuses / total_excuses) * 10`
- **Trend**: `(current_week_rate - previous_week_rate) * 50` (clamped to [-15, +15])

#### 5. Automatic Initialization

When a user sends their first message, OpenPoke automatically:

1. Checks if user has any habits
2. If none, loads defaults from `server/data/default_habits.json`
3. Creates habits with progressive starting frequencies
4. Sets up daily check-in triggers
5. Creates weekly progression trigger
6. Runs in background (non-blocking)

**Default Habits** (3 included):
- Cook dinner - 7x/week target, 3x/week starting
- Go to gym - 5x/week target, 2x/week starting
- Get 8 hours of sleep - 7x/week target, 3x/week starting

#### 6. Fuzzy Habit Matching

The `log_progress_by_name` tool uses fuzzy matching:

```
"gym" → matches "Go to gym"
"dinner" → matches "Cook dinner"
"sleep" → matches "Get 8 hours of sleep"
```

**Algorithm**:
- Case-insensitive search
- Partial name matching
- Returns first match found
- Helpful error if no match (lists available habits)

### Database Schema

#### `habits` Table
```sql
CREATE TABLE habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    target_frequency INTEGER NOT NULL,  -- Times per week (1-7)
    current_frequency INTEGER NOT NULL, -- Current level
    check_in_time TEXT,                 -- HH:MM format or "anytime"
    follow_up_delay_minutes INTEGER,
    progression_start_date TEXT,        -- ISO date
    active BOOLEAN DEFAULT 1,
    created_at TEXT NOT NULL
);
```

#### `progress_log` Table
```sql
CREATE TABLE progress_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,                 -- ISO date
    completed BOOLEAN NOT NULL,
    excuse TEXT,
    excuse_category TEXT,               -- sick, busy, forgot, etc.
    conversation TEXT,                  -- Agent message + user response
    logged_at TEXT NOT NULL,
    FOREIGN KEY (habit_id) REFERENCES habits (id)
);
```

#### `context_memory` Table
```sql
CREATE TABLE context_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    context_type TEXT NOT NULL,         -- sick, exam_period, travel, injury
    description TEXT,
    start_date TEXT NOT NULL,
    expected_end_date TEXT,             -- NULL for open-ended
    check_in_frequency_days INTEGER,    -- 1=daily, 2=every 2 days, etc.
    related_habits TEXT,                -- JSON array of habit IDs
    resolved BOOLEAN DEFAULT 0,
    resolved_at TEXT,
    created_at TEXT NOT NULL
);
```

#### `consistency_score` Table
```sql
CREATE TABLE consistency_score (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    current_score REAL NOT NULL,        -- 0-100
    peak_score REAL NOT NULL,
    score_history TEXT,                 -- JSON array of historical scores
    updated_at TEXT NOT NULL
);
```

### Service Layer Architecture

#### `habit_manager.py`
- `create_habit()` - Creates habit with progressive starting frequency
- `get_habit()` - Retrieves habit by ID
- `list_habits()` - Lists all habits for user
- `update_habit()` - Updates habit properties
- `delete_habit()` - Soft deletes (sets active=False)
- `get_habits_for_check_in()` - Gets habits due for check-in

#### `habit_loader.py`
- `load_default_habits()` - Loads from JSON file
- `validate_habit()` - Validates habit structure
- Handles missing files gracefully

#### `auto_init.py`
- `auto_initialize_habits()` - Auto-creates habits on first interaction
- Uses set to track initialized users (prevents duplicates)
- Non-blocking background execution
- Logs all operations

#### `progress_tracker.py`
- `log_progress()` - Records daily completion
- `get_progress()` - Retrieves history
- `get_todays_progress()` - Gets today's status
- `calculate_statistics()` - Completion rates, streaks
- `get_current_streak()` - Active streak counting

#### `context_manager.py`
- `create_context()` - Creates life situation context
- `get_active_contexts()` - Returns unresolved contexts
- `resolve_context()` - Marks context as resolved
- `auto_resolve_expired()` - Resolves past-date contexts
- `get_context_for_date()` - Checks if date has active context

#### `progression_engine.py`
- `evaluate_habit()` - Analyzes 2-week performance
- `adjust_frequency()` - Increases/decreases/maintains
- `evaluate_all_habits()` - Weekly batch evaluation
- Filters out context days (sick, exams)
- Logs decisions and reasoning

#### `consistency_scorer.py`
- `calculate_score()` - Computes multi-factor score
- `get_score_breakdown()` - Returns detailed component values
- `update_history()` - Appends to historical record
- Weighted calculation based on habit difficulty

#### `trigger_manager.py`
- `create_habit_checkin_trigger()` - Daily reminders
- `create_follow_up_trigger()` - After no response
- `create_weekly_progression_trigger()` - Sunday 11 PM
- `create_context_refresh_trigger()` - For ongoing contexts
- Uses trigger service for scheduling

#### `onboarding.py`
- `onboard_user()` - Bulk habit creation
- Creates all triggers automatically
- Generates welcome message
- Returns comprehensive response

### API Endpoints Reference

See [API Documentation](#api-documentation) section for complete details.

### Customizing Default Habits

Edit `server/data/default_habits.json`:

```json
{
  "habits": [
    {
      "name": "Cook dinner",
      "target_frequency": 7,
      "check_in_time": "20:00",
      "description": "Home-cooked meals every night",
      "follow_up_delay_minutes": 60
    },
    {
      "name": "Go to gym",
      "target_frequency": 5,
      "check_in_time": "anytime",
      "description": "Strength training or cardio",
      "follow_up_delay_minutes": 120
    }
  ]
}
```

**Field Descriptions:**
- `name` (required): Habit name
- `target_frequency` (required): Times per week (1-7)
- `check_in_time` (required): HH:MM format or "anytime"
- `description` (optional): Detailed description
- `follow_up_delay_minutes` (optional): Default 60 minutes

See `server/data/default_habits_sample.json` for extended example with 8 habits.

## 📁 Project Structure

```
openpoke/
├── server/                          # Python FastAPI backend
│   ├── agents/                      # AI agent implementations
│   │   ├── execution_agent/         # Task & reminder agents
│   │   │   ├── agent.py             # Agent instance management
│   │   │   ├── batch_manager.py     # Handles triggered executions
│   │   │   ├── runtime.py           # Async execution loop
│   │   │   ├── system_prompt.md     # Agent personality & instructions
│   │   │   ├── tasks/               # Task implementations
│   │   │   └── tools/               # Agent tools
│   │   │       ├── habits.py        # Habit-related tools (for scheduled check-ins)
│   │   │       ├── registry.py      # Tool registry
│   │   │       └── triggers.py      # Trigger management tools
│   │   └── interaction_agent/       # User-facing conversational agent
│   │       ├── agent.py             # Agent instance
│   │       ├── runtime.py           # Chat runtime
│   │       ├── system_prompt.md     # Conversational personality
│   │       └── tools.py             # Conversation tools
│   ├── anthropic_client/            # Claude API wrapper
│   │   └── client.py                # Streaming client
│   ├── models/                      # Pydantic data models
│   │   ├── chat.py                  # Chat message models
│   │   └── meta.py                  # Metadata models
│   ├── routes/                      # FastAPI route handlers
│   │   ├── chat.py                  # /api/v1/chat/*
│   │   ├── goals.py                 # /api/v1/goals/*
│   │   └── meta.py                  # /api/v1/meta/*
│   ├── services/                    # Business logic layer
│   │   ├── conversation/            # Chat & summarization
│   │   │   ├── chat_handler.py      # Routes to agents
│   │   │   ├── log.py               # Conversation storage
│   │   │   └── summarization/       # Message compression
│   │   │       ├── prompt_builder.py
│   │   │       ├── scheduler.py
│   │   │       ├── state.py
│   │   │       ├── summarizer.py
│   │   │       └── working_memory_log.py
│   │   ├── execution/               # Execution agent management
│   │   │   ├── roster.py            # Agent registry
│   │   │   └── log_store.py         # Agent logs
│   │   ├── goals/                   # Goal tracking services
│   │   │   ├── database.py          # Database setup & singleton
│   │   │   ├── habit_manager.py     # Habit CRUD operations
│   │   │   ├── habit_loader.py      # JSON config loader
│   │   │   ├── auto_init.py         # Auto-initialization logic
│   │   │   ├── progress_tracker.py  # Progress logging & stats
│   │   │   ├── context_manager.py   # Context handling
│   │   │   ├── progression_engine.py # Weekly evaluation
│   │   │   ├── consistency_scorer.py # Score calculation
│   │   │   ├── trigger_manager.py   # Goal triggers
│   │   │   └── onboarding.py        # User onboarding
│   │   ├── triggers/                # Trigger system
│   │   │   ├── store.py             # SQLite storage
│   │   │   ├── service.py           # Trigger operations
│   │   │   ├── models.py            # Data models
│   │   │   └── utils.py             # Utilities
│   │   ├── trigger_scheduler.py     # Background scheduler
│   │   └── timezone_store.py        # User timezone storage
│   ├── utils/                       # Utility functions
│   │   ├── responses.py             # HTTP response helpers
│   │   └── timezones.py             # Timezone utilities
│   ├── data/                        # Runtime data (gitignored)
│   │   ├── conversation/            # Chat logs
│   │   │   ├── poke_conversation.log
│   │   │   └── poke_working_memory.log
│   │   ├── execution_agents/        # Agent logs & roster
│   │   │   └── roster.json
│   │   ├── goals.db                 # Goals database
│   │   ├── triggers.db              # Triggers database
│   │   ├── default_habits.json      # Active habit config
│   │   ├── default_habits_sample.json # Example config
│   │   ├── HABITS_README.md         # Config documentation
│   │   └── timezone.txt             # User timezone
│   ├── config.py                    # Configuration management
│   ├── logging_config.py            # Logging setup
│   ├── app.py                       # FastAPI app setup
│   ├── server.py                    # Server entry point
│   ├── requirements.txt             # Python dependencies
│   └── verify_habits.py             # System verification script
│
├── web/                             # Next.js frontend
│   ├── app/                         # Next.js app directory
│   │   ├── api/                     # API route handlers
│   │   │   ├── chat/                # Chat API proxy
│   │   │   │   ├── route.ts         # POST /api/chat
│   │   │   │   └── history/         
│   │   │   │       └── route.ts     # GET /api/chat/history
│   │   │   └── timezone/            # Timezone API proxy
│   │   │       └── route.ts
│   │   ├── globals.css              # Global styles
│   │   ├── layout.tsx               # Root layout
│   │   └── page.tsx                 # Home page (chat interface)
│   ├── components/                  # React components
│   │   ├── chat/                    # Chat UI components
│   │   │   ├── ChatHeader.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatMessages.tsx
│   │   │   ├── ErrorBanner.tsx
│   │   │   ├── types.ts
│   │   │   └── useAutoScroll.ts
│   │   └── SettingsModal.tsx        # Settings UI
│   ├── package.json                 # Node dependencies
│   ├── postcss.config.js            # PostCSS config
│   ├── tailwind.config.ts           # Tailwind CSS config
│   └── tsconfig.json                # TypeScript config
│
├── .env                             # Environment variables (create this!)
├── .env.example                     # Example env file
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
└── LICENSE                          # MIT License
```

## 🔌 API Documentation

### Base URL
```
http://localhost:8001/api/v1
```

### Chat Endpoints

#### `POST /chat/send`
Send a message to OpenPoke.

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Remind me to call mom tomorrow at 3pm"
    }
  ]
}
```

**Response:** `202 Accepted` (async processing)

#### `GET /chat/history`
Get conversation history.

**Response:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "...",
      "timestamp": "2025-11-03T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "...",
      "timestamp": "2025-11-03T10:30:05Z"
    }
  ]
}
```

### Goals Endpoints

#### `POST /goals/onboarding`
Onboard user with multiple goals. Goals are optional - if not provided, defaults from JSON are loaded.

**Request:**
```json
{
  "user_id": "user123",
  "goals": [  // Optional
    {
      "name": "Cook dinner",
      "target_frequency": 7,
      "check_in_time": "20:00",
      "description": "Home-cooked meals"
    }
  ]
}
```

**Response:**
```json
{
  "user_id": "user123",
  "habits_created": 3,
  "habits": [
    {
      "id": 1,
      "name": "Cook dinner",
      "target_frequency": 7,
      "current_frequency": 3,
      "check_in_time": "20:00",
      "progression_start_date": "2025-11-03"
    }
  ],
  "triggers": [
    {"habit_id": 1, "trigger_id": "abc", "type": "HABIT_CHECKIN"},
    {"habit_id": null, "trigger_id": "xyz", "type": "WEEKLY_PROGRESSION"}
  ],
  "onboarding_message": "Welcome! I'm excited to help you build these habits! 🌟\n..."
}
```

#### `POST /goals/habits`
Create a single habit.

**Request:**
```json
{
  "user_id": "user123",
  "name": "Read for 30 minutes",
  "target_frequency": 7,
  "check_in_time": "21:00",
  "description": "Daily reading habit"
}
```

#### `GET /goals/habits`
List all habits for a user.

**Query Parameters:**
- `user_id` (required): User identifier
- `active_only` (optional): Filter to active habits only

**Response:**
```json
{
  "habits": [
    {
      "id": 1,
      "name": "Cook dinner",
      "target_frequency": 7,
      "current_frequency": 3,
      "active": true,
      "check_in_time": "20:00",
      "progression_start_date": "2025-11-03"
    }
  ]
}
```

#### `GET /goals/habits/{id}`
Get specific habit details.

**Query Parameters:**
- `user_id` (required)

#### `PUT /goals/habits/{id}`
Update a habit.

**Request:**
```json
{
  "user_id": "user123",
  "name": "Cook healthy dinner",
  "description": "Focus on vegetables and lean protein",
  "target_frequency": 5,
  "check_in_time": "19:00"
}
```

#### `DELETE /goals/habits/{id}`
Delete (deactivate) a habit.

**Query Parameters:**
- `user_id` (required)

#### `GET /goals/progress`
Get habit progress history.

**Query Parameters:**
- `habit_id` (required): Habit ID
- `days` (optional): Number of days to retrieve (default: 7)
- `user_id` (required)

**Response:**
```json
{
  "progress": [
    {
      "date": "2025-11-03",
      "completed": true,
      "excuse": null,
      "logged_at": "2025-11-03T20:15:00Z"
    }
  ],
  "stats": {
    "completion_rate": 0.85,
    "current_streak": 5,
    "total_completed": 6,
    "total_days": 7
  }
}
```

#### `GET /goals/progress/today`
Get today's progress for all habits.

**Query Parameters:**
- `user_id` (required)

**Response:**
```json
{
  "date": "2025-11-03",
  "progress": [
    {
      "habit_id": 1,
      "habit_name": "Cook dinner",
      "completed": true
    },
    {
      "habit_id": 2,
      "habit_name": "Go to gym",
      "completed": null
    }
  ]
}
```

#### `GET /goals/consistency`
Get consistency score.

**Query Parameters:**
- `user_id` (required)

**Response:**
```json
{
  "user_id": "user123",
  "current_score": 76.5,
  "peak_score": 82.0,
  "updated_at": "2025-11-03T20:00:00Z",
  "score_history": [
    {"date": "2025-11-01", "score": 75.0},
    {"date": "2025-11-02", "score": 76.0}
  ]
}
```

#### `GET /goals/consistency/breakdown`
Get detailed score breakdown.

**Query Parameters:**
- `user_id` (required)

**Response:**
```json
{
  "current_score": 76.5,
  "peak_score": 82.0,
  "components": {
    "base": 50.0,
    "completion": 30.5,
    "streak": 12.0,
    "progression": 8.5,
    "excuse_grace": 5.0,
    "trend": 10.5
  },
  "updated_at": "2025-11-03T20:00:00Z"
}
```

#### `POST /goals/context`
Create context memory (sick, exams, etc.).

**Request:**
```json
{
  "user_id": "user123",
  "context_type": "sick",
  "description": "Has the flu",
  "expected_end_date": null,
  "related_habits": [1, 2, 3]
}
```

**Context Types:**
- `sick` - Illness or health issues
- `exam_period` - Exams or high-stress study time
- `travel` - Away from home
- `injury` - Physical injury affecting habits

#### `GET /goals/context/active`
Get active contexts.

**Query Parameters:**
- `user_id` (required)

**Response:**
```json
{
  "contexts": [
    {
      "id": 1,
      "context_type": "sick",
      "description": "Has the flu",
      "start_date": "2025-11-03",
      "expected_end_date": null,
      "check_in_frequency_days": 1,
      "related_habits": [1, 2, 3],
      "resolved": false
    }
  ]
}
```

#### `PUT /goals/context/{id}/resolve`
Resolve a context.

**Query Parameters:**
- `user_id` (required)

#### `GET /goals/progression/{habit_id}`
Get progression status for a habit.

**Query Parameters:**
- `user_id` (required)

**Response:**
```json
{
  "habit_id": 1,
  "habit_name": "Cook dinner",
  "current_frequency": 3,
  "target_frequency": 7,
  "weeks_at_current_level": 1,
  "success_rate": 0.85,
  "progress_percentage": 42.86,
  "ready_for_evaluation": false
}
```

#### `POST /goals/progression/evaluate`
Manually trigger weekly progression evaluation.

**Query Parameters:**
- `user_id` (required)

**Response:**
```json
{
  "results": {
    "1": "Increased from 3 to 5 times per week (success rate: 90%)",
    "2": "Maintained at 2 times per week (success rate: 65%)",
    "3": "Only 1 week(s) at current level, need 2"
  }
}
```

### Meta Endpoints

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "ok": true,
  "service": "openpoke",
  "version": "0.3.0"
}
```

#### `GET /timezone`
Get user's timezone.

**Response:**
```json
{
  "timezone": "America/Los_Angeles"
}
```

#### `POST /timezone`
Set user's timezone.

**Request:**
```json
{
  "timezone": "America/New_York"
}
```

### Interactive API Documentation

When the server is running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 👨‍💻 Development Guide

### Running in Development Mode

**Backend with auto-reload:**
```bash
python -m server.server --reload
```

**Frontend with hot-reload:**
```bash
npm run dev --prefix web
```

### Environment Variables

**Backend (Python):**
- `ANTHROPIC_API_KEY` - Required for Claude AI
- `OPENPOKE_HOST` - Server host (default: 0.0.0.0)
- `OPENPOKE_PORT` - Server port (default: 8001)
- `OPENPOKE_CORS_ALLOW_ORIGINS` - CORS origins (default: *)
- `OPENPOKE_ENABLE_DOCS` - Enable /docs endpoint (default: 1)

**Frontend (Next.js):**
- Automatically proxies to backend
- No separate config needed

### Database Management

**Goals Database:**
```bash
# Location
server/data/goals.db

# View with SQLite CLI
sqlite3 server/data/goals.db
.tables
.schema habits
SELECT * FROM habits;
SELECT * FROM progress_log;
.quit
```

**Triggers Database:**
```bash
# Location
server/data/triggers.db

# View triggers
sqlite3 server/data/triggers.db
SELECT * FROM triggers;
.quit
```

**Reset Databases:**
```bash
# Caution: Deletes all data
rm server/data/goals.db server/data/triggers.db*
# Will be recreated on next startup
```

### Adding a New Agent Tool

1. **Define tool in agent's tools.py:**
```python
def my_new_tool(param1: str, param2: int) -> dict:
    """
    Tool description for Claude.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        {"success": bool, "result": any}
    """
    try:
        # Implementation
        return {"success": True, "result": "success"}
    except Exception as e:
        logger.error(f"Error in my_new_tool: {e}")
        return {"success": False, "error": str(e)}
```

2. **Add to tools list:**
```python
MY_TOOLS = [
    # ... existing tools
    {
        "name": "my_new_tool",
        "description": "Tool description for Claude",
        "input_schema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."},
                "param2": {"type": "integer", "description": "..."}
            },
            "required": ["param1", "param2"]
        }
    }
]
```

3. **Add to function registry:**
```python
TOOL_FUNCTIONS = {
    # ... existing functions
    "my_new_tool": my_new_tool,
}
```

4. **Update system prompt** to explain when to use the tool

### Customizing Agent Personality

Edit the system prompt files:

- `server/agents/interaction_agent/system_prompt.md` - User-facing personality and habit tracking behavior
- `server/agents/execution_agent/system_prompt.md` - Task execution and scheduled check-in behavior

**Tips:**
- Use clear, conversational language
- Provide concrete examples
- Specify tone and style preferences
- Include edge cases to handle

### Logging

Logs are configured in `server/logging_config.py`:

```python
# Current level: INFO
# To enable DEBUG logging:
# Edit logging_config.py and change level to DEBUG

# Log locations:
# - Console output
# - Can be configured to write to files
```

**Useful log messages to watch:**
- `"Goals database initialized"` - Database ready
- `"Auto-initializing habits"` - First-time setup
- `"Goals agent calling tool: X"` - Tool execution
- `"Trigger scheduler started"` - Background scheduler active

### Customizing Default Habits

Edit `server/data/default_habits.json`:

```json
{
  "habits": [
    {
      "name": "Your habit name",
      "target_frequency": 5,
      "check_in_time": "18:00",
      "description": "Detailed description",
      "follow_up_delay_minutes": 60
    }
  ]
}
```

**Validation Rules:**
- `name`: Required, non-empty string
- `target_frequency`: Required, integer 1-7
- `check_in_time`: Required, HH:MM format or "anytime"
- `description`: Optional, string
- `follow_up_delay_minutes`: Optional, integer (default 60)

### Verification Script

Run the verification script to check system integrity:

```bash
cd server
python verify_habits.py
```

**Checks:**
- Database connectivity
- Habit loader functionality
- Progress tracker
- Tool availability
- Service initialization

## 🧪 Testing

### Manual Testing with cURL

**Quick health check:**
```bash
curl http://localhost:8001/api/v1/health
```

**Test chat:**
```bash
curl -X POST http://localhost:8001/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

**Test goals onboarding:**
```bash
curl -X POST http://localhost:8001/api/v1/goals/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "goals": [
      {
        "name": "Test habit",
        "target_frequency": 7,
        "check_in_time": "20:00"
      }
    ]
  }'
```

**List habits:**
```bash
curl "http://localhost:8001/api/v1/goals/habits?user_id=test_user"
```

**Get consistency score:**
```bash
curl "http://localhost:8001/api/v1/goals/consistency?user_id=test_user"
```

**Create context:**
```bash
curl -X POST http://localhost:8001/api/v1/goals/context \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "context_type": "sick",
    "description": "Has the flu",
    "related_habits": [1, 2, 3]
  }'
```

### Testing Auto-Initialization

1. **Clear database** (for fresh test):
```bash
rm server/data/goals.db server/data/triggers.db*
```

2. **Start server**:
```bash
python -m server.server
```

3. **Check startup logs**:
```
Should see: "Goals database initialized"
```

4. **Open frontend**:
```bash
# In another terminal
npm run dev --prefix web
# Open http://localhost:3000
```

5. **Send first message**: "hello"

6. **Check auto-init logs**:
```
Should see:
- "Auto-initializing habits for user default_user"
- "Successfully auto-initialized 3 habits for user default_user"
```

7. **Verify habits created**:
```bash
curl http://localhost:8001/api/v1/goals/habits?user_id=default_user
```

### Testing Habit Progress Logging

1. **Via chat interface**:
```
You: "I went to the gym today!"
```

2. **Check logs**:
```
Should see:
- "Routing to goals agent"
- "Goals agent calling tool: log_progress_by_name"
- "Tool log_progress_by_name executed successfully"
```

3. **Verify progress**:
```bash
curl "http://localhost:8001/api/v1/goals/progress/today?user_id=default_user"
```

### Testing Trigger System

**Create a trigger that fires soon:**
```bash
curl -X POST http://localhost:8001/api/v1/goals/habits \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test immediate habit",
    "target_frequency": 5,
    "check_in_time": "23:59",
    "user_id": "test_user"
  }'
```

**Monitor server logs** for trigger creation and firing.

### Testing Progression System

**Manually trigger evaluation:**
```bash
curl -X POST "http://localhost:8001/api/v1/goals/progression/evaluate?user_id=test_user"
```

**Expected response** (before 2 weeks):
```json
{
  "results": {
    "1": "Only 0 week(s) at current level, need 2",
    "2": "Only 0 week(s) at current level, need 2"
  }
}
```

### Testing Context Awareness

1. **Create sick context**:
```bash
curl -X POST http://localhost:8001/api/v1/goals/context \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "context_type": "sick",
    "description": "Has the flu"
  }'
```

2. **Verify context excludes days from progression**:
```bash
curl -X POST "http://localhost:8001/api/v1/goals/progression/evaluate?user_id=test_user"
```

3. **Resolve context**:
```bash
curl -X PUT "http://localhost:8001/api/v1/goals/context/1/resolve?user_id=test_user"
```

## 🔧 Troubleshooting

### Common Issues & Solutions

#### Issue: Anthropic API Errors
**Symptoms**: "API key invalid" or "Rate limit exceeded"

**Solutions**:
- Verify `ANTHROPIC_API_KEY` in `.env`
- Check API key has credits at console.anthropic.com
- Ensure no spaces/quotes around the key
- Check for rate limits if making many requests

#### Issue: "Can't log your gym session properly"
**Symptoms**: Agent can't log habit progress

**Solutions**:
- Check that habits exist: `curl http://localhost:8001/api/v1/goals/habits`
- Verify auto-initialization ran (check logs)
- Try mentioning exact habit name
- Check server logs for specific error message

#### Issue: Database Locked Errors
**Symptoms**: "database is locked" errors in logs

**Solutions**:
- SQLite WAL mode is enabled (reduces locking)
- If persistent, delete and recreate databases:
  ```bash
  rm server/data/goals.db server/data/triggers.db*
  ```
- Check file permissions on `server/data/`
- For production, consider PostgreSQL

#### Issue: Triggers Not Firing
**Symptoms**: No check-in messages at scheduled times

**Solutions**:
- Check server logs for scheduler startup
- Verify timezone is correct: `GET /api/v1/timezone`
- Ensure trigger status is "active" in database:
  ```bash
  sqlite3 server/data/triggers.db "SELECT * FROM triggers;"
  ```
- Check that server is running continuously

#### Issue: Port Already in Use
**Symptoms**: "Address already in use" when starting server

**Solutions**:
- Change port in `.env`: `OPENPOKE_PORT=8002`
- Or kill existing process:
  ```bash
  # Find process
  lsof -ti:8001
  
  # Kill it
  kill -9 $(lsof -ti:8001)
  ```

#### Issue: Frontend Can't Reach Backend
**Symptoms**: Chat messages don't send, network errors

**Solutions**:
- Verify backend is running on port 8001
- Check CORS settings in `server/config.py`
- Ensure no firewall blocking localhost
- Check browser console for specific errors
- Verify API proxy in Next.js is configured correctly

#### Issue: Auto-Initialization Not Running
**Symptoms**: No habits created on first message

**Solutions**:
- Check logs for "Auto-initializing habits"
- Verify `default_habits.json` exists and is valid
- Check that goals database initialized: "Goals database initialized"
- Try manually calling onboarding endpoint

#### Issue: Habits Not Progressing
**Symptoms**: Habits stay at same frequency after 2 weeks

**Solutions**:
- Verify weekly progression trigger exists
- Check that 2 weeks have passed since `progression_start_date`
- Ensure sufficient progress data logged
- Manually trigger evaluation:
  ```bash
  curl -X POST "http://localhost:8001/api/v1/goals/progression/evaluate?user_id=default_user"
  ```

#### Issue: Consistency Score Not Updating
**Symptoms**: Score stays at 50 or doesn't change

**Solutions**:
- Ensure progress is being logged
- Check that habits exist and are active
- View score breakdown for details:
  ```bash
  curl "http://localhost:8001/api/v1/goals/consistency/breakdown?user_id=default_user"
  ```
- Check logs for scoring errors

### Debugging Tips

**Enable Detailed Logging:**
Edit `server/logging_config.py` and change level to `DEBUG`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    # ...
)
```

**Check Database State:**
```bash
# Goals database
sqlite3 server/data/goals.db

# View tables
.tables

# Check habits
SELECT * FROM habits;

# Check progress
SELECT * FROM progress_log ORDER BY date DESC LIMIT 10;

# Check contexts
SELECT * FROM context_memory WHERE resolved = 0;

# Check scores
SELECT * FROM consistency_score;

.quit
```

**Monitor Logs in Real-Time:**
```bash
# Run server with output piped to file
python -m server.server 2>&1 | tee server.log

# In another terminal, watch logs
tail -f server.log
```

**Test Individual Components:**
```bash
# Test habit loader
python -c "from server.services.goals import load_default_habits; print(load_default_habits())"

# Test database
python -c "from server.services.goals import get_goals_database; db = get_goals_database(); print('DB OK')"

# Run verification script
cd server
python verify_habits.py
```

### Performance Considerations

- **Database Indexing**: Indexes on `user_id`, `habit_id`, `date` columns
- **WAL Mode**: SQLite Write-Ahead Logging enabled for better concurrency
- **Connection Pooling**: Thread-safe singleton patterns
- **Async Operations**: All agent executions are async
- **Message Summarization**: Triggers after 100 messages to maintain context

### When to Use PostgreSQL

Consider migrating to PostgreSQL for:
- Multiple concurrent users
- High write frequency (many habit logs)
- Production deployment
- Advanced querying needs
- Better concurrent access

The service layer abstracts database access, making migration straightforward.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- **Mobile App**: iOS/Android clients using the REST API
- **Additional Agent Tools**: Email, calendar, web search, etc.
- **Voice Interface**: Voice input/output for hands-free use
- **Social Features**: Friend challenges, leaderboards
- **Analytics Dashboard**: Visualize progress over time
- **Integration Tests**: Automated test suite
- **Docker Support**: Containerized deployment
- **Multi-user Auth**: User authentication and isolation
- **Habit Templates**: Community-shared habit configurations

## 🗺️ Roadmap

- [ ] Multi-user support with authentication
- [ ] PostgreSQL backend for production
- [ ] Habit insights and pattern recognition
- [ ] Wearable device integration (Apple Watch, Fitbit)
- [ ] Smart scheduling based on user patterns
- [ ] Voice-based check-ins
- [ ] Social sharing and challenges
- [ ] Mobile apps (iOS/Android)
- [ ] Habit templates marketplace
- [ ] Advanced analytics dashboard
- [ ] Integration with calendars (Google Calendar, Apple Calendar)
- [ ] Email/SMS notifications
- [ ] Webhook support for external integrations

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

OpenPoke is an open-source project inspired by [Poke](https://poke.com/) by [The Interaction Company](https://interaction.co/). This is an independent implementation for educational and demonstration purposes.

## 🙏 Acknowledgments

- **Anthropic** for Claude AI and the amazing Sonnet 4 model
- **The Interaction Company** for the inspiration behind Poke
- **FastAPI** for the excellent Python web framework
- **Next.js** for the modern React framework
- **APScheduler** for reliable background job scheduling
- **SQLite** for the embedded database

---

**Built with ❤️ by the OpenPoke community**

Questions? Issues? Check the docs above or [open an issue](https://github.com/shlokkhemani/OpenPoke/issues)!
