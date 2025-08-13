import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { mockData } from '../utils/mock';

const GameCanvas = ({ player, setPlayer, gameState, setGameState }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const [keys, setKeys] = useState({});
  const [powerUps, setPowerUps] = useState([]);
  const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());

  // Game constants
  const CANVAS_WIDTH = 800;
  const CANVAS_HEIGHT = 600;
  const MOVE_SPEED = 3;
  const MIN_SIZE = 10;
  const FOOD_SIZE = 3;

  // Initialize game objects
  useEffect(() => {
    if (gameState.food.length === 0) {
      const initialFood = mockData.generateFood(100, CANVAS_WIDTH, CANVAS_HEIGHT);
      const initialPlayers = mockData.generatePlayers(8, CANVAS_WIDTH, CANVAS_HEIGHT);
      const initialPowerUps = mockData.generatePowerUps(5, CANVAS_WIDTH, CANVAS_HEIGHT);
      
      setGameState(prev => ({
        ...prev,
        food: initialFood,
        otherPlayers: initialPlayers
      }));
      setPowerUps(initialPowerUps);
    }
  }, [gameState.food.length, setGameState]);

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

  // Collision detection
  const checkCollisions = useCallback(() => {
    const playerSize = calculateSize(player.money);
    
    // Check food collisions
    const newFood = gameState.food.filter(food => {
      const dx = player.x - food.x;
      const dy = player.y - food.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < playerSize + FOOD_SIZE) {
        setPlayer(prev => ({
          ...prev,
          virtualMoney: prev.virtualMoney + food.value,
          money: prev.money + food.value,
          score: prev.score + food.value
        }));
        return false;
      }
      return true;
    });

    // Check power-up collisions
    const newPowerUps = powerUps.filter(powerUp => {
      const dx = player.x - powerUp.x;
      const dy = player.y - powerUp.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < playerSize + powerUp.size) {
        // Apply power-up effect
        setPlayer(prev => ({
          ...prev,
          powerUps: [...prev.powerUps, { ...powerUp, duration: 10000 }],
          virtualMoney: prev.virtualMoney + powerUp.value,
          money: prev.money + powerUp.value
        }));
        return false;
      }
      return true;
    });

    // Check other player collisions (eating smaller players)
    const updatedOtherPlayers = gameState.otherPlayers.filter(otherPlayer => {
      const dx = player.x - otherPlayer.x;
      const dy = player.y - otherPlayer.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const otherSize = calculateSize(otherPlayer.money);
      
      if (distance < playerSize + otherSize) {
        if (playerSize > otherSize * 1.2) {
          // Player eats other player
          setPlayer(prev => ({
            ...prev,
            virtualMoney: prev.virtualMoney + Math.floor(otherPlayer.money * 0.8),
            money: prev.money + Math.floor(otherPlayer.money * 0.8),
            score: prev.score + Math.floor(otherPlayer.money * 0.8),
            kills: prev.kills + 1
          }));
          return false;
        } else if (otherSize > playerSize * 1.2) {
          // Other player eats player (game over)
          setPlayer(prev => ({
            ...prev,
            isAlive: false
          }));
        }
      }
      return true;
    });

    if (newFood.length !== gameState.food.length) {
      setGameState(prev => ({ ...prev, food: newFood }));
    }
    
    if (newPowerUps.length !== powerUps.length) {
      setPowerUps(newPowerUps);
    }

    if (updatedOtherPlayers.length !== gameState.otherPlayers.length) {
      setGameState(prev => ({ ...prev, otherPlayers: updatedOtherPlayers }));
    }
  }, [player, gameState.food, gameState.otherPlayers, powerUps, calculateSize, setPlayer, setGameState]);

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

    // Update other players (AI movement)
    setGameState(prev => ({
      ...prev,
      otherPlayers: prev.otherPlayers.map(otherPlayer => {
        const speed = Math.max(MOVE_SPEED - calculateSize(otherPlayer.money) * 0.05, 1);
        let newX = otherPlayer.x + (Math.random() - 0.5) * speed;
        let newY = otherPlayer.y + (Math.random() - 0.5) * speed;

        const size = calculateSize(otherPlayer.money);
        newX = Math.max(size, Math.min(CANVAS_WIDTH - size, newX));
        newY = Math.max(size, Math.min(CANVAS_HEIGHT - size, newY));

        return { ...otherPlayer, x: newX, y: newY };
      })
    }));

    // Add new food periodically
    if (Math.random() < 0.1 && gameState.food.length < 150) {
      const newFood = mockData.generateFood(1, CANVAS_WIDTH, CANVAS_HEIGHT)[0];
      setGameState(prev => ({
        ...prev,
        food: [...prev.food, newFood]
      }));
    }

    checkCollisions();
  }, [player, gameState, calculateSize, setPlayer, setGameState, checkCollisions, lastUpdateTime]);

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
    powerUps.forEach(powerUp => {
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
  }, [player, gameState, powerUps, calculateSize]);

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
            <Button onClick={() => window.location.reload()}>
              Play Again
            </Button>
          </Card>
        </div>
      )}

      <div className="absolute bottom-4 left-4 text-sm text-gray-600 bg-white bg-opacity-90 p-2 rounded">
        <p>Move: Mouse | Boost: Space (coming soon)</p>
      </div>
    </div>
  );
};

export default GameCanvas;