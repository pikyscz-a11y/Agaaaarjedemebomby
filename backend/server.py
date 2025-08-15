from fastapi import FastAPI, APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
import uuid
import asyncio

# Import our modules
from models import *
from database import database
from game_manager import game_manager
from game_room_manager import game_room_manager
from websocket_protocol import websocket_manager, WebSocketGameClient
from utils import *

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Lifespan manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    await game_room_manager.start()
    logging.info("Database connected and game room manager started")
    yield
    # Shutdown
    await game_room_manager.stop()
    await database.disconnect()
    logging.info("Game room manager stopped and database disconnected")

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
    # Clean up inactive games first
    cleaned_games = await game_manager.cleanup_inactive_games()
    if cleaned_games > 0:
        print(f"Cleaned up {cleaned_games} inactive games")
    
    active_games_count = len(game_manager.active_games)
    total_players = sum(len(game.players) for game in game_manager.active_games.values())
    
    return {
        "playersOnline": total_players,
        "activeGames": active_games_count,
        "gamesToday": random.randint(1200, 1300),
        "totalPrizePool": random.randint(12000, 15000)
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

@api_router.post("/games/{game_id}/players/{player_id}/collisions") 
async def check_player_collisions_alt(game_id: str, player_id: str):
    """Alternative collision endpoint format"""
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

# New Enhanced Game Room Endpoints
@api_router.post("/rooms/create")
async def create_game_room(game_mode: str, private: bool = False):
    """Create a new game room"""
    try:
        room_id = game_room_manager.create_room(game_mode, private)
        if not room_id:
            raise HTTPException(status_code=400, detail="Invalid game mode")
        
        room_info = game_room_manager.get_room_info(room_id)
        return {"room_id": room_id, "room_info": room_info}
        
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create room")

@api_router.get("/rooms/list")
async def list_public_rooms():
    """List all public game rooms"""
    try:
        rooms = game_room_manager.list_public_rooms()
        return {"rooms": rooms}
    except Exception as e:
        logger.error(f"Error listing rooms: {e}")
        raise HTTPException(status_code=500, detail="Failed to list rooms")

@api_router.post("/rooms/join/{code}")
async def join_private_room(code: str, player_id: str, player_name: str):
    """Join a private room by code"""
    try:
        room_id = game_room_manager.join_room_by_code(code)
        if not room_id:
            raise HTTPException(status_code=404, detail="Room not found or full")
        
        success = await game_room_manager.add_player_to_room(room_id, player_id, player_name)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to join room")
        
        room_info = game_room_manager.get_room_info(room_id)
        return {"room_id": room_id, "room_info": room_info}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining private room: {e}")
        raise HTTPException(status_code=500, detail="Failed to join room")

@api_router.get("/rooms/{room_id}/info")
async def get_room_info(room_id: str):
    """Get information about a specific room"""
    try:
        room_info = game_room_manager.get_room_info(room_id)
        if not room_info:
            raise HTTPException(status_code=404, detail="Room not found")
        return room_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting room info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get room info")

# WebSocket endpoint for real-time game communication
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time game communication"""
    client = None
    try:
        # Connect client
        client = await websocket_manager.connect_client(websocket, client_id)
        logger.info(f"WebSocket client {client_id} connected")
        
        # Message handling loop
        while True:
            try:
                # Check rate limiting
                if not websocket_manager.is_message_allowed(client_id):
                    logger.warning(f"Rate limit exceeded for client {client_id}")
                    await asyncio.sleep(1)  # Throttle the client
                    continue
                
                # Receive message
                message = await client.receive_message()
                if not message:
                    continue
                
                # Handle different message types
                if message.type == 'join':
                    await handle_join_message(client, message)
                elif message.type == 'input':
                    await handle_input_message(client, message)
                elif message.type == 'action':
                    await handle_action_message(client, message)
                elif message.type == 'chat':
                    await handle_chat_message(client, message)
                else:
                    logger.warning(f"Unknown message type: {message.type}")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {e}")
                # Send error message to client
                try:
                    error_msg = {
                        "type": "error",
                        "timestamp": time.time(),
                        "message": "Message processing failed"
                    }
                    await websocket.send_json(error_msg)
                except:
                    break  # Connection likely closed
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        # Clean up
        if client:
            websocket_manager.disconnect_client(client_id)
            if client.player_id:
                game_room_manager.remove_player_from_room(client.player_id)

# WebSocket message handlers
async def handle_join_message(client: WebSocketGameClient, message):
    """Handle player joining a game"""
    try:
        # Find or create room
        room_id = game_room_manager.find_available_room(message.game_mode)
        if not room_id:
            raise Exception("No rooms available")
        
        # Add player to room
        success = await game_room_manager.add_player_to_room(
            room_id, message.player_id, message.player_name
        )
        
        if success:
            client.player_id = message.player_id
            client.game_id = room_id
            client.is_authenticated = True
            
            logger.info(f"Player {message.player_name} joined room {room_id}")
        else:
            raise Exception("Failed to join room")
            
    except Exception as e:
        logger.error(f"Error handling join message: {e}")
        error_msg = {
            "type": "error",
            "timestamp": time.time(),
            "message": f"Failed to join game: {str(e)}"
        }
        await client.websocket.send_json(error_msg)

async def handle_input_message(client: WebSocketGameClient, message):
    """Handle player input"""
    if not client.is_authenticated or not client.player_id:
        return
    
    try:
        game_room_manager.handle_player_input(
            client.player_id, message.dir_x, message.dir_y
        )
    except Exception as e:
        logger.error(f"Error handling input from {client.player_id}: {e}")

async def handle_action_message(client: WebSocketGameClient, message):
    """Handle player actions (split, eject, respawn)"""
    if not client.is_authenticated or not client.player_id:
        return
    
    try:
        success = await game_room_manager.handle_player_action(
            client.player_id, message.action
        )
        
        # Send action result back to client
        result_msg = {
            "type": "action_result",
            "timestamp": time.time(),
            "action": message.action,
            "success": success
        }
        await client.websocket.send_json(result_msg)
        
    except Exception as e:
        logger.error(f"Error handling action from {client.player_id}: {e}")

async def handle_chat_message(client: WebSocketGameClient, message):
    """Handle chat messages"""
    if not client.is_authenticated or not client.player_id or not client.game_id:
        return
    
    try:
        # Basic chat message validation and sanitization
        chat_text = message.message.strip()[:200]  # Limit length
        if not chat_text:
            return
        
        # Broadcast chat to room
        from websocket_protocol import ChatBroadcastMessage
        chat_msg = ChatBroadcastMessage(
            type="chat",
            timestamp=time.time(),
            player_name=client.player_id,  # TODO: Get actual player name
            message=chat_text
        )
        
        await websocket_manager.broadcast_to_game(
            client.game_id, chat_msg, exclude_client=client.client_id
        )
        
    except Exception as e:
        logger.error(f"Error handling chat from {client.player_id}: {e}")

# Health and metrics endpoints
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0"
    }

@api_router.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint"""
    try:
        room_stats = game_room_manager.get_manager_stats()
        ws_stats = websocket_manager.get_manager_stats()
        
        metrics = {
            "game_rooms_active": room_stats['active_rooms'],
            "game_rooms_total_created": room_stats['rooms_created'],
            "game_rooms_total_closed": room_stats['rooms_closed'],
            "players_active": room_stats['total_players'],
            "websocket_connections_active": ws_stats['active_connections'],
            "websocket_connections_total": ws_stats['connections'],
            "websocket_disconnections_total": ws_stats['disconnections'],
            "websocket_messages_processed_total": ws_stats['messages_processed'],
            "game_ticks_total": room_stats['total_ticks'],
            "game_tick_duration_avg": room_stats['avg_tick_time']
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

# Include router in main app
app.include_router(api_router)