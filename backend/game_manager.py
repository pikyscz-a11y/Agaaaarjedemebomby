import asyncio
import random
import math
from typing import Dict, List, Optional
from models import Game, GamePlayer, Food, PowerUp, GameState
from datetime import datetime, timedelta

class AIBot:
    def __init__(self, bot_id: str, name: str, x: float, y: float):
        self.bot_id = bot_id
        self.name = name
        self.x = x
        self.y = y
        self.money = random.randint(50, 200)
        self.score = self.money
        self.kills = random.randint(0, 5)
        self.color = self._get_random_color()
        self.target_x = x
        self.target_y = y
        self.speed = random.uniform(1.5, 3.5)
        self.aggressiveness = random.uniform(0.2, 0.8)  # How aggressive the bot is
        self.last_direction_change = datetime.now()
        self.direction_change_interval = random.uniform(2, 5)  # Seconds
        self.behavior = random.choice(['aggressive', 'defensive', 'neutral', 'feeder'])
        
    def _get_random_color(self) -> str:
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e', '#ff6b6b', '#4ecdc4']
        return random.choice(colors)
    
    def update_behavior(self, game_players: List[GamePlayer], food_items: List[Food]):
        """Update bot behavior based on surroundings"""
        now = datetime.now()
        
        # Change direction periodically
        if (now - self.last_direction_change).total_seconds() > self.direction_change_interval:
            self._change_direction(game_players, food_items)
            self.last_direction_change = now
            self.direction_change_interval = random.uniform(2, 8)
    
    def _change_direction(self, game_players: List[GamePlayer], food_items: List[Food]):
        """Intelligent direction change based on bot behavior and surroundings"""
        if self.behavior == 'aggressive':
            self._target_smaller_players(game_players)
        elif self.behavior == 'defensive':
            self._avoid_larger_players(game_players)
        elif self.behavior == 'feeder':
            self._target_food(food_items)
        else:  # neutral
            self._random_movement()
    
    def _target_smaller_players(self, players: List[GamePlayer]):
        """Target smaller players aggressively"""
        smaller_players = [p for p in players if p.money < self.money * 0.8]
        if smaller_players:
            target = min(smaller_players, key=lambda p: self._distance_to(p.x, p.y))
            self.target_x = target.x + random.uniform(-50, 50)
            self.target_y = target.y + random.uniform(-50, 50)
        else:
            self._random_movement()
    
    def _avoid_larger_players(self, players: List[GamePlayer]):
        """Avoid larger players defensively"""
        larger_players = [p for p in players if p.money > self.money * 1.2]
        if larger_players:
            # Move away from the closest large player
            closest = min(larger_players, key=lambda p: self._distance_to(p.x, p.y))
            dx = self.x - closest.x
            dy = self.y - closest.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                self.target_x = self.x + (dx / distance) * 100
                self.target_y = self.y + (dy / distance) * 100
        else:
            self._random_movement()
    
    def _target_food(self, food_items: List[Food]):
        """Target nearby food items"""
        if food_items:
            nearby_food = [f for f in food_items if self._distance_to(f.x, f.y) < 150]
            if nearby_food:
                target_food = min(nearby_food, key=lambda f: self._distance_to(f.x, f.y))
                self.target_x = target_food.x
                self.target_y = target_food.y
            else:
                self._random_movement()
        else:
            self._random_movement()
    
    def _random_movement(self):
        """Random movement pattern"""
        self.target_x = random.uniform(50, 750)
        self.target_y = random.uniform(50, 550)
    
    def _distance_to(self, x: float, y: float) -> float:
        """Calculate distance to a point"""
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)
    
    def update_position(self):
        """Update bot position towards target"""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Apply speed with some randomness
            actual_speed = self.speed * random.uniform(0.8, 1.2)
            move_x = (dx / distance) * actual_speed
            move_y = (dy / distance) * actual_speed
            
            # Update position with boundaries
            self.x = max(20, min(780, self.x + move_x))
            self.y = max(20, min(580, self.y + move_y))
    
    def to_game_player(self) -> GamePlayer:
        """Convert bot to GamePlayer format"""
        return GamePlayer(
            playerId=self.bot_id,
            name=self.name,
            x=self.x,
            y=self.y,
            money=self.money,
            score=self.score,
            kills=self.kills,
            color=self.color
        )

class GameManager:
    def __init__(self):
        self.active_games: Dict[str, Game] = {}
        self.player_to_game: Dict[str, str] = {}  # playerId -> gameId
        self.game_bots: Dict[str, List[AIBot]] = {}  # gameId -> List[AIBot]
        
        # Enhanced game configurations for different modes
        self.GAME_CONFIGS = {
            'classic': {
                'FOOD_COUNT': 100,
                'POWERUP_COUNT': 5,
                'FOOD_REPLACEMENT_RATE': 0.1,  # Much lower - only 10%
                'MATCH_DURATION': None,  # Unlimited
                'ARENA_SHRINK': False,
                'BOT_COUNT': 8,
                'SPECIAL_RULES': {}
            },
            'tournament': {
                'FOOD_COUNT': 80,
                'POWERUP_COUNT': 8,
                'FOOD_REPLACEMENT_RATE': 0.15,  # 15%
                'MATCH_DURATION': 900,  # 15 minutes
                'ARENA_SHRINK': False,
                'BOT_COUNT': 10,
                'SPECIAL_RULES': {'elimination_threshold': 10}
            },
            'blitz': {
                'FOOD_COUNT': 120,
                'POWERUP_COUNT': 12,
                'FOOD_REPLACEMENT_RATE': 0.3,  # Still fast but not crazy
                'MATCH_DURATION': 300,  # 5 minutes
                'ARENA_SHRINK': False,
                'BOT_COUNT': 15,
                'SPECIAL_RULES': {'speed_multiplier': 1.5, 'score_multiplier': 2.0}
            },
            'royale': {
                'FOOD_COUNT': 150,
                'POWERUP_COUNT': 15,
                'FOOD_REPLACEMENT_RATE': 0.05,  # Very low for survival mode
                'MATCH_DURATION': 1200,  # 20 minutes
                'ARENA_SHRINK': True,
                'BOT_COUNT': 25,
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
        
        # Create AI bots for the game
        bots = self._create_ai_bots(game.id, config['BOT_COUNT'])
        self.game_bots[game.id] = bots
        
        # Add bots to game as players
        for bot in bots:
            game.players.append(bot.to_game_player())
        
        # Store game
        self.active_games[game.id] = game
        self.player_to_game[player_id] = game.id
        
        # Start bot update loop
        asyncio.create_task(self._bot_update_loop(game.id))
        
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
    
    def _create_ai_bots(self, game_id: str, bot_count: int) -> List[AIBot]:
        """Create AI bots for a game"""
        bots = []
        bot_names = [
            "BotDestroyer", "CashGrabber", "MoneyHunter", "AgarKing", "BlobMaster",
            "CoinCollector", "PowerPlayer", "FastFeeder", "MegaBeast", "ProfitSeeker",
            "GoldRusher", "BallBuster", "MoneyMaker", "AgarLord", "BlobBoss",
            "CashCrusher", "FoodFiend", "ScoreSeeker", "WealthWolf", "BubbleBeast"
        ]
        
        for i in range(bot_count):
            bot_name = random.choice(bot_names) + str(random.randint(1, 999))
            bot_id = f"bot_{game_id}_{i}"
            
            # Random starting position
            x = random.uniform(50, 750)
            y = random.uniform(50, 550)
            
            bot = AIBot(bot_id, bot_name, x, y)
            bots.append(bot)
        
        return bots
    
    async def _bot_update_loop(self, game_id: str):
        """Continuous update loop for bots in a game"""
        while game_id in self.active_games:
            try:
                await self._update_bots(game_id)
                await asyncio.sleep(0.1)  # Update bots 10 times per second
            except Exception as e:
                print(f"Bot update error for game {game_id}: {e}")
                # Clean up inactive games
                if game_id not in self.active_games:
                    print(f"Cleaning up bot loop for inactive game {game_id}")
                    if game_id in self.game_bots:
                        del self.game_bots[game_id]
                break
    
    async def _update_bots(self, game_id: str):
        """Update all bots in a game"""
        if game_id not in self.active_games or game_id not in self.game_bots:
            return
        
        game = self.active_games[game_id]
        bots = self.game_bots[game_id]
        
        print(f"Updating {len(bots)} bots for game {game_id}")  # Debug log
        
        for bot in bots:
            # Update bot behavior and position
            human_players = [p for p in game.players if not p.playerId.startswith('bot_')]
            bot.update_behavior(human_players, game.food)
            bot.update_position()
            
            # Simulate bot food consumption
            if random.random() < 0.02:  # 2% chance per update
                nearby_food = [f for f in game.food if bot._distance_to(f.x, f.y) < 25]
                if nearby_food:
                    consumed_food = random.choice(nearby_food)
                    bot.money += consumed_food.value
                    bot.score += consumed_food.value
                    
                    # Remove consumed food and add new food
                    game.food = [f for f in game.food if f.id != consumed_food.id]
                    config = self.GAME_CONFIGS.get(game.gameMode, self.GAME_CONFIGS['classic'])
                    replacement_rate = config['FOOD_REPLACEMENT_RATE']
                    if random.random() < replacement_rate:  # Only replace based on rate
                        new_food = self._generate_food(1)
                        game.food.extend(new_food)
            
            # Update bot in game players list
            for i, player in enumerate(game.players):
                if player.playerId == bot.bot_id:
                    game.players[i] = bot.to_game_player()
                    break
    
    async def cleanup_inactive_games(self):
        """Clean up games with no active players"""
        games_to_remove = []
        
        for game_id, game in self.active_games.items():
            # Check if game has any human players (non-bot players)
            human_players = [p for p in game.players if not p.playerId.startswith('bot_')]
            
            if len(human_players) == 0:
                games_to_remove.append(game_id)
        
        for game_id in games_to_remove:
            print(f"Cleaning up inactive game: {game_id}")
            # Remove from active games
            del self.active_games[game_id]
            # Remove bot data
            if game_id in self.game_bots:
                del self.game_bots[game_id]
            # Clean up player-to-game mapping
            players_to_remove = [pid for pid, gid in self.player_to_game.items() if gid == game_id]
            for pid in players_to_remove:
                del self.player_to_game[pid]
        
        return len(games_to_remove)

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
            # Use mode-specific replacement rate (proper calculation without forcing minimum)
            replacement_rate = config['FOOD_REPLACEMENT_RATE']
            new_food_count = int(new_food_count * replacement_rate)
            if new_food_count > 0:  # Only generate if result is > 0
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

    async def apply_player_effects(self, player_id: str, inventory_effects: Dict) -> Dict:
        """Apply player's equipped item effects"""
        effects = {
            'speedMultiplier': 1.0,
            'valueMultiplier': 1.0,
            'damageReduction': 0.0,
            'scoreMultiplier': 1.0,
            'invincible': False,
            'vipStatus': False
        }
        
        # Apply effects from equipped items
        for item in inventory_effects:
            if item.get('isEquipped'):
                item_effects = item.get('effects', {})
                for effect_key, effect_value in item_effects.items():
                    if effect_key in effects:
                        if effect_key in ['speedMultiplier', 'valueMultiplier', 'scoreMultiplier']:
                            effects[effect_key] *= effect_value
                        elif effect_key == 'damageReduction':
                            effects[effect_key] = max(effects[effect_key], effect_value)
                        else:
                            effects[effect_key] = effect_value
        
    async def process_player_collisions(self, game_id: str, player_id: str) -> dict:
        """Process player vs player collisions"""
        if game_id not in self.active_games:
            return {"kills": 0, "deaths": 0, "money_gained": 0}
        
        game = self.active_games[game_id]
        current_player = None
        
        # Find current player
        for player in game.players:
            if player.playerId == player_id:
                current_player = player
                break
        
        if not current_player:
            return {"kills": 0, "deaths": 0, "money_gained": 0}
        
        current_size = self._calculate_size(current_player.money)
        kills = 0
        money_gained = 0
        died = False
        
        # Check collisions with other players
        remaining_players = []
        for other_player in game.players:
            if other_player.playerId == player_id:
                remaining_players.append(other_player)
                continue
                
            # Calculate distance
            dx = current_player.x - other_player.x
            dy = current_player.y - other_player.y
            distance = math.sqrt(dx * dx + dy * dy)
            other_size = self._calculate_size(other_player.money)
            
            # Check collision
            if distance < current_size + other_size:
                if current_size > other_size * 1.2:  # Current player eats other
                    earned_money = int(other_player.money * 0.8)
                    money_gained += earned_money
                    kills += 1
                    current_player.money += earned_money
                    current_player.score += earned_money
                    current_player.kills += 1
                    # Don't add eaten player to remaining_players
                elif other_size > current_size * 1.2:  # Other player eats current
                    died = True
                    current_player.isAlive = False
                    break
                else:
                    remaining_players.append(other_player)
            else:
                remaining_players.append(other_player)
        
        # Update game players list
        game.players = remaining_players
        
        return {
            "kills": kills,
            "deaths": 1 if died else 0,
            "money_gained": money_gained,
            "is_alive": not died
        }
    
    def _calculate_size(self, money: int) -> float:
        """Calculate player size based on money"""
        return 12 + math.sqrt(money / 10)  # Same formula as frontend

    async def update_arena_size(self, game_id: str) -> bool:
        """Update arena size for battle royale mode"""
        if game_id not in self.active_games:
            return False
            
        game = self.active_games[game_id]
        config = self.GAME_CONFIGS.get(game.gameMode, self.GAME_CONFIGS['classic'])
        
        if not config.get('ARENA_SHRINK'):
            return False
            
        # Calculate shrinking based on game time
        current_time = datetime.now()
        game_duration = (current_time - game.startTime).total_seconds()
        shrink_start = config['SPECIAL_RULES'].get('shrink_start_time', 300)
        
        if game_duration > shrink_start:
            # Arena starts shrinking after specified time
            shrink_rate = config['SPECIAL_RULES'].get('shrink_rate', 10)
            shrink_amount = (game_duration - shrink_start) * shrink_rate
            
            # Apply shrinking logic (this would be handled in frontend)
            return True
            
        return False

# Global game manager instance
game_manager = GameManager()