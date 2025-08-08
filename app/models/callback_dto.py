from typing_extensions import TypedDict
from typing import Dict, Optional


class CallbackDTO(TypedDict):
    """Callback data transfer object for processing callbacks."""
    url: str
    method: str
    headers: Dict[str, str]