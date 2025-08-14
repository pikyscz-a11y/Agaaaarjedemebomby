#!/usr/bin/env python3
"""
Simple API test
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://7f3909c1-62d1-4ad8-9c01-1975ec06f459.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

async def simple_test():
    async with aiohttp.ClientSession() as session:
        # Test health check first
        async with session.get(f"{API_BASE}/") as response:
            health_response = await response.json()
            print(f"Health check: {response.status} - {health_response}")
        
        # Test player registration
        player_data = {
            "name": "TestPlayer",
            "email": "test@example.com"
        }
        async with session.post(f"{API_BASE}/players/register", json=player_data) as response:
            if response.status == 200:
                player_response = await response.json()
                print(f"Player registration: {response.status} - Success")
                player_id = player_response['id']
                
                # Test game creation
                game_data = {
                    "gameMode": "classic",
                    "playerId": player_id
                }
                async with session.post(f"{API_BASE}/games/create", json=game_data) as response:
                    if response.status == 200:
                        game_response = await response.json()
                        print(f"Game creation: {response.status} - Success")
                        game_id = game_response['id']
                        
                        # Test game state
                        async with session.get(f"{API_BASE}/games/{game_id}/state") as response:
                            if response.status == 200:
                                state_response = await response.json()
                                print(f"Game state: {response.status} - Success")
                                print(f"  Food items: {len(state_response.get('food', []))}")
                                print(f"  Power-ups: {len(state_response.get('powerUps', []))}")
                                print(f"  Players: {len(state_response.get('players', []))}")
                                
                                # Test food consumption
                                food_items = state_response.get('food', [])[:2]
                                if len(food_items) >= 2:
                                    food_ids = [food['id'] for food in food_items]
                                    consume_data = {
                                        "food_ids": food_ids,
                                        "player_id": player_id
                                    }
                                    
                                    async with session.post(f"{API_BASE}/games/{game_id}/consume-food", json=consume_data) as response:
                                        consume_response = await response.json()
                                        print(f"Food consumption: {response.status} - {consume_response}")
                                        
                                # Test collision detection
                                collision_data = {
                                    "player_id": player_id
                                }
                                
                                async with session.post(f"{API_BASE}/games/{game_id}/check-collisions", json=collision_data) as response:
                                    collision_response = await response.json()
                                    print(f"Collision detection: {response.status} - {collision_response}")
                            else:
                                error_response = await response.json()
                                print(f"Game state error: {response.status} - {error_response}")
                    else:
                        error_response = await response.json()
                        print(f"Game creation error: {response.status} - {error_response}")
            else:
                error_response = await response.json()
                print(f"Player registration error: {response.status} - {error_response}")

if __name__ == "__main__":
    asyncio.run(simple_test())