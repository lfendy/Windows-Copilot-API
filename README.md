# Copilot API

An unofficial Python wrapper for Microsoft Copilot's consumer chat
(`copilot.microsoft.com`). It replays Copilot's own chat protocol directly over
HTTP — **no browser needed at request time** — solving the proof-of-work
challenge in-process and clearing Cloudflare with Chrome TLS impersonation.

> **Deep dive / recreation:** see [docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)
> for the full protocol, the hashcash reverse-engineering, and the auth flow.

## Quick start

### 1. Install

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m playwright install chromium   # one-time, for sign-in only
```

### 2. Sign in once

Microsoft geo-restricts the *anonymous* chat experience (e.g. in India the
anonymous socket returns `chat-service-unavailable`). Signing in with a Microsoft
account works in those regions, so authenticate once:

```powershell
.\venv\Scripts\python.exe -m copilot login
```

A browser window opens — sign in, wait for the chat to load, then press Enter.
The session is saved under `session/` and reused automatically afterwards. You
only need to repeat this if the login is revoked or expires.

### 3. Chat

```python
from copilot import CopilotSession

chat = CopilotSession()            # loads your signed-in auth once

# buffered — full reply as a string
print(chat.ask("Hello!"))

# streamed — text as it arrives
for chunk in chat.stream("Tell me a joke"):
    print(chunk, end="", flush=True)

chat.reset()                       # drop context and start a fresh chat
```

One `CopilotSession` keeps a single conversation, so successive `ask`/`stream`
calls share context like a real chat. The short-lived access token is refreshed
transparently from your saved profile — no need to re-run `login`.

Run the included example directly:

```powershell
.\venv\Scripts\python.exe main.py
```

## Options

**Anonymous (no sign-in)** — works only where consumer Copilot is available:

```python
chat = CopilotSession(anonymous=True)
```

**Via a proxy** — route through a supported region if anonymous chat is blocked
where you are:

```python
chat = CopilotSession(proxy="http://user:pass@host:port")   # or socks5://
```

## CLI

```powershell
.\venv\Scripts\python.exe -m copilot login        # interactive sign-in
.\venv\Scripts\python.exe -m copilot ask "hi"     # one-shot reply (browser driver)
```

## How it works

`copilot/client.py` (`Copilot`) speaks the protocol directly over
[`curl_cffi`](https://github.com/lexiforest/curl_cffi):

1. **Cloudflare** — Chrome impersonation clears it; no browser needed.
2. **Conversation** — `POST /c/api/conversations` returns a conversation id.
3. **Proof-of-work** — the chat socket sends a `hashcash` (or `copilot`)
   challenge before streaming; it's solved in-process and the message is
   re-sent, mirroring the official client. See `copilot/challenges.py`.

`CopilotSession` (`copilot/session.py`) is the recommended entry point: it wraps
the low-level `Copilot` driver with auth handling and conversation state. The
Playwright driver in `copilot/browser.py` (`BrowserCopilot`) is an optional
fallback used only for sign-in and the `ask` CLI command.

## Project layout

| Path | Purpose |
| --- | --- |
| `copilot/session.py` | `CopilotSession` — high-level chat (use this) |
| `copilot/client.py` | `Copilot` — pure-HTTP protocol driver |
| `copilot/auth.py` | signed-in token caching / refresh |
| `copilot/challenges.py` | proof-of-work solvers |
| `copilot/browser.py` | Playwright fallback (login + CLI) |
| `main.py` | runnable example |
