"""High-level, reusable Copilot session — the one way to use this package.

Create a :class:`CopilotSession` once and call :meth:`ask` / :meth:`stream` as
many times as you like. It loads the signed-in auth a single time (refreshing the
short-lived access token transparently when it goes stale) and keeps one
conversation, so successive turns share context like a real chat.

    from copilot import CopilotSession

    chat = CopilotSession()
    print(chat.ask("Hello!"))                 # buffered: returns the full reply
    for chunk in chat.stream("And again?"):   # streamed: yields text as it lands
        print(chunk, end="", flush=True)
    chat.reset()                              # start a fresh, context-free chat
"""

import time
from typing import Generator, Optional, Union

from .auth import AUTH_MAX_AGE, load_auth
from .client import Copilot
from .models import Conversation, ImageResponse


class CopilotSession:
    """A long-lived Copilot chat: one object, many requests.

    Parameters
    ----------
    anonymous:
        Skip sign-in and talk to Copilot anonymously. Only works where the
        anonymous consumer experience is available (it is geo-blocked in some
        regions, e.g. India). Default ``False`` uses the signed-in session.
    proxy:
        Optional ``scheme://user:pass@host:port`` proxy, applied to both the
        auth refresh and every request.
    max_age:
        Seconds a cached access token is trusted before it is refreshed.
    """

    def __init__(
        self,
        anonymous: bool = False,
        proxy: Optional[str] = None,
        max_age: int = AUTH_MAX_AGE,
    ):
        self._copilot = Copilot()
        self._anonymous = anonymous
        self._proxy = proxy
        self._max_age = max_age
        self._auth: Optional[dict] = None
        self._conversation: Optional[Conversation] = None

    def stream(
        self,
        prompt: str,
        *,
        new_conversation: bool = False,
        **kwargs,
    ) -> Generator[Union[str, ImageResponse], None, None]:
        """Stream the reply to ``prompt``, yielding text chunks as they arrive.

        Continues the running conversation by default; pass
        ``new_conversation=True`` (or call :meth:`reset`) to start fresh.
        Image results are yielded as :class:`~copilot.models.ImageResponse`.
        """
        if new_conversation:
            self._conversation = None

        auth = self._fresh_auth()
        kw = dict(
            stream=True,
            proxy=self._proxy,
            cookies=auth["cookies"] if auth else None,
            access_token=auth["access_token"] if auth else None,
            **kwargs,
        )
        if self._conversation is None:
            # First turn: have the driver hand back a Conversation we can reuse.
            kw["return_conversation"] = True
        else:
            kw["conversation"] = self._conversation

        for item in self._copilot.create_completion(prompt, **kw):
            if isinstance(item, Conversation):
                self._conversation = item
            else:
                yield item

    def ask(self, prompt: str, *, new_conversation: bool = False, **kwargs) -> str:
        """Return the full reply to ``prompt`` as a single string (text only)."""
        return "".join(
            chunk
            for chunk in self.stream(prompt, new_conversation=new_conversation, **kwargs)
            if isinstance(chunk, str)
        )

    def reset(self) -> None:
        """Forget the current conversation; the next call starts a fresh one."""
        self._conversation = None

    def _fresh_auth(self) -> Optional[dict]:
        """Return current signed-in auth, refreshing it when stale (or None)."""
        if self._anonymous:
            return None
        if self._auth is None or (time.time() - self._auth.get("saved_at", 0)) >= self._max_age:
            self._auth = load_auth(max_age=self._max_age, proxy=self._proxy)
        return self._auth
