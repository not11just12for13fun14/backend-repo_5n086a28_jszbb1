"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Event & Service app schemas

class Event(BaseModel):
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    date: Optional[str] = Field(None, description="ISO date string for the event")
    location: Optional[str] = Field(None, description="Event location")
    price: Optional[float] = Field(0, ge=0, description="Ticket price")
    featured: bool = Field(False, description="Whether the event is featured")
    image_url: Optional[str] = Field(None, description="Cover image URL")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags")

class Service(BaseModel):
    name: str = Field(..., description="Service name")
    description: Optional[str] = Field(None, description="Service description")
    price: Optional[float] = Field(0, ge=0, description="Base price")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Typical duration in minutes")
    image_url: Optional[str] = Field(None, description="Image URL")
    category: Optional[str] = Field(None, description="Category")

class Booking(BaseModel):
    item_type: str = Field(..., description="'event' or 'service'")
    item_id: str = Field(..., description="ID of the event/service")
    customer_name: str = Field(..., description="Customer full name")
    customer_email: str = Field(..., description="Customer email")
    scheduled_for: Optional[str] = Field(None, description="ISO datetime for booking if applicable")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
