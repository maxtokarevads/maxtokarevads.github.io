import logging
import os
import random
import threading
import time
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Retry config for transient errors (429, 5xx)
_MAX_RETRIES  = 3
_BASE_DELAY   = 1.0   # seconds — doubled each attempt (+ jitter)
_MAX_DELAY    = 30.0  # cap per-attempt sleep

# Circuit breaker: after this many consecutive 429s, refuse new requests for _CB_COOLDOWN seconds
_CB_THRESHOLD = 3
_CB_COOLDOWN  = 60.0
_cb_lock             = threading.Lock()
_cb_consecutive_429s = 0
_cb_open_until       = 0.0  # epoch time when circuit re-closes


class ClaudeHTTPAnalyzer:
    """HTTP client for the Anthropic Messages API."""

    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in environment variables")

        self.api_key   = api_key
        self.base_url  = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.full_url  = f"{self.base_url}/v1/messages"
        self.model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.fallback_models = list(dict.fromkeys([
            self.model_name,
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
        ]))
        self._model_lock  = threading.Lock()
        self.client       = httpx.Client(timeout=120.0)
        # Persistent async client — reused across all achat_with_agent/acall_tool calls.
        # Creating a new AsyncClient per-call wastes connection setup overhead.
        # Closed explicitly via aclose() or on GC (httpx handles GC cleanup safely).
        self._async_client = httpx.AsyncClient(timeout=120.0)

    # ── Request builder ──────────────────────────────────────────────────────

    def _build_messages(
        self,
        prompt: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages

    # ── Retry-aware single-model POST ────────────────────────────────────────

    def _check_circuit_breaker(self) -> None:
        """Raise RuntimeError if circuit is open (too many consecutive 429s)."""
        global _cb_consecutive_429s, _cb_open_until
        with _cb_lock:
            if _cb_open_until and time.time() < _cb_open_until:
                remaining = int(_cb_open_until - time.time())
                raise RuntimeError(
                    f"Rate limit circuit open — retry in {remaining}s. "
                    "Too many consecutive 429 responses."
                )

    def _record_429(self) -> None:
        global _cb_consecutive_429s, _cb_open_until
        with _cb_lock:
            _cb_consecutive_429s += 1
            if _cb_consecutive_429s >= _CB_THRESHOLD:
                _cb_open_until = time.time() + _CB_COOLDOWN
                logger.error(
                    "Circuit breaker OPEN: %d consecutive 429s — cooling down %ds",
                    _cb_consecutive_429s, _CB_COOLDOWN,
                )

    def _reset_circuit(self) -> None:
        global _cb_consecutive_429s, _cb_open_until
        with _cb_lock:
            _cb_consecutive_429s = 0
            _cb_open_until = 0.0

    def _post_with_retry(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> httpx.Response:
        """
        POST to the Anthropic API with exponential backoff on 429 / 5xx.
        Raises immediately for all other status codes (404, 400, …).
        """
        self._check_circuit_breaker()
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = self.client.post(self.full_url, json=payload, headers=headers)
                response.raise_for_status()
                self._reset_circuit()
                return response

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code

                if status == 429:
                    self._record_429()
                    # Respect Retry-After header if present
                    retry_after = exc.response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after else min(
                        _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1),
                        _MAX_DELAY,
                    )
                    if attempt < _MAX_RETRIES:
                        logger.warning(
                            "Rate limited (429) — retrying in %.1fs (attempt %d/%d)",
                            delay, attempt + 1, _MAX_RETRIES,
                        )
                        time.sleep(delay)
                        continue
                    raise

                if status >= 500:
                    delay = min(
                        _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1),
                        _MAX_DELAY,
                    )
                    if attempt < _MAX_RETRIES:
                        logger.warning(
                            "Server error %d — retrying in %.1fs (attempt %d/%d)",
                            status, delay, attempt + 1, _MAX_RETRIES,
                        )
                        time.sleep(delay)
                        continue
                    raise

                # 404, 400, 401 etc. — raise immediately, let caller handle
                raise

        raise RuntimeError("Max retries exceeded")  # should never reach here

    # ── Main request method ──────────────────────────────────────────────────

    def _send_message_request(
        self,
        prompt: str,
        system: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        model_override: Optional[str] = None,
        cached_context: Optional[str] = None,
        agent_name: str = "",
        agent_mode: str = "",
    ) -> str:
        messages   = self._build_messages(prompt, history=history)
        headers    = {
            "Content-Type":      "application/json",
            "X-Api-Key":         self.api_key,
            "anthropic-version": os.getenv("ANTHROPIC_API_VERSION", "2023-06-01"),
            "anthropic-beta":    "prompt-caching-2024-07-31",
        }
        max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))
        use_stream = os.getenv("ANTHROPIC_STREAM", "true").lower() != "false"

        with self._model_lock:
            base_models = list(dict.fromkeys(self.fallback_models))

        # model_override goes first in the fallback chain (e.g. opus for audits)
        if model_override and model_override not in base_models:
            models = [model_override] + base_models
        elif model_override:
            models = [model_override] + [m for m in base_models if m != model_override]
        else:
            models = base_models

        last_error = None
        for model in models:
            payload: Dict[str, Any] = {
                "model":      model,
                "messages":   messages,
                "max_tokens": max_tokens,
                "stream":     use_stream,
            }
            if system or cached_context:
                if cached_context:
                    # KB block first with explicit 1-hour TTL.
                    # Anthropic changed default TTL from 60min → 5min in 2026.
                    # Without "ttl": "1h", cache busts after every 5-minute gap.
                    _cache_ttl = os.getenv("CACHE_TTL", "1h")
                    blocks = [
                        {"type": "text", "text": cached_context,
                         "cache_control": {"type": "ephemeral", "ttl": _cache_ttl}},
                    ]
                    if system:
                        blocks.append({"type": "text", "text": system})
                    payload["system"] = blocks
                else:
                    payload["system"] = system

            try:
                if use_stream:
                    text, usage = self._stream_response(payload, headers)
                else:
                    response = self._post_with_retry(payload, headers)
                    data  = response.json()
                    text  = self._parse_response(data)
                    usage = data.get("usage", {})

                with self._model_lock:
                    if self.model_name != model:
                        logger.info("Switched to model %s", model)
                        self.model_name = model

                # Log token usage — best-effort, never blocks the response
                try:
                    import storage as _storage
                    _storage.log_usage(model, usage, agent=agent_name, mode=agent_mode)
                except Exception:
                    pass

                return text

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    try:
                        error = exc.response.json().get("error", {})
                        msg   = error.get("message", "") if isinstance(error, dict) else ""
                    except Exception:
                        msg = ""
                    if "not_found_error" in msg or "model:" in msg:
                        logger.warning("Model %s not available, trying next", model)
                        last_error = exc
                        continue
                raise

            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
                delay = min(_BASE_DELAY * (2 ** 1) + random.uniform(0, 1), _MAX_DELAY)
                if models.index(model) < len(models) - 1:
                    logger.warning("Timeout on model %s — retrying next model in %.1fs", model, delay)
                    time.sleep(delay)
                    last_error = exc
                    continue
                raise

            except Exception as exc:
                last_error = exc
                logger.warning("Request failed for model %s: %s", model, exc)
                continue

        if last_error:
            raise last_error
        raise RuntimeError("All models exhausted without a successful response.")

    def _stream_response(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> tuple:
        """Stream the response. Returns (text, usage_dict)."""
        import json as _json

        for attempt in range(_MAX_RETRIES + 1):
            try:
                chunks: List[str] = []
                usage: Dict[str, Any] = {}
                with self.client.stream(
                    "POST", self.full_url, json=payload, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            event = _json.loads(data_str)
                        except Exception:
                            continue
                        etype = event.get("type")
                        if etype == "message_start":
                            # input_tokens + cache tokens arrive here
                            usage.update(event.get("message", {}).get("usage", {}))
                        elif etype == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                chunks.append(delta.get("text", ""))
                        elif etype == "message_delta":
                            # output_tokens arrive here
                            usage.update(event.get("usage", {}))
                        elif etype == "message_stop":
                            break
                return "".join(chunks).strip(), usage

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    retry_after = exc.response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after else min(
                        _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), _MAX_DELAY
                    )
                    if attempt < _MAX_RETRIES:
                        logger.warning(
                            "Stream: rate limited (429) — retrying in %.1fs (attempt %d/%d)",
                            delay, attempt + 1, _MAX_RETRIES,
                        )
                        time.sleep(delay)
                        continue
                    raise
                if status >= 500:
                    delay = min(
                        _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), _MAX_DELAY
                    )
                    if attempt < _MAX_RETRIES:
                        logger.warning(
                            "Stream: server error %d — retrying in %.1fs (attempt %d/%d)",
                            status, delay, attempt + 1, _MAX_RETRIES,
                        )
                        time.sleep(delay)
                        continue
                raise  # 404, 400, 401 — raise immediately

            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException):
                delay = min(_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), _MAX_DELAY)
                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "Stream: timeout — retrying in %.1fs (attempt %d/%d)",
                        delay, attempt + 1, _MAX_RETRIES,
                    )
                    time.sleep(delay)
                    continue
                raise

        raise RuntimeError("Stream: max retries exceeded")

    def _parse_response(self, data: Dict[str, Any]) -> str:
        if data.get("type") == "message" and isinstance(data.get("content"), list):
            for item in data["content"]:
                if isinstance(item, dict) and item.get("type") == "text":
                    return item["text"].strip()
        raise RuntimeError(f"Unexpected Claude response structure: {data}")

    # ── Agentic loop (tool use) ──────────────────────────────────────────────

    def run_agent_loop(
        self,
        system_prompt: str,
        task: str,
        tools: List[Dict[str, Any]],
        tool_executor,                  # callable(name: str, inputs: dict) -> Any
        model_override: Optional[str] = None,
        max_iterations: int = 10,
        on_tool_call=None,              # optional callback(name, inputs) for progress logging
    ) -> str:
        """
        Agentic loop: sends task to Claude with tools, executes tool calls,
        feeds results back, and loops until stop_reason == 'end_turn'.

        Returns the final text response.
        """
        import json as _json

        model = model_override or os.getenv("AUDIT_MODEL", "claude-opus-4-8")
        messages: List[Dict[str, Any]] = [{"role": "user", "content": task}]
        headers = {
            "Content-Type":      "application/json",
            "X-Api-Key":         self.api_key,
            "anthropic-version": os.getenv("ANTHROPIC_API_VERSION", "2023-06-01"),
        }
        max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))

        for iteration in range(max_iterations):
            payload = {
                "model":      model,
                "max_tokens": max_tokens,
                "system":     system_prompt,
                "tools":      tools,
                "messages":   messages,
            }

            response = self._post_with_retry(payload, headers)
            data = response.json()

            try:
                import storage as _storage
                _storage.log_usage(model, data.get("usage", {}), agent="agentic_loop", mode="tool_use")
            except Exception:
                pass

            stop_reason = data.get("stop_reason")
            content     = data.get("content", [])

            # ── Claude finished ───────────────────────────────────────────────
            if stop_reason == "end_turn":
                text = next(
                    (b["text"] for b in content if b.get("type") == "text"), ""
                )
                logger.info(
                    "Agent loop finished in %d iteration(s): %d chars",
                    iteration + 1, len(text),
                )
                return text.strip()

            # ── Claude wants to call tools ────────────────────────────────────
            if stop_reason == "tool_use":
                # Append assistant's full response (with tool_use blocks) to history
                messages.append({"role": "assistant", "content": content})

                tool_results = []
                for block in content:
                    if block.get("type") != "tool_use":
                        continue

                    name      = block["name"]
                    inputs    = block.get("input", {})
                    use_id    = block["id"]

                    logger.info("Agent tool call [%d]: %s(%s)", iteration + 1, name, inputs)
                    if on_tool_call:
                        on_tool_call(name, inputs)

                    try:
                        result = tool_executor(name, inputs)
                    except Exception as exc:
                        logger.warning("Tool %s failed: %s", name, exc)
                        result = {"error": str(exc)}

                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": use_id,
                        "content":     _json.dumps(result, ensure_ascii=False, default=str),
                    })

                messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason (max_tokens, etc.) — return whatever we have
            logger.warning("Agent loop: unexpected stop_reason=%s", stop_reason)
            text = next((b["text"] for b in content if b.get("type") == "text"), "")
            return text.strip()

        raise RuntimeError(f"Agent loop exhausted after {max_iterations} iterations without end_turn")

    # ── Structured tool-use call ─────────────────────────────────────────────

    def call_tool(
        self,
        user_message: str,
        tool: Dict[str, Any],
        system_prompt: Optional[str] = None,
        model_override: Optional[str] = None,
        cached_context: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a single tool-use request (non-streaming) and return the tool input dict.

        Uses tool_choice={"type": "any"} to force Claude to call the tool.
        Supports cached_context (same prompt-cache mechanic as chat_with_agent).
        Returns None on any error so callers can fall back gracefully.
        """
        model = model_override or self.model_name
        headers = {
            "Content-Type":      "application/json",
            "X-Api-Key":         self.api_key,
            "anthropic-version": os.getenv("ANTHROPIC_API_VERSION", "2023-06-01"),
            "anthropic-beta":    "prompt-caching-2024-07-31",
        }
        max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))
        payload: Dict[str, Any] = {
            "model":       model,
            "max_tokens":  max_tokens,
            "messages":    [{"role": "user", "content": user_message}],
            "tools":       [tool],
            "tool_choice": {"type": "any"},
        }
        if system_prompt or cached_context:
            if cached_context:
                _cache_ttl = os.getenv("CACHE_TTL", "1h")
                blocks = [
                    {"type": "text", "text": cached_context,
                     "cache_control": {"type": "ephemeral", "ttl": _cache_ttl}},
                ]
                if system_prompt:
                    blocks.append({"type": "text", "text": system_prompt})
                payload["system"] = blocks
            else:
                payload["system"] = system_prompt

        try:
            response = self._post_with_retry(payload, headers)
            data = response.json()
            try:
                import storage as _storage
                _storage.log_usage(model, data.get("usage", {}), agent="call_tool", mode="tool_use")
            except Exception:
                pass
            for block in data.get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    return block.get("input", {})
            logger.warning("call_tool: no tool_use block in response")
            return None
        except Exception as exc:
            logger.warning("call_tool failed: %s", exc)
            return None

    def close(self) -> None:
        """Close both sync and async HTTP clients. Call on graceful shutdown."""
        try:
            self.client.close()
        except Exception:
            pass

    async def aclose(self) -> None:
        """Async close — awaited to properly drain the async client connection pool."""
        try:
            await self._async_client.aclose()
        except Exception:
            pass

    # ── Public API (sync) ────────────────────────────────────────────────────

    def chat_with_agent(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        model_override: Optional[str] = None,
        cached_context: Optional[str] = None,
        agent_name: str = "",
        agent_mode: str = "",
    ) -> str:
        return self._send_message_request(
            user_message, system=system_prompt, history=history,
            model_override=model_override, cached_context=cached_context,
            agent_name=agent_name, agent_mode=agent_mode,
        )

    # ── Public API (async) ───────────────────────────────────────────────────
    # Async versions use httpx.AsyncClient for true I/O concurrency.
    # Benefit: multiple achat_with_agent() calls in asyncio.gather() interleave
    # HTTP I/O without blocking threads — better than ThreadPoolExecutor for
    # I/O-bound parallel agent runs.

    def _build_request_payload(
        self,
        prompt: str,
        system: Optional[str],
        history: Optional[List[Dict[str, Any]]],
        model: str,
        cached_context: Optional[str],
    ) -> tuple:
        """Build (payload, headers) for a messages API call."""
        messages  = self._build_messages(prompt, history=history)
        headers   = {
            "Content-Type":      "application/json",
            "X-Api-Key":         self.api_key,
            "anthropic-version": os.getenv("ANTHROPIC_API_VERSION", "2023-06-01"),
            "anthropic-beta":    "prompt-caching-2024-07-31",
        }
        max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))
        payload: Dict[str, Any] = {
            "model":      model,
            "messages":   messages,
            "max_tokens": max_tokens,
        }
        if system or cached_context:
            if cached_context:
                _cache_ttl = os.getenv("CACHE_TTL", "1h")
                blocks: List[Dict[str, Any]] = [
                    {"type": "text", "text": cached_context,
                     "cache_control": {"type": "ephemeral", "ttl": _cache_ttl}},
                ]
                if system:
                    blocks.append({"type": "text", "text": system})
                payload["system"] = blocks
            else:
                payload["system"] = system
        return payload, headers

    async def achat_with_agent(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        model_override: Optional[str] = None,
        cached_context: Optional[str] = None,
        agent_name: str = "",
        agent_mode: str = "",
    ) -> str:
        """
        Async version of chat_with_agent using httpx.AsyncClient.

        Multiple achat_with_agent() calls in asyncio.gather() truly interleave
        HTTP I/O — unlike sync calls in ThreadPoolExecutor which block threads.
        """
        import asyncio

        with self._model_lock:
            base_models = list(dict.fromkeys(self.fallback_models))

        if model_override and model_override not in base_models:
            models = [model_override] + base_models
        elif model_override:
            models = [model_override] + [m for m in base_models if m != model_override]
        else:
            models = base_models

        last_error = None
        client = self._async_client  # reuse persistent client — avoids per-call setup overhead
        for model in models:
            payload, headers = self._build_request_payload(
                user_message, system_prompt, history, model, cached_context
            )
            try:
                for attempt in range(_MAX_RETRIES + 1):
                    try:
                        self._check_circuit_breaker()
                        response = await client.post(
                            self.full_url, json=payload, headers=headers
                        )
                        response.raise_for_status()
                        self._reset_circuit()
                        data  = response.json()
                        text  = self._parse_response(data)
                        usage = data.get("usage", {})

                        try:
                            import storage as _storage
                            _storage.log_usage(model, usage, agent=agent_name, mode=agent_mode)
                        except Exception:
                            pass

                        return text

                    except httpx.HTTPStatusError as exc:
                        status = exc.response.status_code
                        if status == 429:
                            self._record_429()
                            retry_after = exc.response.headers.get("retry-after")
                            delay = float(retry_after) if retry_after else min(
                                _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), _MAX_DELAY
                            )
                            if attempt < _MAX_RETRIES:
                                logger.warning(
                                    "async: rate limited (429) — retrying in %.1fs", delay
                                )
                                await asyncio.sleep(delay)
                                continue
                            raise
                        if status == 404:
                            last_error = exc
                            break  # try next model
                        if status >= 500:
                            delay = min(
                                _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), _MAX_DELAY
                            )
                            if attempt < _MAX_RETRIES:
                                await asyncio.sleep(delay)
                                continue
                            raise
                        raise

                    except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as exc:
                        delay = min(_BASE_DELAY * 2 + random.uniform(0, 1), _MAX_DELAY)
                        if attempt < _MAX_RETRIES:
                            await asyncio.sleep(delay)
                            last_error = exc
                            continue
                        raise

            except Exception as exc:
                last_error = exc
                logger.warning("async request failed for model %s: %s", model, exc)
                continue

        if last_error:
            raise last_error
        raise RuntimeError("async: all models exhausted without a successful response.")

    async def acall_tool(
        self,
        user_message: str,
        tool: Dict[str, Any],
        system_prompt: Optional[str] = None,
        model_override: Optional[str] = None,
        cached_context: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Async version of call_tool — with retry on 429/5xx, matching sync call_tool behaviour."""
        import asyncio

        model = model_override or self.model_name
        headers = {
            "Content-Type":      "application/json",
            "X-Api-Key":         self.api_key,
            "anthropic-version": os.getenv("ANTHROPIC_API_VERSION", "2023-06-01"),
            "anthropic-beta":    "prompt-caching-2024-07-31",
        }
        max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))
        payload: Dict[str, Any] = {
            "model":       model,
            "max_tokens":  max_tokens,
            "messages":    [{"role": "user", "content": user_message}],
            "tools":       [tool],
            "tool_choice": {"type": "any"},
        }
        if system_prompt or cached_context:
            if cached_context:
                _cache_ttl = os.getenv("CACHE_TTL", "1h")
                blocks = [
                    {"type": "text", "text": cached_context,
                     "cache_control": {"type": "ephemeral", "ttl": _cache_ttl}},
                ]
                if system_prompt:
                    blocks.append({"type": "text", "text": system_prompt})
                payload["system"] = blocks
            else:
                payload["system"] = system_prompt

        for attempt in range(_MAX_RETRIES + 1):
            try:
                self._check_circuit_breaker()
                response = await self._async_client.post(self.full_url, json=payload, headers=headers)
                response.raise_for_status()
                self._reset_circuit()
                data = response.json()
                try:
                    import storage as _storage
                    _storage.log_usage(model, data.get("usage", {}), agent="acall_tool", mode="tool_use")
                except Exception:
                    pass
                for block in data.get("content", []):
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        return block.get("input", {})
                logger.warning("acall_tool: no tool_use block in response")
                return None

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    self._record_429()
                    retry_after = exc.response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after else min(
                        _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), _MAX_DELAY
                    )
                    if attempt < _MAX_RETRIES:
                        logger.warning("acall_tool: rate limited (429) — retrying in %.1fs (attempt %d/%d)",
                                       delay, attempt + 1, _MAX_RETRIES)
                        await asyncio.sleep(delay)
                        continue
                elif status >= 500:
                    delay = min(_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), _MAX_DELAY)
                    if attempt < _MAX_RETRIES:
                        logger.warning("acall_tool: server error %d — retrying in %.1fs (attempt %d/%d)",
                                       status, delay, attempt + 1, _MAX_RETRIES)
                        await asyncio.sleep(delay)
                        continue
                logger.warning("acall_tool failed: %s", exc)
                return None

            except Exception as exc:
                logger.warning("acall_tool failed: %s", exc)
                return None

        logger.warning("acall_tool: max retries exceeded")
        return None
