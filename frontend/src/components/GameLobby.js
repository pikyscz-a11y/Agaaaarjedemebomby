import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback } from './ui/avatar';
import { 
  Play, 
  Trophy, 
  Users, 
  Clock, 
  DollarSign, 
  Zap,
  Crown,
  Target,
  Timer,
  ShoppingBag
} from 'lucide-react';
import { playerAPI, statsAPI } from '../services/api';
import { toast } from '../hooks/use-toast';
import Shop from './Shop';
import PaymentModal from './PaymentModal';

const GameLobby = ({ onStartGame, player, setPlayer }) => {
  const [playerName, setPlayerName] = useState(player.name || '');
  const [selectedMode, setSelectedMode] = useState('classic');
  const [isRegistering, setIsRegistering] = useState(false);
  const [tournaments, setTournaments] = useState([]);
  const [recentMatches, setRecentMatches] = useState([]);
  const [platformStats, setPlatformStats] = useState({});
  const [showShop, setShowShop] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  
  const gameModes = [
    {
      id: 'classic',
      name: 'Classic Mode',
      description: 'Traditional Agar.io gameplay with money mechanics',
      minBet: 10,
      maxPlayers: 20,
      icon: Play,
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      id: 'tournament',
      name: 'Tournament',
      description: 'Competitive bracket-style elimination',
      minBet: 50,
      maxPlayers: 16,
      icon: Trophy,
      gradient: 'from-yellow-500 to-orange-500'
    },
    {
      id: 'blitz',
      name: 'Blitz Mode',
      description: 'Fast-paced 5-minute rounds',
      minBet: 25,
      maxPlayers: 12,
      icon: Zap,
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      id: 'royale',
      name: 'Battle Royale',
      description: 'Shrinking arena, last player standing wins',
      minBet: 100,
      maxPlayers: 50,
      icon: Crown,
      gradient: 'from-red-500 to-rose-500'
    }
  ];

  // Load lobby data
  useEffect(() => {
    const loadLobbyData = async () => {
      try {
        const [tournamentsData, matchesData, statsData] = await Promise.all([
          statsAPI.getActiveTournaments(),
          statsAPI.getRecentMatches(),
          statsAPI.getPlatformStats()
        ]);
        
        setTournaments(tournamentsData.tournaments || []);
        setRecentMatches(matchesData.matches || []);
        setPlatformStats(statsData || {});
      } catch (error) {
        console.error('Failed to load lobby data:', error);
      }
    };

    loadLobbyData();
  }, []);

  // Register player when name is entered
  useEffect(() => {
    const registerPlayer = async () => {
      console.log('RegisterPlayer check:', { 
        playerName: playerName.trim(), 
        length: playerName.trim().length, 
        hasPlayerId: !!player.id 
      });
      
      if (playerName.trim() && playerName.trim().length >= 3 && !player.id) {
        console.log('Attempting to register player:', playerName.trim());
        try {
          const registeredPlayer = await playerAPI.register(playerName.trim());
          console.log('Registration successful:', registeredPlayer);
          
          setPlayer(prev => {
            const newPlayer = {
              ...prev,
              id: registeredPlayer.id,
              name: registeredPlayer.name,
              virtualMoney: registeredPlayer.virtualMoney,
              realMoney: registeredPlayer.realMoney,
              totalGames: registeredPlayer.totalGames,
              bestScore: registeredPlayer.bestScore,
              wins: registeredPlayer.wins,
              totalKills: registeredPlayer.totalKills
            };
            console.log('Setting new player state:', newPlayer);
            return newPlayer;
          });
        } catch (error) {
          console.error('Failed to register player:', error);
        }
      }
    };

    // Debounce registration to avoid too many API calls
    const timeoutId = setTimeout(registerPlayer, 500);
    return () => clearTimeout(timeoutId);
  }, [playerName, player.id, setPlayer]);

  const handleStartGame = () => {
    alert('Button clicked!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-pink-900 p-6 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-yellow-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000ms"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000ms"></div>
        
        {/* Floating Money Icons */}
        <div className="absolute top-20 left-1/4 text-yellow-400 text-2xl animate-bounce">💰</div>
        <div className="absolute top-40 right-1/3 text-green-400 text-3xl animate-pulse">💵</div>
        <div className="absolute bottom-32 left-1/2 text-yellow-300 text-xl animate-spin">🪙</div>
        <div className="absolute top-60 left-1/6 text-emerald-400 text-2xl animate-bounce animation-delay-1000ms">💎</div>
        <div className="absolute bottom-40 right-1/4 text-orange-400 text-2xl animate-pulse">🎰</div>
      </div>

      <div className="max-w-6xl mx-auto space-y-6 relative z-10">
        {/* Header with Enhanced Styling */}
        <div className="text-center space-y-4">
          <div className="relative">
            <h1 className="text-7xl font-black bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 bg-clip-text text-transparent drop-shadow-2xl">
              MoneyAgar.io
            </h1>
            <div className="absolute -top-2 -right-2 text-4xl animate-spin">🎯</div>
            <div className="absolute -top-2 -left-2 text-4xl animate-pulse">⚡</div>
          </div>
          <p className="text-2xl text-gray-100 font-bold drop-shadow-lg">
            🔥 The ULTIMATE Real-Money Battle Arena! 🔥
          </p>
          <div className="flex justify-center gap-4 text-lg font-semibold">
            <span className="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-2 rounded-full animate-pulse">
              💸 LIVE CASH PRIZES!
            </span>
            <span className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-full animate-bounce">
              🚀 EAT OR BE EATEN!
            </span>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Game Setup */}
          <div className="lg:col-span-2 space-y-6">
            {/* Player Setup with Enhanced Styling */}
            <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-yellow-500 shadow-2xl">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2 text-2xl">
                  <Users className="w-6 h-6 text-yellow-400" />
                  🎮 Player Setup
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-bold text-yellow-400 mb-2 block">
                    💀 WARRIOR NAME 💀
                  </label>
                  <Input
                    value={playerName}
                    onChange={(e) => {
                      console.log('Input changed:', e.target.value);
                      setPlayerName(e.target.value);
                    }}
                    placeholder="Enter your battle name..."
                    className="bg-gray-700 border-2 border-yellow-500 text-white text-lg font-bold placeholder-gray-400 focus:border-orange-500"
                    maxLength={15}
                    disabled={isRegistering}
                  />
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-center p-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-lg border border-yellow-500">
                  <div className="transform hover:scale-105 transition-transform">
                    <div className="text-3xl font-black text-green-400 drop-shadow-lg">${player.virtualMoney || 250}</div>
                    <div className="text-sm text-green-300 font-bold">💰 Virtual Cash</div>
                  </div>
                  <div className="transform hover:scale-105 transition-transform">
                    <div className="text-3xl font-black text-blue-400 drop-shadow-lg">${player.realMoney || 0}</div>
                    <div className="text-sm text-blue-300 font-bold">💵 Real Money</div>
                  </div>
                  <div className="transform hover:scale-105 transition-transform">
                    <div className="text-3xl font-black text-purple-400 drop-shadow-lg">{player.totalGames || 0}</div>
                    <div className="text-sm text-purple-300 font-bold">🎯 Battles Won</div>
                  </div>
                </div>
                
                {/* Action Buttons with Enhanced Styling */}
                <div className="flex gap-3 mt-6">
                  <Button 
                    onClick={() => setShowShop(true)}
                    variant="outline"
                    className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 border-2 border-purple-400 text-white hover:from-purple-700 hover:to-pink-700 font-bold text-lg py-3 transform hover:scale-105 transition-all"
                    disabled={!player.id}
                  >
                    <ShoppingBag className="w-5 h-5 mr-2" />
                    🛒 Epic Shop
                  </Button>
                  <Button 
                    onClick={() => setShowPaymentModal(true)}
                    variant="outline"
                    className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 border-2 border-green-400 text-white hover:from-green-700 hover:to-emerald-700 font-bold text-lg py-3 transform hover:scale-105 transition-all"
                    disabled={!player.id}
                  >
                    <DollarSign className="w-5 h-5 mr-2" />
                    💸 Add Cash
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Game Modes with Crazy Styling */}
            <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-orange-500 shadow-2xl">
              <CardHeader>
                <CardTitle className="text-white text-2xl flex items-center gap-2">
                  🎯 SELECT YOUR BATTLEGROUND 🎯
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  {gameModes.map((mode) => {
                    const Icon = mode.icon;
                    return (
                      <div
                        key={mode.id}
                        onClick={() => {
                          console.log('Mode clicked:', mode.id);
                          setSelectedMode(mode.id);
                        }}
                        className={`p-6 rounded-xl border-3 cursor-pointer transition-all transform hover:scale-105 ${
                          selectedMode === mode.id
                            ? 'border-yellow-400 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 shadow-xl'
                            : 'border-gray-600 hover:border-gray-500 bg-gradient-to-r from-gray-700/50 to-gray-800/50'
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`p-4 rounded-xl bg-gradient-to-r ${mode.gradient} shadow-lg`}>
                            <Icon className="w-8 h-8 text-white" />
                          </div>
                          <div className="flex-1">
                            <h3 className="text-2xl font-black text-white drop-shadow-lg">{mode.name}</h3>
                            <p className="text-gray-300 text-lg font-semibold">{mode.description}</p>
                            <div className="flex gap-4 mt-3">
                              <Badge variant="secondary" className="bg-gradient-to-r from-green-600 to-emerald-600 text-white font-bold text-sm px-3 py-1">
                                💰 Min: ${mode.minBet}
                              </Badge>
                              <Badge variant="secondary" className="bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-sm px-3 py-1">
                                👥 Max: {mode.maxPlayers} players
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <Button
                  onClick={() => {
                    console.log('START BATTLE clicked!');
                    handleStartGame();
                  }}
                  disabled={isRegistering}
                  className="w-full mt-8 h-16 text-2xl font-black bg-gradient-to-r from-red-600 via-orange-600 to-yellow-600 hover:from-red-700 hover:via-orange-700 hover:to-yellow-700 border-2 border-yellow-400 shadow-2xl transform hover:scale-105 transition-all"
                >
                  <Play className="w-6 h-6 mr-3" />
                  {isRegistering ? '🚀 JOINING BATTLE...' : '⚔️ START BATTLE NOW! ⚔️'}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Active Tournaments */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-yellow-500" />
                  Active Tournaments
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {tournaments.slice(0, 3).map((tournament, index) => (
                    <div key={index} className="p-3 bg-slate-700 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-white">{tournament.name}</h4>
                        <Badge className="bg-green-600">${tournament.prizePool}</Badge>
                      </div>
                      <div className="text-sm text-gray-400 space-y-1">
                        <div className="flex items-center gap-2">
                          <Users className="w-3 h-3" />
                          {tournament.players}/{tournament.maxPlayers} players
                        </div>
                        <div className="flex items-center gap-2">
                          <Timer className="w-3 h-3" />
                          Starts in {tournament.startsIn}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recent Matches */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-500" />
                  Recent Matches
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentMatches.slice(0, 5).map((match, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-slate-700 rounded">
                      <div>
                        <div className="text-white font-medium">{match.winner}</div>
                        <div className="text-sm text-gray-400">{match.mode}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-green-400 font-medium">${match.prize}</div>
                        <div className="text-xs text-gray-400">{match.timeAgo}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Target className="w-5 h-5 text-purple-500" />
                  Platform Stats
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Players Online:</span>
                    <span className="text-white font-medium">{platformStats.playersOnline || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Active Games:</span>
                    <span className="text-white font-medium">{platformStats.activeGames || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Games Today:</span>
                    <span className="text-white font-medium">{platformStats.gamesToday || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Prize Pool:</span>
                    <span className="text-green-400 font-medium">${platformStats.totalPrizePool || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Your Best:</span>
                    <span className="text-yellow-400 font-medium">${player.bestScore || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
        
        {/* Shop Modal */}
        {showShop && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-auto m-4">
              <Shop 
                player={player}
                setPlayer={setPlayer}
                onClose={() => setShowShop(false)}
              />
            </div>
          </div>
        )}
        
        {/* Payment Modal */}
        {showPaymentModal && (
          <PaymentModal 
            player={player}
            setPlayer={setPlayer}
            onClose={() => setShowPaymentModal(false)}
          />
        )}
      </div>
    </div>
  );
};

export default GameLobby;