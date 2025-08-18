"""
Simple in-memory database implementation for development/demo purposes
"""
from models import Player, Game, Transaction, ShopItem, PlayerInventory
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import asyncio

class InMemoryDatabase:
    def __init__(self):
        self.players: Dict[str, Dict] = {}
        self.games: Dict[str, Dict] = {}
        self.transactions: Dict[str, Dict] = {}
        self.shop_items: Dict[str, Dict] = {}
        self.player_inventory: Dict[str, Dict] = {}
        self._initialized = False
    
    async def connect(self):
        """Initialize in-memory database with some sample data"""
        if not self._initialized:
            await self._init_sample_data()
            self._initialized = True
        print("In-memory database connected successfully")
    
    async def disconnect(self):
        """Nothing to disconnect for in-memory DB"""
        pass
    
    async def _init_sample_data(self):
        """Initialize with some sample shop items and data"""
        sample_shop_items = [
            {
                "id": str(uuid.uuid4()),  # Use 'id' for consistency
                "name": "Speed Boost",
                "category": "powerup",
                "price": 50,
                "currency": "virtual",  # Add currency field
                "description": "Increase speed by 20% for 30 seconds",
                "rarity": "common",
                "isAvailable": True
            },
            {
                "id": str(uuid.uuid4()),  # Use 'id' for consistency
                "name": "Gold Skin",
                "category": "skin",
                "price": 200,
                "currency": "virtual",  # Add currency field
                "description": "Shiny gold appearance",
                "rarity": "rare",
                "isAvailable": True
            }
        ]
        
        for item in sample_shop_items:
            self.shop_items[item["id"]] = item
    
    # Player operations
    async def create_player(self, player_data: dict) -> dict:
        player_id = str(uuid.uuid4())
        player = {
            "id": player_id,  # Use 'id' instead of '_id' for consistency with models
            "name": player_data.get("name"),
            "email": player_data.get("email"),
            "virtualMoney": 250,
            "realMoney": 0,
            "totalGames": 0,
            "wins": 0,
            "totalKills": 0,
            "bestScore": 0,
            "createdAt": datetime.utcnow(),
            "isOnline": False
        }
        self.players[player_id] = player
        return player
    
    async def get_player(self, player_id: str) -> Optional[dict]:
        return self.players.get(player_id)
    
    async def get_player_by_name(self, name: str) -> Optional[dict]:
        """Find player by name"""
        for player in self.players.values():
            if player.get("name") == name:
                return player
        return None
    
    async def update_player_stats(self, player_id: str, stats: dict) -> bool:
        if player_id in self.players:
            player = self.players[player_id]
            player.update(stats)
            return True
        return False
    
    async def get_leaderboard(self, limit: int = 10) -> List[dict]:
        # Sort players by best score
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: p.get("bestScore", 0),
            reverse=True
        )
        return sorted_players[:limit]
    
    # Game operations
    async def create_game(self, game_data: dict) -> dict:
        game_id = str(uuid.uuid4())
        game = {
            "id": game_id,  # Use 'id' for consistency
            "gameMode": game_data.get("gameMode", "classic"),
            "players": [],
            "food": [],
            "powerUps": [],
            "startTime": datetime.utcnow(),
            "isActive": True,
            "maxPlayers": game_data.get("maxPlayers", 20)
        }
        self.games[game_id] = game
        return game
    
    async def get_game(self, game_id: str) -> Optional[dict]:
        return self.games.get(game_id)
    
    async def update_game(self, game_id: str, updates: dict) -> bool:
        if game_id in self.games:
            self.games[game_id].update(updates)
            return True
        return False
    
    async def get_active_games(self) -> List[dict]:
        return [game for game in self.games.values() if game.get("isActive", False)]
    
    # Transaction operations
    async def create_transaction(self, transaction_data: dict) -> dict:
        transaction_id = str(uuid.uuid4())
        transaction = {
            "id": transaction_id,  # Use 'id' for consistency
            "playerId": transaction_data.get("playerId"),
            "type": transaction_data.get("type"),
            "amount": transaction_data.get("amount"),
            "status": "completed",
            "transactionId": str(uuid.uuid4()),
            "timestamp": datetime.utcnow()
        }
        self.transactions[transaction_id] = transaction
        return transaction
    
    async def get_player_transactions(self, player_id: str) -> List[dict]:
        return [
            t for t in self.transactions.values()
            if t.get("playerId") == player_id
        ]
    
    # Shop operations
    async def get_shop_items(self, category: str = None, currency: str = None) -> List[dict]:
        """Get shop items, optionally filtered by category and currency"""
        items = [item for item in self.shop_items.values() if item.get("isAvailable", True)]
        
        # Apply filters if provided
        if category:
            items = [item for item in items if item.get("category") == category]
        if currency:
            items = [item for item in items if item.get("currency", "virtual") == currency]
        
        return items
    
    async def get_shop_item(self, item_id: str) -> Optional[dict]:
        return self.shop_items.get(item_id)
    
    # Inventory operations
    async def add_to_inventory(self, player_id: str, item_id: str) -> dict:
        inventory_id = str(uuid.uuid4())
        inventory_item = {
            "id": inventory_id,  # Use 'id' for consistency
            "playerId": player_id,
            "itemId": item_id,
            "quantity": 1,
            "isEquipped": False,
            "acquiredAt": datetime.utcnow()
        }
        self.player_inventory[inventory_id] = inventory_item
        return inventory_item
    
    async def get_player_inventory(self, player_id: str) -> List[dict]:
        return [
            item for item in self.player_inventory.values()
            if item.get("playerId") == player_id
        ]
    
    async def equip_item(self, player_id: str, item_id: str) -> bool:
        # First unequip all items of the same category
        player_items = await self.get_player_inventory(player_id)
        item = await self.get_shop_item(item_id)
        
        if not item:
            return False
        
        category = item.get("category")
        
        # Unequip other items in same category
        for inv_item in player_items:
            if inv_item.get("isEquipped"):
                inv_item_details = await self.get_shop_item(inv_item.get("itemId"))
                if inv_item_details and inv_item_details.get("category") == category:
                    inv_item["isEquipped"] = False
        
        # Equip the specified item
        for inv_item in player_items:
            if inv_item.get("itemId") == item_id:
                inv_item["isEquipped"] = True
                return True
        
        return False

# Create global instance
database = InMemoryDatabase()