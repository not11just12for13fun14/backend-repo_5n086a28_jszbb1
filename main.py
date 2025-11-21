import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

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
