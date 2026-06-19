"""
Copilot API - An unofficial Python wrapper for Microsoft Copilot consumer chat.

Basic usage — create one session, reuse it for many requests:

>>> from copilot import CopilotSession
>>> chat = CopilotSession()
>>> chat.ask("Hello!")                      # buffered: full reply as a string
>>> for chunk in chat.stream("And again?"): # streamed: text as it arrives
...     print(chunk, end="")
"""

__version__ = '1.0.0'

from .auth import load_auth
from .browser import BrowserCopilot
from .client import Copilot
from .session import CopilotSession

__all__ = [
    'CopilotSession',
    'Copilot',
    'BrowserCopilot',
    'load_auth',
]
