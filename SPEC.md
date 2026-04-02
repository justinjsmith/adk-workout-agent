# Swim Workout Agent — Product Spec

## Project Overview

A Google ADK agent that monitors Gmail for swim workout emails from Coach Michael Soderlund, comprehends the loose-format workout descriptions, converts them to a structured schema, and serves them through a web UI where swimmers can view and print workouts. The agent improves its comprehension over time through human feedback and accumulated convention knowledge.

**Repo:** `justinjsmith/adk-workout-agent` (GitHub, private)

**Primary goal:** Learn what it's like to build an agent using Google ADK.

**Team:** Stingrays masters swim group. 6 lanes (L1 slowest, L6 fastest). ~90 swimmers on the email list, 5-10 active users of the web app.

---

## Domain: Coach Michael's Workout Emails

### Email Patterns

- **Sender:** `michael.Soderlund@graphicpkg.com`
- **Cadence:** 3 workouts per week, typically Mon/Wed/Fri (schedule varies — coach specifies in email body)
- **Threading:** Usually one thread per week (`RE: Practices Week of X/XX/XX`), each reply adds the next day's workout. Threading is not guaranteed — sometimes workouts arrive as separate emails.
- **Content:** Plain text in email body. Each email may contain:
  - Practice schedule (times, location)
  - One or more day-labeled workouts
  - Lane-specific intervals (L1-L6)
  - Equipment transitions
  - Named-swimmer variant workouts (e.g., "Patricia/Will/Dustin" Friday distance set)

### Workout Types by Day

| Day | Type | Character |
|---|---|---|
| Monday (typically) | Aerobic | Longer intervals, moderate effort, endurance-focused |
| Wednesday (typically) | Aerobic Threshold | Pace-based sets, descending rest, sustained effort |
| Friday (typically) | Sprint | Heats, fast swims, short rest, race-pace work |
| Friday (Patricia variant) | Distance | Pace Finder sets, longer sustained swims — named "Friday Patricia" |

The schedule can shift (e.g., holidays move Mon to Tue, Fri to Thu). The coach always specifies the actual schedule in the email.

### Coach's Notation — Key Abbreviations

These are the known abbreviations from observed emails. The agent must learn new ones as they appear.

| Abbreviation | Meaning | Category |
|---|---|---|
| Sw | Swim | Stroke type |
| K | Kick | Stroke type |
| P | Pull | Stroke type |
| Ch | Choice (swimmer picks stroke) | Stroke modifier |
| Fr | Freestyle | Stroke |
| IM | Individual Medley | Stroke |
| ST | Stroke (non-free) | Stroke |
| Fins | Fins (equipment) | Equipment |
| Pad / Pads | Paddles | Equipment |
| B / Buoy | Pull buoy | Equipment |
| LB | Lungbuster | Breathing Pattern |
| TX | Texas Kick | Drill modifier |
| R:10 | Rest 10 seconds | Rest |
| @50-1:10 | Interval range across lanes (fastest to slowest) | Interval |
| O: / E: | Odd / Even (alternating pattern) | Set instruction |
| AR | Active Rest | Rest type |
| Mid 50 | Middle 50 of the repeat | Set instruction |
| Speed Play | Alternating fast/easy within the repeat | Set instruction |
| Build | Increase effort/speed across the repeat | Set instruction |
| LT / Long Turns | Longer turns (streamline off the wall) | Instruction |

### Structural Patterns in Emails

1. **Section headers:** `Warm Up:`, `Warm-Up`, `Main Set`, `Sw Set`, `Equipment Set`, `Warm Down`, `Fins On`, `Fins Off, Pads & Buoy On`
2. **Repeat notation:** `4x75` = 4 repeats of 75 yards. `2x` on its own line = repeat the following block twice.
3. **Lane intervals:** When 6 values appear on consecutive lines after a set, they map to L6/L5/L4/L3/L2/L1 (fastest lane first).
4. **Interval formats:**
   - Flat: `45` (seconds), `1:20` (minutes:seconds)
   - Range: `@1:30-2:00` (L6 gets 1:30, L1 gets 2:00, others interpolated)
   - Split: `20/60` = go on :20, extra rest to :60
5. **Lane-specific rep counts:** `All 6 sets / All 6 sets / 5 sets / 5 sets / 4 sets / 3 sets` — faster lanes do more.
6. **Named-swimmer sections:** A line like `Patricia/Will/Dustin` followed by a different workout block. Parse as "Friday Patricia" variant.
7. **Equipment transitions:** `Fins On`, `Fins Off, Pads & Buoy On`, `Pads & Buoy Off` mark mid-workout equipment changes.
8. **Start times:** `Start by 6:00` or `Start 5:30 AM` — indicates a timing gate within the workout.

---

## System Architecture

### Google Cloud Services

| Service | Purpose | Why this one |
|---|---|---|
| **Cloud Run** | Host the agent + web app | Scales to zero, pay-per-use, simple container deployment. Good for <$50/mo budget. |
| **Firestore** | Store workouts, conventions, feedback, user prefs | Serverless NoSQL, generous free tier (1 GiB storage, 50K reads/day), works well with unstructured workout data. |
| **Cloud Scheduler** | Trigger email polling on a cron | Triggers the agent to check Gmail every N minutes. 3 free jobs/month. |
| **Pub/Sub** | Decouple email detection from processing | Agent publishes "new email found" events; processing subscribes. Allows retry, dead-letter. Free tier: 10 GB/month. |
| **Secret Manager** | Store Gmail OAuth tokens, API keys | Secure credential storage. 6 active secret versions free. |
| **Artifact Registry** | Store container images | For Cloud Run deployments. 500 MB free. |
| **Cloud Build** | CI/CD from GitHub | Triggered on push to main. 120 free build-minutes/day. |
| **Vertex AI** | *Not used — using Anthropic models via LiteLLM instead* | — |

### Estimated Monthly Cost

| Service | Estimate |
|---|---|
| Cloud Run | ~$2-5 (scales to zero between requests) |
| Firestore | ~$0 (well within free tier for this volume) |
| Anthropic API (Haiku + Sonnet) | ~$1-2 (see LLM cost breakdown below) |
| Cloud Scheduler | $0 (3 free jobs) |
| Pub/Sub | $0 (free tier) |
| Secret Manager | $0 (free tier) |
| Cloud Build | $0 (free tier) |
| **Total** | **~$3-10/month** |

### High-Level Flow

```
Gmail Inbox
    |
    v
Cloud Scheduler (every 15 min)
    |
    v
Agent: Email Monitor (Cloud Run)
    |  - Query Gmail API for new emails from coach
    |  - Detect new workout content (dedup against Firestore)
    |  - Publish "new workout email" to Pub/Sub
    v
Agent: Workout Parser (Cloud Run, triggered by Pub/Sub)
    |  - Extract workout text from email body (strip reply chains)
    |  - Load conventions doc + few-shot examples from Firestore
    |  - Call Anthropic models (via ADK + LiteLLM) to parse workout into structured schema
    |  - Validate: structural checks + consistency with past workouts
    |  - Flag unknowns (new abbreviations, unusual patterns)
    |  - Store parsed workout in Firestore (status: "pending_review")
    |  - If validation issues: mark for review with details
    v
Firestore
    |  workouts/{id}       — parsed workout JSON
    |  conventions/        — abbreviation mappings, structural rules
    |  examples/           — corrected few-shot examples
    |  feedback/{id}       — human corrections
    v
Web App (Cloud Run)
    |  - List workouts by week/day
    |  - View workout filtered by lane (or full grid)
    |  - Print-friendly layout
    |  - Review & correct parsed workouts (feedback loop)
    v
Swimmer's Browser / Printer
```

---

## Agent Design (Google ADK)

### Agent 1: Email Monitor

**Trigger:** Cloud Scheduler cron (every 15 minutes during 6 PM - 10 PM ET, when coach typically sends emails, and 5 AM - 6 AM ET before morning practice).

**Responsibilities:**
1. Authenticate to Gmail API using stored OAuth credentials
2. Query for new messages from `michael.Soderlund@graphicpkg.com` since last check
3. For each new message:
   - Extract plain-text body
   - Strip quoted reply chains (everything after `From: Soderlund, Michael\nSent:`)
   - Detect workout content vs. schedule-only or logistics emails
   - Deduplicate against already-processed messages (store Gmail message IDs in Firestore)
4. Publish workout text + metadata to Pub/Sub topic

**Not an ADK agent** — this is a straightforward Cloud Function / Cloud Run service. No LLM needed for email detection and extraction.

### Agent 2: Workout Parser (ADK Agent)

This is the core ADK agent. It uses Gemini to comprehend the loose-format workout text and produce structured output.

**Input:** Raw workout text + metadata (date, day of week, subject line)

**Tools available to the agent (ADK tool definitions):**

| Tool | Purpose |
|---|---|
| `load_conventions` | Fetch the current conventions document from Firestore |
| `load_examples` | Fetch relevant few-shot examples (filtered by workout type: aerobic/threshold/sprint) |
| `validate_workout` | Run structural validation on a parsed workout |
| `check_consistency` | Compare parsed workout against patterns from recent workouts |
| `flag_unknown` | Mark an abbreviation or pattern as unknown, requesting human clarification |
| `store_workout` | Save the parsed workout to Firestore |
| `lookup_abbreviation` | Check if an abbreviation is in the conventions doc |

**Agent flow (multi-step reasoning):**

1. **Load context:** Call `load_conventions` and `load_examples` to get current knowledge base.
2. **First pass — structure extraction:** Identify sections (warmup, main set, equipment set, warmdown), named-swimmer variants, equipment transitions, lane intervals.
3. **Second pass — detail parsing:** For each section, parse individual sets: repeat count, distance, stroke, interval/rest, equipment, lane-specific values, instructions.
4. **Third pass — validation:**
   - Call `validate_workout` — checks structural completeness (has warmup? distances reasonable? intervals make sense for the stroke/distance?)
   - Call `check_consistency` — compares against recent workouts of the same type. Flags if, e.g., a "sprint" workout has no fast swims, or total yardage is way off from typical.
5. **Flag unknowns:** If any abbreviation or pattern wasn't resolved, call `flag_unknown` with the raw text and context.
6. **Store:** Call `store_workout` with the structured result and a confidence score.

### Agent 3: Learning Agent (ADK Agent, triggered by human feedback)

When a user corrects a parsed workout through the web UI, this agent processes the feedback:

1. **Diff analysis:** Compare the user's correction against the agent's parse. Identify what changed.
2. **Convention extraction:** If the correction reveals a new abbreviation or pattern rule, propose an update to the conventions document.
3. **Example curation:** Store the corrected workout as a few-shot example, tagged by workout type and the specific pattern it demonstrates.
4. **Convention update:** After human approval, update the conventions doc in Firestore.

---

## LLM Strategy: Anthropic Models via LiteLLM

Google ADK supports non-Google models via LiteLLM. This project uses Anthropic models for all LLM tasks, choosing the cheapest model that can handle each task reliably.

### Model Assignment

| Task | Model | Why | Input Tokens | Output Tokens | Cost/Call |
|---|---|---|---|---|---|
| **Email Triage** (workout or logistics?) | Haiku 4.5 | Simple classification, no reasoning needed | ~500 | ~50 | $0.0006 |
| **Email Cleanup** (strip reply chains) | Haiku 4.5 | Structural extraction, not semantic | ~2,000 | ~1,000 | $0.006 |
| **Workout Parser** (core comprehension) | Sonnet 4.6 | Complex: ambiguous notation, lane grids, equipment transitions | ~8,000 | ~3,000 | $0.069 |
| **Validation Sanity Check** | Haiku 4.5 | "Does this make sense as a workout?" | ~4,000 | ~500 | $0.005 |
| **Learning Agent** (diff analysis, convention extraction) | Sonnet 4.6 | Needs reasoning about *why* a parse was wrong | ~6,000 | ~2,000 | $0.048 |

### Monthly Cost at Steady State

- 12 workouts/month x ~$0.08 = **~$0.96/month**
- 2-4 corrections/month x ~$0.05 = **~$0.15/month**
- **Total LLM spend: ~$1.10/month**

### One-Time Historical Backfill

- ~150 historical emails x $0.08 = **~$12 one-time**

### ADK Configuration

```python
from google.adk import Agent

# Workout parser — needs strong reasoning
parser_agent = Agent(
    model="litellm/anthropic/claude-sonnet-4-6",
    ...
)

# Triage — cheap and fast
triage_agent = Agent(
    model="litellm/anthropic/claude-haiku-4-5-20251001",
    ...
)
```

### When to Escalate to Opus

Opus ($15/MTok input, $75/MTok output) is reserved for:
- One-off bootstrapping tasks (e.g., analyzing the full email corpus to seed conventions)
- Debugging persistent parsing failures that Sonnet can't resolve
- Never used in the automated pipeline

---

## Workout Schema

The stored format uses canonical full-form names internally but preserves the original shorthand for display.

```json
{
  "id": "auto-generated",
  "emailMessageId": "gmail-message-id",
  "emailThreadId": "gmail-thread-id",
  "weekOf": "2026-03-30",
  "dayOfWeek": "thursday",
  "date": "2026-04-02",
  "workoutType": "sprint",
  "practiceTime": "5:30-7:00 AM",
  "location": "MVAC",
  "variant": null,

  "status": "pending_review",
  "confidence": 0.87,
  "flags": [
    { "type": "unknown_abbreviation", "text": "TX", "context": "50K+50Sw TX" }
  ],

  "sections": [
    {
      "name": "Warm Up",
      "sets": [
        {
          "repeats": 1,
          "distance": 400,
          "distanceDisplay": "300-400",
          "stroke": "Choice",
          "strokeShort": "Ch",
          "equipment": [],
          "interval": null,
          "rest": null,
          "instruction": null,
          "laneIntervals": null
        },
        {
          "repeats": 4,
          "distance": 75,
          "distanceDisplay": "4x75",
          "stroke": "Kick",
          "strokeShort": "K",
          "equipment": [],
          "interval": null,
          "rest": { "type": "rest", "seconds": 10 },
          "instruction": null,
          "laneIntervals": null
        },
        {
          "repeats": 8,
          "distance": 50,
          "distanceDisplay": "8x50",
          "stroke": "Swim",
          "strokeShort": "Sw",
          "equipment": [],
          "interval": {
            "type": "range",
            "fast": ":50",
            "slow": "1:10"
          },
          "rest": null,
          "instruction": "F/E, E/F, E, F",
          "laneIntervals": null
        }
      ]
    },
    {
      "name": "Main Set",
      "sets": [
        {
          "repeats": 1,
          "distance": 200,
          "distanceDisplay": "200",
          "stroke": "Swim",
          "strokeShort": "Sw",
          "equipment": [],
          "interval": null,
          "rest": null,
          "instruction": "Fast In Heats",
          "laneIntervals": null
        },
        {
          "repeats": 1,
          "distance": 800,
          "distanceDisplay": "800",
          "stroke": "Swim",
          "strokeShort": "Sw",
          "equipment": [],
          "interval": "16 min",
          "rest": null,
          "instruction": "AR",
          "laneIntervals": null
        }
      ]
    }
  ],

  "variants": [
    {
      "name": "Friday Patricia",
      "targetSwimmers": ["Patricia", "Will", "Dustin"],
      "sections": [
        {
          "name": "Main Set",
          "sets": [
            {
              "repeats": 1,
              "block": [
                {
                  "repeats": 4,
                  "distance": 100,
                  "stroke": "Swim",
                  "strokeShort": "Sw",
                  "instruction": "Pace Finder",
                  "laneIntervals": { "L6": "1:30", "L5": "1:30", "L4": "1:30", "L3": "1:30", "L2": "1:30", "L1": "1:30" }
                }
              ]
            }
          ]
        }
      ]
    }
  ],

  "totalYardage": {
    "estimated": 4500,
    "byLane": { "L6": 4500, "L5": 4500, "L4": 4200, "L3": 4200, "L2": 3800, "L1": 3200 }
  },

  "metadata": {
    "parsedAt": "2026-04-02T06:15:00Z",
    "agentVersion": "1.0.0",
    "modelUsed": "claude-sonnet-4-6",
    "conventionsVersion": "v12",
    "rawEmailText": "..."
  }
}
```

### Schema Notes

- **`distanceDisplay`**: Preserves coach's original notation (`300-400`, `4x75`)
- **`strokeShort`**: Coach's abbreviation for display; `stroke` is the canonical form
- **`laneIntervals`**: When present, maps L1-L6 to their specific interval. `null` when all lanes share the same interval.
- **`interval.type: "range"`**: Captures range notation like `@50-1:10` without forcing interpolation. The UI can interpolate for display.
- **`variants`**: Named-swimmer workouts stored alongside the primary workout
- **`totalYardage.byLane`**: Accounts for lane-specific rep counts (e.g., L6 does all 6 sets, L1 does 3 sets)
- **`status`**: `pending_review` | `approved` | `needs_correction`
- **`flags`**: Anything the agent couldn't confidently resolve

---

## Conventions & Learning System

### Conventions Document (Firestore: `conventions/current`)

A living document the agent loads before each parse. Structured as:

```json
{
  "version": 14,
  "updatedAt": "2026-04-01T12:00:00Z",
  "abbreviations": {
    "Ch": { "meaning": "Choice", "category": "stroke_modifier", "confidence": 1.0 },
    "TX": { "meaning": "Technique", "category": "drill_modifier", "confidence": 0.8, "source": "inferred from context" },
    ...
  },
  "structuralRules": [
    {
      "rule": "When 6 consecutive bare numbers follow a set line, they are lane intervals L6 through L1 (fastest first)",
      "confidence": 1.0,
      "source": "confirmed by user"
    },
    {
      "rule": "Numbers in parentheses like (1x) mean that lane only does 1 round instead of the default repeat count",
      "confidence": 0.9,
      "source": "inferred from pattern"
    }
  ],
  "workoutTypeHeuristics": [
    { "pattern": "Fast In Heats", "suggestsType": "sprint" },
    { "pattern": "Pace Finder", "suggestsType": "distance" },
    { "pattern": "500 Pace", "suggestsType": "threshold" }
  ]
}
```

### Few-Shot Example Bank (Firestore: `examples/`)

Corrected workout parses stored as examples. Each tagged with:
- Workout type (aerobic / threshold / sprint / distance)
- Which patterns it demonstrates (lane intervals, equipment transitions, named variants, etc.)
- The raw email text and the correct structured output

The parser agent loads 2-3 relevant examples before each parse, selected by workout type and structural similarity.

### Learning Loop

```
Swimmer corrects a workout in the web UI
    |
    v
Diff: what changed between agent parse and human correction?
    |
    v
Learning Agent analyzes the diff:
    |
    +-- New abbreviation? → Add to conventions (confidence: 0.7, pending confirmation)
    +-- Structural misparse? → Add corrected example to example bank
    +-- Consistent mistake? → Update/add structural rule in conventions
    +-- Lane interval misread? → Adjust lane mapping rules
    |
    v
Convention/example updates stored in Firestore
    |
    v
Next parse loads updated conventions + examples
```

**Confidence escalation:** New conventions start at low confidence (0.5-0.7). Each time the agent uses a convention and the result is approved, confidence increases. At 1.0, the convention is considered confirmed.

---

## Web Application

### Tech Stack

- **Backend:** Python (Flask or FastAPI), same codebase as the agent
- **Frontend:** Server-rendered HTML + minimal JS (HTMX or similar). No heavy SPA framework — keep it simple for a personal project.
- **Auth:** Google Sign-In (OAuth 2.0). Restrict to a whitelist of allowed Google accounts.
- **Hosting:** Cloud Run (same service as the agent, or a separate service in the same project)

### Pages

#### 1. Workout List (`/`)
- Grouped by week, most recent first
- Each workout card shows: date, day, workout type badge, status badge, estimated yardage
- Filter by: workout type, status (pending review / approved)
- Click to view workout detail

#### 2. Workout Detail (`/workout/{id}`)
- **Lane selector** at top — swimmer picks their lane (default: remembered from last visit via cookie/localStorage)
- **Filtered view** (default): shows only the selected lane's intervals. Sets display as:
  ```
  Warm Up
    300-400 Ch
    4x75 K R:10
    8x50 Sw @:50  [showing L5 interval]

  Main Set
    200 Sw Fast In Heats
    16 min / 800 Sw AR
    ...
  ```
- **Full grid toggle**: shows all 6 lanes in a table
- **Print button**: opens print-friendly layout (see below)
- **Flag/correct button**: opens correction interface (see below)

#### 3. Print View (`/workout/{id}/print?lane=5`)
- Optimized for a single printed page (or two max)
- Large, readable fonts — meant to be read at arm's length on a pool deck
- Shows only the selected lane's intervals
- Sections clearly delineated
- Equipment transitions highlighted
- No navigation chrome, no header/footer
- Date and workout type at top

#### 4. Review/Correct (`/workout/{id}/review`)
- Side-by-side: raw email text (left) and parsed workout (right)
- Editable fields on the parsed side
- "Flag unknown" button for abbreviations/patterns the agent got wrong
- "Approve" button — marks workout as approved, triggers learning agent if corrections were made
- Shows agent's confidence score and any flags

#### 5. Conventions Viewer (`/conventions`)
- Browse current abbreviations and rules
- See confidence levels and sources
- Manually add/edit conventions (for bootstrapping and corrections)

### Print Layout Design

The print layout is critical — this is the primary physical artifact swimmers use at the pool.

```
+--------------------------------------------------+
|  STINGRAYS - Thursday 4/02/26 - Sprint     L5    |
|  MVAC  5:30-7:00 AM                              |
+--------------------------------------------------+
|                                                   |
|  WARM UP                                          |
|  300-400 Ch                                       |
|  4x75 K  R:10                                     |
|  3x100 Sw  R:10                                   |
|  3x50 P  R:10                                     |
|  8x50 Sw  @:55  F/E, E/F, E, F                   |
|                                                   |
|  MAIN SET                                         |
|  1x                                               |
|    200 Sw Fast In Heats                           |
|    16 min / 800 Sw AR                             |
|  2x                                               |
|    100 Sw Fast In Heats                           |
|    8 min / 400 Sw AR                              |
|  3x                                               |
|    50 Sw Fast In Heats                            |
|    5 min / 250 Sw AR                              |
|                                                   |
|  WARM DOWN                                        |
|                                                   |
|  Est. yardage: ~4,500                             |
+--------------------------------------------------+
```

---

## Monorepo Structure

```
swim-workout-agent/
  .github/
    workflows/
      deploy.yml            # Cloud Build trigger on push to main
  agent/
    email_monitor.py        # Email polling service
    workout_parser.py       # ADK agent: parse workout text
    learning_agent.py       # ADK agent: process feedback, update conventions
    tools/                  # ADK tool definitions
      conventions.py
      validation.py
      consistency.py
      storage.py
    prompts/                # Prompt templates for the parser agent
      system_prompt.md
      parse_workout.md
  web/
    app.py                  # Flask/FastAPI app
    templates/              # Jinja2 templates
      layout.html
      workout_list.html
      workout_detail.html
      workout_print.html
      workout_review.html
      conventions.html
    static/
      style.css
      print.css
  shared/
    schema.py               # Workout schema (Pydantic models)
    firestore_client.py     # Firestore access layer
    config.py               # Environment config
  tests/
    test_parser.py
    test_validation.py
    test_email_monitor.py
    fixtures/               # Sample email texts + expected parses
  conventions/
    seed.json               # Initial conventions to bootstrap the system
  Dockerfile
  pyproject.toml
  CLAUDE.md
  SPEC.md                   # This file
  README.md
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
1. Set up GCP project, enable APIs (Gmail, Firestore, Cloud Run, Vertex AI)
2. Set up GitHub repo with monorepo structure
3. Implement Gmail OAuth flow and email fetching
4. Define Pydantic workout schema
5. Seed initial conventions document from known abbreviations
6. Build basic ADK workout parser agent with Gemini
7. Test against 5-10 historical emails manually

### Phase 2: Parsing Quality (Week 2-3)
1. Expand parser to handle all observed patterns (lane intervals, equipment transitions, named variants, rep count modifiers)
2. Build validation tools (structural checks, yardage calculation)
3. Build consistency checker (compare against historical workouts)
4. Create example bank from corrected parses
5. Iterate on prompts using real email corpus (~150+ historical emails available)

### Phase 3: Web App (Week 3-4)
1. Flask/FastAPI app with Google Sign-In
2. Workout list and detail views
3. Lane-filtered view with lane selector
4. Print-friendly layout
5. Review/correct interface
6. Deploy to Cloud Run

### Phase 4: Automation & Learning (Week 4-5)
1. Email monitor service on Cloud Scheduler
2. Pub/Sub pipeline: detect → parse → store → notify
3. Learning agent: process corrections → update conventions → curate examples
4. Confidence scoring and flag system
5. End-to-end: coach sends email → workout appears in web app automatically

### Phase 5: Polish (Week 5-6)
1. Conventions viewer/editor
2. Historical backfill (parse the year+ of existing emails)
3. Yardage tracking over time
4. Mobile-responsive layout (pool deck phone use)
5. Notification when new workout is ready (optional: email or push)

---

## Open Questions (To Resolve During Implementation)

1. **Gmail API vs. Pub/Sub push:** Gmail supports push notifications via Pub/Sub (watch for new messages). This could replace polling with Cloud Scheduler. More efficient but more complex to set up. Decision: start with polling, upgrade to push later if polling latency is annoying.

2. **Gemini model choice:** `gemini-2.0-flash` for cost efficiency, or `gemini-2.0-pro` for harder parsing? Start with Flash, upgrade for specific failure cases.

3. **Lane interval interpolation:** When the coach writes `@1:30-2:00`, how should intermediate lanes be calculated? Linear interpolation? Need to observe more examples to determine coach's pattern. Start by storing the range and displaying it; add interpolation later.

4. **Total yardage for variable sets:** Some sets have variable distances (`300-400 Ch`). Use the higher number? Average? Flag as approximate? Decision: use higher number, mark as estimated.

5. **Thread detection reliability:** The coach usually threads emails per week but sometimes doesn't. The agent should primarily use email date + sender to detect new workouts, not rely on threading. Thread ID is metadata, not a detection signal.

---

## Non-Goals (Explicitly Out of Scope)

- Multi-coach support (only Coach Michael's emails)
- Workout creation/editing by swimmers (read-only, corrections only)
- Swim tracking or performance analytics
- Integration with swim watches or fitness platforms
- Enterprise auth, RBAC, audit logging
- Multi-tenant architecture
- Native mobile app
