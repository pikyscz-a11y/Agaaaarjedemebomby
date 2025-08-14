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

# Global database instance
database = Database()