"""
WebSocket protocol for real-time Agar.io game communication.
Handles client-server messaging, compression, and state synchronization.
"""

import json
import asyncio
import time
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from fastapi import WebSocket, WebSocketDisconnect
import gzip
import base64
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class ClientMessage:
    """Base class for client messages"""
    type: str
    timestamp: float

@dataclass
class JoinMessage(ClientMessage):
    """Client wants to join a game"""
    player_id: str
    player_name: str
    game_mode: str = "classic"

@dataclass
class InputMessage(ClientMessage):
    """Client input for movement"""
    dir_x: float
    dir_y: float

@dataclass
class ActionMessage(ClientMessage):
    """Client action (split, eject, etc.)"""
    action: str  # 'split', 'eject', 'respawn'

@dataclass
class ChatMessage(ClientMessage):
    """Client chat message"""
    message: str

@dataclass
class ServerMessage:
    """Base class for server messages"""
    type: str
    timestamp: float

@dataclass
class InitMessage(ServerMessage):
    """Initial game state when player joins"""
    player_id: str
    world_size: float
    config: Dict[str, Any]

@dataclass
class GameStateMessage(ServerMessage):
    """Full or delta game state update"""
    state: Dict[str, Any]
    is_delta: bool = False

@dataclass
class LeaderboardMessage(ServerMessage):
    """Leaderboard update"""
    leaderboard: List[Dict[str, Any]]

@dataclass
class KillFeedMessage(ServerMessage):
    """Kill feed notification"""
    killer: str
    victim: str
    killer_mass: float

@dataclass
class ChatBroadcastMessage(ServerMessage):
    """Chat message broadcast"""
    player_name: str
    message: str

@dataclass
class PingMessage(ServerMessage):
    """Ping message for latency measurement"""
    ping_id: str

class MessageCompressor:
    """Handles message compression for WebSocket traffic"""
    
    @staticmethod
    def compress_message(message: Dict) -> str:
        """Compress message using gzip and base64 encoding"""
        json_str = json.dumps(message, separators=(',', ':'))
        compressed = gzip.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('ascii')
    
    @staticmethod
    def decompress_message(compressed_data: str) -> Dict:
        """Decompress message from base64 gzip"""
        try:
            compressed = base64.b64decode(compressed_data.encode('ascii'))
            decompressed = gzip.decompress(compressed)
            return json.loads(decompressed.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decompress message: {e}")
            raise

class DeltaCompressor:
    """Handles delta compression for game state updates"""
    
    def __init__(self):
        self.last_states: Dict[str, Dict] = {}  # client_id -> last_state
    
    def create_delta(self, client_id: str, current_state: Dict) -> Dict:
        """Create delta from last known state for client"""
        if client_id not in self.last_states:
            # First update - send full state
            self.last_states[client_id] = current_state.copy()
            return current_state
        
        last_state = self.last_states[client_id]
        delta = {}
        
        # Compare and create delta for each entity type
        for entity_type in ['cells', 'food', 'viruses', 'ejected_mass']:
            if entity_type in current_state:
                delta[entity_type] = self._create_entity_delta(
                    last_state.get(entity_type, []),
                    current_state[entity_type]
                )
        
        # Update last known state
        self.last_states[client_id] = current_state.copy()
        
        return delta
    
    def _create_entity_delta(self, old_entities: List[Dict], new_entities: List[Dict]) -> Dict:
        """Create delta for entity list"""
        # Convert to ID-indexed dicts for easier comparison
        old_dict = {entity['id']: entity for entity in old_entities}
        new_dict = {entity['id']: entity for entity in new_entities}
        
        delta = {
            'added': [],
            'updated': [],
            'removed': []
        }
        
        # Find added and updated entities
        for entity_id, entity in new_dict.items():
            if entity_id not in old_dict:
                delta['added'].append(entity)
            elif entity != old_dict[entity_id]:
                delta['updated'].append(entity)
        
        # Find removed entities
        for entity_id in old_dict:
            if entity_id not in new_dict:
                delta['removed'].append(entity_id)
        
        return delta
    
    def remove_client(self, client_id: str):
        """Remove client from delta tracking"""
        if client_id in self.last_states:
            del self.last_states[client_id]

class RateLimiter:
    """Rate limiting for WebSocket messages"""
    
    def __init__(self, max_messages: int = 100, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.client_messages: Dict[str, deque] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        current_time = time.time()
        
        if client_id not in self.client_messages:
            self.client_messages[client_id] = deque()
        
        messages = self.client_messages[client_id]
        
        # Remove old messages outside the window
        while messages and current_time - messages[0] > self.window_seconds:
            messages.popleft()
        
        # Check if under limit
        if len(messages) >= self.max_messages:
            return False
        
        # Add current message
        messages.append(current_time)
        return True
    
    def remove_client(self, client_id: str):
        """Remove client from rate limiting"""
        if client_id in self.client_messages:
            del self.client_messages[client_id]

class ViewportCuller:
    """Culls entities outside client viewport for bandwidth optimization"""
    
    @staticmethod
    def cull_state_for_viewport(game_state: Dict, player_position: tuple, 
                               viewport_size: float) -> Dict:
        """Remove entities outside viewport to reduce bandwidth"""
        if not player_position:
            return game_state
        
        px, py = player_position
        half_viewport = viewport_size / 2
        
        culled_state = {}
        
        for entity_type, entities in game_state.items():
            if entity_type in ['cells', 'food', 'viruses', 'ejected_mass']:
                culled_entities = []
                for entity in entities:
                    ex, ey = entity.get('x', 0), entity.get('y', 0)
                    
                    # Check if entity is within viewport
                    if (abs(ex - px) <= half_viewport and 
                        abs(ey - py) <= half_viewport):
                        culled_entities.append(entity)
                
                culled_state[entity_type] = culled_entities
            else:
                culled_state[entity_type] = entities
        
        return culled_state

class WebSocketGameClient:
    """Represents a connected WebSocket client"""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.player_id: Optional[str] = None
        self.game_id: Optional[str] = None
        self.last_ping_time = time.time()
        self.is_authenticated = False
        self.viewport_size = 1000.0  # Default viewport size
        
        # Performance tracking
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
    
    async def send_message(self, message: ServerMessage, compress: bool = True):
        """Send message to client"""
        try:
            message_dict = asdict(message)
            
            if compress:
                compressed_data = MessageCompressor.compress_message(message_dict)
                await self.websocket.send_text(f"COMPRESSED:{compressed_data}")
            else:
                await self.websocket.send_json(message_dict)
            
            self.messages_sent += 1
            self.bytes_sent += len(str(message_dict))
            
        except Exception as e:
            logger.error(f"Failed to send message to client {self.client_id}: {e}")
            raise
    
    async def receive_message(self) -> Optional[ClientMessage]:
        """Receive and parse message from client"""
        try:
            data = await self.websocket.receive_text()
            self.bytes_received += len(data)
            
            # Handle compressed messages
            if data.startswith("COMPRESSED:"):
                compressed_data = data[11:]  # Remove "COMPRESSED:" prefix
                message_dict = MessageCompressor.decompress_message(compressed_data)
            else:
                message_dict = json.loads(data)
            
            self.messages_received += 1
            
            # Parse message based on type
            msg_type = message_dict.get('type')
            timestamp = message_dict.get('timestamp', time.time())
            
            if msg_type == 'join':
                return JoinMessage(
                    type=msg_type,
                    timestamp=timestamp,
                    player_id=message_dict['player_id'],
                    player_name=message_dict['player_name'],
                    game_mode=message_dict.get('game_mode', 'classic')
                )
            elif msg_type == 'input':
                return InputMessage(
                    type=msg_type,
                    timestamp=timestamp,
                    dir_x=message_dict['dir_x'],
                    dir_y=message_dict['dir_y']
                )
            elif msg_type == 'action':
                return ActionMessage(
                    type=msg_type,
                    timestamp=timestamp,
                    action=message_dict['action']
                )
            elif msg_type == 'chat':
                return ChatMessage(
                    type=msg_type,
                    timestamp=timestamp,
                    message=message_dict['message']
                )
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                return None
                
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Failed to receive message from client {self.client_id}: {e}")
            return None

class WebSocketManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.clients: Dict[str, WebSocketGameClient] = {}
        self.game_clients: Dict[str, Set[str]] = {}  # game_id -> client_ids
        self.delta_compressor = DeltaCompressor()
        self.rate_limiter = RateLimiter()
        self.stats = {
            'connections': 0,
            'disconnections': 0,
            'messages_processed': 0,
            'bytes_transferred': 0
        }
    
    async def connect_client(self, websocket: WebSocket, client_id: str) -> WebSocketGameClient:
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        client = WebSocketGameClient(websocket, client_id)
        self.clients[client_id] = client
        self.stats['connections'] += 1
        
        logger.info(f"WebSocket client {client_id} connected")
        return client
    
    def disconnect_client(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.clients:
            client = self.clients[client_id]
            
            # Remove from game tracking
            if client.game_id and client.game_id in self.game_clients:
                self.game_clients[client.game_id].discard(client_id)
                if not self.game_clients[client.game_id]:
                    del self.game_clients[client.game_id]
            
            # Clean up tracking data
            self.delta_compressor.remove_client(client_id)
            self.rate_limiter.remove_client(client_id)
            
            del self.clients[client_id]
            self.stats['disconnections'] += 1
            
            logger.info(f"WebSocket client {client_id} disconnected")
    
    def add_client_to_game(self, client_id: str, game_id: str):
        """Add client to game for targeted broadcasts"""
        if client_id in self.clients:
            self.clients[client_id].game_id = game_id
            
            if game_id not in self.game_clients:
                self.game_clients[game_id] = set()
            self.game_clients[game_id].add(client_id)
    
    async def broadcast_to_game(self, game_id: str, message: ServerMessage, 
                               exclude_client: Optional[str] = None,
                               compress: bool = True):
        """Broadcast message to all clients in a game"""
        if game_id not in self.game_clients:
            return
        
        clients_to_send = self.game_clients[game_id].copy()
        if exclude_client:
            clients_to_send.discard(exclude_client)
        
        # Send to all clients concurrently
        tasks = []
        for client_id in clients_to_send:
            if client_id in self.clients:
                client = self.clients[client_id]
                tasks.append(client.send_message(message, compress))
        
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                self.stats['messages_processed'] += len(tasks)
            except Exception as e:
                logger.error(f"Error broadcasting to game {game_id}: {e}")
    
    async def send_game_state_update(self, game_id: str, game_state: Dict,
                                   player_positions: Dict[str, tuple]):
        """Send optimized game state update to clients"""
        if game_id not in self.game_clients:
            return
        
        tasks = []
        
        for client_id in self.game_clients[game_id]:
            if client_id not in self.clients:
                continue
                
            client = self.clients[client_id]
            
            # Get player position for viewport culling
            player_pos = player_positions.get(client.player_id, (0, 0))
            
            # Cull state for viewport
            culled_state = ViewportCuller.cull_state_for_viewport(
                game_state, player_pos, client.viewport_size
            )
            
            # Create delta for bandwidth optimization
            delta_state = self.delta_compressor.create_delta(client_id, culled_state)
            
            # Send update
            message = GameStateMessage(
                type="game_state",
                timestamp=time.time(),
                state=delta_state,
                is_delta=True
            )
            
            tasks.append(client.send_message(message, compress=True))
        
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                self.stats['messages_processed'] += len(tasks)
            except Exception as e:
                logger.error(f"Error sending game state to game {game_id}: {e}")
    
    async def send_to_client(self, client_id: str, message: ServerMessage, 
                           compress: bool = True):
        """Send message to specific client"""
        if client_id in self.clients:
            try:
                await self.clients[client_id].send_message(message, compress)
                self.stats['messages_processed'] += 1
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
    
    def is_message_allowed(self, client_id: str) -> bool:
        """Check if client can send message (rate limiting)"""
        return self.rate_limiter.is_allowed(client_id)
    
    def get_client_stats(self, client_id: str) -> Optional[Dict]:
        """Get statistics for a client"""
        if client_id in self.clients:
            client = self.clients[client_id]
            return {
                'messages_sent': client.messages_sent,
                'messages_received': client.messages_received,
                'bytes_sent': client.bytes_sent,
                'bytes_received': client.bytes_received,
                'ping_time': time.time() - client.last_ping_time
            }
        return None
    
    def get_manager_stats(self) -> Dict:
        """Get overall manager statistics"""
        total_bytes = sum(
            client.bytes_sent + client.bytes_received 
            for client in self.clients.values()
        )
        
        return {
            **self.stats,
            'active_connections': len(self.clients),
            'active_games': len(self.game_clients),
            'total_bytes_transferred': total_bytes
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()