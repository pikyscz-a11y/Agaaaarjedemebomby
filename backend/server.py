from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import our modules
from models import *
from database import database
from game_manager import game_manager
from utils import *

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Lifespan manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    logging.info("Database connected")
    yield
    # Shutdown
    await database.disconnect()
    logging.info("Database disconnected")

# Create the main app
app = FastAPI(lifespan=lifespan)

# Create API router
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Health check
@api_router.get("/")
async def root():
    return {"message": "MoneyAgar.io API is running!"}

# Player Management Endpoints
@api_router.post("/players/register", response_model=Player)
async def register_player(player_data: PlayerCreate):
    """Register a new player"""
    try:
        # Sanitize name
        sanitized_name = sanitize_player_name(player_data.name)
        if not sanitized_name:
            raise HTTPException(status_code=400, detail="Invalid player name")
        
        # Check if name already exists
        existing_player = await database.get_player_by_name(sanitized_name)
        if existing_player:
            return existing_player  # Return existing player instead of error
        
        # Create new player
        player = Player(name=sanitized_name, email=player_data.email)
        created_player = await database.create_player(player)
        
        logger.info(f"New player registered: {created_player.name}")
        return created_player
        
    except Exception as e:
        logger.error(f"Error registering player: {e}")
        raise HTTPException(status_code=500, detail="Failed to register player")

@api_router.get("/players/{player_id}", response_model=Player)
async def get_player(player_id: str):
    """Get player by ID"""
    player = await database.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@api_router.put("/players/{player_id}/stats")
async def update_player_stats(player_id: str, stats: PlayerStats):
    """Update player stats after game"""
    success = await database.update_player_stats(
        player_id, stats.score, stats.kills, stats.gameMode
    )
    if not success:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"success": True}

# Game Management Endpoints
@api_router.post("/games/create", response_model=Game)
async def create_game(game_data: GameCreate):
    """Create or join a game"""
    try:
        # Get player info
        player = await database.get_player(game_data.playerId)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Find or create game
        game = await game_manager.find_or_create_game(
            game_data.gameMode, game_data.playerId, player.name
        )
        
        logger.info(f"Player {player.name} joined game {game.id}")
        return game
        
    except Exception as e:
        logger.error(f"Error creating/joining game: {e}")
        raise HTTPException(status_code=500, detail="Failed to create/join game")

@api_router.get("/games/{game_id}/state", response_model=GameState)
async def get_game_state(game_id: str):
    """Get current game state"""
    game_state = await game_manager.get_game_state(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_state

@api_router.post("/games/{game_id}/update-position")
async def update_position(game_id: str, position_data: PositionUpdate):
    """Update player position"""
    success = await game_manager.update_player_position(
        game_id, position_data.playerId, position_data.x, position_data.y, position_data.money
    )
    if not success:
        raise HTTPException(status_code=404, detail="Game or player not found")
    return {"success": True}

@api_router.delete("/games/{game_id}/leave")
async def leave_game(game_id: str, player_id: str):
    """Leave a game"""
    success = await game_manager.remove_player(player_id)
    return {"success": success}

@api_router.post("/games/{game_id}/consume-food")
async def consume_food(game_id: str, request_data: FoodConsumptionRequest):
    """Process food consumption"""
    food_ids = request_data.food_ids
    player_id = request_data.player_id
    
    if not player_id or not food_ids:
        raise HTTPException(status_code=400, detail="Missing player_id or food_ids")
        
    points_earned = await game_manager.process_food_consumption(game_id, player_id, food_ids)
    return {"pointsEarned": points_earned}

@api_router.post("/games/{game_id}/consume-powerup")
async def consume_power_up(game_id: str, request_data: PowerUpConsumptionRequest):
    """Process power-up consumption"""
    power_up_ids = request_data.power_up_ids
    player_id = request_data.player_id
    
    if not player_id or not power_up_ids:
        raise HTTPException(status_code=400, detail="Missing player_id or power_up_ids")
    
    consumed_power_ups = await game_manager.process_power_up_consumption(game_id, player_id, power_up_ids)
    return {"consumedPowerUps": consumed_power_ups}

# Money Management Endpoints
@api_router.post("/payments/add-money", response_model=PaymentResponse)
async def add_money(payment_data: PaymentRequest):
    """Add money to player account"""
    try:
        # Get player
        player = await database.get_player(payment_data.playerId)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Simulate payment processing
        if not simulate_payment_processing():
            raise HTTPException(status_code=400, detail="Payment failed. Please try again.")
        
        # Create transaction record
        transaction = Transaction(
            playerId=payment_data.playerId,
            type="deposit",
            amount=payment_data.amount,
            transactionId=generate_transaction_id()
        )
        await database.create_transaction(transaction)
        
        # Update player balance
        new_real_money = player.realMoney + payment_data.amount
        new_total_money = player.virtualMoney + new_real_money
        
        await database.update_player(payment_data.playerId, {
            "realMoney": new_real_money
        })
        
        logger.info(f"Payment processed: ${payment_data.amount} for player {player.name}")
        
        return PaymentResponse(
            success=True,
            transactionId=transaction.transactionId,
            newBalance=new_total_money,
            message=f"Successfully added ${payment_data.amount}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        raise HTTPException(status_code=500, detail="Payment processing failed")

@api_router.post("/payments/withdraw", response_model=WithdrawalResponse)
async def withdraw_money(withdrawal_data: WithdrawalRequest):
    """Withdraw money from player account"""
    try:
        # Get player
        player = await database.get_player(withdrawal_data.playerId)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Check sufficient balance
        if player.virtualMoney < withdrawal_data.amount:
            raise HTTPException(status_code=400, detail="Insufficient virtual money balance")
        
        # Simulate withdrawal processing
        if not simulate_withdrawal_processing():
            raise HTTPException(status_code=400, detail="Withdrawal failed. Please contact support.")
        
        # Calculate fee
        fee = calculate_platform_fee(withdrawal_data.amount)
        net_amount = withdrawal_data.amount - fee
        
        # Create transaction record
        transaction = Transaction(
            playerId=withdrawal_data.playerId,
            type="withdrawal",
            amount=withdrawal_data.amount,
            transactionId=generate_transaction_id()
        )
        await database.create_transaction(transaction)
        
        # Update player balance
        new_virtual_money = player.virtualMoney - withdrawal_data.amount
        new_real_money = player.realMoney + net_amount
        
        await database.update_player(withdrawal_data.playerId, {
            "virtualMoney": new_virtual_money,
            "realMoney": new_real_money
        })
        
        logger.info(f"Withdrawal processed: ${withdrawal_data.amount} for player {player.name}")
        
        return WithdrawalResponse(
            success=True,
            withdrawalId=transaction.transactionId,
            amount=net_amount,
            fee=fee,
            message=f"Successfully withdrew ${net_amount} (${fee} platform fee)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing withdrawal: {e}")
        raise HTTPException(status_code=500, detail="Withdrawal processing failed")

@api_router.get("/payments/history/{player_id}")
async def get_payment_history(player_id: str):
    """Get player's payment history"""
    transactions = await database.get_player_transactions(player_id)
    return {"transactions": transactions}

# Leaderboard & Stats Endpoints
@api_router.get("/leaderboard")
async def get_leaderboard():
    """Get current leaderboard"""
    try:
        # Try to get real leaderboard from database
        real_leaderboard = await database.get_leaderboard(10)
        
        if real_leaderboard:
            return {"players": real_leaderboard}
        else:
            # Fallback to mock data if no players yet
            mock_leaderboard = get_mock_leaderboard()
            return {"players": [entry.dict() for entry in mock_leaderboard]}
            
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        # Return mock data on error
        mock_leaderboard = get_mock_leaderboard()
        return {"players": [entry.dict() for entry in mock_leaderboard]}

@api_router.get("/tournaments/active")
async def get_active_tournaments():
    """Get active tournaments"""
    tournaments = get_mock_tournaments()
    return {"tournaments": [t.dict() for t in tournaments]}

@api_router.get("/games/recent-matches")
async def get_recent_matches():
    """Get recent matches"""
    matches = get_mock_recent_matches()
    return {"matches": [m.dict() for m in matches]}

@api_router.get("/stats/platform")
async def get_platform_stats():
    """Get platform statistics"""
    # Count active games and players
    total_active_games = len(game_manager.active_games)
    total_online_players = sum(len(game.players) for game in game_manager.active_games.values())
    
    return {
        "playersOnline": total_online_players,
        "activeGames": total_active_games,
        "gamesToday": 1247,  # Mock data
        "totalPrizePool": 12456  # Mock data
    }

# Shop Endpoints
@api_router.get("/shop/items")
async def get_shop_items(category: str = None, currency: str = None):
    """Get shop items with optional filtering"""
    try:
        # Initialize shop if needed
        await database.initialize_shop_items()
        
        items = await database.get_shop_items(category, currency)
        return {"items": [item.dict() for item in items]}
    except Exception as e:
        logger.error(f"Error getting shop items: {e}")
        raise HTTPException(status_code=500, detail="Failed to get shop items")

@api_router.post("/shop/purchase", response_model=ShopPurchaseResponse)
async def purchase_shop_item(purchase_data: ShopPurchaseRequest):
    """Purchase an item from the shop"""
    try:
        # Get player and item
        player = await database.get_player(purchase_data.playerId)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        item = await database.get_shop_item(purchase_data.itemId)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        total_cost = item.price * purchase_data.quantity
        
        # Check if player has enough money
        if item.currency == "virtual":
            if player.virtualMoney < total_cost:
                raise HTTPException(status_code=400, detail="Insufficient virtual money")
            new_balance = player.virtualMoney - total_cost
            await database.update_player(purchase_data.playerId, {"virtualMoney": new_balance})
        else:  # real money
            if player.realMoney < total_cost:
                raise HTTPException(status_code=400, detail="Insufficient real money")
            new_balance = player.realMoney - total_cost
            await database.update_player(purchase_data.playerId, {"realMoney": new_balance})
        
        # Add item to player's inventory
        success = await database.purchase_item(
            purchase_data.playerId, 
            purchase_data.itemId,
            purchase_data.quantity
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add item to inventory")
        
        # Create transaction record
        transaction = Transaction(
            playerId=purchase_data.playerId,
            type="shop_purchase",
            amount=-total_cost,  # Negative because it's a purchase
            transactionId=generate_transaction_id()
        )
        await database.create_transaction(transaction)
        
        logger.info(f"Shop purchase: {item.name} for player {player.name}")
        
        return ShopPurchaseResponse(
            success=True,
            transactionId=transaction.transactionId,
            item=item,
            newBalance=new_balance,
            message=f"Successfully purchased {item.name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing item: {e}")
        raise HTTPException(status_code=500, detail="Purchase failed")

@api_router.get("/shop/inventory/{player_id}")
async def get_player_inventory(player_id: str):
    """Get player's inventory"""
    try:
        inventory = await database.get_player_inventory(player_id)
        return {"inventory": [item.dict() for item in inventory]}
    except Exception as e:
        logger.error(f"Error getting player inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to get inventory")

@api_router.post("/games/{game_id}/check-collisions")
async def check_player_collisions(game_id: str, request_data: CollisionCheckRequest):
    """Check and process player vs player collisions"""
    player_id = request_data.player_id
    
    if not player_id:
        raise HTTPException(status_code=400, detail="Missing player_id")
        
    collision_results = await game_manager.process_player_collisions(game_id, player_id)
    return collision_results

@api_router.post("/shop/equip")
async def equip_item(player_id: str, item_id: str):
    """Equip an item from player's inventory"""
    try:
        success = await database.equip_item(player_id, item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item not found in inventory")
        return {"success": True, "message": "Item equipped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error equipping item: {e}")
        raise HTTPException(status_code=500, detail="Failed to equip item")

# Include router in main app
app.include_router(api_router)