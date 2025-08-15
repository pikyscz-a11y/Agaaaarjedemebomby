from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from datetime import datetime
import uuid

# Enhanced Player Models with JWT Auth Support
class PlayerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=15)
    email: Optional[str] = None
    password: Optional[str] = None  # For JWT auth

class PlayerLogin(BaseModel):
    email: str
    password: str

class PlayerProfile(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=20)
    name_color: str = Field(default="#4CAF50", pattern=r"^#[0-9A-Fa-f]{6}$")
    avatar_url: Optional[str] = None

class PlayerStats(BaseModel):
    score: int
    kills: int
    gameMode: str

class UserStats(BaseModel):
    """Enhanced user statistics"""
    games_played: int = 0
    best_mass: float = 0.0
    total_score: int = 0
    wins: int = 0
    total_kills: int = 0
    total_deaths: int = 0
    time_played: int = 0  # seconds
    favorite_game_mode: str = "classic"
    achievements: List[str] = Field(default_factory=list)

class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None  # For JWT auth
    name_color: str = Field(default="#4CAF50")
    avatar_url: Optional[str] = None
    credits: int = Field(default=0)  # USDT credits (1:1 ratio)
    virtualMoney: int = Field(default=250)  # Keep for backwards compatibility
    realMoney: int = Field(default=0)  # Keep for backwards compatibility
    stats: UserStats = Field(default_factory=UserStats)
    role: str = Field(default="user")  # "user", "admin"
    is_banned: bool = Field(default=False)
    ban_reason: Optional[str] = None
    ban_expires_at: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    lastActiveAt: datetime = Field(default_factory=datetime.utcnow)
    isOnline: bool = Field(default=True)

# Enhanced Game Models with Server-Authoritative Support
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

class Virus(BaseModel):
    """Virus entity for server-authoritative engine"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    x: float
    y: float
    mass: float = 100.0
    radius: float = Field(default=10.0)
    color: str = "#FF0000"

class EjectedMass(BaseModel):
    """Ejected mass entity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    x: float
    y: float
    mass: float = 10.0
    color: str
    velocity_x: float = 0.0
    velocity_y: float = 0.0

class Cell(BaseModel):
    """Player cell with physics properties"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    x: float
    y: float
    mass: float = 10.0
    radius: float = Field(default=3.16)  # sqrt(10)
    color: str
    velocity_x: float = 0.0
    velocity_y: float = 0.0

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
    cells: List[Cell] = []
    viruses: List[Virus] = []
    ejected_mass: List[EjectedMass] = []
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

# Enhanced Payment Models with USDT Support
class DepositRequest(BaseModel):
    """Request for USDT deposit via NOWPayments"""
    player_id: str
    amount: float  # USDT amount
    currency: str = "USDT"
    network: str = "TRC20"  # Default to TRC20
    callback_url: Optional[str] = None

class DepositResponse(BaseModel):
    """Response from NOWPayments deposit"""
    success: bool
    payment_id: str
    invoice_url: str
    payment_address: str
    amount: float
    currency: str
    status: str = "waiting"
    expires_at: datetime
    message: Optional[str] = None

class PayoutRequest(BaseModel):
    """Request for USDT payout"""
    player_id: str
    amount: float  # USDT amount
    wallet_address: str
    network: str = "TRC20"
    description: Optional[str] = None

class PayoutResponse(BaseModel):
    """Response for payout request"""
    success: bool
    payout_id: str
    amount: float
    fee: float
    net_amount: float
    status: str = "pending"  # "pending", "approved", "rejected", "completed"
    estimated_completion: str = "2-3 business days"
    message: Optional[str] = None

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
    type: str  # 'deposit', 'withdrawal', 'game_earning', 'shop_purchase'
    amount: float
    currency: str = "USDT"
    status: str = "completed"  # 'pending', 'completed', 'failed', 'cancelled'
    payment_id: Optional[str] = None  # External payment system ID
    network: Optional[str] = None
    wallet_address: Optional[str] = None
    fee: float = 0.0
    description: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
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

# Enhanced Admin Models
class AdminAction(BaseModel):
    """Admin action log"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str  # 'approve_payout', 'ban_user', 'create_item', etc.
    target_id: str  # ID of affected entity
    target_type: str  # 'user', 'payout', 'item', etc.
    details: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BanRequest(BaseModel):
    """Request to ban a user"""
    user_id: str
    reason: str
    duration_hours: Optional[int] = None  # None for permanent ban
    admin_notes: Optional[str] = None

class PayoutApproval(BaseModel):
    """Admin payout approval/rejection"""
    payout_id: str
    approved: bool
    admin_notes: Optional[str] = None

# Enhanced Inventory and Shop Models
class Item(BaseModel):
    """Base item model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str  # 'skin', 'boost', 'decoration'
    subcategory: str
    rarity: str = "common"  # 'common', 'rare', 'epic', 'legendary'
    properties: Dict = Field(default_factory=dict)
    image_url: Optional[str] = None

class Skin(BaseModel):
    """Player skin item"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    color_primary: str
    color_secondary: Optional[str] = None
    pattern: str = "solid"  # 'solid', 'gradient', 'striped', 'dotted'
    effects: Dict = Field(default_factory=dict)
    rarity: str = "common"
    preview_url: Optional[str] = None

class ShopItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str  # 'skins', 'powerups', 'boosts', 'decorations'
    subcategory: str  # 'player_skins', 'permanent_powerups', 'temporary_boosts', etc.
    price: float  # Credits/USDT price
    currency: str = "credits"  # 'credits' or 'USDT'
    rarity: str = "common"  # 'common', 'rare', 'epic', 'legendary'
    isAvailable: bool = True
    isPermanent: bool = True
    duration: Optional[int] = None  # Duration in seconds for temporary items
    effects: Dict = {}  # Item effects/properties
    imageUrl: Optional[str] = None
    preview_data: Optional[Dict] = None  # For skin previews
    stock: Optional[int] = None  # Limited stock items
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
    newBalance: float
    message: Optional[str] = None

# Enhanced Room Models
class RoomCreate(BaseModel):
    """Request to create a game room"""
    game_mode: str
    is_private: bool = False
    max_players: Optional[int] = None
    custom_rules: Dict = Field(default_factory=dict)

class RoomJoin(BaseModel):
    """Request to join a room"""
    room_id: Optional[str] = None
    room_code: Optional[str] = None
    player_id: str
    player_name: str

class RoomInfo(BaseModel):
    """Room information"""
    id: str
    game_mode: str
    player_count: int
    max_players: int
    is_private: bool
    room_code: Optional[str] = None
    created_at: datetime
    is_active: bool
    average_ping: Optional[float] = None

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

# Authentication Models
class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    """JWT token payload"""
    user_id: str
    username: str
    role: str = "user"
    exp: Optional[int] = None

class PasswordReset(BaseModel):
    """Password reset request"""
    email: str

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str

# Food and Power-up consumption models
class FoodConsumptionRequest(BaseModel):
    food_ids: List[str]
    player_id: str

class PowerUpConsumptionRequest(BaseModel):
    power_up_ids: List[str]
    player_id: str

class CollisionCheckRequest(BaseModel):
    player_id: str

# WebSocket Message Models
class WSMessage(BaseModel):
    """Base WebSocket message"""
    type: str
    timestamp: float

class WSJoinMessage(WSMessage):
    """Join game message"""
    player_id: str
    player_name: str
    game_mode: str = "classic"
    room_code: Optional[str] = None

class WSInputMessage(WSMessage):
    """Player input message"""
    dir_x: float
    dir_y: float

class WSActionMessage(WSMessage):
    """Player action message"""
    action: str  # 'split', 'eject', 'respawn'

class WSChatMessage(WSMessage):
    """Chat message"""
    message: str

# Configuration Models
class GameConfig(BaseModel):
    """Game configuration"""
    world_size: float = 2000.0
    max_cells_per_player: int = 16
    split_cooldown: float = 1.0
    eject_cooldown: float = 0.1
    merge_time: float = 15.0
    virus_split_threshold: float = 150.0
    eat_margin: float = 0.3
    friction: float = 0.9
    food_count: int = 1000
    virus_count: int = 50