import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Coins, Trophy, Zap, Crown, DollarSign, Users } from 'lucide-react';
import { mockData } from '../utils/mock';

const GameUI = ({ player, setPlayer, gameState }) => {
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');

  const handleAddMoney = (amount) => {
    // Mock payment processing
    setPlayer(prev => ({
      ...prev,
      realMoney: prev.realMoney + amount,
      money: prev.money + amount
    }));
    setShowPaymentModal(false);
    setPaymentAmount('');
  };

  const handleWithdraw = (amount) => {
    if (player.virtualMoney >= amount) {
      setPlayer(prev => ({
        ...prev,
        virtualMoney: prev.virtualMoney - amount,
        realMoney: prev.realMoney + (amount * 0.9), // 10% platform fee
        money: prev.money - amount
      }));
    }
  };

  const activePowerUps = player.powerUps.filter(p => p.duration > 0);
  const leaderboard = mockData.getLeaderboard();

  return (
    <div className="w-80 space-y-4">
      {/* Player Stats */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-blue-500 text-white text-sm">
                {player.name.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            {player.name}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">${player.score}</div>
              <div className="text-sm text-gray-600">Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{player.kills}</div>
              <div className="text-sm text-gray-600">Kills</div>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Size Progress</span>
              <span className="text-sm text-gray-600">{Math.round(10 + Math.sqrt(player.money / 10))}px</span>
            </div>
            <Progress value={Math.min((player.money / 1000) * 100, 100)} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Money Management */}
      <Card className="bg-gradient-to-br from-green-50 to-emerald-100 border-green-200">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Coins className="w-5 h-5 text-green-600" />
            Money Management
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center">
              <div className="text-xl font-bold text-green-600">${player.virtualMoney}</div>
              <div className="text-sm text-gray-600">Virtual</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-blue-600">${player.realMoney}</div>
              <div className="text-sm text-gray-600">Real Money</div>
            </div>
          </div>
          
          <div className="space-y-2">
            <Button 
              onClick={() => setShowPaymentModal(true)}
              className="w-full bg-green-600 hover:bg-green-700"
              size="sm"
            >
              <DollarSign className="w-4 h-4 mr-2" />
              Add Money
            </Button>
            <Button 
              onClick={() => handleWithdraw(100)}
              variant="outline"
              className="w-full"
              size="sm"
              disabled={player.virtualMoney < 100}
            >
              Withdraw $100
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Active Power-ups */}
      {activePowerUps.length > 0 && (
        <Card className="bg-gradient-to-br from-purple-50 to-pink-100 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Zap className="w-5 h-5 text-purple-600" />
              Active Power-ups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activePowerUps.map((powerUp, index) => (
                <div key={index} className="flex items-center justify-between">
                  <Badge variant="secondary" className="bg-purple-100">
                    {powerUp.type}
                  </Badge>
                  <span className="text-sm text-gray-600">
                    {Math.ceil(powerUp.duration / 1000)}s
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Leaderboard */}
      <Card className="bg-gradient-to-br from-yellow-50 to-orange-100 border-yellow-200">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Trophy className="w-5 h-5 text-yellow-600" />
            Leaderboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {leaderboard.slice(0, 5).map((player, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant={index === 0 ? "default" : "secondary"} className={
                    index === 0 ? "bg-yellow-500" : ""
                  }>
                    {index + 1}
                  </Badge>
                  <span className="text-sm font-medium">{player.name}</span>
                </div>
                <span className="text-sm text-gray-600">${player.score}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Game Stats */}
      <Card className="bg-gradient-to-br from-gray-50 to-slate-100 border-gray-200">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Users className="w-5 h-5 text-gray-600" />
            Game Stats
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Players Online:</span>
              <span className="font-medium">{gameState.otherPlayers.length + 1}</span>
            </div>
            <div className="flex justify-between">
              <span>Food Items:</span>
              <span className="font-medium">{gameState.food.length}</span>
            </div>
            <div className="flex justify-between">
              <span>Your Rank:</span>
              <span className="font-medium text-blue-600">#{Math.floor(Math.random() * 10) + 1}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Payment Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-96 max-w-md">
            <CardHeader>
              <CardTitle>Add Real Money</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-2">
                {[10, 25, 50, 100, 200, 500].map(amount => (
                  <Button
                    key={amount}
                    onClick={() => handleAddMoney(amount)}
                    variant="outline"
                    className="h-12"
                  >
                    ${amount}
                  </Button>
                ))}
              </div>
              <div className="text-center">
                <Button onClick={() => setShowPaymentModal(false)} variant="secondary">
                  Cancel
                </Button>
              </div>
              <div className="text-xs text-gray-500 text-center">
                * This is a demo. No real money will be charged.
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default GameUI;