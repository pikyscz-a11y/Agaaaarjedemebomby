#!/usr/bin/env python3
"""
Debug test for critical bug fixes
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://7f3909c1-62d1-4ad8-9c01-1975ec06f459.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

async def debug_api_calls():
    async with aiohttp.ClientSession() as session:
        # Step 1: Register a player
        player_data = {
            "name": "DebugPlayer",
            "email": "debug@example.com"
        }
        async with session.post(f"{API_BASE}/players/register", json=player_data) as response:
            player_response = await response.json()
            print(f"Player registration: {response.status} - {player_response}")
            
        if response.status != 200:
            return
            
        player_id = player_response['id']
        
        # Step 2: Create a game
        game_data = {
            "gameMode": "classic",
            "playerId": player_id
        }
        async with session.post(f"{API_BASE}/games/create", json=game_data) as response:
            game_response = await response.json()
            print(f"Game creation: {response.status} - {game_response}")
            
        if response.status != 200:
            return
            
        game_id = game_response['id']
        
        # Step 3: Get game state
        async with session.get(f"{API_BASE}/games/{game_id}/state") as response:
            state_response = await response.json()
            print(f"Game state: {response.status}")
            print(f"  Players: {len(state_response.get('players', []))}")
            print(f"  Food: {len(state_response.get('food', []))}")
            print(f"  PowerUps: {len(state_response.get('powerUps', []))}")
            
        if response.status != 200:
            return
            
        # Step 4: Test food consumption
        food_items = state_response.get('food', [])[:2]
        if len(food_items) >= 2:
            food_ids = [food['id'] for food in food_items]
            consume_data = {
                "food_ids": food_ids,
                "player_id": player_id
            }
            
            print(f"Attempting food consumption with data: {consume_data}")
            async with session.post(f"{API_BASE}/games/{game_id}/consume-food", json=consume_data) as response:
                consume_response = await response.json()
                print(f"Food consumption: {response.status} - {consume_response}")
        
        # Step 5: Test power-up consumption
        power_ups = state_response.get('powerUps', [])
        if len(power_ups) > 0:
            powerup_data = {
                "power_up_ids": [power_ups[0]['id']],
                "player_id": player_id
            }
            
            print(f"Attempting power-up consumption with data: {powerup_data}")
            async with session.post(f"{API_BASE}/games/{game_id}/consume-powerup", json=powerup_data) as response:
                powerup_response = await response.json()
                print(f"Power-up consumption: {response.status} - {powerup_response}")
        
        # Step 6: Test collision detection
        collision_data = {
            "player_id": player_id
        }
        
        print(f"Attempting collision detection with data: {collision_data}")
        async with session.post(f"{API_BASE}/games/{game_id}/check-collisions", json=collision_data) as response:
            collision_response = await response.json()
            print(f"Collision detection: {response.status} - {collision_response}")

if __name__ == "__main__":
    asyncio.run(debug_api_calls())