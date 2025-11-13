"""
Database Schemas for Mazzura

Each Pydantic model represents a collection in MongoDB. The collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Userprofile(BaseModel):
    """
    Fashion DNA / Profile
    Collection: "userprofile"
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address (unique)")
    body_type: Optional[str] = Field(None, description="Body type descriptor")
    skin_tone: Optional[str] = Field(None, description="Skin tone descriptor")
    preferred_colors: List[str] = Field(default_factory=list, description="List of preferred colors")
    vibe: Optional[str] = Field(None, description="Emotional style vibe e.g. minimal, bold, soft")
    location: Optional[str] = Field(None, description="City or region for weather/context")

class Wardrobeitem(BaseModel):
    """
    Smart Closet item
    Collection: "wardrobeitem"
    """
    owner_email: str = Field(..., description="Owner email")
    name: str = Field(..., description="Item name")
    category: str = Field(..., description="top, bottom, outerwear, footwear, accessory")
    color: Optional[str] = Field(None, description="Primary color")
    size: Optional[str] = Field(None, description="Size label")
    image_url: Optional[str] = Field(None, description="Image URL")
    brand: Optional[str] = Field(None, description="Brand name")
    price: Optional[float] = Field(None, ge=0, description="Price paid")
    tags: List[str] = Field(default_factory=list, description="Style tags")
    warmth: Optional[int] = Field(None, ge=0, le=10, description="Warmth score 0-10")

class Outfit(BaseModel):
    """
    Outfit generated or suggested
    Collection: "outfit"
    """
    owner_email: str = Field(..., description="Owner email")
    title: str = Field(..., description="Outfit title")
    items: List[dict] = Field(default_factory=list, description="List of item snapshots in outfit")
    mood: Optional[str] = None
    weather: Optional[str] = None
    event: Optional[str] = None

class Challenge(BaseModel):
    """
    Community style challenges
    Collection: "challenge"
    """
    title: str
    prompt: str
    reward_points: int = 50
