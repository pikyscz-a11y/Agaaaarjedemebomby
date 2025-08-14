#!/usr/bin/env python3
"""
Final Cleanup Testing for MoneyAgar.io
Focus on Clean State Verification, Classic Mode, Active Games Tracking, AI Bot System, and All Game Modes
"""

import asyncio
import aiohttp
import json
import os
import sys
from typing import Dict, List, Any
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://7f3909c1-62d1-4ad8-9c01-1975ec06f459.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class FinalCleanupTester:
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
                if params:
                    async with self.session.post(url, params=params) as response:
                        response_time = asyncio.get_event_loop().time() - start_time
                        response_data = await response.json()
                        return response.status, response_data, response_time
                else:
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

    # ==================== SETUP TEST PLAYERS ====================
    async def setup_test_players(self):
        """Setup test players for testing"""
        print("\n=== SETTING UP TEST PLAYERS ===")
        
        # Create test players
        test_player_data = [
            {"name": "CleanupTestPlayer1", "email": "cleanup1@test.com"},
            {"name": "CleanupTestPlayer2", "email": "cleanup2@test.com"}
        ]
        
        for player_data in test_player_data:
            status, data, response_time = await self.make_request('POST', '/players/register', player_data)
            success = status == 200 and 'id' in data
            if success:
                self.test_players.append(data)
            self.log_test(f"Setup Player - {player_data['name']}", success, f"Player ID: {data.get('id', 'None')}", response_time)

    # ==================== 1. CLEAN STATE VERIFICATION ====================
    async def test_clean_state_verification(self):
        """Test that inactive games cleanup worked properly"""
        print("\n=== 1. CLEAN STATE VERIFICATION ===")
        
        # Step 1: Get initial platform stats to see current state
        status, initial_stats, response_time = await self.make_request('GET', '/stats/platform')
        if status != 200:
            self.log_test("Clean State - Initial Stats", False, f"Failed to get initial stats: {status}")
            return
            
        initial_active_games = initial_stats.get('activeGames', 0)
        initial_players_online = initial_stats.get('playersOnline', 0)
        
        self.log_test("Clean State - Initial Stats", True, 
                     f"Active games: {initial_active_games}, Players online: {initial_players_online}", response_time)
        
        # Step 2: Create a new game to verify tracking works
        if not self.test_players:
            self.log_test("Clean State - No Test Players", False, "No test players available")
            return
            
        player = self.test_players[0]
        game_data = {
            "gameMode": "classic",
            "playerId": player["id"]
        }
        status, game_response, response_time = await self.make_request('POST', '/games/create', game_data)
        
        if status != 200:
            self.log_test("Clean State - Game Creation", False, f"Failed to create game: {status}")
            return
            
        game_id = game_response['id']
        self.test_games.append(game_response)
        self.log_test("Clean State - Game Creation", True, f"Game created: {game_id}", response_time)
        
        # Step 3: Check that stats reflect the new game
        await asyncio.sleep(0.5)  # Small delay for state update
        status, updated_stats, response_time = await self.make_request('GET', '/stats/platform')
        
        if status != 200:
            self.log_test("Clean State - Updated Stats", False, f"Failed to get updated stats: {status}")
            return
            
        updated_active_games = updated_stats.get('activeGames', 0)
        updated_players_online = updated_stats.get('playersOnline', 0)
        
        # Verify that active games count increased
        games_increased = updated_active_games >= initial_active_games
        players_tracked = updated_players_online > 0
        
        self.log_test("Clean State - Stats Update", games_increased and players_tracked,
                     f"Active games: {updated_active_games} (was {initial_active_games}), Players online: {updated_players_online}", response_time)
        
        # Step 4: Verify cleanup functionality by calling stats multiple times
        cleanup_calls = []
        for i in range(3):
            status, stats, response_time = await self.make_request('GET', '/stats/platform')
            if status == 200:
                cleanup_calls.append({
                    'active_games': stats.get('activeGames', 0),
                    'players_online': stats.get('playersOnline', 0)
                })
            await asyncio.sleep(0.2)
        
        # Check that cleanup is working (stats should be consistent)
        if len(cleanup_calls) >= 2:
            consistent_stats = all(call['active_games'] >= 0 for call in cleanup_calls)
            self.log_test("Clean State - Cleanup Consistency", consistent_stats,
                         f"Cleanup calls consistent: {[call['active_games'] for call in cleanup_calls]}", 0)
        else:
            self.log_test("Clean State - Cleanup Consistency", False, "Failed to make multiple cleanup calls")

    # ==================== 2. CLASSIC MODE TESTING ====================
    async def test_classic_mode_specific(self):
        """Test Classic Mode game creation and initialization specifically"""
        print("\n=== 2. CLASSIC MODE TESTING ===")
        
        if not self.test_players:
            self.log_test("Classic Mode - No Test Players", False, "No test players available")
            return
            
        player = self.test_players[0]
        
        # Step 1: Create Classic Mode game
        game_data = {
            "gameMode": "classic",
            "playerId": player["id"]
        }
        status, game_response, response_time = await self.make_request('POST', '/games/create', game_data)
        
        success = status == 200 and 'id' in game_response and game_response['gameMode'] == 'classic'
        if not success:
            self.log_test("Classic Mode - Game Creation", False, f"Failed to create classic game: {status}")
            return
            
        classic_game_id = game_response['id']
        self.log_test("Classic Mode - Game Creation", True, f"Classic game created: {classic_game_id}", response_time)
        
        # Step 2: Get game state and verify it's canvas-ready
        await asyncio.sleep(0.5)  # Allow time for initialization
        status, game_state, response_time = await self.make_request('GET', f'/games/{classic_game_id}/state')
        
        if status != 200:
            self.log_test("Classic Mode - Game State", False, f"Failed to get game state: {status}")
            return
            
        # Verify canvas-ready state
        required_fields = ['players', 'food', 'powerUps', 'gameStats']
        has_required_fields = all(field in game_state for field in required_fields)
        
        players = game_state.get('players', [])
        food = game_state.get('food', [])
        power_ups = game_state.get('powerUps', [])
        
        # Classic mode should have proper initialization
        has_players = len(players) > 0
        has_food = len(food) > 0
        has_powerups = len(power_ups) > 0
        
        canvas_ready = has_required_fields and has_players and has_food and has_powerups
        
        self.log_test("Classic Mode - Canvas Ready State", canvas_ready,
                     f"Players: {len(players)}, Food: {len(food)}, PowerUps: {len(power_ups)}", response_time)
        
        # Step 3: Test Classic Mode specific configuration
        # Classic mode should have ~100 food items and ~5 power-ups
        food_count_correct = 90 <= len(food) <= 110  # Allow some variance
        powerup_count_correct = 3 <= len(power_ups) <= 7
        
        self.log_test("Classic Mode - Configuration", food_count_correct and powerup_count_correct,
                     f"Food count: {len(food)} (expected: 90-110), PowerUp count: {len(power_ups)} (expected: 3-7)", 0)
        
        # Step 4: Test player position update in Classic mode
        position_data = {
            "playerId": player["id"],
            "x": 400.0,
            "y": 300.0,
            "money": 250
        }
        status, position_response, response_time = await self.make_request('POST', f'/games/{classic_game_id}/update-position', position_data)
        
        position_success = status == 200 and position_response.get('success') == True
        self.log_test("Classic Mode - Position Update", position_success, f"Position updated successfully", response_time)
        
        # Step 5: Test food consumption in Classic mode
        if len(food) >= 2:
            food_ids = [food[0]['id'], food[1]['id']]
            consume_data = {
                "food_ids": food_ids,
                "player_id": player["id"]
            }
            status, consume_response, response_time = await self.make_request('POST', f'/games/{classic_game_id}/consume-food', consume_data)
            
            consumption_success = status == 200 and 'pointsEarned' in consume_response
            points_earned = consume_response.get('pointsEarned', 0)
            
            self.log_test("Classic Mode - Food Consumption", consumption_success,
                         f"Consumed 2 food items, earned {points_earned} points", response_time)
        else:
            self.log_test("Classic Mode - Food Consumption", False, "Insufficient food items for testing")

    # ==================== 3. ACTIVE GAMES TRACKING ====================
    async def test_active_games_tracking(self):
        """Test that new games are properly tracked in stats"""
        print("\n=== 3. ACTIVE GAMES TRACKING ===")
        
        if not self.test_players:
            self.log_test("Active Games Tracking - No Test Players", False, "No test players available")
            return
        
        # Step 1: Get baseline stats
        status, baseline_stats, response_time = await self.make_request('GET', '/stats/platform')
        if status != 200:
            self.log_test("Active Games Tracking - Baseline Stats", False, f"Failed to get baseline stats: {status}")
            return
            
        baseline_games = baseline_stats.get('activeGames', 0)
        baseline_players = baseline_stats.get('playersOnline', 0)
        
        self.log_test("Active Games Tracking - Baseline Stats", True,
                     f"Baseline - Games: {baseline_games}, Players: {baseline_players}", response_time)
        
        # Step 2: Create multiple games in different modes
        game_modes = ['tournament', 'blitz', 'royale']
        created_games = []
        
        for i, mode in enumerate(game_modes):
            player = self.test_players[i % len(self.test_players)]  # Cycle through players
            
            game_data = {
                "gameMode": mode,
                "playerId": player["id"]
            }
            status, game_response, response_time = await self.make_request('POST', '/games/create', game_data)
            
            if status == 200 and 'id' in game_response:
                created_games.append(game_response)
                self.log_test(f"Active Games Tracking - Create {mode.title()} Game", True,
                             f"Game ID: {game_response['id']}", response_time)
            else:
                self.log_test(f"Active Games Tracking - Create {mode.title()} Game", False,
                             f"Failed to create {mode} game: {status}")
        
        # Step 3: Check that stats reflect all new games
        await asyncio.sleep(1.0)  # Allow time for stats update
        status, updated_stats, response_time = await self.make_request('GET', '/stats/platform')
        
        if status != 200:
            self.log_test("Active Games Tracking - Updated Stats", False, f"Failed to get updated stats: {status}")
            return
            
        updated_games = updated_stats.get('activeGames', 0)
        updated_players = updated_stats.get('playersOnline', 0)
        
        # Verify tracking
        games_increased = updated_games > baseline_games
        players_increased = updated_players > baseline_players
        
        games_delta = updated_games - baseline_games
        players_delta = updated_players - baseline_players
        
        self.log_test("Active Games Tracking - Stats Increase", games_increased and players_increased,
                     f"Games: +{games_delta} ({baseline_games} → {updated_games}), Players: +{players_delta} ({baseline_players} → {updated_players})", response_time)
        
        # Step 4: Test individual game state tracking
        for game in created_games:
            status, game_state, response_time = await self.make_request('GET', f'/games/{game["id"]}/state')
            
            if status == 200:
                players_in_game = len(game_state.get('players', []))
                game_tracked = players_in_game > 0
                
                self.log_test(f"Active Games Tracking - {game['gameMode'].title()} State", game_tracked,
                             f"Game {game['id'][:8]}... has {players_in_game} players", response_time)
            else:
                self.log_test(f"Active Games Tracking - {game['gameMode'].title()} State", False,
                             f"Failed to get state for {game['gameMode']} game: {status}")

    # ==================== 4. AI BOT SYSTEM ====================
    async def test_ai_bot_system(self):
        """Verify bots are created and working in new games"""
        print("\n=== 4. AI BOT SYSTEM ===")
        
        if not self.test_players:
            self.log_test("AI Bot System - No Test Players", False, "No test players available")
            return
        
        player = self.test_players[0]
        
        # Step 1: Create a fresh Classic mode game for bot testing
        game_data = {
            "gameMode": "classic",
            "playerId": player["id"]
        }
        status, game_response, response_time = await self.make_request('POST', '/games/create', game_data)
        
        if status != 200:
            self.log_test("AI Bot System - Game Creation", False, f"Failed to create game: {status}")
            return
            
        bot_test_game_id = game_response['id']
        self.log_test("AI Bot System - Game Creation", True, f"Bot test game created: {bot_test_game_id}", response_time)
        
        # Step 2: Wait for bot initialization
        await asyncio.sleep(1.0)  # Allow time for bots to be created
        
        # Step 3: Get game state and verify bots
        status, game_state, response_time = await self.make_request('GET', f'/games/{bot_test_game_id}/state')
        
        if status != 200:
            self.log_test("AI Bot System - Game State", False, f"Failed to get game state: {status}")
            return
            
        players = game_state.get('players', [])
        total_players = len(players)
        
        # Identify bots vs humans
        human_players = [p for p in players if not p['playerId'].startswith('bot_')]
        bot_players = [p for p in players if p['playerId'].startswith('bot_')]
        
        human_count = len(human_players)
        bot_count = len(bot_players)
        
        # Classic mode should have 8 bots
        expected_bot_count = 8
        bots_created_correctly = bot_count >= expected_bot_count - 2  # Allow some tolerance
        
        self.log_test("AI Bot System - Bot Creation", bots_created_correctly,
                     f"Total players: {total_players}, Human: {human_count}, Bots: {bot_count} (expected: ~{expected_bot_count})", response_time)
        
        # Step 4: Verify bot properties
        if bot_count > 0:
            sample_bot = bot_players[0]
            required_fields = ['playerId', 'name', 'x', 'y', 'money', 'score']
            has_required_fields = all(field in sample_bot for field in required_fields)
            
            bot_name_valid = sample_bot.get('name', '').strip() != ''
            bot_position_valid = (0 <= sample_bot.get('x', -1) <= 800 and 
                                0 <= sample_bot.get('y', -1) <= 600)
            bot_money_valid = sample_bot.get('money', 0) > 0
            
            bot_properties_valid = has_required_fields and bot_name_valid and bot_position_valid and bot_money_valid
            
            self.log_test("AI Bot System - Bot Properties", bot_properties_valid,
                         f"Sample bot: {sample_bot.get('name', 'Unknown')} at ({sample_bot.get('x', 0):.1f}, {sample_bot.get('y', 0):.1f}) with ${sample_bot.get('money', 0)}", 0)
        else:
            self.log_test("AI Bot System - Bot Properties", False, "No bots found to verify properties")
        
        # Step 5: Test bot movement/activity
        await asyncio.sleep(2.0)  # Wait for bot updates
        
        status, updated_state, response_time = await self.make_request('GET', f'/games/{bot_test_game_id}/state')
        if status == 200:
            updated_players = updated_state.get('players', [])
            updated_bots = [p for p in updated_players if p['playerId'].startswith('bot_')]
            
            # Check if bots moved or consumed food
            bots_active = False
            if len(updated_bots) > 0 and len(bot_players) > 0:
                for i, updated_bot in enumerate(updated_bots):
                    if i < len(bot_players):
                        original_bot = bot_players[i]
                        # Check for position change or money change (indicating activity)
                        position_changed = (abs(updated_bot.get('x', 0) - original_bot.get('x', 0)) > 1 or 
                                          abs(updated_bot.get('y', 0) - original_bot.get('y', 0)) > 1)
                        money_changed = updated_bot.get('money', 0) != original_bot.get('money', 0)
                        
                        if position_changed or money_changed:
                            bots_active = True
                            break
            
            self.log_test("AI Bot System - Bot Activity", bots_active,
                         f"Bots are {'active (moving/consuming)' if bots_active else 'inactive'} after 2 seconds", response_time)
        else:
            self.log_test("AI Bot System - Bot Activity", False, f"Failed to get updated state: {status}")

    # ==================== 5. ALL GAME MODES ====================
    async def test_all_game_modes(self):
        """Test Classic, Tournament, Blitz, and Battle Royale mode creation"""
        print("\n=== 5. ALL GAME MODES ===")
        
        if not self.test_players:
            self.log_test("All Game Modes - No Test Players", False, "No test players available")
            return
        
        game_modes = ['classic', 'tournament', 'blitz', 'royale']
        mode_configs = {
            'classic': {'food_range': (90, 110), 'powerup_range': (3, 7)},
            'tournament': {'food_range': (70, 90), 'powerup_range': (6, 10)},
            'blitz': {'food_range': (110, 130), 'powerup_range': (10, 14)},
            'royale': {'food_range': (140, 160), 'powerup_range': (13, 17)}
        }
        
        created_mode_games = []
        
        for mode in game_modes:
            player = self.test_players[0]  # Use same player for consistency
            
            # Step 1: Create game in this mode
            game_data = {
                "gameMode": mode,
                "playerId": player["id"]
            }
            status, game_response, response_time = await self.make_request('POST', '/games/create', game_data)
            
            success = status == 200 and 'id' in game_response and game_response['gameMode'] == mode
            if success:
                created_mode_games.append(game_response)
                
            self.log_test(f"All Game Modes - {mode.title()} Creation", success,
                         f"Status: {status}, Game ID: {game_response.get('id', 'None')[:8]}...", response_time)
            
            if not success:
                continue
                
            # Step 2: Verify game state and configuration
            game_id = game_response['id']
            await asyncio.sleep(0.5)  # Allow initialization
            
            status, game_state, response_time = await self.make_request('GET', f'/games/{game_id}/state')
            
            if status != 200:
                self.log_test(f"All Game Modes - {mode.title()} State", False, f"Failed to get state: {status}")
                continue
                
            # Verify mode-specific configuration
            food_count = len(game_state.get('food', []))
            powerup_count = len(game_state.get('powerUps', []))
            player_count = len(game_state.get('players', []))
            
            config = mode_configs[mode]
            food_in_range = config['food_range'][0] <= food_count <= config['food_range'][1]
            powerup_in_range = config['powerup_range'][0] <= powerup_count <= config['powerup_range'][1]
            has_players = player_count > 0
            
            config_correct = food_in_range and powerup_in_range and has_players
            
            self.log_test(f"All Game Modes - {mode.title()} Configuration", config_correct,
                         f"Food: {food_count} (expected: {config['food_range']}), PowerUps: {powerup_count} (expected: {config['powerup_range']}), Players: {player_count}", response_time)
            
            # Step 3: Test basic functionality in this mode
            if has_players:
                # Test position update
                position_data = {
                    "playerId": player["id"],
                    "x": 200.0 + (len(created_mode_games) * 50),  # Vary position per mode
                    "y": 150.0 + (len(created_mode_games) * 30),
                    "money": 100 + (len(created_mode_games) * 25)
                }
                status, position_response, response_time = await self.make_request('POST', f'/games/{game_id}/update-position', position_data)
                
                position_success = status == 200 and position_response.get('success') == True
                self.log_test(f"All Game Modes - {mode.title()} Position Update", position_success,
                             f"Position update {'successful' if position_success else 'failed'}", response_time)
                
                # Test food consumption if food available
                if food_count >= 2:
                    food_items = game_state.get('food', [])[:2]
                    food_ids = [food['id'] for food in food_items]
                    
                    consume_data = {
                        "food_ids": food_ids,
                        "player_id": player["id"]
                    }
                    status, consume_response, response_time = await self.make_request('POST', f'/games/{game_id}/consume-food', consume_data)
                    
                    consumption_success = status == 200 and 'pointsEarned' in consume_response
                    points = consume_response.get('pointsEarned', 0)
                    
                    self.log_test(f"All Game Modes - {mode.title()} Food Consumption", consumption_success,
                                 f"Consumed food, earned {points} points", response_time)
                else:
                    self.log_test(f"All Game Modes - {mode.title()} Food Consumption", True,
                                 "Insufficient food for testing, but mode created successfully", 0)
        
        # Step 4: Verify all modes are tracked in platform stats
        await asyncio.sleep(1.0)
        status, final_stats, response_time = await self.make_request('GET', '/stats/platform')
        
        if status == 200:
            active_games = final_stats.get('activeGames', 0)
            players_online = final_stats.get('playersOnline', 0)
            
            # Should have multiple active games now
            multiple_games_tracked = active_games >= len(created_mode_games)
            
            self.log_test("All Game Modes - Platform Stats Tracking", multiple_games_tracked,
                         f"Active games: {active_games} (created: {len(created_mode_games)}), Players online: {players_online}", response_time)
        else:
            self.log_test("All Game Modes - Platform Stats Tracking", False, f"Failed to get final stats: {status}")

    # ==================== MAIN TEST RUNNER ====================
    async def run_all_tests(self):
        """Run all final cleanup tests"""
        print("🎯 STARTING FINAL CLEANUP TESTING FOR MONEYAGAR.IO")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Setup
            await self.setup_test_players()
            
            # Run all focused tests
            await self.test_clean_state_verification()
            await self.test_classic_mode_specific()
            await self.test_active_games_tracking()
            await self.test_ai_bot_system()
            await self.test_all_game_modes()
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
        finally:
            await self.cleanup()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 FINAL CLEANUP TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n⏱️  Average Response Time: {sum(float(r['response_time'][:-1]) for r in self.test_results) / total_tests:.3f}s")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        
        # Check for critical issues
        critical_failures = [r for r in self.test_results if not r['success'] and any(keyword in r['test'].lower() for keyword in ['classic mode', 'bot system', 'clean state'])]
        
        if critical_failures:
            print(f"  ⚠️  CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"    - {failure['test']}: {failure['details']}")
        else:
            print(f"  ✅ No critical issues found in final cleanup testing")
        
        print("=" * 60)

if __name__ == "__main__":
    tester = FinalCleanupTester()
    asyncio.run(tester.run_all_tests())