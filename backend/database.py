from motor.motor_asyncio import AsyncIOMotorClient
from models import Player, Game, Transaction, ShopItem, PlayerInventory
from typing import Optional, List
import os
import uuid
from datetime import datetime

class Database:
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME', 'moneyagar')
        
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        
        # Create indexes
        await self.create_indexes()
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Players collection indexes
            await self.db.players.create_index("name", unique=True)
            await self.db.players.create_index("email", unique=True, sparse=True)
            await self.db.players.create_index("credits")
            await self.db.players.create_index("stats.best_mass")
            await self.db.players.create_index("isOnline")
            await self.db.players.create_index("role")
            await self.db.players.create_index("is_banned")
            await self.db.players.create_index("lastActiveAt")
            
            # Games collection indexes
            await self.db.games.create_index("isActive")
            await self.db.games.create_index("gameMode")
            await self.db.games.create_index("startTime")
            
            # Transactions collection indexes
            await self.db.transactions.create_index("playerId")
            await self.db.transactions.create_index("timestamp")
            await self.db.transactions.create_index("status")
            await self.db.transactions.create_index("type")
            await self.db.transactions.create_index("payment_id", sparse=True)
            await self.db.transactions.create_index("currency")
            
            # Shop collection indexes
            await self.db.shopItems.create_index("category")
            await self.db.shopItems.create_index("isAvailable")
            await self.db.shopItems.create_index("price")
            await self.db.shopItems.create_index("rarity")
            await self.db.shopItems.create_index("currency")
            
            # Player inventory indexes
            await self.db.playerInventory.create_index("playerId")
            await self.db.playerInventory.create_index("itemId")
            await self.db.playerInventory.create_index("isEquipped")
            await self.db.playerInventory.create_index("expiresAt", sparse=True)
            
            # Admin actions indexes
            await self.db.adminActions.create_index("admin_id")
            await self.db.adminActions.create_index("timestamp")
            await self.db.adminActions.create_index("action")
            await self.db.adminActions.create_index("target_id")
            
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
    
    # Enhanced Player Operations
    async def create_player(self, player: Player) -> Player:
        """Create a new player"""
        player_dict = player.dict()
        result = await self.db.players.insert_one(player_dict)
        player_dict['_id'] = str(result.inserted_id)
        return Player(**player_dict)
    
    async def get_player(self, player_id: str) -> Optional[Player]:
        """Get player by ID"""
        player_data = await self.db.players.find_one({"id": player_id})
        if player_data:
            return Player(**player_data)
        return None
    
    async def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get player by name"""
        player_data = await self.db.players.find_one({"name": name})
        if player_data:
            return Player(**player_data)
        return None
    
    async def get_player_by_email(self, email: str) -> Optional[Player]:
        """Get player by email"""
        player_data = await self.db.players.find_one({"email": email})
        if player_data:
            return Player(**player_data)
        return None
    
    async def update_player(self, player_id: str, update_data: dict) -> bool:
        """Update player data"""
        result = await self.db.players.update_one(
            {"id": player_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def update_player_stats(self, player_id: str, score: int, kills: int, game_mode: str) -> bool:
        """Update player stats after game"""
        player = await self.get_player(player_id)
        if not player:
            return False
        
        # Update stats
        new_stats = player.stats.dict()
        new_stats['games_played'] += 1
        new_stats['total_kills'] += kills
        new_stats['total_score'] += score
        new_stats['best_mass'] = max(new_stats['best_mass'], score)
        
        # Check for win (top score threshold)
        if score > 1000:
            new_stats['wins'] += 1
        
        # Update favorite game mode
        new_stats['favorite_game_mode'] = game_mode
        
        update_data = {
            "stats": new_stats,
            "lastActiveAt": datetime.utcnow()
        }
        
        return await self.update_player(player_id, update_data)
    
    async def get_leaderboard(self, limit: int = 10, sort_by: str = "best_mass") -> List[dict]:
        """Get top players leaderboard"""
        sort_field = f"stats.{sort_by}"
        
        pipeline = [
            {"$match": {sort_field: {"$gt": 0}}},
            {"$sort": {sort_field: -1}},
            {"$limit": limit},
            {"$project": {
                "name": 1, 
                "display_name": 1,
                "stats": 1, 
                "_id": 0
            }}
        ]
        
        cursor = self.db.players.aggregate(pipeline)
        players = await cursor.to_list(length=limit)
        
        # Add rank and format response
        for i, player in enumerate(players):
            player["rank"] = i + 1
            player["score"] = player["stats"][sort_by]
        
        return players
    
    async def ban_player(self, player_id: str, reason: str, 
                        expires_at: Optional[datetime] = None) -> bool:
        """Ban a player"""
        update_data = {
            "is_banned": True,
            "ban_reason": reason,
            "ban_expires_at": expires_at,
            "isOnline": False
        }
        return await self.update_player(player_id, update_data)
    
    async def unban_player(self, player_id: str) -> bool:
        """Unban a player"""
        update_data = {
            "is_banned": False,
            "ban_reason": None,
            "ban_expires_at": None
        }
        return await self.update_player(player_id, update_data)
    
    # Game Operations (existing)
    async def save_game(self, game: Game) -> Game:
        """Save game to database"""
        game_dict = game.dict()
        await self.db.games.insert_one(game_dict)
        return game
    
    async def get_active_games(self, game_mode: str = None) -> List[Game]:
        """Get active games"""
        query = {"isActive": True}
        if game_mode:
            query["gameMode"] = game_mode
            
        cursor = self.db.games.find(query)
        games = await cursor.to_list(length=100)
        return [Game(**game_data) for game_data in games]
    
    async def update_game(self, game_id: str, update_data: dict) -> bool:
        """Update game data"""
        result = await self.db.games.update_one(
            {"id": game_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # Enhanced Transaction Operations
    async def create_transaction(self, transaction: Transaction) -> Transaction:
        """Create a new transaction"""
        transaction_dict = transaction.dict()
        await self.db.transactions.insert_one(transaction_dict)
        return transaction
    
    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        transaction_data = await self.db.transactions.find_one({"id": transaction_id})
        if transaction_data:
            return Transaction(**transaction_data)
        return None
    
    async def get_transactions_by_payment_id(self, payment_id: str) -> List[Transaction]:
        """Get transactions by external payment ID"""
        cursor = self.db.transactions.find({"payment_id": payment_id})
        transactions = await cursor.to_list(length=100)
        return [Transaction(**t) for t in transactions]
    
    async def get_player_transactions(self, player_id: str, limit: int = 50,
                                    transaction_type: str = None) -> List[Transaction]:
        """Get player's transaction history"""
        query = {"playerId": player_id}
        if transaction_type:
            query["type"] = transaction_type
            
        cursor = self.db.transactions.find(query).sort("timestamp", -1).limit(limit)
        transactions = await cursor.to_list(length=limit)
        return [Transaction(**t) for t in transactions]
    
    async def update_transaction(self, transaction_id: str, update_data: dict) -> bool:
        """Update transaction data"""
        result = await self.db.transactions.update_one(
            {"id": transaction_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def update_transaction_status(self, transaction_id: str, status: str) -> bool:
        """Update transaction status"""
        return await self.update_transaction(transaction_id, {"status": status})
    
    async def get_pending_payouts(self) -> List[Transaction]:
        """Get all pending payout requests"""
        cursor = self.db.transactions.find({
            "type": "payout_request",
            "status": "pending"
        }).sort("timestamp", 1)
        
        transactions = await cursor.to_list(length=1000)
        return [Transaction(**t) for t in transactions]

    # Enhanced Shop Operations
    async def initialize_shop_items(self) -> bool:
        """Initialize shop with default items"""
        # Check if shop already has items
        existing_count = await self.db.shopItems.count_documents({})
        if existing_count > 0:
            return True
        
        # Default shop items with USDT pricing
        default_items = [
            # Player Skins (Credits)
            ShopItem(
                name="Ocean Wave",
                description="A calming blue gradient skin with wave patterns",
                category="skins",
                subcategory="player_skins",
                price=5.0,  # 5 USDT credits
                currency="credits",
                rarity="common",
                effects={"color": "#0ea5e9", "pattern": "gradient", "secondary": "#06b6d4"},
                preview_data={"demo_size": 50, "animated": True}
            ),
            ShopItem(
                name="Fire Storm",
                description="Fierce red and orange flames surrounding your player",
                category="skins",
                subcategory="player_skins",
                price=12.5,
                currency="credits",
                rarity="rare",
                effects={"color": "#dc2626", "pattern": "flame", "secondary": "#ea580c"},
                preview_data={"demo_size": 50, "animated": True, "particle_effect": "fire"}
            ),
            ShopItem(
                name="Golden Royalty",
                description="Luxurious gold with sparkling effects",
                category="skins",
                subcategory="player_skins",
                price=25.0,
                currency="credits",
                rarity="epic",
                effects={"color": "#fbbf24", "pattern": "sparkle", "secondary": "#f59e0b"},
                preview_data={"demo_size": 50, "animated": True, "glow_effect": True}
            ),
            ShopItem(
                name="Rainbow Prism",
                description="Constantly shifting rainbow colors",
                category="skins",
                subcategory="player_skins",
                price=50.0,
                currency="credits",
                rarity="legendary",
                effects={"color": "#8b5cf6", "pattern": "rainbow", "animation": "shift"},
                preview_data={"demo_size": 50, "animated": True, "color_cycle": True}
            ),
            
            # Permanent Power-ups
            ShopItem(
                name="Speed Demon",
                description="Permanently increases movement speed by 25%",
                category="powerups",
                subcategory="permanent_boosts",
                price=15.0,
                currency="credits",
                rarity="rare",
                isPermanent=True,
                effects={"speedMultiplier": 1.25},
                preview_data={"icon": "speed", "effect_preview": "25% faster movement"}
            ),
            ShopItem(
                name="Mass Magnet",
                description="Increases food value collection by 50%",
                category="powerups",
                subcategory="permanent_boosts",
                price=20.0,
                currency="credits",
                rarity="rare",
                isPermanent=True,
                effects={"valueMultiplier": 1.5},
                preview_data={"icon": "magnet", "effect_preview": "50% more mass gain"}
            ),
            ShopItem(
                name="Iron Armor",
                description="Reduces damage taken from other players by 30%",
                category="powerups",
                subcategory="permanent_boosts",
                price=30.0,
                currency="credits",
                rarity="epic",
                isPermanent=True,
                effects={"damageReduction": 0.3},
                preview_data={"icon": "shield", "effect_preview": "30% damage reduction"}
            ),
            
            # Temporary Boosts
            ShopItem(
                name="Mega Boost (1 Hour)",
                description="2x score multiplier for 1 hour",
                category="boosts",
                subcategory="temporary_boosts",
                price=2.5,
                currency="credits",
                rarity="common",
                isPermanent=False,
                duration=3600,
                effects={"scoreMultiplier": 2.0},
                preview_data={"icon": "boost", "duration_text": "1 hour"}
            ),
            ShopItem(
                name="Shield Generator (30 min)",
                description="Temporary invincibility for 30 minutes",
                category="boosts",
                subcategory="temporary_boosts",
                price=5.0,
                currency="credits",
                rarity="rare",
                isPermanent=False,
                duration=1800,
                effects={"invincible": True},
                preview_data={"icon": "protection", "duration_text": "30 minutes"}
            ),
            
            # Premium Items (Direct USDT)
            ShopItem(
                name="VIP Status (30 Days)",
                description="VIP perks: 2x earnings, priority matchmaking, exclusive features",
                category="premium",
                subcategory="vip_status",
                price=49.99,
                currency="USDT",
                rarity="legendary",
                isPermanent=False,
                duration=2592000,  # 30 days
                effects={"vipStatus": True, "earningsMultiplier": 2.0, "priorityQueue": True},
                preview_data={"icon": "vip", "duration_text": "30 days", "exclusive": True}
            ),
            ShopItem(
                name="Diamond Crown",
                description="Ultra-rare diamond skin with crown decoration and exclusive particle effects",
                category="skins",
                subcategory="premium_skins",
                price=99.99,
                currency="USDT",
                rarity="legendary",
                effects={"color": "#e5e7eb", "pattern": "diamond", "decoration": "crown", "glow": True},
                preview_data={"demo_size": 60, "animated": True, "premium_effects": True, "exclusive": True}
            )
        ]
        
        # Insert all default items
        for item in default_items:
            await self.db.shopItems.insert_one(item.dict())
        
        return True
    
    async def get_shop_items(self, category: str = None, currency: str = None) -> List[ShopItem]:
        """Get shop items with optional filtering"""
        query = {"isAvailable": True}
        if category:
            query["category"] = category
        if currency:
            query["currency"] = currency
            
        cursor = self.db.shopItems.find(query).sort("price", 1)
        items = await cursor.to_list(length=100)
        return [ShopItem(**item_data) for item_data in items]
    
    async def get_shop_item(self, item_id: str) -> Optional[ShopItem]:
        """Get specific shop item"""
        item_data = await self.db.shopItems.find_one({"id": item_id, "isAvailable": True})
        if item_data:
            return ShopItem(**item_data)
        return None
    
    async def purchase_item(self, player_id: str, item_id: str, quantity: int = 1) -> bool:
        """Add purchased item to player's inventory"""
        item = await self.get_shop_item(item_id)
        if not item:
            return False
            
        inventory_item = PlayerInventory(
            playerId=player_id,
            itemId=item_id,
            itemName=item.name,
            category=item.category,
            subcategory=item.subcategory,
            quantity=quantity,
            expiresAt=datetime.utcnow().timestamp() + item.duration if item.duration else None
        )
        
        await self.db.playerInventory.insert_one(inventory_item.dict())
        return True
    
    async def get_player_inventory(self, player_id: str) -> List[PlayerInventory]:
        """Get player's inventory"""
        cursor = self.db.playerInventory.find({"playerId": player_id})
        items = await cursor.to_list(length=200)
        return [PlayerInventory(**item_data) for item_data in items]
    
    async def equip_item(self, player_id: str, item_id: str) -> bool:
        """Equip an item from player's inventory"""
        # First unequip any items of the same category
        inventory_item = await self.db.playerInventory.find_one({
            "playerId": player_id, 
            "itemId": item_id
        })
        
        if not inventory_item:
            return False
            
        # Unequip other items in same category
        await self.db.playerInventory.update_many(
            {"playerId": player_id, "category": inventory_item["category"]},
            {"$set": {"isEquipped": False}}
        )
        
        # Equip the selected item
        result = await self.db.playerInventory.update_one(
            {"playerId": player_id, "itemId": item_id},
            {"$set": {"isEquipped": True}}
        )
        
        return result.modified_count > 0
    
    # Admin Operations
    async def create_admin_action(self, admin_id: str, action: str, target_id: str,
                                 target_type: str, details: dict = None) -> bool:
        """Log admin action"""
        action_data = {
            "id": str(uuid.uuid4()),
            "admin_id": admin_id,
            "action": action,
            "target_id": target_id,
            "target_type": target_type,
            "details": details or {},
            "timestamp": datetime.utcnow()
        }
        
        await self.db.adminActions.insert_one(action_data)
        return True
    
    async def get_admin_actions(self, limit: int = 100, admin_id: str = None) -> List[dict]:
        """Get admin action log"""
        query = {}
        if admin_id:
            query["admin_id"] = admin_id
        
        cursor = self.db.adminActions.find(query).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def create_admin_user(self, username: str, password_hash: str, email: str) -> bool:
        """Create admin user"""
        try:
            from models import Player, UserStats
            admin_user = Player(
                name=username,
                display_name=username,
                email=email,
                password_hash=password_hash,
                role="admin",
                credits=0,
                stats=UserStats(),
                createdAt=datetime.utcnow()
            )
            
            await self.create_player(admin_user)
            return True
        except Exception:
            return False

# Global database instance
database = Database()