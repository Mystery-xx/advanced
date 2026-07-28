# OPENCODE AGENT CONFIGURATION

**Generated 2026-07-28  
**Type:** Agent workspace configuration

## OVERVIEW

OpenCode agent workspace with MCP server integrations, custom agents, and prompt templates. Configures AI agent behavior for this codebase.

## STRUCTURE

```
.opencode/
├── mcp.json                 # MCP server configuration
├── system-prompt.md         # ⚠️ MISMATCHED (describes Kotlin project)
├── config.json              # Agent settings
├── agents/                  # Custom agent definitions
│   ├── bug-fix.md           # Bug-fixing agent
│   └── research.md          # Research agent
└── prompts/                 # Prompt templates
    └── ...
```

## WHERE TO LOOK

| Concern | Location |
|---------|----------|
| MCP servers | `.opencode/mcp.json` |
| System prompt | `.opencode/system-prompt.md` (⚠️ mismatched) |
| Agent definitions | `.opencode/agents/` |
| Prompt templates | `.opencode/prompts/` |
| Agent config | `.opencode/config.json` |

## CODE MAP

| MCP Server | Purpose | Status |
|------------|---------|--------|
| Playwright | Browser automation, E2E testing | ✅ Configured |
| CodeGraph | Code intelligence, symbol search | ⚠️ Not indexed (`.codegraph/` empty) |
| AST-Index | AST-based code search | ⚠️ Not indexed |

## CONVENTIONS

- **MCP config:** JSON schema in `mcp.json`
- **Agent definitions:** Markdown with YAML frontmatter
- **Prompts:** Markdown templates with variable substitution
- **System prompt:** Defines agent identity and constraints

## ANTI-PATTERNS (.OPENCODE)

- ⚠️ `system-prompt.md` describes DIFFERENT PROJECT (Leroy Merlin Kotlin/Cucumber BFF)
- ⚠️ CodeGraph MCP configured but `.codegraph/` directory is EMPTY
- ⚠️ AST-Index MCP configured but not initialized
- ⚠️ Custom agents (`bug-fix.md`, `research.md`) may reference wrong codebase
- ⚠️ No agent for BDD step generation (journeys/steps/ is empty)

## UNIQUE STYLES

- Multi-agent orchestration (explore, librarian, oracle, plan, etc.)
- Background task execution with `run_in_background=true`
- Task-based decomposition with todo tracking
- Boulder state management for long-running work (`.omo/boulder.json`)

## MCP SERVERS

```json
{
  "mcpServers": {
    "playwright": { /* Browser automation */ },
    "codegraph": { /* Code intelligence - NOT INDEXED */ },
    "ast-index": { /* AST search - NOT INDEXED */ }
  }
}
```

## COMMANDS

```bash
# Initialize CodeGraph (required for codegraph_explore)
npx codegraph init

# Run agent with custom prompt
opencode "explain the auth flow"

# Start work plan execution
/start-work init-deep-agents-md
```

## NOTES

- **Critical mismatch:** `system-prompt.md` and `rules/AGENTSv*.md` describe a completely different codebase (Leroy Merlin Kotlin/Cucumber project)
- **CodeGraph:** Must run `npx codegraph init` before codegraph_explore works
- **Agents:** Custom agents in `.opencode/agents/` need review for this project
- **Prompts:** Templates in `.opencode/prompts/` may need updating
- **Boulder:** Long-running work tracked in `.omo/boulder.json` with session continuity