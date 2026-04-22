# Nova v5 — Agent-Native Platform

**Owner:** Santiago Covelli (Santi)  
**Account:** nova@covelli.ai  
**Started:** 2026-04-17  
**Current Phase:** Production runtime build (día 10)

## What is Nova v5?

Agent-native platform for SC17 Agent Army. Powers **Atlas**, the PM-Agent operating across 7 companies: Felirni, CuraPlan, M1, Lorentz, INTELIGENCIA, Lulo, Robot Land.

**Core pivot from v1-v4:** skills-first → agent-native with structured safety rails (inspired by Dan Shipper's Every.to guide).

## Project Structure

```
Nova/
├── runtime/              # Production runtime code
│   ├── tools/           # Python wrappers: felirni_api, slack_bot, secrets_manager
│   ├── felirni-api/     # Lambda handler code (downloaded from AWS)
│   └── mcp_server.py    # MCP server exposing tools to Agent SDK
├── tools/               # Primitives (read_file, write_file, run_bash)
├── companies/           # Context per company (context.md files)
├── outcomes/            # Agent prompts by company/outcome
├── tests/               # Pytest suite
├── governance/          # Architecture, security, session logs
│   ├── sessions/        # Daily session logs
│   ├── architecture/    # Production architecture docs
│   └── security/        # Guardian reports
├── Dockerfile           # Dual-mode container (slack_listener/cli)
└── requirements.txt     # Pinned runtime dependencies
```

## Tech Stack

- **Language:** Python 3.14+ (requires PEP 604 union syntax: `str | Path`)
- **AI Models:**
  - Claude (Anthropic): primary via `anthropic` SDK
  - Gemini (Google): secondary via `google-genai`
  - ~~Claude Agent SDK~~: being removed (subprocess_cli incompatible with ECS)
- **Infrastructure:** AWS ECS Fargate + EventBridge + Lambda + Secrets Manager
- **Slack:** Socket Mode (dev/staging) + HTTP mode (Lambda/EventBridge prod)
- **IaC:** CloudFormation YAML (consistent with existing M1/Felirni Lambdas)

## Runtime Dependencies (requirements.txt)

```
anthropic==0.96.0
boto3==1.42.92
botocore==1.42.92
claude-agent-sdk==0.1.63    # being phased out
google-genai==1.73.1
aiohttp==3.13.5
slack_sdk==3.41.0
```

## Key Components

### Atlas PM-Agent
Slack bot + scheduled agent for project management across 7 companies.

**Runtime modes:**
- `MODE=slack_listener`: persistent Socket Mode connection (ECS Fargate)
- `MODE=cli`: CLI runner for smoke tests and dev

**Current state:**
- Felirni: operational Lambda API (31 endpoints) + DB with 145+ items
- Other companies: boards exist, Atlas integration pending

### Security Guardrails (Guardian)

**Current Risk Score:** 18/100 (Low)

**Safety layers:**
1. Path confinement: `_safety.py` with `assert_path_in_allowed_root()`
2. Command injection: `shell=False` + `FORBIDDEN_CHARS` allowlist
3. Slack signature verification: HMAC-SHA256 + 5min anti-replay window
4. Prompt injection: XML delimiters `<user_message>...</user_message>` + 4000 char truncation
5. SSRF prevention: blocks link-local, RFC1918, loopback in URLs
6. Zero secret leakage: errors never expose values, keys, or paths

**Guardian workflow:** audit → fix → re-audit → commit

### Secrets Management

**Pattern:** AWS Secrets Manager with namespace `nova/atlas/{company}/config`

**Structure per company:**
```json
{
  "api_base_url": "https://...",
  "api_key": "...",
  "slack_bot_token": "xoxb-...",
  "slack_app_token": "xapp-...",
  "slack_signing_secret": "...",
  "slack_channel_ops": "#company-ops"
}
```

**Helper:** `runtime/tools/secrets_manager.py` with 15min thread-safe cache

## Development Workflow

### Running Tests
```bash
pytest -v                    # All tests
pytest tests/tools/ -v       # Tool tests only
```

**Current coverage:** 108 tests PASSED

### Local Setup
```bash
cd ~/Documents/Nova
direnv allow                 # Loads .envrc (symlinked to ~/Nova-local/.envrc)
# Context switches to SC17-NOVA
```

**Required env vars (from .envrc):**
- `ANTHROPIC_API_KEY`: Claude API access (nova@covelli.ai account)
- `AWS_PROFILE`: m1-deploy-user (for Secrets Manager access)

### Git Workflow
```bash
git status                   # Check current changes
pytest -v                    # Run tests before commit
# Guardian audit if code changes affect security
git add <files>
git commit -m "día N: <description>"
```

**Commit message style:** `día N: <what was done> — <optional context>`

## Production Architecture

**Target:** ECS Fargate (persistent Slack listener) + EventBridge (schedules) + Lambda (scheduled tasks)

**Cost estimate:** ~13 USD/month for 7 companies

**Deployment phases (days 5-12):**
1. ✅ Tool wrappers (felirni_api, slack_bot, secrets_manager)
2. ✅ Dockerfile + dual-mode entrypoint
3. ✅ MCP server
4. ✅ Smoke test with Haiku
5. ⏳ CloudFormation stack (atlas-platform)
6. ⏳ ECR + first image push
7. ⏳ ECS task definition + service
8. ⏳ EventBridge schedules
9. ⏳ First live Monday Kickoff

## Current Work (Día 10)

### Just Completed
- ✅ Fixed `slack_bot.py` `_run_agent()`: removed `ClaudeSDKClient` (subprocess_cli bug)
- ✅ Now uses `anthropic.AsyncAnthropic().messages.create()` directly
- ✅ Model: `claude-haiku-4-5-20251001` (protocol from día 2)
- ✅ Anti-injection: `text[:4000]` + XML delimiters

### Open Technical Debt
- M-3 felirni_api: HTTP client leak (no context manager)
- B-2 secrets_manager: no company allowlist (deferred until 2nd company)
- B-3 secrets_manager: tracebacks not logged (pending structured logger)

### Next Steps
1. Create venv for running tests
2. Run full test suite
3. Commit: "día 9/10: _run_agent usa anthropic.AsyncAnthropic directo"
4. Continue with CloudFormation stack creation

## Communication Guidelines

**Language:** Spanish neutral with "tuteo" (tú, not vos)  
**Tone:** Direct, concise, technical  
**Name:** Call user "Santi"  
**No signatures:** Don't sign off responses with names/emojis

## Session Logs

All daily work logged in `governance/sessions/YYYY-MM-DD-diaN-description.md`

**Key sessions to review:**
- `2026-04-17-fundacion-tecnica.md`: v5 foundation, architecture decisions
- `2026-04-20-dia4-security-and-production-plan.md`: Guardian workflow, multi-company architecture
- `2026-04-21-dia5-felirni-wrapper-slack.md`: Tool wrappers build
- `2026-04-21-dia6-dockerfile-mcp-smoketest.md`: Docker + MCP + smoke test
- `2026-04-22-dia9-continuacion.md`: subprocess_cli bug diagnosis

## Important Context

### Felirni Production API
- **URL:** `https://le0dj70e7i.execute-api.us-east-1.amazonaws.com/prod`
- **Lambda:** felirni-project-api-prod
- **DynamoDB:** felirni-db-prod (145+ items)
- **Code:** `runtime/felirni-api/handler.py` (1001 lines, version 3.0.0)
- **Endpoints:** 31 total (tickets, epics, sprints, people, decisions, metrics)

### Slack Setup
- **Strategy:** One Slack App per company (decided día 4, decision D1)
- **Felirni workspace:** Felirni Labs workspace
- **Test channel:** #nova-atlas-sandbox
- **Bot name:** @atlas

### Models & Costs
- **Primary:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) for cost efficiency
- **Dev/test:** Claude Sonnet 4.6 for complex tasks
- **Smoke test día 6:** 76 input / 87 output tokens
- **Budget:** $50 loaded, alerts at $30, hard limit $80

## Do Not

- ❌ Use `claude_agent_sdk.ClaudeSDKClient` (subprocess_cli incompatible with containers)
- ❌ Add cache_control to system prompts (causes issues)
- ❌ Hardcode secrets in code
- ❌ Use `shell=True` in subprocess calls
- ❌ Expose stack traces or secret values in error messages
- ❌ Create documentation files unless explicitly requested

## Do

- ✅ Use `anthropic.AsyncAnthropic()` directly for Claude API calls
- ✅ Run Guardian audit before commits that touch security-sensitive code
- ✅ Pin dependencies in requirements.txt
- ✅ Write tests for all new runtime code
- ✅ Log session work in `governance/sessions/`
- ✅ Use XML delimiters for user input: `<user_message>...</user_message>`
- ✅ Truncate user input to prevent injection: `text[:4000]`
