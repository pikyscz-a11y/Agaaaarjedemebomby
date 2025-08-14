import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { gameAPI } from '../services/api';

const GameCanvas = ({ player, setPlayer, gameState, setGameState, gameId }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const [keys, setKeys] = useState({});
  const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());
  const [lastPositionUpdate, setLastPositionUpdate] = useState(Date.now());

  // Game constants
  const CANVAS_WIDTH = 800;
  const CANVAS_HEIGHT = 600;
  const MOVE_SPEED = 4; // Increased base speed
  const MIN_SIZE = 12; // Slightly larger min size
  const FOOD_SIZE = 4; // Slightly larger food
  const POSITION_UPDATE_INTERVAL = 50; // Faster updates for smoother gameplay
  const SMOOTH_FACTOR = 0.15; // Smoothing factor for movement
  const TRAIL_LENGTH = 8; // Trail effect length

  // Calculate player size based on money
  const calculateSize = useCallback((money) => {
    return MIN_SIZE + Math.sqrt(money / 10);
  }, []);

  // Handle keyboard input
  useEffect(() => {
    const handleKeyDown = (e) => {
      setKeys(prev => ({ ...prev, [e.key.toLowerCase()]: true }));
    };

    const handleKeyUp = (e) => {
      setKeys(prev => ({ ...prev, [e.key.toLowerCase()]: false }));
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // Mouse movement for direction
  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const deltaX = mouseX - player.x;
    const deltaY = mouseY - player.y;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    if (distance > 0) {
      setPlayer(prev => ({
        ...prev,
        targetX: mouseX,
        targetY: mouseY,
        direction: { x: deltaX / distance, y: deltaY / distance }
      }));
    }
  }, [player.x, player.y, setPlayer]);

  // Update game state from server
  const updateGameStateFromServer = useCallback(async () => {
    if (!gameId) return;
    
    try {
      const serverGameState = await gameAPI.getGameState(gameId);
      
      setGameState(prev => ({
        ...prev,
        food: serverGameState.food || [],
        otherPlayers: (serverGameState.players || []).filter(p => p.playerId !== player.id),
        powerUps: serverGameState.powerUps || [],
        gameStats: serverGameState.gameStats || {}
      }));
    } catch (error) {
      console.error('Failed to update game state:', error);
    }
  }, [gameId, player.id, setGameState]);

  // Send position update to server
  const sendPositionUpdate = useCallback(async () => {
    if (!gameId || !player.id) return;
    
    try {
      await gameAPI.updatePosition(gameId, player.id, player.x, player.y, player.money);
    } catch (error) {
      console.error('Failed to update position:', error);
    }
  }, [gameId, player.id, player.x, player.y, player.money]);

  // Collision detection
  const checkCollisions = useCallback(async () => {
    const playerSize = calculateSize(player.money);
    let pointsEarned = 0;
    let consumedFoodIds = [];
    let consumedPowerUpIds = [];
    
    // Check food collisions
    gameState.food.forEach(food => {
      const dx = player.x - food.x;
      const dy = player.y - food.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < playerSize + FOOD_SIZE) {
        pointsEarned += food.value;
        consumedFoodIds.push(food.id);
      }
    });

    // Check power-up collisions
    gameState.powerUps.forEach(powerUp => {
      const dx = player.x - powerUp.x;
      const dy = player.y - powerUp.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < playerSize + powerUp.size) {
        pointsEarned += powerUp.value;
        consumedPowerUpIds.push(powerUp.id);
      }
    });

    // Send consumption updates to server
    if (consumedFoodIds.length > 0 && gameId) {
      try {
        await gameAPI.consumeFood(gameId, player.id, consumedFoodIds);
      } catch (error) {
        console.error('Failed to consume food:', error);
      }
    }

    if (consumedPowerUpIds.length > 0 && gameId) {
      try {
        const result = await gameAPI.consumePowerUp(gameId, player.id, consumedPowerUpIds);
        // Handle power-up effects
        if (result.consumedPowerUps) {
          setPlayer(prev => ({
            ...prev,
            powerUps: [...prev.powerUps, ...result.consumedPowerUps.map(p => ({ ...p, duration: 10000 }))]
          }));
        }
      } catch (error) {
        console.error('Failed to consume power-up:', error);
      }
    }

    // Update player stats locally
    if (pointsEarned > 0) {
      setPlayer(prev => ({
        ...prev,
        virtualMoney: prev.virtualMoney + pointsEarned,
        money: prev.money + pointsEarned,
        score: prev.score + pointsEarned
      }));
    }

    // Check other player collisions (eating smaller players)
    gameState.otherPlayers.forEach(otherPlayer => {
      const dx = player.x - otherPlayer.x;
      const dy = player.y - otherPlayer.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const otherSize = calculateSize(otherPlayer.money);
      
      if (distance < playerSize + otherSize) {
        if (playerSize > otherSize * 1.2) {
          // Player eats other player
          const earnedMoney = Math.floor(otherPlayer.money * 0.8);
          setPlayer(prev => ({
            ...prev,
            virtualMoney: prev.virtualMoney + earnedMoney,
            money: prev.money + earnedMoney,
            score: prev.score + earnedMoney,
            kills: prev.kills + 1
          }));
        } else if (otherSize > playerSize * 1.2) {
          // Other player eats player (game over)
          setPlayer(prev => ({
            ...prev,
            isAlive: false
          }));
        }
      }
    });
  }, [player, gameState.food, gameState.otherPlayers, gameState.powerUps, calculateSize, setPlayer, gameId]);

  // Game loop
  const gameLoop = useCallback(() => {
    const now = Date.now();
    const deltaTime = now - lastUpdateTime;
    setLastUpdateTime(now);

    if (!player.isAlive) return;

    // Update player position
    setPlayer(prev => {
      const size = calculateSize(prev.money);
      const speed = Math.max(MOVE_SPEED - size * 0.05, 1);
      
      let newX = prev.x;
      let newY = prev.y;

      if (prev.direction) {
        newX += prev.direction.x * speed;
        newY += prev.direction.y * speed;
      }

      // Boundary checking
      newX = Math.max(size, Math.min(CANVAS_WIDTH - size, newX));
      newY = Math.max(size, Math.min(CANVAS_HEIGHT - size, newY));

      return { ...prev, x: newX, y: newY };
    });

    // Send position update to server periodically
    if (now - lastPositionUpdate > POSITION_UPDATE_INTERVAL) {
      sendPositionUpdate();
      setLastPositionUpdate(now);
    }

    checkCollisions();
  }, [player, calculateSize, setPlayer, checkCollisions, sendPositionUpdate, lastUpdateTime, lastPositionUpdate]);

  // Render function
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Draw grid background
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let x = 0; x <= CANVAS_WIDTH; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, CANVAS_HEIGHT);
      ctx.stroke();
    }
    for (let y = 0; y <= CANVAS_HEIGHT; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(CANVAS_WIDTH, y);
      ctx.stroke();
    }

    // Draw food
    gameState.food.forEach(food => {
      ctx.fillStyle = food.color;
      ctx.beginPath();
      ctx.arc(food.x, food.y, FOOD_SIZE, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Draw power-ups
    gameState.powerUps.forEach(powerUp => {
      ctx.fillStyle = powerUp.color;
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(powerUp.x, powerUp.y, powerUp.size, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    });

    // Draw other players
    gameState.otherPlayers.forEach(otherPlayer => {
      const size = calculateSize(otherPlayer.money);
      ctx.fillStyle = otherPlayer.color;
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(otherPlayer.x, otherPlayer.y, size, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Draw name
      ctx.fillStyle = '#000';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(otherPlayer.name, otherPlayer.x, otherPlayer.y + 4);
    });

    // Draw player
    if (player.isAlive) {
      const size = calculateSize(player.money);
      ctx.fillStyle = player.color;
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(player.x, player.y, size, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Draw player name
      ctx.fillStyle = '#000';
      ctx.font = 'bold 14px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(player.name, player.x, player.y + 4);
    }
  }, [player, gameState, calculateSize]);

  // Animation loop
  useEffect(() => {
    const animate = () => {
      gameLoop();
      render();
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [gameLoop, render]);

  // Update game state from server periodically
  useEffect(() => {
    const interval = setInterval(updateGameStateFromServer, 1000); // Update every second
    return () => clearInterval(interval);
  }, [updateGameStateFromServer]);

  const handleGameOver = async () => {
    // Send final stats to server
    if (gameId && player.id) {
      try {
        await gameAPI.leaveGame(gameId, player.id);
      } catch (error) {
        console.error('Failed to leave game:', error);
      }
    }
    window.location.reload();
  };

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={CANVAS_WIDTH}
        height={CANVAS_HEIGHT}
        onMouseMove={handleMouseMove}
        className="border-2 border-gray-300 rounded-lg cursor-none bg-gradient-to-br from-blue-50 to-purple-50"
        style={{ display: 'block' }}
      />
      
      {!player.isAlive && (
        <div className="absolute inset-0 bg-black bg-opacity-75 flex items-center justify-center rounded-lg">
          <Card className="p-8 text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Game Over!</h2>
            <p className="text-gray-600 mb-4">Final Score: ${player.score}</p>
            <p className="text-gray-600 mb-6">Kills: {player.kills}</p>
            <Button onClick={handleGameOver}>
              Play Again
            </Button>
          </Card>
        </div>
      )}

      <div className="absolute bottom-4 left-4 text-sm text-gray-600 bg-white bg-opacity-90 p-2 rounded">
        <p>Move: Mouse | Online Game Active</p>
      </div>
    </div>
  );
};

export default GameCanvas;