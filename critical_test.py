#!/usr/bin/env python3
"""
Focused test for critical bug fixes
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://7f3909c1-62d1-4ad8-9c01-1975ec06f459.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

async def test_critical_fixes():
    async with aiohttp.ClientSession() as session:
        print("=== CRITICAL BUG FIXES TESTING ===")
        
        # Step 1: Register a player
        player_data = {
            "name": "CriticalTest",
            "email": "critical@example.com"
        }
        async with session.post(f"{API_BASE}/players/register", json=player_data) as response:
            player_response = await response.json()
            print(f"✅ Player registration: {response.status}")
            
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
            print(f"✅ Game creation: {response.status}")
            
        if response.status != 200:
            return
            
        game_id = game_response['id']
        
        # Step 3: Get initial game state
        async with session.get(f"{API_BASE}/games/{game_id}/state") as response:
            initial_state = await response.json()
            print(f"✅ Initial game state: {response.status}")
            print(f"   Initial food count: {len(initial_state.get('food', []))}")
            print(f"   Initial power-ups: {len(initial_state.get('powerUps', []))}")
            print(f"   Players: {len(initial_state.get('players', []))}")
            
        if response.status != 200:
            return
            
        # Step 4: Test AI Bot Verification
        players = initial_state.get('players', [])
        human_players = [p for p in players if not p['playerId'].startswith('bot_')]
        bot_players = [p for p in players if p['playerId'].startswith('bot_')]
        
        print(f"🤖 AI Bot Verification:")
        print(f"   Human players: {len(human_players)}")
        print(f"   Bot players: {len(bot_players)}")
        print(f"   Expected bots: ~8 for classic mode")
        
        if len(bot_players) >= 6:  # Allow some tolerance
            print(f"   ✅ AI bots are working correctly")
        else:
            print(f"   ❌ AI bots not working as expected")
            
        # Step 5: Test Food Respawn Rate (50% fix)
        food_items = initial_state.get('food', [])[:4]
        if len(food_items) >= 4:
            food_ids = [food['id'] for food in food_items]
            initial_food_count = len(initial_state.get('food', []))
            
            # Try food consumption with correct format
            consume_data = {
                "food_ids": food_ids,
                "player_id": player_id
            }
            
            print(f"🍎 Testing Food Respawn Rate Fix:")
            print(f"   Consuming 4 food items from {initial_food_count} total")
            
            async with session.post(f"{API_BASE}/games/{game_id}/consume-food", json=consume_data) as response:
                if response.status == 200:
                    consume_response = await response.json()
                    print(f"   ✅ Food consumption successful: {consume_response}")
                    
                    # Check food count after consumption
                    async with session.get(f"{API_BASE}/games/{game_id}/state") as response:
                        after_state = await response.json()
                        after_food_count = len(after_state.get('food', []))
                        
                        # With 50% respawn rate: initial - 4 + (4 * 0.5) = initial - 2
                        expected_count = initial_food_count - 2
                        actual_change = initial_food_count - after_food_count
                        
                        print(f"   Food count after consumption: {after_food_count}")
                        print(f"   Expected change: ~2 (50% respawn rate)")
                        print(f"   Actual change: {actual_change}")
                        
                        if abs(actual_change - 2) <= 1:  # Allow tolerance
                            print(f"   ✅ Food respawn rate fix working correctly")
                        else:
                            print(f"   ❌ Food respawn rate fix not working as expected")
                else:
                    error_response = await response.json()
                    print(f"   ❌ Food consumption failed: {response.status} - {error_response}")
        
        # Step 6: Test Power-up Consumption API Fix
        power_ups = initial_state.get('powerUps', [])
        if len(power_ups) > 0:
            powerup_data = {
                "power_up_ids": [power_ups[0]['id']],
                "player_id": player_id
            }
            
            print(f"⚡ Testing Power-up Consumption API Fix:")
            
            async with session.post(f"{API_BASE}/games/{game_id}/consume-powerup", json=powerup_data) as response:
                if response.status == 200:
                    powerup_response = await response.json()
                    print(f"   ✅ Power-up consumption successful: {powerup_response}")
                else:
                    error_response = await response.json()
                    print(f"   ❌ Power-up consumption failed: {response.status} - {error_response}")
        
        # Step 7: Test Player Collision Detection
        collision_data = {
            "player_id": player_id
        }
        
        print(f"💥 Testing Player Collision Detection:")
        
        async with session.post(f"{API_BASE}/games/{game_id}/check-collisions", json=collision_data) as response:
            if response.status == 200:
                collision_response = await response.json()
                print(f"   ✅ Collision detection successful: {collision_response}")
                
                # Check if response has expected keys
                expected_keys = ['kills', 'deaths', 'money_gained', 'is_alive']
                has_keys = all(key in collision_response for key in expected_keys)
                
                if has_keys:
                    print(f"   ✅ Collision response format correct")
                else:
                    print(f"   ❌ Collision response missing expected keys")
            else:
                error_response = await response.json()
                print(f"   ❌ Collision detection failed: {response.status} - {error_response}")
        
        print(f"\n=== CRITICAL BUG FIXES TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_critical_fixes())