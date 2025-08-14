from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid

# Player Models
class PlayerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=15)
    email: Optional[str] = None

class PlayerStats(BaseModel):
    score: int
    kills: int
    gameMode: str

class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: Optional[str] = None
    virtualMoney: int = Field(default=250)
    realMoney: int = Field(default=0)
    totalGames: int = Field(default=0)
    wins: int = Field(default=0)
    totalKills: int = Field(default=0)
    bestScore: int = Field(default=0)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    isOnline: bool = Field(default=True)

# Game Models
class Position(BaseModel):
    x: float
    y: float

class GamePlayer(BaseModel):
    playerId: str
    name: str
    x: float
    y: float
    money: int
    score: int
    kills: int
    isAlive: bool = True
    color: str

class Food(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    x: float
    y: float
    color: str
    value: int

class PowerUp(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    x: float
    y: float
    type: str
    color: str
    size: int
    value: int

class GameState(BaseModel):
    players: List[GamePlayer] = []
    food: List[Food] = []
    powerUps: List[PowerUp] = []
    gameStats: Dict = {}

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gameMode: str
    players: List[GamePlayer] = []
    food: List[Food] = []
    powerUps: List[PowerUp] = []
    startTime: datetime = Field(default_factory=datetime.utcnow)
    isActive: bool = True
    maxPlayers: int = 20

class GameCreate(BaseModel):
    gameMode: str
    playerId: str

class PositionUpdate(BaseModel):
    playerId: str
    x: float
    y: float
    money: int

# Payment Models
class PaymentRequest(BaseModel):
    playerId: str
    amount: int
    paymentMethod: str = "card"

class WithdrawalRequest(BaseModel):
    playerId: str
    amount: int

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    playerId: str
    type: str  # 'deposit', 'withdrawal', 'game_earning'
    amount: int
    status: str = "completed"  # 'pending', 'completed', 'failed'
    transactionId: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaymentResponse(BaseModel):
    success: bool
    transactionId: str
    newBalance: int
    message: Optional[str] = None

class WithdrawalResponse(BaseModel):
    success: bool
    withdrawalId: str
    amount: int
    fee: int
    estimatedArrival: str = "2-3 business days"
    message: Optional[str] = None

# Leaderboard Models
class LeaderboardEntry(BaseModel):
    name: str
    score: int
    rank: int

class Tournament(BaseModel):
    name: str
    prizePool: int
    players: int
    maxPlayers: int
    startsIn: str
    entryFee: int

class RecentMatch(BaseModel):
    winner: str
    mode: str
    prize: int
    timeAgo: str

# Shop System Models
class ShopItemType(BaseModel):
    category: str  # 'skin', 'powerup', 'boost', 'decoration'
    subcategory: str  # 'player_skin', 'permanent_boost', 'temporary_boost', etc.

class ShopItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str  # 'skins', 'powerups', 'boosts', 'decorations'
    subcategory: str  # 'player_skins', 'permanent_powerups', 'temporary_boosts', etc.
    price: int
    currency: str = "virtual"  # 'virtual' or 'real'
    rarity: str = "common"  # 'common', 'rare', 'epic', 'legendary'
    isAvailable: bool = True
    isPermanent: bool = True
    duration: Optional[int] = None  # Duration in seconds for temporary items
    effects: Dict = {}  # Item effects/properties
    imageUrl: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class PlayerInventory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    playerId: str
    itemId: str
    itemName: str
    category: str
    subcategory: str
    quantity: int = 1
    isEquipped: bool = False
    purchasedAt: datetime = Field(default_factory=datetime.utcnow)
    expiresAt: Optional[datetime] = None

class PlayerSkin(BaseModel):
    skinId: str
    name: str
    color: str
    pattern: str = "solid"  # 'solid', 'gradient', 'striped', 'dotted'
    effects: Dict = {}

class ShopPurchaseRequest(BaseModel):
    playerId: str
    itemId: str
    quantity: int = 1

class ShopPurchaseResponse(BaseModel):
    success: bool
    transactionId: str
    item: ShopItem
    newBalance: int
    message: Optional[str] = None

# Food and Power-up consumption models
class FoodConsumptionRequest(BaseModel):
    food_ids: List[str]
    player_id: str

class PowerUpConsumptionRequest(BaseModel):
    power_up_ids: List[str]
    player_id: str

class CollisionCheckRequest(BaseModel):
    player_id: str