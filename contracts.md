# MoneyAgar.io - Backend Integration Contracts

## API Contracts

### 1. Player Management
```
POST /api/players/register
- Input: { name: string, email?: string }
- Output: { id, name, virtualMoney: 250, realMoney: 0, totalGames: 0, bestScore: 0 }

GET /api/players/{playerId}
- Output: Player profile with stats

PUT /api/players/{playerId}/stats
- Input: { score: number, kills: number, gameMode: string }
- Output: Updated player stats
```

### 2. Game Management
```
POST /api/games/create
- Input: { gameMode: string, playerId: string }
- Output: { gameId, gameState, otherPlayers }

GET /api/games/{gameId}/state
- Output: { food, otherPlayers, powerUps, gameStats }

POST /api/games/{gameId}/update-position
- Input: { playerId: string, x: number, y: number, money: number }
- Output: { success: boolean }

DELETE /api/games/{gameId}/leave
- Input: { playerId: string }
```

### 3. Money Management
```
POST /api/payments/add-money
- Input: { playerId: string, amount: number, paymentMethod: string }
- Output: { success: boolean, transactionId: string, newBalance: number }

POST /api/payments/withdraw
- Input: { playerId: string, amount: number }
- Output: { success: boolean, withdrawalId: string, fee: number }

GET /api/payments/history/{playerId}
- Output: { transactions: [] }
```

### 4. Leaderboard & Stats
```
GET /api/leaderboard
- Output: { players: [{ name, score, rank }] }

GET /api/tournaments/active
- Output: { tournaments: [] }

GET /api/games/recent-matches
- Output: { matches: [] }
```

## Mock Data Replacement Plan

### Current Mock Data (to replace):
1. **mockData.generateFood()** → Real-time food generation in game state
2. **mockData.generatePlayers()** → Real connected players from database
3. **mockData.generatePowerUps()** → Server-managed power-ups
4. **mockData.getLeaderboard()** → Real player rankings from database
5. **mockData.getTournaments()** → Real tournament data
6. **mockData.processPayment()** → Real payment processing (mock for demo)

## Database Models

### Players Collection
```javascript
{
  _id: ObjectId,
  name: String,
  email: String (optional),
  virtualMoney: Number (default: 250),
  realMoney: Number (default: 0),
  totalGames: Number (default: 0),
  wins: Number (default: 0),
  totalKills: Number (default: 0),
  bestScore: Number (default: 0),
  createdAt: Date,
  isOnline: Boolean
}
```

### Games Collection
```javascript
{
  _id: ObjectId,
  gameMode: String,
  players: [{ playerId, x, y, money, score, kills, isAlive }],
  food: [{ x, y, color, value }],
  powerUps: [{ x, y, type, color, size, value }],
  startTime: Date,
  isActive: Boolean,
  maxPlayers: Number
}
```

### Transactions Collection
```javascript
{
  _id: ObjectId,
  playerId: ObjectId,
  type: String, // 'deposit', 'withdrawal', 'game_earning'
  amount: Number,
  status: String, // 'pending', 'completed', 'failed'
  transactionId: String,
  timestamp: Date
}
```

## Frontend-Backend Integration

### 1. Replace Mock Imports
- Remove all `mockData` imports from components
- Add axios API calls to backend endpoints

### 2. Real-time Updates
- Implement WebSocket connections for real-time game state
- Update player positions and game state every 100ms
- Handle player disconnections gracefully

### 3. Error Handling
- Add try-catch blocks for all API calls
- Show user-friendly error messages
- Handle network failures and retries

### 4. State Management
- Replace mock state with real API data
- Implement proper loading states
- Add optimistic updates for better UX

## Implementation Priority

### Phase 1: Core Backend (Essential)
1. Player registration and management
2. Basic game state management
3. Money transaction endpoints
4. Database models and connections

### Phase 2: Real-time Features
1. Game state synchronization
2. Real-time player updates
3. Food and power-up management
4. Collision detection on server

### Phase 3: Advanced Features
1. Tournament system
2. Leaderboard calculations
3. Payment processing (mock)
4. Game analytics and stats

## Testing Strategy
- Test each API endpoint individually
- Verify real-time game synchronization
- Test payment flows (with mock data)
- Ensure proper error handling
- Test multiplayer scenarios

## Security Considerations
- Input validation on all endpoints
- Rate limiting for API calls
- Sanitize player names and data
- Secure payment processing (demo mode)