import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timedelta

from database import db, create_document, get_documents
from schemas import Event, Service, Booking

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Events & Services API"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Helper to convert Mongo documents

def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

# Seed endpoint to populate sample data
@app.post("/api/seed", response_model=dict)
async def seed_sample_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    created = {"events": 0, "services": 0}

    # Only seed if empty
    if db["event"].count_documents({}) == 0:
        now = datetime.utcnow()
        samples_events = [
            Event(
                title="Summer Music Fest",
                description="An open-air festival with indie and electronic artists.",
                date=(now + timedelta(days=14)).strftime("%Y-%m-%d"),
                location="Central Park",
                price=49.0,
                featured=True,
                image_url="https://images.unsplash.com/photo-1472653431158-6364773b2a56?q=80&w=1600&auto=format&fit=crop",
                tags=["music", "festival", "outdoor"],
            ),
            Event(
                title="Tech Talks Night",
                description="Lightning talks on AI, Web, and Cloud.",
                date=(now + timedelta(days=7)).strftime("%Y-%m-%d"),
                location="Innovation Hub",
                price=0.0,
                featured=True,
                image_url="https://images.unsplash.com/photo-1551836022-d5d88e9218df?q=80&w=1600&auto=format&fit=crop",
                tags=["tech", "networking"],
            ),
            Event(
                title="Art & Wine Evening",
                description="Sip and paint with local artists guiding the way.",
                date=(now + timedelta(days=21)).strftime("%Y-%m-%d"),
                location="Studio 54B",
                price=35.0,
                featured=False,
                image_url="https://images.unsplash.com/photo-1490474418585-ba9bad8fd0ea?q=80&w=1600&auto=format&fit=crop",
                tags=["art", "social"],
            ),
            Event(
                title="Community Yoga",
                description="Morning flow suitable for all levels.",
                date=(now + timedelta(days=3)).strftime("%Y-%m-%d"),
                location="Riverside Lawn",
                price=10.0,
                featured=False,
                image_url="https://images.unsplash.com/photo-1552196563-55cd4e45efb3?q=80&w=1600&auto=format&fit=crop",
                tags=["wellness"],
            ),
        ]
        for ev in samples_events:
            create_document("event", ev)
            created["events"] += 1

    if db["service"].count_documents({}) == 0:
        samples_services = [
            Service(
                name="Event Photography",
                description="Professional photo coverage for events and portraits.",
                price=120.0,
                duration_minutes=120,
                image_url="https://images.unsplash.com/photo-1487412912498-0447578fcca8?q=80&w=1600&auto=format&fit=crop",
                category="Media",
            ),
            Service(
                name="Catering Essentials",
                description="Buffet-style catering for small to medium gatherings.",
                price=300.0,
                duration_minutes=0,
                image_url="https://images.unsplash.com/photo-1551218808-94e220e084d2?q=80&w=1600&auto=format&fit=crop",
                category="Food",
            ),
            Service(
                name="DJ & Sound",
                description="Music and sound system for parties and events.",
                price=200.0,
                duration_minutes=240,
                image_url="https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?q=80&w=1600&auto=format&fit=crop",
                category="Entertainment",
            ),
        ]
        for sv in samples_services:
            create_document("service", sv)
            created["services"] += 1

    return {"status": "ok", "created": created}

# Events endpoints

@app.post("/api/events", response_model=dict)
async def create_event(event: Event):
    event_id = create_document("event", event)
    return {"id": event_id}

@app.get("/api/events", response_model=List[dict])
async def list_events(q: Optional[str] = None, featured: Optional[bool] = None, limit: int = 50):
    filt = {}
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}
    if featured is not None:
        filt["featured"] = featured
    docs = get_documents("event", filt, limit)
    return [serialize_doc(d) for d in docs]

# Services endpoints

@app.post("/api/services", response_model=dict)
async def create_service(service: Service):
    service_id = create_document("service", service)
    return {"id": service_id}

@app.get("/api/services", response_model=List[dict])
async def list_services(q: Optional[str] = None, category: Optional[str] = None, limit: int = 50):
    filt = {}
    if q:
        filt["name"] = {"$regex": q, "$options": "i"}
    if category:
        filt["category"] = category
    docs = get_documents("service", filt, limit)
    return [serialize_doc(d) for d in docs]

# Booking endpoint (can book events or services)

@app.post("/api/bookings", response_model=dict)
async def create_booking(booking: Booking):
    if booking.item_type not in ["event", "service"]:
        raise HTTPException(status_code=400, detail="item_type must be 'event' or 'service'")

    # Validate that the referenced item exists
    try:
        _id = ObjectId(booking.item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item_id")

    coll = db[booking.item_type]
    if coll.find_one({"_id": _id}) is None:
        raise HTTPException(status_code=404, detail=f"{booking.item_type.capitalize()} not found")

    booking_id = create_document("booking", booking)
    return {"id": booking_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
