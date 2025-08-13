import React, { useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import GameLobby from "./components/GameLobby";
import GameCanvas from "./components/GameCanvas";
import GameUI from "./components/GameUI";
import { Toaster } from "./components/ui/sonner";

function App() {
  const [gameStarted, setGameStarted] = useState(false);
  const [selectedMode, setSelectedMode] = useState('classic');
  
  // Player state
  const [player, setPlayer] = useState({
    id: Math.random().toString(36).substr(2, 9),
    name: "Player",
    x: 400,
    y: 300,
    money: 100,
    virtualMoney: 250,
    realMoney: 50,
    score: 0,
    kills: 0,
    totalGames: 0,
    bestScore: 1250,
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
    isActive: false
  });

  const handleStartGame = (mode) => {
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
      food: [],
      otherPlayers: [],
      powerUps: []
    }));
    setGameStarted(true);
  };

  const handleBackToLobby = () => {
    setGameStarted(false);
    setPlayer(prev => ({
      ...prev,
      totalGames: prev.totalGames + 1,
      bestScore: Math.max(prev.bestScore, prev.score)
    }));
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
                    </div>
                    
                    <GameCanvas 
                      player={player}
                      setPlayer={setPlayer}
                      gameState={gameState}
                      setGameState={setGameState}
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