from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class Pool:
    link: str
    range: str
    token: str
    amount: float  # Changed from int to float to support decimal amounts
    upper_range: Optional[float] = None  # Upper price range
    lower_range: Optional[float] = None  # Lower price range
    owner_chat_id: Optional[int] = None
    last_status: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
