# MoneyAgar.io - Production-Grade Agar.io Game

A fully-featured, server-authoritative Agar.io-style multiplayer game with USDT payments, real-time gameplay, and enterprise-level architecture.

## 🎮 Features

### Core Gameplay
- **Server-Authoritative Engine**: Cheat-proof physics simulation at 30 TPS
- **Full Agar.io Mechanics**: Split, eject, merge, viruses, food consumption
- **Multiple Game Modes**: Classic, Fast, Hardcore, Teams with different rules
- **Real-time Multiplayer**: WebSocket-based with delta compression
- **Advanced Physics**: Mass-based speed, collision detection, spatial optimization

### Economy & Payments
- **USDT Integration**: 1:1 credit ratio via NOWPayments (TRC20/ERC20)
- **Payout System**: Admin-approved withdrawals with fee management
- **Shop System**: Skins, power-ups, temporary boosts with rarity tiers
- **Entry Fees**: Configurable per game mode with prize distribution

### User Management
- **JWT Authentication**: Secure login with refresh tokens
- **User Profiles**: Avatar upload, stats tracking, achievements
- **Admin System**: User moderation, ban management, payout approvals
- **Anti-Cheat**: Server-side validation with anomaly detection

### Production Features
- **Docker Deployment**: Multi-container setup with orchestration
- **CI/CD Pipeline**: Automated testing, security scanning, deployment
- **Monitoring**: Prometheus metrics, Grafana dashboards, health checks
- **Security**: Rate limiting, CORS, HMAC webhook validation

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (MongoDB)     │
│   PixiJS        │    │   WebSocket     │    │   Redis Cache   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN/Nginx     │    │   NOWPayments   │    │   Monitoring    │
│   Load Balancer │    │   USDT Gateway  │    │   Prometheus    │
│   SSL/Security  │    │   Webhooks      │    │   Grafana       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)

### Production Deployment

1. **Clone the repository**
```bash
git clone https://github.com/pikyscz-a11y/Agaaaarjedemebomby.git
cd Agaaaarjedemebomby
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your production settings
```

3. **Start the application**
```bash
docker-compose up -d
```

4. **Initialize database**
```bash
docker-compose exec backend python -c "
from database import database
from auth import PasswordHasher
import asyncio
import os

async def init_db():
    await database.connect()
    await database.initialize_shop_items()
    
    # Create admin user
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    admin_hash = PasswordHasher.hash_password(admin_password)
    
    await database.create_admin_user(
        os.getenv('ADMIN_USERNAME', 'admin'),
        admin_hash,
        os.getenv('ADMIN_EMAIL', 'admin@example.com')
    )
    print('Database initialized successfully')

asyncio.run(init_db())
"
```

The application will be available at:
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **Monitoring**: http://localhost:9090 (Prometheus), http://localhost:3001 (Grafana)

## 🔧 Game Mechanics

### Physics Engine
- **Mass-Speed Relationship**: `speed = base_speed * mass^(-0.3)`
- **Cell Radius**: `radius = sqrt(mass)`
- **Consumption Rule**: Larger cell must be 20% bigger to consume smaller
- **Split Mechanics**: Divide mass equally, max 16 cells per player
- **Merge Cooldown**: 15 seconds before cells can merge

### Economy System
- **Credits**: 1 USDT = 1 Credit (fixed rate)
- **Deposit**: Instant via NOWPayments (TRC20/ERC20)
- **Withdrawals**: Min 10 USDT, 2.5% fee, admin approval required
- **Shop**: Skins (5-50 credits), Power-ups (15-30 credits), Premium items (direct USDT)

## 📊 API Reference

See the full API documentation at `/api/docs` when running the server.

## 🔒 Security

The system implements multiple security layers:
- Server-authoritative game engine
- HMAC webhook validation
- JWT authentication with refresh tokens
- Rate limiting and DDoS protection
- Input validation and sanitization

## 📈 Monitoring

Production monitoring includes:
- Prometheus metrics at `/api/metrics`
- Health checks at `/api/health`
- Structured logging with configurable levels
- Performance tracking for game engine

## 🚢 Deployment

Production deployment uses Docker with:
- Multi-stage builds for optimization
- Health checks and restart policies
- Monitoring and logging integration
- SSL termination and security headers

For detailed deployment instructions, see the full documentation above.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
