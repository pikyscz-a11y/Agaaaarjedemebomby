import random
import string
from datetime import datetime, timedelta
from typing import List
from models import LeaderboardEntry, Tournament, RecentMatch

def generate_transaction_id() -> str:
    """Generate a random transaction ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def calculate_platform_fee(amount: int) -> int:
    """Calculate platform fee (10%)"""
    return int(amount * 0.1)

def get_mock_leaderboard() -> List[LeaderboardEntry]:
    """Get mock leaderboard data (will be replaced with real data)"""
    return [
        LeaderboardEntry(name="MoneyKing", score=2847, rank=1),
        LeaderboardEntry(name="CellMaster", score=2156, rank=2),
        LeaderboardEntry(name="BlobLord", score=1923, rank=3),
        LeaderboardEntry(name="AgarPro", score=1756, rank=4),
        LeaderboardEntry(name="CoinHunter", score=1543, rank=5),
        LeaderboardEntry(name="SkillzPlayer", score=1432, rank=6),
        LeaderboardEntry(name="EliteGamer", score=1289, rank=7),
        LeaderboardEntry(name="MegaBlob", score=1156, rank=8)
    ]

def get_mock_tournaments() -> List[Tournament]:
    """Get mock tournament data"""
    return [
        Tournament(
            name="Weekly Championship",
            prizePool=5000,
            players=142,
            maxPlayers=256,
            startsIn="2h 15m",
            entryFee=50
        ),
        Tournament(
            name="Blitz Tournament",
            prizePool=1500,
            players=67,
            maxPlayers=128,
            startsIn="45m",
            entryFee=25
        ),
        Tournament(
            name="Mega Battle Royale",
            prizePool=10000,
            players=203,
            maxPlayers=500,
            startsIn="6h 30m",
            entryFee=100
        )
    ]

def get_mock_recent_matches() -> List[RecentMatch]:
    """Get mock recent matches data"""
    return [
        RecentMatch(winner="ProGamer99", mode="Classic", prize=156, timeAgo="2m ago"),
        RecentMatch(winner="CellDestroyer", mode="Blitz", prize=89, timeAgo="5m ago"),
        RecentMatch(winner="MoneyMaster", mode="Tournament", prize=1250, timeAgo="12m ago"),
        RecentMatch(winner="BlobKing", mode="Classic", prize=67, timeAgo="18m ago"),
        RecentMatch(winner="AgarLord", mode="Royale", prize=2100, timeAgo="25m ago")
    ]

def simulate_payment_processing() -> bool:
    """Simulate payment processing with 95% success rate"""
    return random.random() > 0.05

def simulate_withdrawal_processing() -> bool:
    """Simulate withdrawal processing with 90% success rate"""
    return random.random() > 0.1

def sanitize_player_name(name: str) -> str:
    """Sanitize player name"""
    # Remove special characters and limit length
    sanitized = ''.join(c for c in name if c.isalnum() or c.isspace())
    return sanitized.strip()[:15]

def calculate_player_size(money: int) -> float:
    """Calculate player size based on money"""
    MIN_SIZE = 10
    return MIN_SIZE + (money ** 0.5) / 3.16  # Square root scaling

def is_collision(x1: float, y1: float, size1: float, x2: float, y2: float, size2: float) -> bool:
    """Check if two circles collide"""
    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return distance < (size1 + size2)

def get_time_ago(timestamp: datetime) -> str:
    """Get human-readable time ago string"""
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now"