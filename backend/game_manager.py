import asyncio
import random
import math
from typing import Dict, List, Optional
from models import Game, GamePlayer, Food, PowerUp, GameState
from datetime import datetime, timedelta

class GameManager:
    def __init__(self):
        self.active_games: Dict[str, Game] = {}
        self.player_to_game: Dict[str, str] = {}  # playerId -> gameId
        
        # Enhanced game configurations for different modes
        self.GAME_CONFIGS = {
            'classic': {
                'FOOD_COUNT': 100,
                'POWERUP_COUNT': 5,
                'FOOD_REPLACEMENT_RATE': 0.5,
                'MATCH_DURATION': None,  # Unlimited
                'ARENA_SHRINK': False,
                'SPECIAL_RULES': {}
            },
            'tournament': {
                'FOOD_COUNT': 80,
                'POWERUP_COUNT': 8,
                'FOOD_REPLACEMENT_RATE': 0.4,
                'MATCH_DURATION': 900,  # 15 minutes
                'ARENA_SHRINK': False,
                'SPECIAL_RULES': {'elimination_threshold': 10}
            },
            'blitz': {
                'FOOD_COUNT': 120,
                'POWERUP_COUNT': 12,
                'FOOD_REPLACEMENT_RATE': 0.8,  # Fast-paced
                'MATCH_DURATION': 300,  # 5 minutes
                'ARENA_SHRINK': False,
                'SPECIAL_RULES': {'speed_multiplier': 1.5, 'score_multiplier': 2.0}
            },
            'royale': {
                'FOOD_COUNT': 150,
                'POWERUP_COUNT': 15,
                'FOOD_REPLACEMENT_RATE': 0.3,
                'MATCH_DURATION': 1200,  # 20 minutes
                'ARENA_SHRINK': True,
                'SPECIAL_RULES': {'shrink_start_time': 300, 'shrink_rate': 10}
            }
        }
        
    async def create_game(self, game_mode: str, player_id: str, player_name: str) -> Game:
        """Create a new game and add the player"""
        config = self.GAME_CONFIGS.get(game_mode, self.GAME_CONFIGS['classic'])
        
        game = Game(
            gameMode=game_mode,
            maxPlayers=self._get_max_players(game_mode)
        )
        
        # Add initial player
        game_player = GamePlayer(
            playerId=player_id,
            name=player_name,
            x=400.0,
            y=300.0,
            money=100,
            score=0,
            kills=0,
            color=self._get_random_color()
        )
        
        game.players.append(game_player)
        
        # Generate initial game content based on mode configuration
        game.food = self._generate_food(config['FOOD_COUNT'])
        game.powerUps = self._generate_power_ups(config['POWERUP_COUNT'])
        
        # Store game
        self.active_games[game.id] = game
        self.player_to_game[player_id] = game.id
        
        return game
    
    async def join_game(self, game_id: str, player_id: str, player_name: str) -> Optional[Game]:
        """Join an existing game"""
        if game_id not in self.active_games:
            return None
            
        game = self.active_games[game_id]
        
        if len(game.players) >= game.maxPlayers:
            return None
            
        # Check if player already in game
        for player in game.players:
            if player.playerId == player_id:
                return game
                
        # Add new player
        game_player = GamePlayer(
            playerId=player_id,
            name=player_name,
            x=random.uniform(50, 750),
            y=random.uniform(50, 550),
            money=100,
            score=0,
            kills=0,
            color=self._get_random_color()
        )
        
        game.players.append(game_player)
        self.player_to_game[player_id] = game_id
        
        return game
    
    async def find_or_create_game(self, game_mode: str, player_id: str, player_name: str) -> Game:
        """Find an available game or create a new one"""
        # Look for available games
        for game in self.active_games.values():
            if (game.gameMode == game_mode and 
                game.isActive and 
                len(game.players) < game.maxPlayers):
                joined_game = await self.join_game(game.id, player_id, player_name)
                if joined_game:
                    return joined_game
        
        # No available games, create new one
        return await self.create_game(game_mode, player_id, player_name)
    
    async def update_player_position(self, game_id: str, player_id: str, x: float, y: float, money: int) -> bool:
        """Update player position and money"""
        if game_id not in self.active_games:
            return False
            
        game = self.active_games[game_id]
        
        for player in game.players:
            if player.playerId == player_id:
                player.x = x
                player.y = y
                player.money = money
                return True
                
        return False
    
    async def get_game_state(self, game_id: str) -> Optional[GameState]:
        """Get current game state"""
        if game_id not in self.active_games:
            return None
            
        game = self.active_games[game_id]
        
        # Update game stats
        game_stats = {
            "playersOnline": len(game.players),
            "foodItems": len(game.food),
            "powerUps": len(game.powerUps),
            "gameMode": game.gameMode
        }
        
        return GameState(
            players=game.players,
            food=game.food,
            powerUps=game.powerUps,
            gameStats=game_stats
        )
    
    async def remove_player(self, player_id: str) -> bool:
        """Remove player from game"""
        if player_id not in self.player_to_game:
            return False
            
        game_id = self.player_to_game[player_id]
        game = self.active_games.get(game_id)
        
        if not game:
            return False
            
        # Remove player from game
        game.players = [p for p in game.players if p.playerId != player_id]
        del self.player_to_game[player_id]
        
        # Remove game if empty
        if len(game.players) == 0:
            del self.active_games[game_id]
            
        return True
    
    async def process_food_consumption(self, game_id: str, player_id: str, food_ids: List[str]) -> int:
        """Process food consumption and return points earned"""
        if game_id not in self.active_games:
            return 0
            
        game = self.active_games[game_id]
        config = self.GAME_CONFIGS.get(game.gameMode, self.GAME_CONFIGS['classic'])
        points_earned = 0
        
        # Remove consumed food and calculate points
        remaining_food = []
        for food in game.food:
            if food.id in food_ids:
                points_earned += food.value
            else:
                remaining_food.append(food)
                
        game.food = remaining_food
        
        # Generate new food based on game mode configuration
        new_food_count = len(food_ids)
        if new_food_count > 0:
            # Use mode-specific replacement rate
            replacement_rate = config['FOOD_REPLACEMENT_RATE']
            new_food_count = max(1, int(new_food_count * replacement_rate))
            new_food = self._generate_food(new_food_count)
            game.food.extend(new_food)
            
        return points_earned
    
    async def process_power_up_consumption(self, game_id: str, player_id: str, power_up_ids: List[str]) -> List[PowerUp]:
        """Process power-up consumption and return consumed power-ups"""
        if game_id not in self.active_games:
            return []
            
        game = self.active_games[game_id]
        consumed_power_ups = []
        
        # Remove consumed power-ups
        remaining_power_ups = []
        for power_up in game.powerUps:
            if power_up.id in power_up_ids:
                consumed_power_ups.append(power_up)
            else:
                remaining_power_ups.append(power_up)
                
        game.powerUps = remaining_power_ups
        
        # Generate new power-ups occasionally
        if len(consumed_power_ups) > 0 and random.random() < 0.3:
            new_power_ups = self._generate_power_ups(1)
            game.powerUps.extend(new_power_ups)
            
        return consumed_power_ups
    
    def _generate_food(self, count: int) -> List[Food]:
        """Generate random food items"""
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b', '#eb4d4b', '#6c5ce7', '#a29bfe', '#fd79a8', '#e84393']
        food_items = []
        
        for _ in range(count):
            food = Food(
                x=random.uniform(10, 790),
                y=random.uniform(10, 590),
                color=random.choice(colors),
                value=random.randint(1, 5)
            )
            food_items.append(food)
            
        return food_items
    
    def _generate_power_ups(self, count: int) -> List[PowerUp]:
        """Generate random power-ups"""
        power_up_types = [
            {"type": "Speed Boost", "color": "#ff9f43", "size": 8, "value": 20},
            {"type": "Size Boost", "color": "#10ac84", "size": 10, "value": 50},
            {"type": "Money Multiplier", "color": "#feca57", "size": 12, "value": 30},
            {"type": "Shield", "color": "#5f27cd", "size": 9, "value": 40},
            {"type": "Magnet", "color": "#00d2d3", "size": 7, "value": 25}
        ]
        
        power_ups = []
        for _ in range(count):
            power_up_data = random.choice(power_up_types)
            power_up = PowerUp(
                x=random.uniform(20, 780),
                y=random.uniform(20, 580),
                **power_up_data
            )
            power_ups.append(power_up)
            
        return power_ups
    
    def _get_random_color(self) -> str:
        """Get random player color"""
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
        return random.choice(colors)
    
    def _get_max_players(self, game_mode: str) -> int:
        """Get max players for game mode"""
        mode_limits = {
            'classic': 20,
            'tournament': 16,
            'blitz': 12,
            'royale': 50
        }
        return mode_limits.get(game_mode, 20)

# Global game manager instance
game_manager = GameManager()