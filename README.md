# Agar.io MVP - Crypto Skills Game

A minimal viable product for an agar.io-style skills game with USDT deposits and withdrawals.

## Features

### Backend (FastAPI + SQLAlchemy)
- User registration and JWT authentication
- Room-based game system with entry fees
- USDT deposits via NOWPayments integration
- Internal balance/ledger system
- Payout requests with minimum withdrawal
- WebSocket support for real-time gameplay

### Frontend (React)
- User authentication (login/register)
- Room listing and joining
- USDT deposit modal with hosted invoices
- Balance management
- Responsive design

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your values:
   - `JWT_SECRET`: A secure secret key for JWT tokens
   - `NOWPAYMENTS_API_KEY`: Your NOWPayments API key
   - `NOWPAYMENTS_IPN_SECRET`: Your NOWPayments IPN secret
   - `PUBLIC_BASE_URL`: Your public URL for webhooks

4. Run the server:
   ```bash
   python main.py
   ```

The backend will start on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend will start on `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### User Profile
- `GET /api/user/profile` - Get current user profile with balance

### Payments
- `POST /api/payments/deposit` - Create USDT deposit invoice
- `POST /api/payments/payout` - Request USDT withdrawal
- `POST /api/payments/ipn` - NOWPayments webhook endpoint

### Rooms
- `GET /api/rooms` - List available rooms
- `POST /api/rooms/join` - Join a room (deducts entry fee)

### WebSocket
- `WS /ws/room/{room_id}` - Real-time room communication

## Game Configuration

The system supports three game modes:

1. **Classic** - Entry fee: $0.10 USDT, Unlimited duration, 20 max players
2. **Fast** - Entry fee: $0.15 USDT, 5 minutes, 15 max players  
3. **Hardcore** - Entry fee: $0.25 USDT, 10 minutes, 10 max players

## Payment Integration

### NOWPayments Setup

1. Sign up at [NOWPayments](https://nowpayments.io/)
2. Get your API key and IPN secret
3. Configure webhook URL: `{YOUR_DOMAIN}/api/payments/ipn`
4. Update environment variables

### USDT Network
- Default network: TRC20 (Tron)
- Minimum withdrawal: 100 USDT (configurable)
- 1 USDT = 100 credits (internal currency)

## Important Notes

⚠️ **This is a skills game, NOT gambling**
- Deposits are for game credits
- Payouts are withdrawals of earned credits
- Players earn through skill-based gameplay
- Clear minimum withdrawal limits are enforced

## Development

### Database
- Uses SQLite for development
- Production should use PostgreSQL
- Auto-creates tables on startup

### Security
- JWT authentication with configurable expiration
- CORS protection
- Input validation on all endpoints
- HMAC signature verification for webhooks

### Testing

Test the API endpoints:
```bash
# Health check
curl http://localhost:8000/api/

# List rooms
curl http://localhost:8000/api/rooms
```

## Deployment

For production:

1. Set up proper environment variables
2. Use a production database (PostgreSQL)
3. Configure reverse proxy (nginx)
4. Set up SSL certificates
5. Configure NOWPayments webhooks
6. Monitor logs and transactions

## License

This project is for demonstration purposes. Ensure compliance with local gambling and financial regulations before deployment.
