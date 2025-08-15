import React, { useState, useEffect } from 'react';
import './App.css';

// API Service
class ApiService {
  constructor() {
    this.baseUrl = 'http://localhost:8000/api';
    this.token = localStorage.getItem('token');
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async register(data) {
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return response.json();
  }

  async login(data) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (result.access_token) {
      this.token = result.access_token;
      localStorage.setItem('token', this.token);
    }
    return result;
  }

  async getProfile() {
    const response = await fetch(`${this.baseUrl}/user/profile`, {
      headers: this.getHeaders(),
    });
    return response.json();
  }

  async getRooms() {
    const response = await fetch(`${this.baseUrl}/rooms`, {
      headers: this.getHeaders(),
    });
    return response.json();
  }

  async createDepositInvoice(amount_usd) {
    const response = await fetch(`${this.baseUrl}/payments/deposit`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ amount_usd }),
    });
    return response.json();
  }

  async joinRoom(room_id) {
    const response = await fetch(`${this.baseUrl}/rooms/join`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ room_id }),
    });
    return response.json();
  }

  logout() {
    this.token = null;
    localStorage.removeItem('token');
  }
}

const api = new ApiService();

// Components
const AuthForm = ({ mode, onSubmit, onToggleMode }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ username, password });
  };

  return (
    <div className="auth-form">
      <h2>{mode === 'login' ? 'Login' : 'Register'}</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">
          {mode === 'login' ? 'Login' : 'Register'}
        </button>
      </form>
      <p>
        {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
        <button type="button" onClick={onToggleMode}>
          {mode === 'login' ? 'Register' : 'Login'}
        </button>
      </p>
    </div>
  );
};

const Dashboard = ({ user, rooms, onDeposit, onJoinRoom, onLogout }) => {
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Agar.io MVP</h1>
        <div className="user-info">
          <span>Welcome, {user.username}!</span>
          <span>Balance: ${(user.balance / 100).toFixed(2)} USDT</span>
          <button onClick={onDeposit} className="deposit-btn">
            Deposit USDT
          </button>
          <button onClick={onLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <section className="rooms-section">
          <h2>Available Rooms</h2>
          <div className="rooms-grid">
            {rooms.map((room) => (
              <div key={room.id} className="room-card">
                <h3>{room.name}</h3>
                <p>Mode: {room.mode}</p>
                <p>Entry Fee: ${(room.entry_fee / 100).toFixed(2)} USDT</p>
                <p>
                  Players: {room.current_players}/{room.max_players}
                </p>
                <button
                  onClick={() => onJoinRoom(room.id)}
                  disabled={room.current_players >= room.max_players}
                >
                  Join Room
                </button>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

const DepositModal = ({ isOpen, onClose, onDeposit }) => {
  const [amount, setAmount] = useState(10);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Deposit USDT</h2>
        <p>Select amount to deposit:</p>
        <div className="amount-buttons">
          {[10, 25, 50, 100, 200, 500].map((amt) => (
            <button
              key={amt}
              onClick={() => setAmount(amt)}
              className={amount === amt ? 'selected' : ''}
            >
              ${amt}
            </button>
          ))}
        </div>
        <div>
          <label>Custom Amount:</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            min="1"
          />
        </div>
        <div className="modal-actions">
          <button onClick={() => onDeposit(amount)}>Create Invoice</button>
          <button onClick={onClose}>Cancel</button>
        </div>
        <p className="disclaimer">
          This is a demo. Real payments will be processed via NOWPayments.
        </p>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [user, setUser] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      api.getProfile()
        .then((profile) => {
          setUser(profile);
          setIsAuthenticated(true);
          loadRooms();
        })
        .catch(() => {
          // Token invalid, clear it
          api.logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const loadRooms = async () => {
    try {
      const response = await api.getRooms();
      setRooms(response.rooms);
    } catch (error) {
      console.error('Failed to load rooms:', error);
    }
  };

  const handleAuth = async (data) => {
    try {
      let result;
      if (authMode === 'register') {
        await api.register(data);
        result = await api.login(data);
      } else {
        result = await api.login(data);
      }

      if (result.access_token) {
        const profile = await api.getProfile();
        setUser(profile);
        setIsAuthenticated(true);
        loadRooms();
      }
    } catch (error) {
      console.error('Authentication failed:', error);
      alert('Authentication failed. Please try again.');
    }
  };

  const handleDeposit = async (amount) => {
    try {
      const result = await api.createDepositInvoice(amount);
      if (result.invoice_url) {
        window.open(result.invoice_url, '_blank');
      }
      setShowDepositModal(false);
    } catch (error) {
      console.error('Failed to create deposit invoice:', error);
      alert('Failed to create deposit invoice. Please try again.');
    }
  };

  const handleJoinRoom = async (roomId) => {
    try {
      await api.joinRoom(roomId);
      alert('Joined room successfully!');
      // Refresh user profile to update balance
      const profile = await api.getProfile();
      setUser(profile);
    } catch (error) {
      console.error('Failed to join room:', error);
      alert('Failed to join room. Please check your balance.');
    }
  };

  const handleLogout = () => {
    api.logout();
    setIsAuthenticated(false);
    setUser(null);
    setRooms([]);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="App">
      {!isAuthenticated ? (
        <AuthForm
          mode={authMode}
          onSubmit={handleAuth}
          onToggleMode={() =>
            setAuthMode(authMode === 'login' ? 'register' : 'login')
          }
        />
      ) : (
        user && (
          <Dashboard
            user={user}
            rooms={rooms}
            onDeposit={() => setShowDepositModal(true)}
            onJoinRoom={handleJoinRoom}
            onLogout={handleLogout}
          />
        )
      )}

      <DepositModal
        isOpen={showDepositModal}
        onClose={() => setShowDepositModal(false)}
        onDeposit={handleDeposit}
      />
    </div>
  );
}

export default App;