from motor.motor_asyncio import AsyncIOMotorClient
from models import Player, Game, Transaction, ShopItem, PlayerInventory
from typing import Optional, List
import os
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
            await self.db.players.create_index("name")
            await self.db.players.create_index("bestScore")
            await self.db.players.create_index("isOnline")
            
            # Games collection indexes
            await self.db.games.create_index("isActive")
            await self.db.games.create_index("gameMode")
            await self.db.games.create_index("startTime")
            
            # Transactions collection indexes
            await self.db.transactions.create_index("playerId")
            await self.db.transactions.create_index("timestamp")
            await self.db.transactions.create_index("status")
            
            # Shop collection indexes
            await self.db.shopItems.create_index("category")
            await self.db.shopItems.create_index("isAvailable")
            await self.db.shopItems.create_index("price")
            await self.db.shopItems.create_index("rarity")
            
            # Player inventory indexes
            await self.db.playerInventory.create_index("playerId")
            await self.db.playerInventory.create_index("itemId")
            await self.db.playerInventory.create_index("isEquipped")
            
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
    
    # Player Operations
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
        
        update_data = {
            "totalGames": player.totalGames + 1,
            "totalKills": player.totalKills + kills,
            "bestScore": max(player.bestScore, score)
        }
        
        # Update win count if score is high enough (top 3)
        if score > 1000:  # Arbitrary threshold for "winning"
            update_data["wins"] = player.wins + 1
        
        return await self.update_player(player_id, update_data)
    
    async def get_leaderboard(self, limit: int = 10) -> List[dict]:
        """Get top players leaderboard"""
        pipeline = [
            {"$match": {"bestScore": {"$gt": 0}}},
            {"$sort": {"bestScore": -1}},
            {"$limit": limit},
            {"$project": {"name": 1, "bestScore": 1, "_id": 0}}
        ]
        
        cursor = self.db.players.aggregate(pipeline)
        players = await cursor.to_list(length=limit)
        
        # Add rank
        for i, player in enumerate(players):
            player["rank"] = i + 1
            player["score"] = player["bestScore"]
        
        return players
    
    # Game Operations
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
    
    # Transaction Operations
    async def create_transaction(self, transaction: Transaction) -> Transaction:
        """Create a new transaction"""
        transaction_dict = transaction.dict()
        await self.db.transactions.insert_one(transaction_dict)
        return transaction
    
    async def get_player_transactions(self, player_id: str, limit: int = 50) -> List[Transaction]:
        """Get player's transaction history"""
        cursor = self.db.transactions.find(
            {"playerId": player_id}
        ).sort("timestamp", -1).limit(limit)
        
        transactions = await cursor.to_list(length=limit)
        return [Transaction(**t) for t in transactions]
    
    async def update_transaction_status(self, transaction_id: str, status: str) -> bool:
        """Update transaction status"""
        result = await self.db.transactions.update_one(
            {"id": transaction_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0

    # Shop Operations
    async def initialize_shop_items(self) -> bool:
        """Initialize shop with default items"""
        # Check if shop already has items
        existing_count = await self.db.shopItems.count_documents({})
        if existing_count > 0:
            return True
        
        # Default shop items
        default_items = [
            # Player Skins
            ShopItem(
                name="Ocean Wave",
                description="A calming blue gradient skin with wave patterns",
                category="skins",
                subcategory="player_skins",
                price=100,
                currency="virtual",
                rarity="common",
                effects={"color": "#0ea5e9", "pattern": "gradient", "secondary": "#06b6d4"}
            ),
            ShopItem(
                name="Fire Storm",
                description="Fierce red and orange flames surrounding your player",
                category="skins",
                subcategory="player_skins",
                price=250,
                currency="virtual",
                rarity="rare",
                effects={"color": "#dc2626", "pattern": "flame", "secondary": "#ea580c"}
            ),
            ShopItem(
                name="Golden Royalty",
                description="Luxurious gold with sparkling effects",
                category="skins",
                subcategory="player_skins",
                price=500,
                currency="virtual",
                rarity="epic",
                effects={"color": "#fbbf24", "pattern": "sparkle", "secondary": "#f59e0b"}
            ),
            ShopItem(
                name="Rainbow Prism",
                description="Constantly shifting rainbow colors",
                category="skins",
                subcategory="player_skins",
                price=1000,
                currency="virtual",
                rarity="legendary",
                effects={"color": "#8b5cf6", "pattern": "rainbow", "animation": "shift"}
            ),
            
            # Permanent Power-ups
            ShopItem(
                name="Speed Demon",
                description="Permanently increases movement speed by 25%",
                category="powerups",
                subcategory="permanent_boosts",
                price=300,
                currency="virtual",
                rarity="rare",
                isPermanent=True,
                effects={"speedMultiplier": 1.25}
            ),
            ShopItem(
                name="Money Magnet",
                description="Increases food value collection by 50%",
                category="powerups",
                subcategory="permanent_boosts",
                price=400,
                currency="virtual",
                rarity="rare",
                isPermanent=True,
                effects={"valueMultiplier": 1.5}
            ),
            ShopItem(
                name="Iron Armor",
                description="Reduces damage taken from other players by 30%",
                category="powerups",
                subcategory="permanent_boosts",
                price=600,
                currency="virtual",
                rarity="epic",
                isPermanent=True,
                effects={"damageReduction": 0.3}
            ),
            
            # Temporary Boosts
            ShopItem(
                name="Mega Boost (1 Hour)",
                description="2x score multiplier for 1 hour",
                category="boosts",
                subcategory="temporary_boosts",
                price=50,
                currency="virtual",
                rarity="common",
                isPermanent=False,
                duration=3600,
                effects={"scoreMultiplier": 2.0}
            ),
            ShopItem(
                name="Shield Generator (30 min)",
                description="Temporary invincibility for 30 minutes",
                category="boosts",
                subcategory="temporary_boosts",
                price=100,
                currency="virtual",
                rarity="rare",
                isPermanent=False,
                duration=1800,
                effects={"invincible": True}
            ),
            
            # Premium Items (Real Money)
            ShopItem(
                name="VIP Status (30 Days)",
                description="VIP perks: 2x earnings, priority matchmaking, exclusive skins",
                category="premium",
                subcategory="vip_status",
                price=999,
                currency="real",
                rarity="legendary",
                isPermanent=False,
                duration=2592000,  # 30 days
                effects={"vipStatus": True, "earningsMultiplier": 2.0, "priorityQueue": True}
            ),
            ShopItem(
                name="Diamond Crown",
                description="Ultra-rare diamond skin with crown decoration",
                category="skins",
                subcategory="premium_skins",
                price=1999,
                currency="real",
                rarity="legendary",
                effects={"color": "#e5e7eb", "pattern": "diamond", "decoration": "crown", "glow": True}
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

# Global database instance
database = Database()