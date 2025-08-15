"""
Production game room manager with server-authoritative physics engine.
Handles game rooms, player management, and real-time game loops.
"""

import asyncio
import time
import logging
import random
import uuid
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from game_engine import GameEngine, Vector2
from websocket_protocol import (
    WebSocketManager, websocket_manager,
    GameStateMessage, LeaderboardMessage, KillFeedMessage,
    InitMessage
)

logger = logging.getLogger(__name__)

@dataclass
class GameModeConfig:
    """Configuration for different game modes"""
    name: str
    entry_fee: int
    max_players: int
    world_size: float
    match_duration: Optional[int] = None  # seconds, None for endless
    food_count: int = 1000
    virus_count: int = 50
    spawn_protection_time: float = 3.0  # seconds
    special_rules: Dict = field(default_factory=dict)

@dataclass
class PlayerState:
    """Player state in a game room"""
    player_id: str
    name: str
    join_time: float
    last_activity: float
    is_alive: bool = True
    is_spectating: bool = False
    score: int = 0
    kills: int = 0
    spawn_protection_until: float = 0.0
    
    def update_activity(self):
        self.last_activity = time.time()

@dataclass
class GameRoom:
    """Game room with server-authoritative engine"""
    id: str
    game_mode: str
    config: GameModeConfig
    engine: GameEngine
    players: Dict[str, PlayerState] = field(default_factory=dict)
    spectators: Set[str] = field(default_factory=set)
    created_time: float = field(default_factory=time.time)
    last_tick_time: float = field(default_factory=time.time)
    tick_count: int = 0
    is_active: bool = True
    private_code: Optional[str] = None
    leaderboard: List[Dict] = field(default_factory=list)
    kill_feed: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        # Set up engine with mode-specific configuration
        self.engine.config.update({
            'food_count': self.config.food_count,
            'virus_count': self.config.virus_count,
        })
        
        # Apply special rules
        if 'speed_multiplier' in self.config.special_rules:
            # Modify engine speed calculations if needed
            pass
    
    def add_player(self, player_id: str, name: str) -> bool:
        """Add player to the room"""
        if len(self.players) >= self.config.max_players:
            return False
        
        current_time = time.time()
        player_state = PlayerState(
            player_id=player_id,
            name=name,
            join_time=current_time,
            last_activity=current_time,
            spawn_protection_until=current_time + self.config.spawn_protection_time
        )
        
        self.players[player_id] = player_state
        
        # Add to engine
        cell_id = self.engine.add_player(player_id, name)
        
        logger.info(f"Player {name} ({player_id}) joined room {self.id}")
        return True
    
    def remove_player(self, player_id: str):
        """Remove player from the room"""
        if player_id in self.players:
            player_name = self.players[player_id].name
            del self.players[player_id]
            
            # Remove from engine
            self.engine.remove_player(player_id)
            
            logger.info(f"Player {player_name} ({player_id}) left room {self.id}")
    
    def add_spectator(self, player_id: str):
        """Add player as spectator"""
        self.spectators.add(player_id)
        if player_id in self.players:
            self.players[player_id].is_spectating = True
    
    def respawn_player(self, player_id: str) -> bool:
        """Respawn a dead player"""
        if player_id not in self.players:
            return False
        
        player = self.players[player_id]
        if player.is_alive:
            return False
        
        current_time = time.time()
        
        # Reset player state
        player.is_alive = True
        player.is_spectating = False
        player.spawn_protection_until = current_time + self.config.spawn_protection_time
        player.update_activity()
        
        # Add back to engine
        self.engine.add_player(player_id, player.name)
        
        logger.info(f"Player {player.name} respawned in room {self.id}")
        return True
    
    def is_player_protected(self, player_id: str) -> bool:
        """Check if player has spawn protection"""
        if player_id not in self.players:
            return False
        
        player = self.players[player_id]
        return time.time() < player.spawn_protection_until
    
    def update_leaderboard(self):
        """Update room leaderboard"""
        player_scores = []
        
        for player_id, player in self.players.items():
            if not player.is_alive:
                continue
                
            player_state = self.engine.get_player_state(player_id)
            if player_state:
                total_mass = player_state['total_mass']
                player_scores.append({
                    'name': player.name,
                    'score': int(total_mass),
                    'kills': player.kills
                })
        
        # Sort by score (mass)
        player_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(player_scores):
            entry['rank'] = i + 1
        
        self.leaderboard = player_scores[:10]  # Top 10
    
    def add_kill_feed_entry(self, killer_id: str, victim_id: str, killer_mass: float):
        """Add entry to kill feed"""
        killer_name = self.players.get(killer_id, {}).get('name', 'Unknown')
        victim_name = self.players.get(victim_id, {}).get('name', 'Unknown')
        
        entry = {
            'killer': killer_name,
            'victim': victim_name,
            'killer_mass': killer_mass,
            'timestamp': time.time()
        }
        
        self.kill_feed.append(entry)
        
        # Keep only last 10 entries
        if len(self.kill_feed) > 10:
            self.kill_feed = self.kill_feed[-10:]
        
        # Update killer's kill count
        if killer_id in self.players:
            self.players[killer_id].kills += 1
    
    def should_close(self) -> bool:
        """Check if room should be closed"""
        # Close if empty for too long
        if not self.players and time.time() - self.created_time > 300:  # 5 minutes
            return True
        
        # Close if match duration exceeded
        if (self.config.match_duration and 
            time.time() - self.created_time > self.config.match_duration):
            return True
        
        return False

class GameRoomManager:
    """Manages game rooms and orchestrates real-time gameplay"""
    
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.private_codes: Dict[str, str] = {}  # code -> room_id
        self.player_rooms: Dict[str, str] = {}  # player_id -> room_id
        
        # Game mode configurations
        self.game_modes = {
            'classic': GameModeConfig(
                name='Classic',
                entry_fee=10,
                max_players=30,
                world_size=2000.0,
                food_count=1000,
                virus_count=50
            ),
            'fast': GameModeConfig(
                name='Fast Mode',
                entry_fee=15,
                max_players=25,
                world_size=1500.0,
                food_count=800,
                virus_count=40,
                special_rules={'speed_multiplier': 1.5}
            ),
            'hardcore': GameModeConfig(
                name='Hardcore',
                entry_fee=25,
                max_players=20,
                world_size=2500.0,
                food_count=600,
                virus_count=80,
                special_rules={'no_respawn': True}
            ),
            'teams': GameModeConfig(
                name='Team Mode',
                entry_fee=10,
                max_players=40,
                world_size=2500.0,
                food_count=1200,
                virus_count=60,
                special_rules={'team_mode': True}
            )
        }
        
        # Performance tracking
        self.stats = {
            'rooms_created': 0,
            'rooms_closed': 0,
            'total_ticks': 0,
            'avg_tick_time': 0.0
        }
        
        # Start the main game loop
        self.running = False
        self.tick_task = None
    
    async def start(self):
        """Start the game room manager"""
        if not self.running:
            self.running = True
            self.tick_task = asyncio.create_task(self._main_loop())
            logger.info("Game room manager started")
    
    async def stop(self):
        """Stop the game room manager"""
        self.running = False
        if self.tick_task:
            self.tick_task.cancel()
            try:
                await self.tick_task
            except asyncio.CancelledError:
                pass
        logger.info("Game room manager stopped")
    
    async def _main_loop(self):
        """Main game loop running at ~30 TPS"""
        target_fps = 30
        frame_time = 1.0 / target_fps
        
        while self.running:
            start_time = time.time()
            
            try:
                await self._tick_all_rooms()
                await self._cleanup_rooms()
            except Exception as e:
                logger.error(f"Error in main game loop: {e}")
            
            # Calculate sleep time to maintain target FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            
            # Update stats
            actual_frame_time = time.time() - start_time
            self.stats['avg_tick_time'] = (
                self.stats['avg_tick_time'] * 0.95 + actual_frame_time * 0.05
            )
    
    async def _tick_all_rooms(self):
        """Tick all active game rooms"""
        current_time = time.time()
        
        for room in list(self.rooms.values()):
            if not room.is_active:
                continue
            
            dt = current_time - room.last_tick_time
            room.last_tick_time = current_time
            room.tick_count += 1
            
            # Tick game engine
            room.engine.tick(dt)
            
            # Update room state
            await self._update_room_state(room)
            
            # Broadcast updates to clients
            await self._broadcast_room_updates(room)
        
        self.stats['total_ticks'] += len(self.rooms)
    
    async def _update_room_state(self, room: GameRoom):
        """Update room-specific state"""
        # Check for player eliminations
        eliminated_players = []
        
        for player_id, player in room.players.items():
            if not player.is_alive:
                continue
            
            player_state = room.engine.get_player_state(player_id)
            if not player_state or not player_state['cells']:
                # Player eliminated
                player.is_alive = False
                player.is_spectating = True
                eliminated_players.append(player_id)
                logger.info(f"Player {player.name} eliminated in room {room.id}")
        
        # Update leaderboard
        room.update_leaderboard()
        
        # Handle match end conditions
        if room.config.match_duration:
            match_time = time.time() - room.created_time
            if match_time >= room.config.match_duration:
                await self._end_match(room)
    
    async def _broadcast_room_updates(self, room: GameRoom):
        """Broadcast game state updates to room clients"""
        if not room.players and not room.spectators:
            return
        
        # Get current game state
        game_state = room.engine.get_game_state()
        
        # Get player positions for viewport culling
        player_positions = {}
        for player_id in room.players:
            player_state = room.engine.get_player_state(player_id)
            if player_state and player_state['cells']:
                # Use position of largest cell
                largest_cell = max(player_state['cells'], key=lambda c: c['mass'])
                player_positions[player_id] = (largest_cell['x'], largest_cell['y'])
        
        # Send game state update
        await websocket_manager.send_game_state_update(
            room.id, game_state, player_positions
        )
        
        # Broadcast leaderboard every 2 seconds
        if room.tick_count % 60 == 0:  # 30 TPS, so every 60 ticks = 2 seconds
            leaderboard_msg = LeaderboardMessage(
                type='leaderboard',
                timestamp=time.time(),
                leaderboard=room.leaderboard
            )
            await websocket_manager.broadcast_to_game(room.id, leaderboard_msg)
    
    async def _cleanup_rooms(self):
        """Clean up inactive or empty rooms"""
        rooms_to_remove = []
        
        for room_id, room in self.rooms.items():
            if room.should_close():
                rooms_to_remove.append(room_id)
        
        for room_id in rooms_to_remove:
            await self._close_room(room_id)
    
    async def _close_room(self, room_id: str):
        """Close a game room"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        
        # Remove all players
        for player_id in list(room.players.keys()):
            self.remove_player_from_room(player_id)
        
        # Remove private code mapping
        if room.private_code and room.private_code in self.private_codes:
            del self.private_codes[room.private_code]
        
        del self.rooms[room_id]
        self.stats['rooms_closed'] += 1
        
        logger.info(f"Closed room {room_id}")
    
    async def _end_match(self, room: GameRoom):
        """End a timed match"""
        # Determine winners based on leaderboard
        winners = room.leaderboard[:3] if room.leaderboard else []
        
        # TODO: Award prizes, update player stats
        
        # Mark room as inactive
        room.is_active = False
        
        logger.info(f"Match ended in room {room.id}, winners: {[w['name'] for w in winners]}")
    
    def create_room(self, game_mode: str, private: bool = False) -> Optional[str]:
        """Create a new game room"""
        if game_mode not in self.game_modes:
            logger.error(f"Unknown game mode: {game_mode}")
            return None
        
        room_id = str(uuid.uuid4())
        config = self.game_modes[game_mode]
        engine = GameEngine(world_size=config.world_size)
        
        room = GameRoom(
            id=room_id,
            game_mode=game_mode,
            config=config,
            engine=engine
        )
        
        if private:
            # Generate private code
            code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
            room.private_code = code
            self.private_codes[code] = room_id
        
        self.rooms[room_id] = room
        self.stats['rooms_created'] += 1
        
        logger.info(f"Created {game_mode} room {room_id}" + 
                   (f" with code {code}" if private else ""))
        
        return room_id
    
    def find_available_room(self, game_mode: str) -> Optional[str]:
        """Find an available room for the game mode"""
        for room_id, room in self.rooms.items():
            if (room.game_mode == game_mode and 
                room.is_active and 
                not room.private_code and
                len(room.players) < room.config.max_players):
                return room_id
        
        # Create new room if none available
        return self.create_room(game_mode)
    
    def join_room_by_code(self, code: str) -> Optional[str]:
        """Join a private room by code"""
        if code in self.private_codes:
            room_id = self.private_codes[code]
            if room_id in self.rooms:
                room = self.rooms[room_id]
                if len(room.players) < room.config.max_players:
                    return room_id
        return None
    
    async def add_player_to_room(self, room_id: str, player_id: str, 
                                player_name: str) -> bool:
        """Add player to a room"""
        if room_id not in self.rooms:
            return False
        
        room = self.rooms[room_id]
        
        # Remove from previous room if any
        if player_id in self.player_rooms:
            old_room_id = self.player_rooms[player_id]
            self.remove_player_from_room(player_id)
        
        # Add to new room
        if room.add_player(player_id, player_name):
            self.player_rooms[player_id] = room_id
            
            # Add to WebSocket tracking
            websocket_manager.add_client_to_game(player_id, room_id)
            
            # Send initial game state to player
            await self._send_initial_state(player_id, room)
            
            return True
        
        return False
    
    def remove_player_from_room(self, player_id: str):
        """Remove player from their current room"""
        if player_id not in self.player_rooms:
            return
        
        room_id = self.player_rooms[player_id]
        if room_id in self.rooms:
            self.rooms[room_id].remove_player(player_id)
        
        del self.player_rooms[player_id]
    
    async def _send_initial_state(self, player_id: str, room: GameRoom):
        """Send initial game state to a joining player"""
        init_msg = InitMessage(
            type='init',
            timestamp=time.time(),
            player_id=player_id,
            world_size=room.config.world_size,
            config={
                'game_mode': room.game_mode,
                'max_players': room.config.max_players,
                'entry_fee': room.config.entry_fee
            }
        )
        
        await websocket_manager.send_to_client(player_id, init_msg)
    
    def handle_player_input(self, player_id: str, dir_x: float, dir_y: float):
        """Handle player movement input"""
        if player_id not in self.player_rooms:
            return
        
        room_id = self.player_rooms[player_id]
        if room_id in self.rooms:
            room = self.rooms[room_id]
            
            # Update player activity
            if player_id in room.players:
                room.players[player_id].update_activity()
            
            # Send input to engine
            direction = Vector2(dir_x, dir_y)
            room.engine.update_player_input(player_id, direction)
    
    async def handle_player_action(self, player_id: str, action: str) -> bool:
        """Handle player actions (split, eject, respawn)"""
        if player_id not in self.player_rooms:
            return False
        
        room_id = self.player_rooms[player_id]
        if room_id not in self.rooms:
            return False
        
        room = self.rooms[room_id]
        
        # Update player activity
        if player_id in room.players:
            room.players[player_id].update_activity()
        
        if action == 'split':
            return room.engine.player_split(player_id)
        elif action == 'eject':
            return room.engine.player_eject_mass(player_id)
        elif action == 'respawn':
            return room.respawn_player(player_id)
        
        return False
    
    def get_room_info(self, room_id: str) -> Optional[Dict]:
        """Get information about a room"""
        if room_id not in self.rooms:
            return None
        
        room = self.rooms[room_id]
        
        return {
            'id': room.id,
            'game_mode': room.game_mode,
            'player_count': len(room.players),
            'max_players': room.config.max_players,
            'is_private': room.private_code is not None,
            'created_time': room.created_time,
            'is_active': room.is_active
        }
    
    def list_public_rooms(self) -> List[Dict]:
        """List all public rooms"""
        public_rooms = []
        
        for room in self.rooms.values():
            if not room.private_code and room.is_active:
                public_rooms.append({
                    'id': room.id,
                    'game_mode': room.game_mode,
                    'player_count': len(room.players),
                    'max_players': room.config.max_players,
                    'created_time': room.created_time
                })
        
        return public_rooms
    
    def get_manager_stats(self) -> Dict:
        """Get manager statistics"""
        return {
            **self.stats,
            'active_rooms': len(self.rooms),
            'total_players': len(self.player_rooms),
            'game_modes': list(self.game_modes.keys())
        }

# Global game room manager
game_room_manager = GameRoomManager()