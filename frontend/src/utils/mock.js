// Mock data and utilities for the game

export const mockData = {
  // Generate random food pellets
  generateFood: (count, canvasWidth, canvasHeight) => {
    const food = [];
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b', '#eb4d4b', '#6c5ce7', '#a29bfe', '#fd79a8', '#e84393'];
    
    for (let i = 0; i < count; i++) {
      food.push({
        id: Math.random().toString(36).substr(2, 9),
        x: Math.random() * (canvasWidth - 20) + 10,
        y: Math.random() * (canvasHeight - 20) + 10,
        color: colors[Math.floor(Math.random() * colors.length)],
        value: Math.floor(Math.random() * 5) + 1
      });
    }
    return food;
  },

  // Generate AI players
  generatePlayers: (count, canvasWidth, canvasHeight) => {
    const names = [
      'ProGamer', 'AgarMaster', 'CellDestroyer', 'BlobKing', 'MoneyHunter',
      'SkillzBot', 'MegaCell', 'CoinCollector', 'ElitePlayer', 'ChampionX',
      'CellCrusher', 'AgarLord', 'BlobBeast', 'MoneyMaker', 'TopPlayer'
    ];
    const colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e'];
    
    const players = [];
    for (let i = 0; i < count; i++) {
      players.push({
        id: Math.random().toString(36).substr(2, 9),
        name: names[Math.floor(Math.random() * names.length)] + Math.floor(Math.random() * 100),
        x: Math.random() * (canvasWidth - 100) + 50,
        y: Math.random() * (canvasHeight - 100) + 50,
        money: Math.floor(Math.random() * 500) + 50,
        color: colors[Math.floor(Math.random() * colors.length)],
        isBot: true
      });
    }
    return players;
  },

  // Generate power-ups
  generatePowerUps: (count, canvasWidth, canvasHeight) => {
    const powerUpTypes = [
      { type: 'Speed Boost', color: '#ff9f43', size: 8, value: 20 },
      { type: 'Size Boost', color: '#10ac84', size: 10, value: 50 },
      { type: 'Money Multiplier', color: '#feca57', size: 12, value: 30 },
      { type: 'Shield', color: '#5f27cd', size: 9, value: 40 },
      { type: 'Magnet', color: '#00d2d3', size: 7, value: 25 }
    ];

    const powerUps = [];
    for (let i = 0; i < count; i++) {
      const powerUpType = powerUpTypes[Math.floor(Math.random() * powerUpTypes.length)];
      powerUps.push({
        id: Math.random().toString(36).substr(2, 9),
        x: Math.random() * (canvasWidth - 40) + 20,
        y: Math.random() * (canvasHeight - 40) + 20,
        ...powerUpType
      });
    }
    return powerUps;
  },

  // Get leaderboard data
  getLeaderboard: () => {
    return [
      { name: 'MoneyKing', score: 2847, rank: 1 },
      { name: 'CellMaster', score: 2156, rank: 2 },
      { name: 'BlobLord', score: 1923, rank: 3 },
      { name: 'AgarPro', score: 1756, rank: 4 },
      { name: 'CoinHunter', score: 1543, rank: 5 },
      { name: 'SkillzPlayer', score: 1432, rank: 6 },
      { name: 'EliteGamer', score: 1289, rank: 7 },
      { name: 'MegaBlob', score: 1156, rank: 8 }
    ];
  },

  // Get tournament data
  getTournaments: () => {
    return [
      {
        name: 'Weekly Championship',
        prizePool: 5000,
        players: 142,
        maxPlayers: 256,
        startsIn: '2h 15m',
        entryFee: 50
      },
      {
        name: 'Blitz Tournament',
        prizePool: 1500,
        players: 67,
        maxPlayers: 128,
        startsIn: '45m',
        entryFee: 25
      },
      {
        name: 'Mega Battle Royale',
        prizePool: 10000,
        players: 203,
        maxPlayers: 500,
        startsIn: '6h 30m',
        entryFee: 100
      }
    ];
  },

  // Get recent matches
  getRecentMatches: () => {
    return [
      { winner: 'ProGamer99', mode: 'Classic', prize: 156, timeAgo: '2m ago' },
      { winner: 'CellDestroyer', mode: 'Blitz', prize: 89, timeAgo: '5m ago' },
      { winner: 'MoneyMaster', mode: 'Tournament', prize: 1250, timeAgo: '12m ago' },
      { winner: 'BlobKing', mode: 'Classic', prize: 67, timeAgo: '18m ago' },
      { winner: 'AgarLord', mode: 'Royale', prize: 2100, timeAgo: '25m ago' }
    ];
  },

  // Get player statistics
  getPlayerStats: () => {
    return {
      totalGames: 47,
      wins: 23,
      losses: 24,
      winRate: 48.9,
      totalEarnings: 3456,
      bestScore: 2847,
      averageScore: 892,
      totalKills: 156,
      averageKills: 3.3,
      timePlayedMinutes: 1247
    };
  },

  // Mock payment processing
  processPayment: async (amount, method = 'card') => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Simulate 95% success rate
    if (Math.random() > 0.05) {
      return {
        success: true,
        transactionId: Math.random().toString(36).substr(2, 12).toUpperCase(),
        amount: amount,
        timestamp: new Date().toISOString()
      };
    } else {
      throw new Error('Payment failed. Please try again.');
    }
  },

  // Mock withdrawal processing
  processWithdrawal: async (amount) => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Simulate 90% success rate
    if (Math.random() > 0.1) {
      return {
        success: true,
        withdrawalId: Math.random().toString(36).substr(2, 12).toUpperCase(),
        amount: amount * 0.9, // 10% platform fee
        fee: amount * 0.1,
        estimatedArrival: '2-3 business days',
        timestamp: new Date().toISOString()
      };
    } else {
      throw new Error('Withdrawal failed. Please contact support.');
    }
  }
};