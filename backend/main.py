from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, List
import json
import asyncio
from datetime import datetime

# Import our modules
from app.config import settings
from app.db import get_db, init_db
from app.models import User, Balance, Transaction, Payout, Room
from app.auth import register_user, login_user
from app.deps import get_current_user_id, get_current_user
from app.payments.nowpayments import nowpayments
from pydantic import BaseModel

# Initialize database
init_db()

# Create the main app
app = FastAPI(title="Agar.io MVP", version="1.0.0")

# Create API router
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class RegisterRequest(BaseModel):
    username: str
    password: str
    avatar: str = "default.png"
    color: str = "#4A90E2"

class LoginRequest(BaseModel):
    username: str
    password: str

class DepositRequest(BaseModel):
    amount_usd: float

class PayoutRequest(BaseModel):
    amount: int  # In cents
    address: str  # USDT wallet address

class JoinRoomRequest(BaseModel):
    room_id: str

class UserResponse(BaseModel):
    id: str
    username: str
    avatar: str
    color: str
    balance: int

# Room manager for WebSocket connections
class RoomManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.room_states: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections[room_id].remove(conn)

room_manager = RoomManager()

# Health check
@api_router.get("/")
async def root():
    return {"message": "Agar.io MVP API is running!"}

# Authentication endpoints
@api_router.post("/auth/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = register_user(db, request.username, request.password, request.avatar, request.color)
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    return login_user(db, request.username, request.password)

# User profile endpoint
@api_router.get("/user/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile with balance"""
    balance = db.query(Balance).filter(Balance.user_id == current_user.id).first()
    balance_amount = balance.amount if balance else 0
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        avatar=current_user.avatar,
        color=current_user.color,
        balance=balance_amount
    )

# Payment endpoints
@api_router.post("/payments/deposit")
async def create_deposit(
    request: DepositRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create USDT deposit invoice"""
    try:
        invoice = await nowpayments.create_invoice(current_user_id, request.amount_usd)
        return {
            "success": True,
            "invoice_url": invoice.get("invoice_url"),
            "payment_id": invoice.get("payment_id"),
            "amount_usd": request.amount_usd
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create deposit invoice: {str(e)}")

@api_router.post("/payments/ipn")
async def handle_ipn(request: Request, db: Session = Depends(get_db)):
    """Handle IPN webhook from NOWPayments"""
    try:
        body = await request.body()
        payload = await request.json()
        signature = request.headers.get("x-nowpayments-sig")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        success = await nowpayments.process_ipn_webhook(db, payload, signature)
        if success:
            return {"status": "ok"}
        else:
            raise HTTPException(status_code=400, detail="Invalid webhook")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/payments/payout")
async def request_payout(
    request: PayoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request USDT payout"""
    try:
        # Check minimum withdrawal amount
        if request.amount < settings.withdraw_min_amount * 100:  # Convert to cents
            raise HTTPException(
                status_code=400, 
                detail=f"Minimum withdrawal amount is {settings.withdraw_min_amount} USDT"
            )
        
        # Check user balance
        balance = db.query(Balance).filter(Balance.user_id == current_user.id).first()
        if not balance or balance.amount < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Create payout record
        payout = Payout(
            user_id=current_user.id,
            amount=request.amount,
            address=request.address,
            status="pending"
        )
        db.add(payout)
        
        # Deduct from balance
        balance.amount -= request.amount
        
        # Create transaction record
        transaction = Transaction(
            user_id=current_user.id,
            type="withdrawal",
            amount=-request.amount,  # Negative for withdrawal
            ref=payout.id,
            status="pending"
        )
        db.add(transaction)
        
        db.commit()
        
        return {
            "success": True,
            "payout_id": payout.id,
            "message": "Payout request submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Room management endpoints
@api_router.get("/rooms")
async def list_rooms(db: Session = Depends(get_db)):
    """List available rooms"""
    rooms = db.query(Room).filter(Room.active == True).all()
    return {
        "rooms": [
            {
                "id": room.id,
                "name": room.name,
                "mode": room.mode,
                "entry_fee": room.entry_fee,
                "max_players": room.max_players,
                "current_players": len(room_manager.active_connections.get(room.id, []))
            }
            for room in rooms
        ]
    }

@api_router.post("/rooms/join")
async def join_room(
    request: JoinRoomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a room (deduct entry fee)"""
    try:
        room = db.query(Room).filter(Room.id == request.room_id, Room.active == True).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Check if room has space
        current_players = len(room_manager.active_connections.get(room.id, []))
        if current_players >= room.max_players:
            raise HTTPException(status_code=400, detail="Room is full")
        
        # Check user balance
        balance = db.query(Balance).filter(Balance.user_id == current_user.id).first()
        if not balance or balance.amount < room.entry_fee:
            raise HTTPException(status_code=400, detail="Insufficient balance for entry fee")
        
        # Deduct entry fee
        balance.amount -= room.entry_fee
        
        # Create transaction record
        transaction = Transaction(
            user_id=current_user.id,
            type="entry_fee",
            amount=-room.entry_fee,
            ref=room.id,
            status="completed"
        )
        db.add(transaction)
        
        db.commit()
        
        return {
            "success": True,
            "room_id": room.id,
            "message": f"Joined room successfully. Entry fee: {room.entry_fee/100} USDT"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for room gameplay
@app.websocket("/ws/room/{room_id}")
async def websocket_room(websocket: WebSocket, room_id: str, token: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time room communication"""
    try:
        # Verify JWT token
        # Simple token verification - in production, use proper JWT validation
        await room_manager.connect(websocket, room_id)
        
        # Initialize room state if not exists
        if room_id not in room_manager.room_states:
            room_manager.room_states[room_id] = {
                "players": {},
                "food": [],
                "last_tick": datetime.now().timestamp()
            }
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message["type"] == "player_update":
                    # Update player position
                    room_manager.room_states[room_id]["players"][message["player_id"]] = {
                        "x": message["x"],
                        "y": message["y"],
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    # Broadcast update to all players in room
                    await room_manager.broadcast_to_room(room_id, {
                        "type": "game_state",
                        "state": room_manager.room_states[room_id]
                    })
                
                elif message["type"] == "ping":
                    # Send pong response
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
        except WebSocketDisconnect:
            room_manager.disconnect(websocket, room_id)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

# Create default rooms on startup
@app.on_event("startup")
async def create_default_rooms():
    """Create default game rooms"""
    db = next(get_db())
    try:
        # Check if rooms already exist
        existing_rooms = db.query(Room).count()
        if existing_rooms == 0:
            # Create default rooms for each game mode
            for mode, config in settings.game_modes.items():
                room = Room(
                    name=f"{mode.title()} Room",
                    mode=mode,
                    entry_fee=config["entry_fee"] * 100,  # Convert to cents
                    max_players=config["max_players"],
                    active=True
                )
                db.add(room)
            
            db.commit()
            print("Created default rooms")
    except Exception as e:
        print(f"Error creating default rooms: {e}")
    finally:
        db.close()

# Include router in main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)