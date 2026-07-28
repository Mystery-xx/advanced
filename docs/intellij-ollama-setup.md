# IntelliJ IDEA + Ollama Local LLM Setup

> **Last updated:** 2025-07-26

This guide documents how to integrate IntelliJ IDEA with a locally running Ollama instance for AI-assisted coding — code completion, chat, refactoring, and agent-mode features — without sending any code to external cloud services.

---

## Prerequisites

- **IntelliJ IDEA** 2023.3.4+ (Community or Ultimate) — or any JetBrains IDE (PyCharm, WebStorm, GoLand, Rider, etc.)
- **Ollama** installed and running locally
- At least one model pulled (see [Models Available](#models-available))

## Verify Ollama Is Running

```bash
# List pulled models
ollama list

# Expected output (example):
# NAME                           ID              SIZE      MODIFIED
# llama3.1:8b-instruct-q4_K_M    46e0c10c039e    4.9 GB    2 weeks ago
# llama3.2:latest                a80c4f17acd5    2.0 GB    2 weeks ago

# Check the Ollama server is listening
curl http://localhost:11434/api/tags
# Should return a JSON list of available models
```

## Plugin Options

There are **multiple** plugins for using Ollama inside IntelliJ IDEA:

| Plugin | Features | Best For | Price | Availability |
|--------|----------|----------|-------|--------------|
| **Twinny** | Chat, inline completion (FIM), local-first | Local LLMs, offline use | Free (OSS) | ✅ Works in RU |
| **Lingma (Alibaba)** | Chat, code completion, multi-language | Chinese/English devs | Free | ✅ Works in RU |
| **CodeGPT** | Chat, autocomplete, multi-provider, session restore | Multi-model flexibility | Free tier + paid | ⚠️ May be blocked |
| **JetBrains AI Assistant** (built-in) | Chat, inline completion, refactoring, commit messages | Official JetBrains integration | Needs AI subscription | ⚠️ May be blocked |
| **DevoxxGenie** | Chat, inline completion, agent mode, code review | Local LLMs first | Free (OSS) | ❌ Blocked in RU |
| **Continue** | Chat, inline completion, custom models | VS Code users | Free (OSS) | ✅ Works in RU (VS Code only) |
| **Windsurf / Cursor** | Full AI IDE with local model support | Alternative to IntelliJ | Free tier + paid | ✅ Standalone IDE |

> **Note for Russian users:** Due to sanctions, some plugins may not be available in JetBrains Marketplace. **Twinny** and **Lingma** are the recommended alternatives that work without restrictions. For VS Code users, **Continue** is the best option.

---

## Recommended: Twinny (Works in Russia)

[**Twinny**](https://github.com/rjmacarthy/twinny) is the best option for Russian users — it's free, open-source, designed specifically for local LLMs like Ollama, and **not affected by sanctions**.

### Installation

1. Open **IntelliJ IDEA**
2. Go to **Settings** → **Plugins** → **Marketplace**
3. Search for **Twinny** (or "twinny")
4. Click **Install**
5. **Restart** the IDE

> **If Twinny is not found in Marketplace:**
> 1. Download latest `.jar` from [Twinny GitHub Releases](https://github.com/rjmacarthy/twinny/releases)
> 2. **Settings** → **Plugins** → ⚙️ (gear icon) → **Install Plugin from Disk**
> 3. Select downloaded `.jar` file
> 4. Restart IDE

### Configuration

1. Open **Settings** → **Tools** → **Twinny**
2. In the **Provider** section, select **Ollama**
3. **Base URL:** `http://localhost:11434` (default)
4. Click **Refresh Models** or **Test Connection**
5. **Model:** Select `llama3.1:8b-instruct-q4_K_M`
6. Click **Apply**

### Usage

- Open **Twinny tool window** (icon in the right sidebar)
- Type questions in the chat panel
- **Inline completion:** Twinny supports FIM (Fill-in-the-Middle) automatically
- **Agent mode:** Available for models with tool-use support

---

## Alternative: Lingma (Alibaba) — Works in Russia

[**Lingma**](https://plugins.jetbrains.com/plugin/23863-lingma) by Alibaba is another plugin that works in Russia and supports custom Ollama endpoints.

### Installation

1. **Settings** → **Plugins** → **Marketplace**
2. Search for **"Lingma"** or **"Alibaba Lingma"**
3. Install → Restart

### Configuration

1. **Settings** → **Tools** → **Lingma**
2. Select **Custom Model** or **Local Model**
3. **API Endpoint:** `http://localhost:11434/v1`
4. **Model Name:** `llama3.1:8b-instruct-q4_K_M`
5. Test connection → Apply

---

## Alternative: Continue (VS Code Only)

If you use **VS Code** alongside IntelliJ, [**Continue**](https://continue.dev) is the best option:

### Installation (VS Code)

1. Open **VS Code**
2. Extensions → Search **"Continue"**
3. Install extension
4. Reload VS Code

### Configuration

Create `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "Ollama",
      "provider": "ollama",
      "model": "llama3.1:8b-instruct-q4_K_M",
      "apiBase": "http://localhost:11434"
    }
  ]
}
```

### Usage

- Chat: `Cmd+L` (Mac) or `Ctrl+L` (Win/Linux)
- Inline edit: `Cmd+I` (Mac) or `Ctrl+I` (Win/Linux)
- Tab to autocomplete

---

## Alternative: Manual .jar Installation (Any Plugin)

If a plugin is blocked in your region, you can install it manually:

1. Download `.jar` from:
   - [GitHub Releases](https://github.com/search?q=jetbrains+plugin+ollama&type=repositories)
   - [Plugin Repository Mirror](https://plugins.jetbrains.com/plugin/[ID]/versions)
2. **Settings** → **Plugins** → ⚙️ → **Install Plugin from Disk**
3. Select `.jar` → Restart IDE

---

## Alternative: Standalone AI IDEs

Consider using an AI-native IDE that has built-in Ollama support:

| IDE | Based On | Ollama Support | Price |
|-----|----------|----------------|-------|
| **Cursor** | VS Code fork | ✅ Native | Free + paid |
| **Windsurf** | VS Code fork | ✅ Native | Free + paid |
| **Codeium** | Standalone | ✅ Via extension | Free tier |

These IDEs often have better local model integration than plugins.

---

## Alternative: JetBrains AI Assistant (Built-in)

If you have a **JetBrains AI subscription**, the built-in AI Assistant has native Ollama support:

1. Go to **Settings** → **Tools** → **AI Assistant** → **Providers & API keys**
2. In **Third-party AI providers**, select **Ollama**
3. **URL:** `http://localhost:11434`
4. Click **Test Connection** to verify
5. In **Models Assignment**, assign models to:
   - **Core features** → `llama3.1:8b-instruct-q4_K_M`
   - **Instant helpers** → `llama3.2:latest` (lighter model for quick tasks)
   - **Context window:** 64000 (default)
6. Click **Apply**

> **Note:** JetBrains AI Assistant requires an active AI subscription even when using local models.

---

## Alternative: CodeGPT

[CodeGPT](https://www.codegpt.co/) is another solid option with multi-model support:

1. Install from **Settings** → **Plugins** → **Marketplace** → search "CodeGPT"
2. Open CodeGPT panel → **Manage AI Models** → **Local** tab
3. Select **Ollama** as provider
4. **API URL:** `http://localhost:11434`
5. Click **Connect**
6. Select `llama3.1:8b-instruct-q4_K_M` from the model dropdown

---

## Models Available

The following models are currently pulled locally on this machine:

| Model | Size | Purpose |
|-------|------|---------|
| `llama3.1:8b-instruct-q4_K_M` | 4.9 GB | Main model — chat, refactoring, agent mode |
| `llama3.2:latest` | 2.0 GB | Lightweight — fast responses, inline completion |
| `nomic-embed-text:latest` | 274 MB | Embeddings — codebase indexing / RAG |

### Recommended Additional Models for Code Completion

For Fill-in-the-Middle (FIM) inline completion, consider pulling:

```bash
ollama pull qwen3:0.6b        # Tiny & fast for inline completion
ollama pull starcoder2:3b     # Excellent FIM model
ollama pull deepseek-coder:1.3b  # Lightweight FIM
```

---

## Troubleshooting

### Plugin not found in Marketplace (Russia/Belarus sanctions)

**Option 1: Use Twinny (recommended)**
- Twinny is typically available in RU region
- Search for "twinny" in Marketplace

**Option 2: Use Lingma (Alibaba)**
- Lingma works in Russia
- Search for "Lingma" or "Alibaba Lingma"

**Option 3: Manual .jar installation**
1. Download plugin `.jar` from GitHub releases:
   - [Twinny Releases](https://github.com/rjmacarthy/twinny/releases)
   - [CodeGPT JetBrains Releases](https://github.com/codegpt/codegpt-jetbrains/releases)
   - [Lingma Releases](https://github.com/search?q=lingma+jetbrains&type=repositories)
2. **Settings** → **Plugins** → ⚙️ (gear icon) → **Install Plugin from Disk**
3. Select downloaded `.jar` file
4. Restart IDE

**Option 4: Use VS Code with Continue**
- If IntelliJ plugins are blocked, consider using VS Code temporarily
- Install [Continue](https://continue.dev) extension
- Configure with Ollama endpoint

**Option 5: Use AI-native IDE**
- [Cursor](https://cursor.sh) — VS Code fork with native AI
- [Windsurf](https://windsurf.ai) — Another AI IDE with local model support

### "No models found" in plugin

```bash
# Ensure Ollama is running
ollama serve

# Verify at least one model is pulled
ollama list

# Click "Refresh Models" in DevoxxGenie settings after pulling a new model
```

### Connection refused

```bash
# Check Ollama server is listening
curl http://localhost:11434

# Expected response: "Ollama is running"

# If not running, start it:
ollama serve
```

### Slow responses

- Switch to a smaller model (`llama3.2:latest` or `qwen3:0.6b`)
- For chat heavy use, consider a model that fits in your RAM comfortably

### Model not showing in dropdown

- Pull the model first: `ollama pull llama3.1:8b-instruct-q4_K_M`
- Click **Refresh Models** in the plugin settings after pulling

### Plugin compatibility

- Ensure IntelliJ IDEA is version **2023.3.4 or newer**
- DevoxxGenie requires **JDK 17+**

---

## Testing the Integration

```bash
# 1. Quick Ollama health check
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# 2. Test model response
curl -s http://localhost:11434/api/generate \
  -d '{"model":"llama3.1:8b-instruct-q4_K_M","prompt":"Say hello in one word","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('response',''))"

# 3. From the IDE: open DevoxxGenie chat and ask a question
```

---

## References

- [Ollama JetBrains Integration Docs](https://docs.ollama.com/integrations/jetbrains)
- [**Twinny GitHub**](https://github.com/rjmacarthy/twinny) — **Recommended for Russia**
- [**Lingma Plugin**](https://plugins.jetbrains.com/plugin/23863-lingma) — Works in Russia
- [**Continue**](https://continue.dev) — Best for VS Code
- [**Cursor IDE**](https://cursor.sh) — AI-native VS Code fork
- [**Windsurf IDE**](https://windsurf.ai) — AI-native IDE with local models
- [JetBrains AI Assistant: Custom Models](https://www.jetbrains.com/help/ai-assistant/use-custom-models.html)
- [CodeGPT Local Models](https://www.codegpt.co/docs/local-models)
- [Manual Plugin Installation (.jar)](https://www.jetbrains.com/help/idea/managing-plugins.html#install-plugins-from-disk)
