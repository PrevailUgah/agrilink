import asyncio
import random
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- SQLALCHEMY IMPORTS (The Database Layer) ---
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- 1. DATABASE SETUP (SQLite) ---
# This creates a real file 'agrilink.db' in your folder.
SQLALCHEMY_DATABASE_URL = "sqlite:///./agrilink.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. DATABASE MODELS (The Tables) ---
class BuyerDB(Base):
    __tablename__ = "buyers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    needs = Column(String) # Stored as comma-separated string: "tomatoes,onions"
    price_per_basket = Column(Integer)

# Create the tables automatically
Base.metadata.create_all(bind=engine)

# --- 3. APP CONFIGURATION ---
app = FastAPI(title="AgriLink Neural Dispatch v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4. SEED DATA (Run once to populate DB) ---
# In a real app, this is a separate script.
def seed_database(db: Session):
    if db.query(BuyerDB).first():
        return # DB already has data
    
    print("--- SEEDING DATABASE ---")
    buyers = [
        BuyerDB(name="Alhaji Musa Processing", location="zaria", needs="tomatoes,pepper", price_per_basket=5000),
        BuyerDB(name="Lagos Mile 12 Aggregator", location="lagos", needs="tomatoes,onions", price_per_basket=12000),
        BuyerDB(name="Shoprite Logistics Abuja", location="abuja", needs="tomatoes,cabbage", price_per_basket=15000),
        BuyerDB(name="Kano Central Market", location="kano", needs="onions,grains", price_per_basket=7000)
    ]
    db.add_all(buyers)
    db.commit()

# --- 5. Pydantic Models (Frontend Communication) ---
class IncomingMessage(BaseModel):
    farmer_name: str
    message: str

class DispatchResult(BaseModel):
    status: str
    extracted_data: dict
    matched_buyer: Optional[str] = None
    estimated_payout: int
    route_id: str

# --- 6. AI SIMULATION LAYER ---
async def simulate_llm_extraction(text: str):
    await asyncio.sleep(1.0)
    text_lower = text.lower()
    product = "unknown"
    location = "unknown"
    quantity = 0
    
    # NLP Logic
    if "tomato" in text_lower: product = "tomatoes"
    elif "onion" in text_lower: product = "onions"
    elif "pepper" in text_lower: product = "pepper"
    
    if "zaria" in text_lower: location = "zaria"
    elif "lagos" in text_lower: location = "lagos"
    elif "abuja" in text_lower: location = "abuja"
    elif "kano" in text_lower: location = "kano"
    
    import re
    numbers = re.findall(r'\d+', text)
    if numbers: quantity = int(numbers[0])
        
    return {"product": product, "quantity": quantity, "location": location}

# --- 7. API ENDPOINTS ---

@app.on_event("startup")
def startup_event():
    # Initialize DB on startup
    db = SessionLocal()
    seed_database(db)
    db.close()

@app.post("/analyze-dispatch", response_model=DispatchResult)
async def process_dispatch(msg: IncomingMessage, db: Session = Depends(get_db)):
    print(f"\n[REQUEST] Farmer: {msg.farmer_name} | Msg: {msg.message}")
    
    # 1. Extract
    extracted = await simulate_llm_extraction(msg.message)
    
    if extracted['product'] == "unknown":
        raise HTTPException(status_code=400, detail="Product not recognized.")

    # 2. Query Database (The "Fixed" Logic)
    # This now searches the Real SQL Database, not a list.
    
    # Logic: Find buyers who need this product
    possible_buyers = db.query(BuyerDB).filter(
        BuyerDB.needs.contains(extracted['product'])
    ).all()
    
    best_match = None
    highest_payout = 0
    
    for buyer in possible_buyers:
        # Check location match (simplified)
        # In a real app, we would calculate distance
        payout = buyer.price_per_basket * extracted['quantity']
        
        # Priority to local buyers, or highest price
        if buyer.location == extracted['location']:
            payout += 5000 # Bonus for proximity
            
        if payout > highest_payout:
            highest_payout = payout
            best_match = buyer

    # 3. Response
    if best_match:
        return {
            "status": "DISPATCH_APPROVED",
            "extracted_data": extracted,
            "matched_buyer": f"{best_match.name} ({best_match.location.upper()})",
            "estimated_payout": highest_payout,
            "route_id": f"RTE-{random.randint(1000,9999)}"
        }
    else:
        return {
            "status": "PENDING_WAREHOUSE",
            "extracted_data": extracted,
            "matched_buyer": "None",
            "estimated_payout": 0,
            "route_id": "HOLD-000"
        }