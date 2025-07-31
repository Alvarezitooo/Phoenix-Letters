"""
Entités de données pour le domaine utilisateur.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class UserTier(Enum):
    FREE = "free"
    PREMIUM = "premium"
    PREMIUM_PLUS = "premium_plus"

@dataclass
class UserSubscription:
    current_tier: UserTier = UserTier.FREE
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    auto_renewal: bool = False

@dataclass
class User:
    id: uuid.UUID
    email: str
    username: Optional[str] = None
    status: str = 'pending'
    email_verified: bool = False
    newsletter_opt_in: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    subscription: UserSubscription = field(default_factory=UserSubscription)
