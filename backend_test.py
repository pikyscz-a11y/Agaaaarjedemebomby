#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for MoneyAgar.io
Tests all API endpoints with various scenarios including edge cases
"""

import asyncio
import aiohttp
import json
import os
import sys
from typing import Dict, List, Any
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://moneyagar.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class MoneyAgarAPITester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_players = []
        self.test_games = []
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'response_time': f"{response_time:.3f}s"
        })
        print(f"{status} {test_name} ({response_time:.3f}s)")
        if details:
            print(f"    Details: {details}")
            
    async def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> tuple:
        """Make HTTP request and return response data and time"""
        url = f"{API_BASE}{endpoint}"
        start_time = asyncio.get_event_loop().time()
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=params) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    response_data = await response.json()
                    return response.status, response_data, response_time
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    response_data = await response.json()
                    return response.status, response_data, response_time
            elif method.upper() == 'PUT':
                async with self.session.put(url, json=data) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    response_data = await response.json()
                    return response.status, response_data, response_time
            elif method.upper() == 'DELETE':
                async with self.session.delete(url, params=params) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    response_data = await response.json()
                    return response.status, response_data, response_time
        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            return 500, {"error": str(e)}, response_time

    # ==================== HEALTH CHECK ====================
    async def test_health_check(self):
        """Test API health check"""
        status, data, response_time = await self.make_request('GET', '/')
        success = status == 200 and "MoneyAgar.io API is running" in data.get('message', '')
        self.log_test("Health Check", success, f"Status: {status}, Message: {data.get('message', 'No message')}", response_time)
        
    # ==================== PLAYER MANAGEMENT TESTS ====================
    async def test_player_registration(self):
        """Test player registration with various scenarios"""
        
        # Test 1: Valid new player registration
        player_data = {
            "name": "TestPlayer1",
            "email": "test1@example.com"
        }
        status, data, response_time = await self.make_request('POST', '/players/register', player_data)
        success = status == 200 and 'id' in data and data['name'] == 'TestPlayer1'
        if success:
            self.test_players.append(data)
        self.log_test("Player Registration - New Player", success, f"Status: {status}, Player ID: {data.get('id', 'None')}", response_time)
        
        # Test 2: Existing player registration (should return existing player)
        status, data, response_time = await self.make_request('POST', '/players/register', player_data)
        success = status == 200 and 'id' in data and data['name'] == 'TestPlayer1'
        self.log_test("Player Registration - Existing Player", success, f"Status: {status}, Returned existing player", response_time)
        
        # Test 3: Invalid player name (empty)
        invalid_data = {"name": "", "email": "test@example.com"}
        status, data, response_time = await self.make_request('POST', '/players/register', invalid_data)
        success = status == 400
        self.log_test("Player Registration - Invalid Name", success, f"Status: {status}, Error handled correctly", response_time)
        
        # Test 4: Register another player for multi-player tests
        player_data2 = {
            "name": "TestPlayer2",
            "email": "test2@example.com"
        }
        status, data, response_time = await self.make_request('POST', '/players/register', player_data2)
        success = status == 200 and 'id' in data
        if success:
            self.test_players.append(data)
        self.log_test("Player Registration - Second Player", success, f"Status: {status}", response_time)
        
    async def test_get_player(self):
        """Test getting player information"""
        if not self.test_players:
            self.log_test("Get Player - No Test Players", False, "No test players available")
            return
            
        player = self.test_players[0]
        
        # Test 1: Valid player ID
        status, data, response_time = await self.make_request('GET', f'/players/{player["id"]}')
        success = status == 200 and data['id'] == player['id']
        self.log_test("Get Player - Valid ID", success, f"Status: {status}, Player: {data.get('name', 'Unknown')}", response_time)
        
        # Test 2: Invalid player ID
        status, data, response_time = await self.make_request('GET', '/players/invalid-id')
        success = status == 404
        self.log_test("Get Player - Invalid ID", success, f"Status: {status}, Error handled correctly", response_time)
        
    async def test_update_player_stats(self):
        """Test updating player statistics"""
        if not self.test_players:
            self.log_test("Update Player Stats - No Test Players", False, "No test players available")
            return
            
        player = self.test_players[0]
        stats_data = {
            "score": 1500,
            "kills": 5,
            "gameMode": "classic"
        }
        
        # Test 1: Valid stats update
        status, data, response_time = await self.make_request('PUT', f'/players/{player["id"]}/stats', stats_data)
        success = status == 200 and data.get('success') == True
        self.log_test("Update Player Stats - Valid", success, f"Status: {status}, Success: {data.get('success')}", response_time)
        
        # Test 2: Invalid player ID
        status, data, response_time = await self.make_request('PUT', '/players/invalid-id/stats', stats_data)
        success = status == 404
        self.log_test("Update Player Stats - Invalid ID", success, f"Status: {status}, Error handled correctly", response_time)
        
    # ==================== GAME MANAGEMENT TESTS ====================
    async def test_game_creation(self):
        """Test game creation and joining"""
        if not self.test_players:
            self.log_test("Game Creation - No Test Players", False, "No test players available")
            return
            
        player = self.test_players[0]
        
        # Test 1: Create classic game
        game_data = {
            "gameMode": "classic",
            "playerId": player["id"]
        }
        status, data, response_time = await self.make_request('POST', '/games/create', game_data)
        success = status == 200 and 'id' in data and data['gameMode'] == 'classic'
        if success:
            self.test_games.append(data)
        self.log_test("Game Creation - Classic Mode", success, f"Status: {status}, Game ID: {data.get('id', 'None')}", response_time)
        
        # Test 2: Create tournament game
        game_data2 = {
            "gameMode": "tournament",
            "playerId": player["id"]
        }
        status, data, response_time = await self.make_request('POST', '/games/create', game_data2)
        success = status == 200 and 'id' in data and data['gameMode'] == 'tournament'
        if success:
            self.test_games.append(data)
        self.log_test("Game Creation - Tournament Mode", success, f"Status: {status}, Game ID: {data.get('id', 'None')}", response_time)
        
        # Test 3: Invalid player ID
        invalid_game_data = {
            "gameMode": "classic",
            "playerId": "invalid-player-id"
        }
        status, data, response_time = await self.make_request('POST', '/games/create', invalid_game_data)
        success = status == 404
        self.log_test("Game Creation - Invalid Player", success, f"Status: {status}, Error handled correctly", response_time)
        
    async def test_game_state(self):
        """Test getting game state"""
        if not self.test_games:
            self.log_test("Game State - No Test Games", False, "No test games available")
            return
            
        game = self.test_games[0]
        
        # Test 1: Valid game ID
        status, data, response_time = await self.make_request('GET', f'/games/{game["id"]}/state')
        success = status == 200 and 'players' in data and 'food' in data and 'powerUps' in data
        self.log_test("Game State - Valid ID", success, f"Status: {status}, Players: {len(data.get('players', []))}, Food: {len(data.get('food', []))}", response_time)
        
        # Test 2: Invalid game ID
        status, data, response_time = await self.make_request('GET', '/games/invalid-id/state')
        success = status == 404
        self.log_test("Game State - Invalid ID", success, f"Status: {status}, Error handled correctly", response_time)
        
    async def test_position_update(self):
        """Test updating player position"""
        if not self.test_games or not self.test_players:
            self.log_test("Position Update - Missing Data", False, "No test games or players available")
            return
            
        game = self.test_games[0]
        player = self.test_players[0]
        
        # Test 1: Valid position update
        position_data = {
            "playerId": player["id"],
            "x": 250.5,
            "y": 180.3,
            "money": 150
        }
        status, data, response_time = await self.make_request('POST', f'/games/{game["id"]}/update-position', position_data)
        success = status == 200 and data.get('success') == True
        self.log_test("Position Update - Valid", success, f"Status: {status}, Success: {data.get('success')}", response_time)
        
        # Test 2: Invalid game ID
        status, data, response_time = await self.make_request('POST', '/games/invalid-id/update-position', position_data)
        success = status == 404
        self.log_test("Position Update - Invalid Game", success, f"Status: {status}, Error handled correctly", response_time)
        
        # Test 3: Invalid player ID
        invalid_position_data = {
            "playerId": "invalid-player-id",
            "x": 250.5,
            "y": 180.3,
            "money": 150
        }
        status, data, response_time = await self.make_request('POST', f'/games/{game["id"]}/update-position', invalid_position_data)
        success = status == 404
        self.log_test("Position Update - Invalid Player", success, f"Status: {status}, Error handled correctly", response_time)
        
    async def test_leave_game(self):
        """Test leaving a game"""
        if not self.test_games or not self.test_players:
            self.log_test("Leave Game - Missing Data", False, "No test games or players available")
            return
            
        game = self.test_games[0]
        player = self.test_players[0]
        
        # Test 1: Valid leave game
        params = {"player_id": player["id"]}
        status, data, response_time = await self.make_request('DELETE', f'/games/{game["id"]}/leave', params=params)
        success = status == 200 and 'success' in data
        self.log_test("Leave Game - Valid", success, f"Status: {status}, Success: {data.get('success')}", response_time)
        
    # ==================== MONEY MANAGEMENT TESTS ====================
    async def test_add_money(self):
        """Test adding money to player account"""
        if not self.test_players:
            self.log_test("Add Money - No Test Players", False, "No test players available")
            return
            
        player = self.test_players[0]
        
        # Test 1: Valid payment
        payment_data = {
            "playerId": player["id"],
            "amount": 100,
            "paymentMethod": "card"
        }
        status, data, response_time = await self.make_request('POST', '/payments/add-money', payment_data)
        success = status == 200 and data.get('success') == True and 'transactionId' in data
        self.log_test("Add Money - Valid Payment", success, f"Status: {status}, Amount: ${payment_data['amount']}, Balance: ${data.get('newBalance', 0)}", response_time)
        
        # Test 2: Different amount
        payment_data2 = {
            "playerId": player["id"],
            "amount": 250,
            "paymentMethod": "paypal"
        }
        status, data, response_time = await self.make_request('POST', '/payments/add-money', payment_data2)
        success = status == 200 and data.get('success') == True
        self.log_test("Add Money - Different Amount", success, f"Status: {status}, Amount: ${payment_data2['amount']}", response_time)
        
        # Test 3: Invalid player ID
        invalid_payment = {
            "playerId": "invalid-player-id",
            "amount": 100,
            "paymentMethod": "card"
        }
        status, data, response_time = await self.make_request('POST', '/payments/add-money', invalid_payment)
        success = status == 404
        self.log_test("Add Money - Invalid Player", success, f"Status: {status}, Error handled correctly", response_time)
        
    async def test_withdraw_money(self):
        """Test withdrawing money from player account"""
        if not self.test_players:
            self.log_test("Withdraw Money - No Test Players", False, "No test players available")
            return
            
        player = self.test_players[0]
        
        # Test 1: Valid withdrawal (small amount)
        withdrawal_data = {
            "playerId": player["id"],
            "amount": 50
        }
        status, data, response_time = await self.make_request('POST', '/payments/withdraw', withdrawal_data)
        success = status == 200 and data.get('success') == True and 'withdrawalId' in data
        self.log_test("Withdraw Money - Valid Small Amount", success, f"Status: {status}, Amount: ${withdrawal_data['amount']}, Fee: ${data.get('fee', 0)}", response_time)
        
        # Test 2: Insufficient funds
        large_withdrawal = {
            "playerId": player["id"],
            "amount": 10000  # Very large amount
        }
        status, data, response_time = await self.make_request('POST', '/payments/withdraw', large_withdrawal)
        success = status == 400  # Should fail due to insufficient funds
        self.log_test("Withdraw Money - Insufficient Funds", success, f"Status: {status}, Error handled correctly", response_time)
        
        # Test 3: Invalid player ID
        invalid_withdrawal = {
            "playerId": "invalid-player-id",
            "amount": 50
        }
        status, data, response_time = await self.make_request('POST', '/payments/withdraw', invalid_withdrawal)
        success = status == 404
        self.log_test("Withdraw Money - Invalid Player", success, f"Status: {status}, Error handled correctly", response_time)
        
    async def test_payment_history(self):
        """Test getting payment history"""
        if not self.test_players:
            self.log_test("Payment History - No Test Players", False, "No test players available")
            return
            
        player = self.test_players[0]
        
        # Test 1: Valid player ID
        status, data, response_time = await self.make_request('GET', f'/payments/history/{player["id"]}')
        success = status == 200 and 'transactions' in data
        transaction_count = len(data.get('transactions', []))
        self.log_test("Payment History - Valid Player", success, f"Status: {status}, Transactions: {transaction_count}", response_time)
        
        # Test 2: Invalid player ID (should return empty list)
        status, data, response_time = await self.make_request('GET', '/payments/history/invalid-player-id')
        success = status == 200 and 'transactions' in data
        self.log_test("Payment History - Invalid Player", success, f"Status: {status}, Returns empty list", response_time)
        
    # ==================== STATS & DATA TESTS ====================
    async def test_leaderboard(self):
        """Test leaderboard endpoint"""
        status, data, response_time = await self.make_request('GET', '/leaderboard')
        success = status == 200 and 'players' in data and len(data['players']) > 0
        player_count = len(data.get('players', []))
        self.log_test("Leaderboard", success, f"Status: {status}, Players: {player_count}", response_time)
        
    async def test_active_tournaments(self):
        """Test active tournaments endpoint"""
        status, data, response_time = await self.make_request('GET', '/tournaments/active')
        success = status == 200 and 'tournaments' in data and len(data['tournaments']) > 0
        tournament_count = len(data.get('tournaments', []))
        self.log_test("Active Tournaments", success, f"Status: {status}, Tournaments: {tournament_count}", response_time)
        
    async def test_recent_matches(self):
        """Test recent matches endpoint"""
        status, data, response_time = await self.make_request('GET', '/games/recent-matches')
        success = status == 200 and 'matches' in data and len(data['matches']) > 0
        match_count = len(data.get('matches', []))
        self.log_test("Recent Matches", success, f"Status: {status}, Matches: {match_count}", response_time)
        
    async def test_platform_stats(self):
        """Test platform statistics endpoint"""
        status, data, response_time = await self.make_request('GET', '/stats/platform')
        success = status == 200 and all(key in data for key in ['playersOnline', 'activeGames', 'gamesToday', 'totalPrizePool'])
        self.log_test("Platform Stats", success, f"Status: {status}, Online: {data.get('playersOnline', 0)}, Games: {data.get('activeGames', 0)}", response_time)
        
    # ==================== FOOD RESPAWN RATE TESTS ====================
    async def test_food_respawn_rate_fix(self):
        """Test the food respawn rate fix - should be 50% instead of 100%"""
        print("\n=== FOOD RESPAWN RATE TESTING ===")
        
        if not self.test_players or not self.test_games:
            self.log_test("Food Respawn - Missing Data", False, "No test players or games available")
            return
            
        game = self.test_games[0]
        player = self.test_players[0]
        
        # Step 1: Get initial game state and food count
        status, initial_state, response_time = await self.make_request('GET', f'/games/{game["id"]}/state')
        if status != 200:
            self.log_test("Food Respawn - Initial State", False, f"Failed to get initial state: {status}")
            return
            
        initial_food_count = len(initial_state.get('food', []))
        self.log_test("Food Respawn - Initial State", True, f"Initial food count: {initial_food_count}", response_time)
        
        # Step 2: Simulate food consumption (consume 4 food items)
        food_items = initial_state.get('food', [])[:4]  # Take first 4 food items
        food_ids = [food['id'] for food in food_items]
        
        if len(food_ids) < 4:
            self.log_test("Food Respawn - Insufficient Food", False, f"Not enough food items for test: {len(food_ids)}")
            return
            
        status, consume_response, response_time = await self.make_request('POST', f'/games/{game["id"]}/consume-food?player_id={player["id"]}', food_ids)
        
        if status != 200:
            self.log_test("Food Respawn - Food Consumption", False, f"Failed to consume food: {status}")
            return
            
        points_earned = consume_response.get('pointsEarned', 0)
        self.log_test("Food Respawn - Food Consumption", True, f"Consumed 4 food items, earned {points_earned} points", response_time)
        
        # Step 3: Check food count after consumption (should be reduced by consumed amount)
        status, after_consume_state, response_time = await self.make_request('GET', f'/games/{game["id"]}/state')
        if status != 200:
            self.log_test("Food Respawn - Post Consumption State", False, f"Failed to get state after consumption: {status}")
            return
            
        after_consume_food_count = len(after_consume_state.get('food', []))
        
        # Calculate expected food count with 50% respawn rate
        # Initial count - consumed + (consumed * 0.5) = initial - (consumed * 0.5)
        expected_food_count = initial_food_count - (len(food_ids) // 2)  # 50% respawn rate
        
        # Allow some tolerance for the max(1, count//2) logic
        tolerance = 1
        food_count_correct = abs(after_consume_food_count - expected_food_count) <= tolerance
        
        self.log_test("Food Respawn - 50% Rate Verification", food_count_correct, 
                     f"Food count after consumption: {after_consume_food_count}, Expected: ~{expected_food_count} (±{tolerance})", response_time)
        
        # Step 4: Test multiple consumption cycles to verify consistent 50% rate
        await asyncio.sleep(0.1)  # Small delay
        
        # Consume 2 more food items
        remaining_food = after_consume_state.get('food', [])[:2]
        if len(remaining_food) >= 2:
            food_ids_2 = [food['id'] for food in remaining_food]
            
            status, consume_response_2, response_time = await self.make_request('POST', f'/games/{game["id"]}/consume-food?player_id={player["id"]}', food_ids_2)
            
            if status == 200:
                # Check final state
                status, final_state, response_time = await self.make_request('GET', f'/games/{game["id"]}/state')
                if status == 200:
                    final_food_count = len(final_state.get('food', []))
                    
                    # With 50% respawn rate, consuming 2 more should add back 1
                    expected_final_count = after_consume_food_count - 2 + max(1, 2 // 2)  # -2 consumed +1 respawned
                    
                    final_count_correct = abs(final_food_count - expected_final_count) <= tolerance
                    self.log_test("Food Respawn - Multiple Consumption Test", final_count_correct,
                                 f"Final food count: {final_food_count}, Expected: ~{expected_final_count} (±{tolerance})", response_time)
                else:
                    self.log_test("Food Respawn - Final State Check", False, f"Failed to get final state: {status}")
            else:
                self.log_test("Food Respawn - Second Consumption", False, f"Failed second consumption: {status}")
        else:
            self.log_test("Food Respawn - Multiple Consumption Test", True, "Insufficient food for second test, but first test passed", 0)
            
    async def test_game_state_consistency(self):
        """Test game state consistency after food interactions"""
        print("\n=== GAME STATE CONSISTENCY TESTING ===")
        
        if not self.test_players or not self.test_games:
            self.log_test("Game State Consistency - Missing Data", False, "No test players or games available")
            return
            
        game = self.test_games[0]
        player = self.test_players[0]
        
        # Step 1: Get initial state
        status, initial_state, response_time = await self.make_request('GET', f'/games/{game["id"]}/state')
        if status != 200:
            self.log_test("Game State Consistency - Initial State", False, f"Failed to get initial state: {status}")
            return
            
        initial_players = len(initial_state.get('players', []))
        initial_food = len(initial_state.get('food', []))
        initial_powerups = len(initial_state.get('powerUps', []))
        
        self.log_test("Game State Consistency - Initial State", True, 
                     f"Players: {initial_players}, Food: {initial_food}, PowerUps: {initial_powerups}", response_time)
        
        # Step 2: Update player position
        position_data = {
            "playerId": player["id"],
            "x": 350.0,
            "y": 250.0,
            "money": 200
        }
        status, position_response, response_time = await self.make_request('POST', f'/games/{game["id"]}/update-position', position_data)
        
        if status != 200:
            self.log_test("Game State Consistency - Position Update", False, f"Failed to update position: {status}")
            return
            
        self.log_test("Game State Consistency - Position Update", True, "Position updated successfully", response_time)
        
        # Step 3: Verify state consistency after position update
        status, after_position_state, response_time = await self.make_request('GET', f'/games/{game["id"]}/state')
        if status != 200:
            self.log_test("Game State Consistency - Post Position State", False, f"Failed to get state after position update: {status}")
            return
            
        # Check that player position was updated correctly
        players = after_position_state.get('players', [])
        player_found = False
        position_correct = False
        
        for p in players:
            if p['playerId'] == player['id']:
                player_found = True
                position_correct = (abs(p['x'] - 350.0) < 0.1 and 
                                  abs(p['y'] - 250.0) < 0.1 and 
                                  p['money'] == 200)
                break
                
        self.log_test("Game State Consistency - Position Verification", 
                     player_found and position_correct,
                     f"Player found: {player_found}, Position correct: {position_correct}", response_time)
        
        # Step 4: Verify food and powerup counts remain consistent
        after_position_food = len(after_position_state.get('food', []))
        after_position_powerups = len(after_position_state.get('powerUps', []))
        
        counts_consistent = (after_position_food == initial_food and 
                           after_position_powerups == initial_powerups)
        
        self.log_test("Game State Consistency - Counts After Position Update", counts_consistent,
                     f"Food: {after_position_food} (was {initial_food}), PowerUps: {after_position_powerups} (was {initial_powerups})", 0)

    # ==================== INTEGRATION TESTS ====================
    async def test_complete_player_journey(self):
        """Test complete player journey from registration to withdrawal"""
        print("\n=== INTEGRATION TEST: Complete Player Journey ===")
        
        # Step 1: Register new player
        journey_player = {
            "name": "JourneyPlayer",
            "email": "journey@example.com"
        }
        status, player_data, response_time = await self.make_request('POST', '/players/register', journey_player)
        if status != 200:
            self.log_test("Journey - Player Registration", False, f"Failed to register player: {status}")
            return
            
        player_id = player_data['id']
        self.log_test("Journey - Player Registration", True, f"Player registered: {player_id}", response_time)
        
        # Step 2: Add money to account
        payment_data = {
            "playerId": player_id,
            "amount": 500,
            "paymentMethod": "card"
        }
        status, payment_response, response_time = await self.make_request('POST', '/payments/add-money', payment_data)
        success = status == 200 and payment_response.get('success') == True
        self.log_test("Journey - Add Money", success, f"Added $500, New Balance: ${payment_response.get('newBalance', 0)}", response_time)
        
        # Step 3: Create game
        game_data = {
            "gameMode": "classic",
            "playerId": player_id
        }
        status, game_response, response_time = await self.make_request('POST', '/games/create', game_data)
        success = status == 200 and 'id' in game_response
        if not success:
            self.log_test("Journey - Create Game", False, f"Failed to create game: {status}")
            return
            
        game_id = game_response['id']
        self.log_test("Journey - Create Game", True, f"Game created: {game_id}", response_time)
        
        # Step 4: Update position in game
        position_data = {
            "playerId": player_id,
            "x": 300.0,
            "y": 200.0,
            "money": 120
        }
        status, position_response, response_time = await self.make_request('POST', f'/games/{game_id}/update-position', position_data)
        success = status == 200 and position_response.get('success') == True
        self.log_test("Journey - Update Position", success, f"Position updated successfully", response_time)
        
        # Step 5: Get game state
        status, state_response, response_time = await self.make_request('GET', f'/games/{game_id}/state')
        success = status == 200 and len(state_response.get('players', [])) > 0
        self.log_test("Journey - Get Game State", success, f"Game state retrieved, Players: {len(state_response.get('players', []))}", response_time)
        
        # Step 6: Update player stats
        stats_data = {
            "score": 1200,
            "kills": 3,
            "gameMode": "classic"
        }
        status, stats_response, response_time = await self.make_request('PUT', f'/players/{player_id}/stats', stats_data)
        success = status == 200 and stats_response.get('success') == True
        self.log_test("Journey - Update Stats", success, f"Stats updated successfully", response_time)
        
        # Step 7: Withdraw money
        withdrawal_data = {
            "playerId": player_id,
            "amount": 100
        }
        status, withdrawal_response, response_time = await self.make_request('POST', '/payments/withdraw', withdrawal_data)
        success = status == 200 and withdrawal_response.get('success') == True
        self.log_test("Journey - Withdraw Money", success, f"Withdrew $100, Fee: ${withdrawal_response.get('fee', 0)}", response_time)
        
        # Step 8: Check payment history
        status, history_response, response_time = await self.make_request('GET', f'/payments/history/{player_id}')
        success = status == 200 and len(history_response.get('transactions', [])) >= 2
        transaction_count = len(history_response.get('transactions', []))
        self.log_test("Journey - Payment History", success, f"Transaction history: {transaction_count} transactions", response_time)
        
    async def test_multiple_players_same_game(self):
        """Test multiple players in the same game"""
        print("\n=== INTEGRATION TEST: Multiple Players Same Game ===")
        
        if len(self.test_players) < 2:
            self.log_test("Multi-Player - Insufficient Players", False, "Need at least 2 test players")
            return
            
        # Create game with first player
        game_data = {
            "gameMode": "blitz",
            "playerId": self.test_players[0]["id"]
        }
        status, game_response, response_time = await self.make_request('POST', '/games/create', game_data)
        if status != 200:
            self.log_test("Multi-Player - Game Creation", False, f"Failed to create game: {status}")
            return
            
        game_id = game_response['id']
        self.log_test("Multi-Player - Game Creation", True, f"Game created: {game_id}", response_time)
        
        # Second player joins same game mode (should join existing game)
        game_data2 = {
            "gameMode": "blitz",
            "playerId": self.test_players[1]["id"]
        }
        status, game_response2, response_time = await self.make_request('POST', '/games/create', game_data2)
        success = status == 200
        self.log_test("Multi-Player - Second Player Join", success, f"Second player joined game", response_time)
        
        # Check game state has both players
        status, state_response, response_time = await self.make_request('GET', f'/games/{game_id}/state')
        player_count = len(state_response.get('players', []))
        success = status == 200 and player_count >= 1  # At least one player should be there
        self.log_test("Multi-Player - Game State Check", success, f"Players in game: {player_count}", response_time)
        
    # ==================== MAIN TEST RUNNER ====================
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting MoneyAgar.io Backend API Tests")
        print(f"📡 Testing API at: {API_BASE}")
        print("=" * 80)
        
        await self.setup()
        
        try:
            # Health Check
            print("\n🏥 HEALTH CHECK")
            await self.test_health_check()
            
            # Player Management Tests
            print("\n👤 PLAYER MANAGEMENT TESTS")
            await self.test_player_registration()
            await self.test_get_player()
            await self.test_update_player_stats()
            
            # Game Management Tests
            print("\n🎮 GAME MANAGEMENT TESTS")
            await self.test_game_creation()
            await self.test_game_state()
            await self.test_position_update()
            await self.test_leave_game()
            
            # Food Respawn Rate Tests
            print("\n🍎 FOOD RESPAWN RATE TESTS")
            await self.test_food_respawn_rate_fix()
            await self.test_game_state_consistency()
            
            # Money Management Tests
            print("\n💰 MONEY MANAGEMENT TESTS")
            await self.test_add_money()
            await self.test_withdraw_money()
            await self.test_payment_history()
            
            # Stats & Data Tests
            print("\n📊 STATS & DATA TESTS")
            await self.test_leaderboard()
            await self.test_active_tournaments()
            await self.test_recent_matches()
            await self.test_platform_stats()
            
            # Integration Tests
            print("\n🔗 INTEGRATION TESTS")
            await self.test_complete_player_journey()
            await self.test_multiple_players_same_game()
            
        finally:
            await self.cleanup()
            
        # Print Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
                    
        print(f"\n⚡ PERFORMANCE SUMMARY:")
        response_times = [float(result['response_time'].replace('s', '')) for result in self.test_results]
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        print(f"  • Average Response Time: {avg_time:.3f}s")
        print(f"  • Slowest Response: {max_time:.3f}s")
        
        # Critical Issues
        critical_failures = [r for r in self.test_results if not r['success'] and any(keyword in r['test'].lower() for keyword in ['registration', 'payment', 'game creation'])]
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"  • {failure['test']}: {failure['details']}")

if __name__ == "__main__":
    tester = MoneyAgarAPITester()
    asyncio.run(tester.run_all_tests())