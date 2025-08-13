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
  Timer
} from 'lucide-react';
import { playerAPI, statsAPI } from '../services/api';
import { toast } from '../hooks/use-toast';

const GameLobby = ({ onStartGame, player, setPlayer }) => {
  const [playerName, setPlayerName] = useState(player.name || '');
  const [selectedMode, setSelectedMode] = useState('classic');
  const [isRegistering, setIsRegistering] = useState(false);
  const [tournaments, setTournaments] = useState([]);
  const [recentMatches, setRecentMatches] = useState([]);
  const [platformStats, setPlatformStats] = useState({});
  
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

  const handleStartGame = async () => {
    if (!playerName.trim()) {
      toast({
        title: "Name Required",
        description: "Please enter your player name",
        variant: "destructive",
      });
      return;
    }

    setIsRegistering(true);
    try {
      // Register or get existing player
      const registeredPlayer = await playerAPI.register(playerName.trim());
      
      setPlayer(prev => ({
        ...prev,
        id: registeredPlayer.id,
        name: registeredPlayer.name,
        virtualMoney: registeredPlayer.virtualMoney,
        realMoney: registeredPlayer.realMoney,
        totalGames: registeredPlayer.totalGames,
        bestScore: registeredPlayer.bestScore,
        wins: registeredPlayer.wins,
        totalKills: registeredPlayer.totalKills
      }));

      toast({
        title: "Welcome!",
        description: `Starting ${selectedMode} mode...`,
      });

      onStartGame(selectedMode);
    } catch (error) {
      console.error('Failed to register player:', error);
      toast({
        title: "Registration Failed",
        description: "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsRegistering(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            MoneyAgar.io
          </h1>
          <p className="text-xl text-gray-200">
            The ultimate real-money battle arena game
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Game Setup */}
          <div className="lg:col-span-2 space-y-6">
            {/* Player Setup */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Player Setup
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-300 mb-2 block">
                    Player Name
                  </label>
                  <Input
                    value={playerName}
                    onChange={(e) => setPlayerName(e.target.value)}
                    placeholder="Enter your name"
                    className="bg-slate-700 border-slate-600 text-white"
                    maxLength={15}
                    disabled={isRegistering}
                  />
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-400">${player.virtualMoney || 250}</div>
                    <div className="text-sm text-gray-400">Virtual Money</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-400">${player.realMoney || 0}</div>
                    <div className="text-sm text-gray-400">Real Money</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-400">{player.totalGames || 0}</div>
                    <div className="text-sm text-gray-400">Games Played</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Game Modes */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Select Game Mode</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  {gameModes.map((mode) => {
                    const Icon = mode.icon;
                    return (
                      <div
                        key={mode.id}
                        onClick={() => setSelectedMode(mode.id)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          selectedMode === mode.id
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-slate-600 hover:border-slate-500'
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`p-3 rounded-lg bg-gradient-to-r ${mode.gradient}`}>
                            <Icon className="w-6 h-6 text-white" />
                          </div>
                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-white">{mode.name}</h3>
                            <p className="text-gray-400 text-sm">{mode.description}</p>
                            <div className="flex gap-4 mt-2">
                              <Badge variant="secondary" className="bg-slate-700">
                                Min: ${mode.minBet}
                              </Badge>
                              <Badge variant="secondary" className="bg-slate-700">
                                Max: {mode.maxPlayers} players
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <Button
                  onClick={handleStartGame}
                  disabled={!playerName.trim() || isRegistering}
                  className="w-full mt-6 h-12 text-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  <Play className="w-5 h-5 mr-2" />
                  {isRegistering ? 'Starting Game...' : 'Start Game'}
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
      </div>
    </div>
  );
};

export default GameLobby;