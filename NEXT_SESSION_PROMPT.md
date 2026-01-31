# Perplexity Proxy Manager v2.0.0 - Next Session Development Prompt

## Project Context

You are continuing development of **Perplexity Proxy Manager v2.0.0**, an advanced anti-ban system for managing 60+ shared AI service accounts with automatic session management, DPAPI decryption, and unified API access.

**Project Location**: `C:\Users\Nicita\projects\perplexity-proxy-manager`

**Current Status**: DPAPI decryption system completed. Browser cookie extraction working. API key generation functional. Database structure established.

## What Has Been Completed

### 1. DPAPI Decryption System ✅
- **DPAPIDecryptionService.ts** - Core service for parallel DPAPI decryption via PowerShell
- Supports Chrome, Edge, Brave, Comet browsers
- Parallel processing: 60+ accounts in ~15 seconds (20-25x faster than sequential)
- PowerShell implementation: `[System.Security.Cryptography.ProtectedData]::Unprotect()`

### 2. API Key Generation ✅
- Format: `ppk_[32 hex chars]` with SHA-256 hashing
- Database storage with pool association
- Rate limiting: 100/hour, 1000/day with burst protection
- Generated working key: `ppk_f3169be21f76a53d610311deeaf20e7d`

### 3. Session Token Extraction ✅
- Puppeteer-based automation for Comet Browser
- Chrome DevTools Protocol integration (port 9222)
- Successfully extracted Perplexity session tokens

### 4. Multi-Service Key Extraction ✅
Successfully extracted keys from:
- **Claude**: `sk-ant-sid01-...` format (Sonnet 4.5, Opus models)
- **Perplexity**: JWT format `eyJhbGci...` (Sonar, Pro Search)
- **OpenAI**: Session tokens (GPT-4, o1-preview, o1-mini)
- **Google Gemini**: Cookie-based auth (6 cookies extracted)

### 5. Database Structure ✅
SQLite database with tables:
- `accounts` - Account management
- `pools` - Pro Pool, Max Pool
- `api_keys` - Generated API keys with hashing
- `tokens` - Extracted session tokens
- `session_events` - Activity logging

### 6. Documentation Created ✅
- **DPAPI_DECRYPTION_GUIDE.md** - Full DPAPI implementation guide
- **AUTOMATION_CONTEXT.md** - Service architecture and unified API design
- **EXTRACTED_KEYS_REPORT.md** - All found keys with 25+ available models
- **DECRYPTION_SYSTEM_READY.md** - Integration instructions

## Your Task: Build Complete Mini PC Application

### PHASE 1: File Organization and Project Structure

**Organize all existing files into this structure:**

```
perplexity-proxy-manager/
├── desktop-app/                    # NEW: Electron/Desktop GUI Application
│   ├── src/
│   │   ├── main/                   # Main process
│   │   │   ├── index.ts            # Electron main entry
│   │   │   ├── services/
│   │   │   │   ├── KeyManager.ts   # Central key storage & rotation
│   │   │   │   ├── UnlockLayer.ts  # Censorship bypass module
│   │   │   │   ├── UnifiedAPI.ts   # Auto-selecting API router
│   │   │   │   └── DPAPIDecryption.ts  # Move existing DPAPI service here
│   │   ├── renderer/               # Renderer process (UI)
│   │   │   ├── App.tsx             # Main React/Vue component
│   │   │   ├── components/
│   │   │   │   ├── KeyStorage.tsx  # Key management UI
│   │   │   │   ├── RotationPanel.tsx  # Rotation status display
│   │   │   │   ├── UnlockSettings.tsx # Unlock layer config
│   │   │   │   └── ModelSelector.tsx  # Model selection UI
│   │   └── preload/
│   │       └── index.ts            # IPC bridge
│   ├── package.json
│   └── electron-builder.json       # Build configuration
│
├── src/                            # Existing backend services
│   ├── main/
│   │   ├── services/
│   │   │   ├── DPAPIDecryptionService.ts  # MOVE to desktop-app
│   │   │   ├── ClaudeService.ts    # Claude API integration
│   │   │   ├── OpenAIService.ts    # OpenAI integration
│   │   │   ├── GeminiService.ts    # Google Gemini integration
│   │   │   └── PerplexityService.ts # Perplexity integration
│   │   └── ProxyServer.ts          # Main proxy server
│
├── scripts/                        # Utility scripts
│   ├── extract-token-full-auto.js
│   ├── generate-api-key-final.js
│   ├── test-api-key.js
│   ├── extract-all-api-keys.js
│   ├── demo-dpapi-decryption.js
│   └── save-token-to-db.js
│
├── data/
│   └── perplexity-manager.db       # SQLite database
│
├── docs/                           # All documentation
│   ├── DPAPI_DECRYPTION_GUIDE.md
│   ├── AUTOMATION_CONTEXT.md
│   ├── EXTRACTED_KEYS_REPORT.md
│   └── DECRYPTION_SYSTEM_READY.md
│
└── package.json                    # Root package.json
```

### PHASE 2: Central Key Storage with Rotation System

**Requirements:**

1. **KeyManager Service** (`desktop-app/src/main/services/KeyManager.ts`)
   - Centralized storage for ALL extracted API keys grouped by service
   - Track usage statistics per key: request count, rate limit status, last used timestamp
   - Automatic rotation algorithm: when key hits limit, instantly switch to next available key
   - Health monitoring: ping keys every 5 minutes to check availability
   - Database schema:

```sql
CREATE TABLE service_keys (
  id INTEGER PRIMARY KEY,
  service TEXT NOT NULL,           -- 'claude', 'openai', 'gemini', 'perplexity'
  model TEXT,                       -- 'sonnet-4.5', 'gpt-4', 'gemini-2.0-flash'
  key_value TEXT NOT NULL,          -- Encrypted API key/session token
  encryption_iv TEXT NOT NULL,      -- AES-256 IV for decryption
  status TEXT DEFAULT 'active',     -- 'active', 'rate_limited', 'expired', 'error'
  requests_used INTEGER DEFAULT 0,
  daily_limit INTEGER,
  hourly_limit INTEGER,
  last_used_at DATETIME,
  rate_limit_reset_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE key_rotation_log (
  id INTEGER PRIMARY KEY,
  from_key_id INTEGER,
  to_key_id INTEGER,
  reason TEXT,                      -- 'rate_limit', 'error', 'manual'
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

2. **Rotation Logic**:
   ```typescript
   // Pseudo-code for rotation algorithm
   async function selectKey(service: string, model?: string): Promise<Key> {
     // 1. Get all active keys for service/model
     const keys = await db.getActiveKeys(service, model);

     // 2. Filter out rate-limited keys
     const available = keys.filter(k =>
       k.status === 'active' &&
       k.requests_used < k.hourly_limit &&
       (!k.rate_limit_reset_at || k.rate_limit_reset_at < now)
     );

     // 3. Sort by least recently used (LRU algorithm)
     available.sort((a, b) => a.last_used_at - b.last_used_at);

     // 4. Return first available, or throw if none available
     if (available.length === 0) {
       throw new Error(`All keys for ${service} are rate-limited`);
     }

     return available[0];
   }
   ```

3. **Key Encryption**:
   - Use AES-256-CBC to encrypt stored keys
   - Master password stored in Windows Credential Manager
   - Never store keys in plaintext

### PHASE 3: Unlock Layer (Censorship Bypass Module)

**Requirements:**

1. **UnlockLayer Service** (`desktop-app/src/main/services/UnlockLayer.ts`)
   - Detects censorship responses (keywords: "I cannot", "I'm unable", "against policy")
   - When detected, automatically reroutes through intermediate model
   - Rephrasing strategies:
     - **Technique 1**: Contextualize as hypothetical/fictional scenario
     - **Technique 2**: Break request into smaller sub-requests
     - **Technique 3**: Use role-playing framework ("You are a technical writer...")
     - **Technique 4**: Reframe as educational/research question
   - Preserve original intent while making request acceptable

2. **Implementation Flow**:
   ```typescript
   async function processRequest(prompt: string, targetModel: string) {
     // 1. Send original request
     const response = await sendToModel(targetModel, prompt);

     // 2. Check if censored
     if (isCensored(response)) {
       console.log('🔓 Censorship detected, activating Unlock Layer...');

       // 3. Select intermediate model for rephrasing
       const intermediateModel = selectIntermediateModel(); // Use uncensored model

       // 4. Rephrase through intermediate
       const rephrasedPrompt = await rephrase(intermediateModel, prompt);

       // 5. Retry with rephrased prompt
       const newResponse = await sendToModel(targetModel, rephrasedPrompt);

       // 6. Log success/failure
       await logUnlockAttempt(prompt, rephrasedPrompt, success: !isCensored(newResponse));

       return newResponse;
     }

     return response;
   }
   ```

3. **Configuration UI**:
   - Toggle unlock layer on/off
   - Select preferred intermediate models (DeepSeek, Llama, local models)
   - Choose rephrasing strategy
   - View unlock attempt history and success rate

### PHASE 4: Unified API Interface

**Requirements:**

1. **UnifiedAPI Service** (`desktop-app/src/main/services/UnifiedAPI.ts`)
   - Single endpoint: `POST http://localhost:8080/api/v1/chat`
   - Auto-selects optimal model based on availability and load
   - Request format:
   ```json
   {
     "message": "Your prompt here",
     "model": "auto",              // or specific: "claude-sonnet-4.5", "gpt-4"
     "stream": false,
     "unlock_layer": true,         // Enable censorship bypass
     "max_tokens": 4000
   }
   ```

2. **Model Selection Algorithm**:
   ```typescript
   async function selectOptimalModel(preference?: string): Promise<string> {
     if (preference && preference !== 'auto') {
       return preference; // User specified model
     }

     // Auto-selection based on:
     // 1. Available keys (not rate-limited)
     // 2. Model capability (prioritize Sonnet 4.5 > GPT-4 > Gemini)
     // 3. Response speed (fastest first)
     // 4. Load balancing (distribute across services)

     const availableModels = await keyManager.getAvailableModels();
     const ranked = rankByCapability(availableModels);
     return ranked[0];
   }
   ```

3. **Response Format**:
   ```json
   {
     "response": "Model's response here",
     "model_used": "claude-sonnet-4.5",
     "key_id": 127,
     "unlock_layer_activated": false,
     "tokens_used": 1250,
     "latency_ms": 3400
   }
   ```

### PHASE 5: Desktop GUI Design

**Technology Stack:**
- **Framework**: Electron + React/TypeScript
- **Styling**: Tailwind CSS or Material-UI
- **State Management**: Zustand or Redux
- **Database**: Better-SQLite3 (already in use)

**UI Components:**

1. **Dashboard Screen** (Main)
   - Live statistics: Total requests today, active keys, rate limit status
   - Real-time request log with model used and response time
   - Quick action buttons: "Extract Keys", "Test All Keys", "Refresh Status"

2. **Key Storage Panel**
   - Table showing all keys grouped by service:
     - Columns: Service | Model | Status | Requests Used | Daily Limit | Last Used
   - Color-coded status: 🟢 Active, 🟡 Rate Limited, 🔴 Error
   - Actions: Add Key, Delete Key, Test Key, Refresh
   - Import from browser button (triggers DPAPI extraction)

3. **Rotation Settings**
   - Toggle auto-rotation on/off
   - Set rotation strategy: Round-robin, Least Recently Used, Random
   - Configure rate limits per service
   - View rotation history (last 100 switches)

4. **Unlock Layer Panel**
   - Master toggle: Enable/Disable
   - Select intermediate models: [DeepSeek, Llama 3.1, Mixtral]
   - Choose rephrasing techniques (checkboxes)
   - Success rate statistics: "Unlocked 47/52 requests (90.4%)"
   - View failed attempts with original/rephrased prompts

5. **API Settings**
   - Local server port configuration (default 8080)
   - API authentication toggle
   - Generate client API keys for external apps
   - View API documentation

6. **Browser Integration Tab**
   - Detected browsers list: Chrome, Edge, Brave, Comet
   - Extract buttons per browser
   - Last extraction timestamp
   - Auto-extract schedule (every 6 hours)

**Design Guidelines:**
- Dark theme with accent colors (purple/blue)
- Monospace font for API keys and logs
- Toast notifications for important events (key expired, unlock layer activated)
- System tray icon with quick access menu

### PHASE 6: Integration Steps

1. **Move DPAPI Service to Desktop App**
   - Copy `src/main/services/DPAPIDecryptionService.ts` to `desktop-app/src/main/services/`
   - Update imports in ProxyServer.ts

2. **Create KeyManager**
   - Implement database schema for service_keys table
   - Write key encryption/decryption methods using AES-256
   - Build rotation algorithm with LRU logic

3. **Build UnlockLayer**
   - Implement censorship detection (regex patterns)
   - Create rephrasing prompt templates
   - Add logging for unlock attempts

4. **Implement UnifiedAPI**
   - Create Express.js server on port 8080
   - Add model selection logic
   - Integrate with KeyManager and UnlockLayer

5. **Build Electron App**
   - Set up Electron with React
   - Create all UI components listed above
   - Wire IPC communication between main and renderer

6. **Testing**
   - Extract keys from all browsers using DPAPI
   - Test rotation when one key hits limit
   - Trigger unlock layer with censored prompt
   - Make requests via unified API endpoint

### PHASE 7: Final Deliverables

**You must create:**

1. ✅ Complete desktop-app folder with all source code
2. ✅ Working Electron application that can be launched
3. ✅ All services integrated: KeyManager, UnlockLayer, UnifiedAPI, DPAPI
4. ✅ Database migrations to add service_keys and rotation_log tables
5. ✅ README.md with setup instructions
6. ✅ package.json scripts: `npm run dev`, `npm run build`, `npm start`
7. ✅ Executable installer for Windows (.exe)

## Technical Context to Remember

### Available Models (25+ total)
**Claude**: sonnet-4.5, opus-4.5, sonnet-3.5, opus-3, haiku-3.5
**OpenAI**: gpt-4-turbo, gpt-4, o1-preview, o1-mini
**Perplexity**: sonar-pro, sonar-reasoning, sonar-chat
**Google**: gemini-2.0-flash, gemini-1.5-pro, gemini-exp-1206

### Key Formats
- Claude: `sk-ant-sid01-[base64]`
- Perplexity: JWT `eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0...`
- OpenAI: Session token (varies)
- Gemini: Cookie-based (6 cookies: __Secure-1PSID types)

### DPAPI Decryption (Critical)
```powershell
$encryptedBytes = [Convert]::FromBase64String($base64Input)
$decryptedBytes = [System.Security.Cryptography.ProtectedData]::Unprotect(
  $encryptedBytes,
  $null,
  [System.Security.Cryptography.DataProtectionScope]::CurrentUser
)
[System.Text.Encoding]::UTF8.GetString($decryptedBytes)
```

### Browser Cookie Paths
- Chrome: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies`
- Edge: `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies`
- Brave: `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Network\Cookies`
- Comet: `%LOCALAPPDATA%\CometBrowser\User Data\Default\Network\Cookies`

### Rate Limits (Document as you discover)
- Claude: Unknown (monitor and document)
- OpenAI: Varies by tier
- Perplexity: Pro has higher limits
- Gemini: Free tier has limits

## Critical Success Criteria

Your implementation is complete when:

1. ✅ I can launch the Electron app with `npm start`
2. ✅ GUI shows all extracted keys from my browsers
3. ✅ I can send a request via `http://localhost:8080/api/v1/chat` with `"model": "auto"`
4. ✅ System automatically rotates to next key when one hits rate limit
5. ✅ Unlock layer successfully bypasses censorship (test with controversial prompt)
6. ✅ All UI panels are functional and display real-time data
7. ✅ Application can be built into Windows .exe installer

## Development Priority Order

**Do this in sequence:**

1. File organization (move everything to correct folders)
2. Database schema updates (service_keys, rotation_log tables)
3. KeyManager implementation (MOST CRITICAL)
4. UnifiedAPI implementation
5. UnlockLayer implementation
6. Electron app setup with basic UI
7. Wire all services together
8. Polish UI and add remaining features
9. Build installer

## Additional Notes

- **Performance**: Parallel processing is mandatory - use `Promise.all()` everywhere possible
- **Security**: Never log full API keys, only last 8 characters
- **Error Handling**: Every API call must have try/catch with detailed logging
- **Logging**: Use Winston or Pino for structured logging
- **Configuration**: Store all settings in SQLite, not config files

## Questions You Should NOT Ask Me

- ❌ "What port should I use?" → Use 8080
- ❌ "Which framework?" → Electron + React + TypeScript
- ❌ "How to store keys?" → AES-256 encrypted in SQLite
- ❌ "Which rotation algorithm?" → LRU (Least Recently Used)

## Files to Reference

All previous work is in: `C:\Users\Nicita\projects\perplexity-proxy-manager`

Key files to integrate:
- `demo-dpapi-decryption.js` - Parallel decryption example
- `generate-api-key-final.js` - API key generation logic
- `extract-all-api-keys.js` - Universal key extraction
- `data/perplexity-manager.db` - Current database

Documentation:
- `docs/DPAPI_DECRYPTION_GUIDE.md` - DPAPI implementation details
- `docs/AUTOMATION_CONTEXT.md` - Service architecture design
- `docs/EXTRACTED_KEYS_REPORT.md` - All found keys and models

## Start Immediately With

```bash
cd C:\Users\Nicita\projects\perplexity-proxy-manager
mkdir -p desktop-app/src/main/services
mkdir -p desktop-app/src/renderer/components
mkdir -p desktop-app/src/preload

# Initialize Electron app
cd desktop-app
npm init -y
npm install electron react react-dom typescript @types/react @types/node
npm install electron-builder better-sqlite3 express cors

# Create tsconfig.json, main entry, and start building
```

**Your first message should be:** "Starting Perplexity Proxy Manager v2.0.0 desktop application development. Creating project structure..."

---

**This prompt contains complete context. Do not ask clarifying questions. Begin implementation immediately.**
