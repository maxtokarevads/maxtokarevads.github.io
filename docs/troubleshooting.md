# Troubleshooting Guide

Common errors and how to fix them.

---

## API & Authentication

### `ANTHROPIC_API_KEY is not set`
**Cause:** `.env` file missing or key not set.  
**Fix:** Copy `.env.example` to `.env` and add your key: `ANTHROPIC_API_KEY=sk-ant-...`

### `API authentication error` in Telegram
**Cause:** Key is invalid or expired.  
**Fix:** Regenerate at console.anthropic.com. The bot will retry automatically after 30s on 429s.

### `Rate limit circuit open — retry in Xs`
**Cause:** >3 consecutive 429 responses. Circuit breaker opened.  
**Fix:** Wait 60 seconds. The circuit auto-resets. Reduce concurrent requests or add `RATE_LIMIT_MAX=5` to `.env`.

### `All models exhausted without a successful response`
**Cause:** All models in the fallback chain failed (404, 5xx, timeout).  
**Fix:** Check `ANTHROPIC_MODEL` in `.env`. Default is `claude-sonnet-4-6`. Set `ANALYZER_BACKEND=claude_code` as fallback.

---

## SEO Enrichment

### SEO audit says `NOT CONFIGURED — PAGESPEED_API_KEY is missing`
**Cause:** `PAGESPEED_API_KEY` is not in `.env`.  
**Fix:**
1. Get a key at console.cloud.google.com → APIs → PageSpeed Insights API
2. Add to `.env`: `PAGESPEED_API_KEY=AIza...`
3. Re-run the audit.

**What you lose without it:** Core Web Vitals (LCP, INP, CLS), mobile/desktop scores. The analysis will still run but without real performance data.

### SEO audit says `NOT CONFIGURED — GSC_CREDENTIALS_FILE is missing`
**Cause:** Google Search Console OAuth not set up.  
**Fix:**
```bash
python setup_gsc_oauth.py
```
This creates `credentials/gsc_credentials.json`. Then add to `.env`:
```
GSC_CREDENTIALS_FILE=credentials/gsc_credentials.json
```

**What you lose without it:** Impressions, clicks, CTR, average position data.

### GSC says `NOT CONNECTED — property not verified`
**Cause:** The site URL doesn't match your GSC property format.  
**Fix:** GSC has two property types:
- URL-prefix: `https://example.com/` (must include trailing slash)
- Domain: `sc-domain:example.com`

The enricher tries URL-prefix format. If your property is domain type, pass `site=sc-domain:example.com` in the payload.

### `URL inspection FAILED — ...`
**Cause:** The URL inspector integration failed (network error, timeout, or credentials issue).  
**Fix:** The audit continues without live indexability data. Check logs for the root cause. Common issues:
- Network timeout (site unreachable)
- Missing OAuth credentials
- URL returns 4xx/5xx

---

## Telegram Bot

### Bot doesn't respond to messages
**Check these in order:**
1. `TELEGRAM_BOT_TOKEN` in `.env` — get it from @BotFather
2. Bot is running: check `bot.pid` file exists and the process is alive
3. Only one instance: `_ensure_single_instance()` exits if another PID is running
4. `ALLOWED_CHAT_IDS` — if set, your chat ID must be in the list. Get yours from @userinfobot.

### `Access denied. Contact the administrator.`
**Cause:** Your chat ID is not in `ALLOWED_CHAT_IDS`.  
**Fix:** Add your Telegram ID to `.env`: `ALLOWED_CHAT_IDS=123456789`

### `Too many requests. Please wait X seconds.`
**Cause:** Rate limit hit. Default: 10 requests per 60 seconds per chat.  
**Fix (for your own bot):** Increase limits in `.env`:
```
RATE_LIMIT_MAX=20
RATE_LIMIT_WINDOW=60
```

### Bot response is slow (30-90 seconds)
**Normal for:** Canon audits, orchestration with multiple agents.  
**Faster options:**
- Use `/plan` or `/copy` instead of `/audit` for quick tasks
- Set `MODEL_ROUTING=false` to stay on Sonnet (Opus is slower but more thorough for audits)
- Use Haiku for quick questions: set `ANTHROPIC_MODEL=claude-haiku-4-5-20251001` (lower quality)

---

## Platform Integrations (Google/Meta/TikTok Ads)

### `/liveaudit` says `Google Ads API not configured`
**Fix:** Run the OAuth setup script:
```bash
python setup_google_ads_oauth.py
```
Then add to `.env`:
```
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_CUSTOMER_ID=1234567890
```

### Google Ads `PERMISSION_DENIED`
**Cause:** Developer token not approved for the account, or OAuth scope mismatch.  
**Fix:** Apply for Google Ads API access at https://developers.google.com/google-ads/api/docs/access-levels

---

## Structured Output

### Response missing `structured` key
**Cause:** `call_tool()` returned `None`. The agent fell back to plain chat.  
**Signal:** Response will contain `"structured_fallback": True`.  
**Fix:** Usually a transient API issue. Retry the request. If persistent, check logs for `call_tool failed` warnings.

### Vault file not saving
**Cause:** Permission error or disk full.  
**Fix:** Check the warning in logs: `Failed to save to vault: ...`. The agent response is still returned — vault saving is best-effort.

---

## Database

### `bot_state.db` locked / SQLite errors
**Cause:** Two bot instances running simultaneously.  
**Fix:** Kill all Python processes, delete `bot.pid`, restart the bot.

### Lost history after restart
**Cause:** Expected. History is in-memory + SQLite. If SQLite was corrupted or deleted, history is gone.  
**Fix:** History is per-chat. Users can rebuild context by starting a new conversation.

---

## Development / Testing

### Tests failing: `SEO enrichment making real HTTP calls`
**Fix:** Set env var: `SEO_SKIP_ENRICHMENT=true`. This is the test flag that skips live enrichment.

### Import errors after refactoring
**Common cause:** Circular imports. The project uses lazy imports in `BaseAgent` to avoid this:
```python
# In base_agent.py — always import inside the function, never at module level:
import storage as _storage
```

### Running tests locally
```bash
python -m pytest tests/ -x -q
```
All 360+ tests should pass in under 90 seconds. If slow, check if `SEO_SKIP_ENRICHMENT=true` is set.
