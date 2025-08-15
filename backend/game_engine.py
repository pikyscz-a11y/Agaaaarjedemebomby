"""
Server-authoritative game engine for Agar.io-style gameplay.
Implements physics, collision detection, and game mechanics.
"""

import math
import random
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class Vector2:
    """2D Vector for position and velocity calculations"""
    x: float = 0.0
    y: float = 0.0
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalized(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector2(0, 0)
        return Vector2(self.x / mag, self.y / mag)
    
    def distance_to(self, other) -> float:
        return (self - other).magnitude()

@dataclass
class Cell:
    """Player cell entity with physics properties"""
    id: str
    player_id: str
    position: Vector2
    velocity: Vector2 = field(default_factory=Vector2)
    mass: float = 10.0
    color: str = "#4CAF50"
    target_direction: Vector2 = field(default_factory=Vector2)
    last_split_time: float = 0.0
    last_eject_time: float = 0.0
    merge_cooldown: float = 0.0
    
    @property
    def radius(self) -> float:
        """Calculate radius from mass: r = sqrt(mass)"""
        return math.sqrt(self.mass)
    
    @property
    def speed(self) -> float:
        """Calculate speed from mass: v = v0 * mass^(-alpha)"""
        # Base speed and mass decay factor (tunable)
        v0 = 200.0  # Base speed
        alpha = 0.3  # Mass decay factor
        return v0 * (self.mass ** (-alpha))

@dataclass
class Food:
    """Food pellet entity"""
    id: str
    position: Vector2
    color: str
    value: float = 1.0
    radius: float = 3.0

@dataclass
class Virus:
    """Virus entity that can split large cells"""
    id: str
    position: Vector2
    mass: float = 100.0
    color: str = "#FF0000"
    
    @property
    def radius(self) -> float:
        return math.sqrt(self.mass)

@dataclass
class EjectedMass:
    """Mass ejected by players"""
    id: str
    position: Vector2
    velocity: Vector2
    mass: float = 10.0
    color: str = "#FFFF00"
    created_time: float = field(default_factory=time.time)
    
    @property
    def radius(self) -> float:
        return math.sqrt(self.mass)

class SpatialGrid:
    """Spatial partitioning for efficient collision detection"""
    
    def __init__(self, world_size: float, cell_size: float = 100.0):
        self.world_size = world_size
        self.cell_size = cell_size
        self.grid_size = int(world_size / cell_size) + 1
        self.grid: Dict[Tuple[int, int], List] = defaultdict(list)
    
    def clear(self):
        """Clear all grid cells"""
        self.grid.clear()
    
    def _get_grid_coords(self, position: Vector2) -> Tuple[int, int]:
        """Get grid coordinates for a position"""
        x = max(0, min(self.grid_size - 1, int(position.x / self.cell_size)))
        y = max(0, min(self.grid_size - 1, int(position.y / self.cell_size)))
        return (x, y)
    
    def add_entity(self, entity, entity_type: str):
        """Add entity to spatial grid"""
        grid_pos = self._get_grid_coords(entity.position)
        self.grid[grid_pos].append((entity, entity_type))
    
    def get_nearby_entities(self, position: Vector2, radius: float) -> List:
        """Get entities within radius of position"""
        nearby = []
        
        # Check surrounding grid cells
        grid_x, grid_y = self._get_grid_coords(position)
        cell_radius = math.ceil(radius / self.cell_size)
        
        for x in range(max(0, grid_x - cell_radius), min(self.grid_size, grid_x + cell_radius + 1)):
            for y in range(max(0, grid_y - cell_radius), min(self.grid_size, grid_y + cell_radius + 1)):
                nearby.extend(self.grid.get((x, y), []))
        
        return nearby

class GameEngine:
    """Core game engine handling physics and game mechanics"""
    
    def __init__(self, world_size: float = 2000.0):
        self.world_size = world_size
        self.spatial_grid = SpatialGrid(world_size)
        
        # Game entities
        self.cells: Dict[str, Cell] = {}
        self.food: Dict[str, Food] = {}
        self.viruses: Dict[str, Virus] = {}
        self.ejected_mass: Dict[str, EjectedMass] = {}
        
        # Player tracking
        self.player_cells: Dict[str, List[str]] = defaultdict(list)  # player_id -> cell_ids
        
        # Game configuration
        self.config = {
            'max_cells_per_player': 16,
            'split_cooldown': 1.0,  # seconds
            'eject_cooldown': 0.1,  # seconds
            'merge_time': 15.0,  # seconds before cells can merge
            'virus_split_threshold': 150.0,  # mass threshold for virus splits
            'eat_margin': 0.3,  # smaller cell must be this fraction to be eaten
            'friction': 0.9,  # velocity decay
            'border_size': 50.0,  # safe border around world
            'food_count': 1000,
            'virus_count': 50,
        }
        
        self._initialize_world()
    
    def _initialize_world(self):
        """Initialize food and viruses in the world"""
        self._spawn_food(self.config['food_count'])
        self._spawn_viruses(self.config['virus_count'])
    
    def _spawn_food(self, count: int):
        """Spawn food pellets randomly in the world"""
        for _ in range(count):
            food_id = f"food_{random.randint(10000, 99999)}"
            position = Vector2(
                random.uniform(0, self.world_size),
                random.uniform(0, self.world_size)
            )
            color = f"#{random.randint(0, 0xFFFFFF):06x}"
            
            self.food[food_id] = Food(
                id=food_id,
                position=position,
                color=color,
                value=random.uniform(0.5, 2.0)
            )
    
    def _spawn_viruses(self, count: int):
        """Spawn viruses randomly in the world"""
        for _ in range(count):
            virus_id = f"virus_{random.randint(10000, 99999)}"
            position = Vector2(
                random.uniform(50, self.world_size - 50),
                random.uniform(50, self.world_size - 50)
            )
            
            self.viruses[virus_id] = Virus(
                id=virus_id,
                position=position,
                mass=random.uniform(80, 120)
            )
    
    def add_player(self, player_id: str, name: str) -> str:
        """Add a new player to the game"""
        # Find safe spawn position
        spawn_pos = self._find_safe_spawn()
        
        cell_id = f"cell_{player_id}_{int(time.time())}"
        cell = Cell(
            id=cell_id,
            player_id=player_id,
            position=spawn_pos,
            mass=10.0,
            color=f"#{random.randint(0, 0xFFFFFF):06x}"
        )
        
        self.cells[cell_id] = cell
        self.player_cells[player_id].append(cell_id)
        
        logger.info(f"Player {player_id} spawned at {spawn_pos.x:.1f}, {spawn_pos.y:.1f}")
        return cell_id
    
    def _find_safe_spawn(self) -> Vector2:
        """Find a safe spawn position away from other players"""
        max_attempts = 20
        min_distance = 100.0
        
        for _ in range(max_attempts):
            pos = Vector2(
                random.uniform(self.config['border_size'], 
                             self.world_size - self.config['border_size']),
                random.uniform(self.config['border_size'], 
                             self.world_size - self.config['border_size'])
            )
            
            # Check distance to other players
            safe = True
            for cell in self.cells.values():
                if pos.distance_to(cell.position) < min_distance:
                    safe = False
                    break
            
            if safe:
                return pos
        
        # Fallback to center if no safe spot found
        return Vector2(self.world_size / 2, self.world_size / 2)
    
    def update_player_input(self, player_id: str, direction: Vector2):
        """Update player's movement direction"""
        for cell_id in self.player_cells[player_id]:
            if cell_id in self.cells:
                self.cells[cell_id].target_direction = direction.normalized()
    
    def player_split(self, player_id: str) -> bool:
        """Split player's cells"""
        current_time = time.time()
        cells_to_split = []
        
        # Check which cells can split
        for cell_id in self.player_cells[player_id]:
            if cell_id not in self.cells:
                continue
                
            cell = self.cells[cell_id]
            
            # Check split conditions
            if (cell.mass >= 20.0 and 
                current_time - cell.last_split_time >= self.config['split_cooldown'] and
                len(self.player_cells[player_id]) < self.config['max_cells_per_player']):
                cells_to_split.append(cell_id)
        
        if not cells_to_split:
            return False
        
        # Split the cells
        for cell_id in cells_to_split:
            cell = self.cells[cell_id]
            
            # Create new cell with half the mass
            new_mass = cell.mass / 2
            cell.mass = new_mass
            
            new_cell_id = f"cell_{player_id}_{int(time.time() * 1000)}"
            
            # Calculate split direction (in target direction)
            split_direction = cell.target_direction
            if split_direction.magnitude() == 0:
                split_direction = Vector2(1, 0)
            
            split_distance = cell.radius + math.sqrt(new_mass)
            new_position = cell.position + split_direction * split_distance
            
            new_cell = Cell(
                id=new_cell_id,
                player_id=player_id,
                position=new_position,
                velocity=split_direction * 200.0,  # Initial split velocity
                mass=new_mass,
                color=cell.color,
                target_direction=cell.target_direction,
                last_split_time=current_time,
                merge_cooldown=current_time + self.config['merge_time']
            )
            
            self.cells[new_cell_id] = new_cell
            self.player_cells[player_id].append(new_cell_id)
            
            # Update original cell
            cell.last_split_time = current_time
            cell.merge_cooldown = current_time + self.config['merge_time']
        
        logger.info(f"Player {player_id} split into {len(self.player_cells[player_id])} cells")
        return True
    
    def player_eject_mass(self, player_id: str) -> bool:
        """Eject mass from player's cells"""
        current_time = time.time()
        ejected = False
        
        for cell_id in self.player_cells[player_id]:
            if cell_id not in self.cells:
                continue
                
            cell = self.cells[cell_id]
            
            # Check eject conditions
            if (cell.mass >= 15.0 and 
                current_time - cell.last_eject_time >= self.config['eject_cooldown']):
                
                # Reduce cell mass
                eject_mass = min(cell.mass * 0.1, 10.0)
                cell.mass -= eject_mass
                cell.last_eject_time = current_time
                
                # Create ejected mass
                eject_direction = cell.target_direction
                if eject_direction.magnitude() == 0:
                    eject_direction = Vector2(1, 0)
                
                eject_distance = cell.radius + 15
                eject_position = cell.position + eject_direction * eject_distance
                
                ejected_id = f"ejected_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
                
                self.ejected_mass[ejected_id] = EjectedMass(
                    id=ejected_id,
                    position=eject_position,
                    velocity=eject_direction * 300.0,
                    mass=eject_mass,
                    color=cell.color
                )
                
                ejected = True
        
        return ejected
    
    def tick(self, dt: float):
        """Main game tick - updates physics and handles collisions"""
        # Update spatial grid
        self.spatial_grid.clear()
        
        # Add all entities to spatial grid
        for cell in self.cells.values():
            self.spatial_grid.add_entity(cell, 'cell')
        for food in self.food.values():
            self.spatial_grid.add_entity(food, 'food')
        for virus in self.viruses.values():
            self.spatial_grid.add_entity(virus, 'virus')
        for ejected in self.ejected_mass.values():
            self.spatial_grid.add_entity(ejected, 'ejected')
        
        # Update cell physics
        self._update_cell_physics(dt)
        
        # Update ejected mass physics
        self._update_ejected_mass_physics(dt)
        
        # Handle collisions
        self._handle_collisions()
        
        # Clean up expired entities
        self._cleanup_entities()
        
        # Maintain food count
        self._maintain_food_count()
    
    def _update_cell_physics(self, dt: float):
        """Update cell movement and physics"""
        for cell in self.cells.values():
            # Calculate movement toward target
            if cell.target_direction.magnitude() > 0:
                target_velocity = cell.target_direction * cell.speed
                # Smooth velocity transition
                cell.velocity = cell.velocity * 0.7 + target_velocity * 0.3
            
            # Apply friction
            cell.velocity = cell.velocity * self.config['friction']
            
            # Update position
            cell.position = cell.position + cell.velocity * dt
            
            # Apply world boundaries
            border = self.config['border_size']
            cell.position.x = max(border, min(self.world_size - border, cell.position.x))
            cell.position.y = max(border, min(self.world_size - border, cell.position.y))
    
    def _update_ejected_mass_physics(self, dt: float):
        """Update ejected mass movement"""
        to_remove = []
        current_time = time.time()
        
        for ejected_id, ejected in self.ejected_mass.items():
            # Apply friction to ejected mass
            ejected.velocity = ejected.velocity * 0.95
            ejected.position = ejected.position + ejected.velocity * dt
            
            # Remove after 30 seconds
            if current_time - ejected.created_time > 30.0:
                to_remove.append(ejected_id)
        
        for ejected_id in to_remove:
            del self.ejected_mass[ejected_id]
    
    def _handle_collisions(self):
        """Handle all collision detection and resolution"""
        self._handle_food_consumption()
        self._handle_cell_consumption()
        self._handle_virus_interactions()
        self._handle_ejected_mass_consumption()
        self._handle_cell_merging()
    
    def _handle_food_consumption(self):
        """Handle cells eating food"""
        food_to_remove = []
        
        for cell in self.cells.values():
            nearby = self.spatial_grid.get_nearby_entities(cell.position, cell.radius + 20)
            
            for entity, entity_type in nearby:
                if entity_type == 'food':
                    food = entity
                    distance = cell.position.distance_to(food.position)
                    
                    if distance < cell.radius + food.radius:
                        # Consume food
                        cell.mass += food.value
                        food_to_remove.append(food.id)
        
        # Remove consumed food
        for food_id in food_to_remove:
            if food_id in self.food:
                del self.food[food_id]
    
    def _handle_cell_consumption(self):
        """Handle cells eating other cells"""
        cells_to_remove = []
        
        for cell1 in self.cells.values():
            # Skip cells from same player
            for cell2 in self.cells.values():
                if (cell1.id == cell2.id or 
                    cell1.player_id == cell2.player_id):
                    continue
                
                distance = cell1.position.distance_to(cell2.position)
                
                # Check if larger cell can eat smaller cell
                if cell1.radius > cell2.radius:
                    eat_threshold = cell1.radius - cell2.radius * self.config['eat_margin']
                    if distance < eat_threshold and cell1.mass > cell2.mass * 1.2:
                        # Cell1 eats cell2
                        cell1.mass += cell2.mass
                        cells_to_remove.append(cell2.id)
                        
                        # Remove from player tracking
                        if cell2.id in self.player_cells[cell2.player_id]:
                            self.player_cells[cell2.player_id].remove(cell2.id)
                        
                        logger.info(f"Cell {cell1.id} consumed cell {cell2.id}")
        
        # Remove consumed cells
        for cell_id in cells_to_remove:
            if cell_id in self.cells:
                del self.cells[cell_id]
    
    def _handle_virus_interactions(self):
        """Handle virus interactions with cells and ejected mass"""
        for cell in self.cells.values():
            for virus in self.viruses.values():
                distance = cell.position.distance_to(virus.position)
                
                # Cell hits virus
                if distance < cell.radius + virus.radius:
                    if cell.mass > self.config['virus_split_threshold']:
                        # Split cell into multiple pieces
                        self._virus_split_cell(cell, virus)
        
        # Handle feeding viruses with ejected mass
        ejected_to_remove = []
        for ejected in self.ejected_mass.values():
            for virus in self.viruses.values():
                distance = ejected.position.distance_to(virus.position)
                
                if distance < virus.radius + ejected.radius:
                    # Virus consumes ejected mass and grows
                    virus.mass += ejected.mass
                    ejected_to_remove.append(ejected.id)
                    
                    # If virus gets too big, it splits
                    if virus.mass > 200:
                        self._split_virus(virus)
        
        for ejected_id in ejected_to_remove:
            if ejected_id in self.ejected_mass:
                del self.ejected_mass[ejected_id]
    
    def _virus_split_cell(self, cell: Cell, virus: Virus):
        """Split a large cell when it hits a virus"""
        original_mass = cell.mass
        pieces = min(7, int(original_mass / 20))  # Split into 3-7 pieces
        
        if pieces < 2:
            return
        
        piece_mass = original_mass / pieces
        
        # Update original cell
        cell.mass = piece_mass
        
        # Create additional pieces
        for i in range(pieces - 1):
            new_cell_id = f"cell_{cell.player_id}_{int(time.time() * 1000)}_{i}"
            
            # Random direction for scattered pieces
            angle = random.uniform(0, 2 * math.pi)
            direction = Vector2(math.cos(angle), math.sin(angle))
            scatter_distance = virus.radius + math.sqrt(piece_mass) + random.uniform(20, 50)
            
            new_position = virus.position + direction * scatter_distance
            
            new_cell = Cell(
                id=new_cell_id,
                player_id=cell.player_id,
                position=new_position,
                velocity=direction * 150.0,
                mass=piece_mass,
                color=cell.color,
                merge_cooldown=time.time() + self.config['merge_time']
            )
            
            self.cells[new_cell_id] = new_cell
            self.player_cells[cell.player_id].append(new_cell_id)
        
        logger.info(f"Virus split cell {cell.id} into {pieces} pieces")
    
    def _split_virus(self, virus: Virus):
        """Split a virus that has grown too large"""
        # Create 2-3 smaller viruses
        pieces = random.randint(2, 3)
        piece_mass = virus.mass / pieces
        
        virus.mass = piece_mass
        
        for i in range(pieces - 1):
            new_virus_id = f"virus_{int(time.time() * 1000)}_{i}"
            angle = random.uniform(0, 2 * math.pi)
            direction = Vector2(math.cos(angle), math.sin(angle))
            new_position = virus.position + direction * 50
            
            self.viruses[new_virus_id] = Virus(
                id=new_virus_id,
                position=new_position,
                mass=piece_mass
            )
    
    def _handle_ejected_mass_consumption(self):
        """Handle cells eating ejected mass"""
        ejected_to_remove = []
        
        for cell in self.cells.values():
            for ejected in self.ejected_mass.values():
                distance = cell.position.distance_to(ejected.position)
                
                if distance < cell.radius + ejected.radius:
                    cell.mass += ejected.mass
                    ejected_to_remove.append(ejected.id)
        
        for ejected_id in ejected_to_remove:
            if ejected_id in self.ejected_mass:
                del self.ejected_mass[ejected_id]
    
    def _handle_cell_merging(self):
        """Handle merging of player's own cells"""
        current_time = time.time()
        
        for player_id, cell_ids in self.player_cells.items():
            if len(cell_ids) <= 1:
                continue
            
            cells_to_merge = []
            
            # Check each pair of cells for merging
            for i, cell_id1 in enumerate(cell_ids):
                if cell_id1 not in self.cells:
                    continue
                    
                cell1 = self.cells[cell_id1]
                
                if current_time < cell1.merge_cooldown:
                    continue
                
                for cell_id2 in cell_ids[i+1:]:
                    if cell_id2 not in self.cells:
                        continue
                        
                    cell2 = self.cells[cell_id2]
                    
                    if current_time < cell2.merge_cooldown:
                        continue
                    
                    distance = cell1.position.distance_to(cell2.position)
                    
                    # Cells can merge if they're touching
                    if distance < cell1.radius + cell2.radius:
                        cells_to_merge.append((cell_id1, cell_id2))
            
            # Perform merges
            for cell_id1, cell_id2 in cells_to_merge:
                if cell_id1 in self.cells and cell_id2 in self.cells:
                    cell1 = self.cells[cell_id1]
                    cell2 = self.cells[cell_id2]
                    
                    # Merge into larger cell
                    if cell1.mass >= cell2.mass:
                        cell1.mass += cell2.mass
                        del self.cells[cell_id2]
                        self.player_cells[player_id].remove(cell_id2)
                    else:
                        cell2.mass += cell1.mass
                        del self.cells[cell_id1]
                        self.player_cells[player_id].remove(cell_id1)
    
    def _cleanup_entities(self):
        """Clean up dead players and invalid entities"""
        # Remove players with no cells
        empty_players = []
        for player_id, cell_ids in self.player_cells.items():
            # Remove invalid cell references
            valid_cells = [cid for cid in cell_ids if cid in self.cells]
            self.player_cells[player_id] = valid_cells
            
            if not valid_cells:
                empty_players.append(player_id)
        
        for player_id in empty_players:
            del self.player_cells[player_id]
            logger.info(f"Player {player_id} eliminated - no cells remaining")
    
    def _maintain_food_count(self):
        """Maintain target food count by spawning new food"""
        current_food_count = len(self.food)
        target_count = self.config['food_count']
        
        if current_food_count < target_count:
            spawn_count = min(50, target_count - current_food_count)  # Spawn max 50 per tick
            self._spawn_food(spawn_count)
    
    def remove_player(self, player_id: str):
        """Remove a player from the game"""
        if player_id in self.player_cells:
            # Remove all player's cells
            for cell_id in self.player_cells[player_id]:
                if cell_id in self.cells:
                    del self.cells[cell_id]
            del self.player_cells[player_id]
            logger.info(f"Player {player_id} removed from game")
    
    def get_game_state(self) -> Dict:
        """Get current game state for clients"""
        return {
            'cells': [
                {
                    'id': cell.id,
                    'player_id': cell.player_id,
                    'x': cell.position.x,
                    'y': cell.position.y,
                    'radius': cell.radius,
                    'mass': cell.mass,
                    'color': cell.color
                }
                for cell in self.cells.values()
            ],
            'food': [
                {
                    'id': food.id,
                    'x': food.position.x,
                    'y': food.position.y,
                    'color': food.color,
                    'value': food.value,
                    'radius': food.radius
                }
                for food in self.food.values()
            ],
            'viruses': [
                {
                    'id': virus.id,
                    'x': virus.position.x,
                    'y': virus.position.y,
                    'radius': virus.radius,
                    'color': virus.color
                }
                for virus in self.viruses.values()
            ],
            'ejected_mass': [
                {
                    'id': ejected.id,
                    'x': ejected.position.x,
                    'y': ejected.position.y,
                    'radius': ejected.radius,
                    'color': ejected.color
                }
                for ejected in self.ejected_mass.values()
            ]
        }
    
    def get_player_state(self, player_id: str) -> Optional[Dict]:
        """Get state for a specific player"""
        if player_id not in self.player_cells:
            return None
        
        player_cells = []
        total_mass = 0
        
        for cell_id in self.player_cells[player_id]:
            if cell_id in self.cells:
                cell = self.cells[cell_id]
                player_cells.append({
                    'id': cell.id,
                    'x': cell.position.x,
                    'y': cell.position.y,
                    'radius': cell.radius,
                    'mass': cell.mass,
                    'color': cell.color
                })
                total_mass += cell.mass
        
        return {
            'cells': player_cells,
            'total_mass': total_mass,
            'cell_count': len(player_cells),
            'can_split': len(player_cells) < self.config['max_cells_per_player'] and total_mass >= 20,
            'can_eject': total_mass >= 15
        }