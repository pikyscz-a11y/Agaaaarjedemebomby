import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Player API
export const playerAPI = {
  register: async (name, email = null) => {
    const response = await apiClient.post('/players/register', { name, email });
    return response.data;
  },

  getPlayer: async (playerId) => {
    const response = await apiClient.get(`/players/${playerId}`);
    return response.data;
  },

  updateStats: async (playerId, score, kills, gameMode) => {
    const response = await apiClient.put(`/players/${playerId}/stats`, {
      score,
      kills,
      gameMode
    });
    return response.data;
  }
};

// Game API
export const gameAPI = {
  createGame: async (gameMode, playerId) => {
    const response = await apiClient.post('/games/create', {
      gameMode,
      playerId
    });
    return response.data;
  },

  getGameState: async (gameId) => {
    const response = await apiClient.get(`/games/${gameId}/state`);
    return response.data;
  },

  updatePosition: async (gameId, playerId, x, y, money) => {
    const response = await apiClient.post(`/games/${gameId}/update-position`, {
      playerId,
      x,
      y,
      money
    });
    return response.data;
  },

  leaveGame: async (gameId, playerId) => {
    const response = await apiClient.delete(`/games/${gameId}/leave`, {
      params: { player_id: playerId }
    });
    return response.data;
  },

  consumeFood: async (gameId, playerId, foodIds) => {
    const response = await apiClient.post(`/games/${gameId}/consume-food`, foodIds, {
      params: { player_id: playerId }
    });
    return response.data;
  },

  consumePowerUp: async (gameId, playerId, powerUpIds) => {
    const response = await apiClient.post(`/games/${gameId}/consume-powerup`, {
      power_up_ids: powerUpIds,
      player_id: playerId
    });
    return response.data;
  }
};

// Payment API
export const paymentAPI = {
  addMoney: async (playerId, amount, paymentMethod = 'card') => {
    const response = await apiClient.post('/payments/add-money', {
      playerId,
      amount,
      paymentMethod
    });
    return response.data;
  },

  withdraw: async (playerId, amount) => {
    const response = await apiClient.post('/payments/withdraw', {
      playerId,
      amount
    });
    return response.data;
  },

  getHistory: async (playerId) => {
    const response = await apiClient.get(`/payments/history/${playerId}`);
    return response.data;
  }
};

// Stats API
export const statsAPI = {
  getLeaderboard: async () => {
    const response = await apiClient.get('/leaderboard');
    return response.data;
  },

  getActiveTournaments: async () => {
    const response = await apiClient.get('/tournaments/active');
    return response.data;
  },

  getRecentMatches: async () => {
    const response = await apiClient.get('/games/recent-matches');
    return response.data;
  },

  getPlatformStats: async () => {
    const response = await apiClient.get('/stats/platform');
    return response.data;
  }
};

// Shop API
export const shopAPI = {
  getItems: async (category = null, currency = null) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (currency) params.append('currency', currency);
    
    const response = await apiClient.get(`/shop/items?${params.toString()}`);
    return response.data;
  },

  purchaseItem: async (playerId, itemId, quantity = 1) => {
    const response = await apiClient.post('/shop/purchase', {
      playerId,
      itemId,
      quantity
    });
    return response.data;
  },

  getInventory: async (playerId) => {
    const response = await apiClient.get(`/shop/inventory/${playerId}`);
    return response.data;
  },

  equipItem: async (playerId, itemId) => {
    const response = await apiClient.post('/shop/equip', null, {
      params: { player_id: playerId, item_id: itemId }
    });
    return response.data;
  }
};

// Error handling interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);