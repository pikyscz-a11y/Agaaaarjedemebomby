import React, { useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import GameLobby from "./components/GameLobby";
import GameCanvas from "./components/GameCanvas";
import GameUI from "./components/GameUI";
import { Toaster } from "./components/ui/sonner";
import { gameAPI, playerAPI } from "./services/api";
import { toast } from "./hooks/use-toast";

function App() {
  const [gameStarted, setGameStarted] = useState(false);
  const [selectedMode, setSelectedMode] = useState('classic');
  const [currentGameId, setCurrentGameId] = useState(null);
  
  // Player state
  const [player, setPlayer] = useState({
    id: null,
    name: "",
    x: 400,
    y: 300,
    money: 100,
    virtualMoney: 250,
    realMoney: 0,
    score: 0,
    kills: 0,
    totalGames: 0,
    bestScore: 0,
    wins: 0,
    totalKills: 0,
    isAlive: true,
    color: '#3498db',
    powerUps: [],
    direction: null,
    targetX: 400,
    targetY: 300
  });

  // Game state
  const [gameState, setGameState] = useState({
    food: [],
    otherPlayers: [],
    powerUps: [],
    gameMode: 'classic',
    timeRemaining: 0,
    isActive: false,
    gameStats: {}
  });

  const handleStartGame = async (mode) => {
    if (!player.id) {
      toast({
        title: "Error",
        description: "Player not registered",
        variant: "destructive",
      });
      return;
    }

    try {
      // Create or join game
      const game = await gameAPI.createGame(mode, player.id);
      
      setCurrentGameId(game.id);
      setSelectedMode(mode);
      setPlayer(prev => ({
        ...prev,
        isAlive: true,
        score: 0,
        kills: 0,
        x: 400,
        y: 300,
        powerUps: []
      }));
      
      setGameState(prev => ({
        ...prev,
        gameMode: mode,
        isActive: true,
        food: game.food || [],
        otherPlayers: game.players?.filter(p => p.playerId !== player.id) || [],
        powerUps: game.powerUps || [],
        gameStats: {
          playersOnline: game.players?.length || 1,
          foodItems: game.food?.length || 0,
          gameMode: mode
        }
      }));
      
      setGameStarted(true);
      
      toast({
        title: "Game Started!",
        description: `Joined ${mode} mode game`,
      });
      
    } catch (error) {
      console.error('Failed to start game:', error);
      toast({
        title: "Failed to Start Game",
        description: "Please try again",
        variant: "destructive",
      });
    }
  };

  const handleBackToLobby = async () => {
    try {
      // Update player stats
      if (currentGameId && player.id && (player.score > 0 || player.kills > 0)) {
        await playerAPI.updateStats(player.id, player.score, player.kills, selectedMode);
      }
      
      // Leave current game
      if (currentGameId && player.id) {
        await gameAPI.leaveGame(currentGameId, player.id);
      }
      
      // Reset game state
      setGameStarted(false);
      setCurrentGameId(null);
      setPlayer(prev => ({
        ...prev,
        totalGames: prev.totalGames + 1,
        bestScore: Math.max(prev.bestScore, prev.score),
        isAlive: true,
        score: 0,
        kills: 0,
        x: 400,
        y: 300
      }));
      
      setGameState({
        food: [],
        otherPlayers: [],
        powerUps: [],
        gameMode: 'classic',
        timeRemaining: 0,
        isActive: false,
        gameStats: {}
      });
      
    } catch (error) {
      console.error('Failed to leave game properly:', error);
      // Still go back to lobby even if API calls fail
      setGameStarted(false);
      setCurrentGameId(null);
    }
  };

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={
            gameStarted ? (
              <div className="min-h-screen bg-gradient-to-br from-slate-100 to-blue-50 p-4">
                <div className="flex gap-4 max-w-7xl mx-auto">
                  {/* Game Area */}
                  <div className="flex-1 flex flex-col items-center">
                    <div className="mb-4 flex gap-4">
                      <button 
                        onClick={handleBackToLobby}
                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                      >
                        ← Back to Lobby
                      </button>
                      <div className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium">
                        Mode: {selectedMode.charAt(0).toUpperCase() + selectedMode.slice(1)}
                      </div>
                      <div className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium">
                        Game ID: {currentGameId?.slice(-6)}
                      </div>
                    </div>
                    
                    <GameCanvas 
                      player={player}
                      setPlayer={setPlayer}
                      gameState={gameState}
                      setGameState={setGameState}
                      gameId={currentGameId}
                    />
                  </div>
                  
                  {/* UI Sidebar */}
                  <GameUI 
                    player={player}
                    setPlayer={setPlayer}
                    gameState={gameState}
                  />
                </div>
              </div>
            ) : (
              <GameLobby 
                onStartGame={handleStartGame}
                player={player}
                setPlayer={setPlayer}
              />
            )
          } />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;