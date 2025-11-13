import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import create_document, get_documents, db
from schemas import Userprofile, Wardrobeitem, Outfit, Challenge

app = FastAPI(title="Mazzura API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Mazzura Backend ✅", "version": "0.1.0"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from Mazzura API!"}

# -----------------------------
# Health / Database Test
# -----------------------------
@app.get("/test")
def test_database():
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
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# -----------------------------
# Schemas Introspection (for viewers)
# -----------------------------
@app.get("/schema")
def get_schema():
    def model_to_schema(m):
        fields = {}
        for name, field in m.model_fields.items():
            fields[name] = {
                "type": str(field.annotation),
                "required": field.is_required(),
                "default": None if field.is_required() else field.default,
                "description": getattr(field, 'description', None)
            }
        return {"collection": m.__name__.lower(), "fields": fields}

    return {
        "userprofile": model_to_schema(Userprofile),
        "wardrobeitem": model_to_schema(Wardrobeitem),
        "outfit": model_to_schema(Outfit),
        "challenge": model_to_schema(Challenge),
    }

# -----------------------------
# Profiles
# -----------------------------
@app.post("/api/profile")
def create_profile(profile: Userprofile):
    try:
        inserted_id = create_document("userprofile", profile)
        return {"id": inserted_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile")
def get_profile(email: str = Query(..., description="Email to fetch profile")):
    try:
        docs = get_documents("userprofile", {"email": email}, limit=1)
        if not docs:
            raise HTTPException(status_code=404, detail="Profile not found")
        # Convert ObjectId to str
        doc = docs[0]
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Wardrobe
# -----------------------------
@app.post("/api/wardrobe")
def add_wardrobe_item(item: Wardrobeitem):
    try:
        inserted_id = create_document("wardrobeitem", item)
        return {"id": inserted_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/wardrobe")
def list_wardrobe(email: str = Query(..., description="Owner email")):
    try:
        docs = get_documents("wardrobeitem", {"owner_email": email})
        result = []
        for d in docs:
            d["id"] = str(d.pop("_id"))
            result.append(d)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Outfit Generation (simple rules placeholder)
# -----------------------------
class OutfitRequest(BaseModel):
    email: str
    mood: Optional[str] = None
    weather: Optional[str] = None  # e.g., cold, warm, rainy
    event: Optional[str] = None

@app.post("/api/outfits/generate")
def generate_outfit(req: OutfitRequest):
    try:
        items = get_documents("wardrobeitem", {"owner_email": req.email})
        if not items:
            raise HTTPException(status_code=404, detail="No wardrobe items found")

        # Basic categorization
        by_cat: Dict[str, List[Dict[str, Any]]] = {}
        for it in items:
            cat = (it.get("category") or "").lower()
            by_cat.setdefault(cat, []).append(it)

        def pick_from(cat_list: List[Dict[str, Any]]):
            if not cat_list:
                return None
            # Mood/Color bias
            if req.mood:
                mood = req.mood.lower()
                colored = [i for i in cat_list if (i.get("color") or "").lower() in mood or any(t.lower() in mood for t in i.get("tags", []))]
                if colored:
                    return colored[0]
            # Weather bias by warmth
            if req.weather:
                w = req.weather.lower()
                if w in ["cold", "chilly"]:
                    scored = sorted(cat_list, key=lambda x: -(x.get("warmth") or 0))
                    return scored[0]
                if w in ["hot", "warm"]:
                    scored = sorted(cat_list, key=lambda x: (x.get("warmth") or 0))
                    return scored[0]
            return cat_list[0]

        selected = []
        for cat in ["top", "bottom", "footwear"]:
            sel = pick_from(by_cat.get(cat, []))
            if sel:
                selected.append({k: (str(v) if k == "_id" else v) for k, v in sel.items() if k != "_id"})

        # Optional outerwear if cold
        if req.weather and req.weather.lower() in ["cold", "chilly"]:
            outer = pick_from(by_cat.get("outerwear", []))
            if outer:
                selected.append({k: (str(v) if k == "_id" else v) for k, v in outer.items() if k != "_id"})

        if not selected:
            raise HTTPException(status_code=400, detail="Could not compose an outfit from wardrobe")

        outfit_doc = Outfit(
            owner_email=req.email,
            title=f"Auto outfit - {req.mood or 'style'} / {req.weather or 'weather'}",
            items=selected,
            mood=req.mood,
            weather=req.weather,
            event=req.event,
        )
        inserted_id = create_document("outfit", outfit_doc)
        return {"id": inserted_id, "items": selected, "title": outfit_doc.title}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Community Challenges (static seed)
# -----------------------------
@app.get("/api/challenges")
def get_challenges():
    return [
        {"title": "Monochrome Monday", "prompt": "Build a single-tone look with texture play", "reward_points": 50},
        {"title": "Festival Fusion", "prompt": "Blend regional craft with streetwear", "reward_points": 75},
        {"title": "Eco Remix", "prompt": "Re-style one item 3 ways for 3 days", "reward_points": 100},
    ]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
