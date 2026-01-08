from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime
import uuid
import logging

# --- 🌍 SYSTEM LOGGING ---
# In a distributed logistics network, visibility is survival.
# We track every heartbeat of the system from Lagos to Kano.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgriLink-Neural-Core")

# --- 🚀 NEURAL CORE INITIALIZATION ---
# This isn't just an API; it's the digital backbone for food security.
# Version 2.2 focuses on latency reduction for EDGE networks (2G/3G areas).
app = FastAPI(
    title="AgriLink Neural Dispatch API",
    description="High-performance logistics engine connecting Rural Supply to Urban Demand.",
    version="2.2.0"
)

# --- 🔓 CROSS-ORIGIN RESOURCE SHARING (CORS) ---
# We allow our "Zero-Build" frontend to connect from anywhere.
# In production, we'd lock this to our specific domain, but for the showcase,
# we want zero friction.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🏗️ DATA MODELS (The Schema of Truth) ---
# We use Pydantic to enforce data integrity. 
# Bad data in a supply chain leads to rotten food. We don't allow that.

class ListingRequest(BaseModel):
    farmer_id: str
    item_name: str
    quantity: float
    unit: str = "kg"
    location_zone: str
    price_total: float

class BuyRequest(BaseModel):
    buyer_id: str
    listing_id: str

class MarketListing(BaseModel):
    id: str
    item: str
    qty: float
    unit: str
    zone: str
    price: float
    seller: str
    time: str
    type: Literal['supply', 'demand']
    
    # Auto-generated timestamp for analytics
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- 💾 IN-MEMORY STATE LAYER ---
# ARCHITECTURAL NOTE:
# For this prototype/hackathon build, we keep state 'hot' in RAM.
# This ensures instant read/write speeds (<10ms).
#
# ROADMAP: In a deployed environment, this is replaced by:
# 1. Redis (Hot Cache) for the real-time feed.
# 2. PostgreSQL (Persistent Storage) for ledger history.
market_feed: List[MarketListing] = [
    MarketListing(
        id="1",
        item="Onions",
        qty=50,
        unit="Baskets",
        zone="North-West (Kano)",
        price=8500,
        seller="Sani Farms",
        time="2m ago",
        type="supply"
    ),
    MarketListing(
        id="2", 
        item="Rice 50kg", 
        qty=200, 
        unit="Bags", 
        zone="Lagos", 
        price=65000, 
        seller="Mega Stores", 
        time="10m ago", 
        type="demand"
    ),
    MarketListing(
        id="3",
        item="Yams",
        qty=400,
        unit="Tubers",
        zone="Benue",
        price=1200,
        seller="Mama Nkechi",
        time="45m ago",
        type="supply"
    )
]

# --- 📡 ENDPOINTS ( The Neural Interface ) ---

@app.get("/")
async def health_check():
    """
    System Heartbeat.
    Verifies that the Neural Core is online and ready to process vectors.
    """
    logger.info("Health check ping received.")
    return {"status": "neural_link_active", "timestamp": datetime.utcnow().isoformat(), "region": "West-Africa-1"}

@app.get("/market/feed", response_model=List[MarketListing])
async def get_market_feed():
    """
    The Pulse of the Market.
    Returns the real-time commodity board. Optimized for low-bandwidth JSON payload.
    """
    return market_feed

@app.post("/market/create_listing", status_code=status.HTTP_201_CREATED)
async def create_listing(request: ListingRequest):
    """
    The 'Harvest Signal'.
    A farmer signals availability. We ingest, validate, and broadcast instantly.
    """
    logger.info(f"New Harvest Signal from {request.farmer_id}: {request.item_name}")
    
    # Generate unique ID for tracking
    new_id = str(uuid.uuid4())
    
    # Construct the digital asset
    new_listing = MarketListing(
        id=new_id,
        item=request.item_name,
        qty=request.quantity,
        unit=request.unit,
        zone=request.location_zone,
        price=request.price_total,
        seller=request.farmer_id, 
        time="Just Now",
        type="supply"
    )
    
    # LIFO (Last In, First Out) - Newest harvest hits the top of the feed.
    market_feed.insert(0, new_listing)
    
    return {
        "status": "created",
        "listing_id": new_listing.id,
        "message": "Harvest signal broadcasted to the neural network."
    }

@app.post("/market/buy")
async def buy_item(request: BuyRequest):
    """
    The 'Handshake Protocol'.
    Executes the transaction logic between Buyer and Farmer.
    """
    logger.info(f"Transaction Request: Buyer {request.buyer_id} -> Listing {request.listing_id}")

    # Vector Search (Linear Scan for prototype)
    listing = next((x for x in market_feed if x.id == request.listing_id), None)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Asset not found. It may have already been dispatched.")
        
    if listing.type != 'supply':
        raise HTTPException(status_code=400, detail="Protocol Error: Cannot purchase a Demand request.")

    # Remove from feed to prevent double-spending/double-booking
    market_feed.remove(listing)
    
    # Generate Dispatch Token
    dispatch_id = f"TRUCK-{uuid.uuid4().hex[:6].upper()}"
    
    return {
        "status": "success",
        "message": f"Transaction confirmed. {listing.qty} {listing.unit} of {listing.item} secured.",
        "dispatch_status": "FLEET_DISPATCHED",
        "dispatch_id": dispatch_id
    }
