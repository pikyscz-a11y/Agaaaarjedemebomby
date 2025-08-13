import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Coins, Trophy, Zap, Crown, DollarSign, Users } from 'lucide-react';
import { paymentAPI, statsAPI, playerAPI } from '../services/api';
import { toast } from '../hooks/use-toast';

const GameUI = ({ player, setPlayer, gameState }) => {
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [leaderboard, setLeaderboard] = useState([]);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  // Load leaderboard data
  useEffect(() => {
    const loadLeaderboard = async () => {
      try {
        const data = await statsAPI.getLeaderboard();
        setLeaderboard(data.players || []);
      } catch (error) {
        console.error('Failed to load leaderboard:', error);
      }
    };

    loadLeaderboard();
    const interval = setInterval(loadLeaderboard, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const handleAddMoney = async (amount) => {
    if (isProcessingPayment || !player.id) return;
    
    setIsProcessingPayment(true);
    try {
      const result = await paymentAPI.addMoney(player.id, amount);
      
      if (result.success) {
        // Update player money locally
        setPlayer(prev => ({
          ...prev,
          realMoney: prev.realMoney + amount,
          money: prev.money + amount
        }));
        
        // Refresh player data from server
        const updatedPlayer = await playerAPI.getPlayer(player.id);
        setPlayer(prev => ({
          ...prev,
          realMoney: updatedPlayer.realMoney,
          virtualMoney: updatedPlayer.virtualMoney
        }));
        
        toast({
          title: "Payment Successful",
          description: `Added $${amount} to your account`,
        });
      }
    } catch (error) {
      console.error('Payment failed:', error);
      toast({
        title: "Payment Failed",
        description: "Please try again later",
        variant: "destructive",
      });
    } finally {
      setIsProcessingPayment(false);
      setShowPaymentModal(false);
    }
  };

  const handleWithdraw = async (amount) => {
    if (isProcessingPayment || !player.id) return;
    
    if (player.virtualMoney < amount) {
      toast({
        title: "Insufficient Balance",
        description: "Not enough virtual money to withdraw",
        variant: "destructive",
      });
      return;
    }
    
    setIsProcessingPayment(true);
    try {
      const result = await paymentAPI.withdraw(player.id, amount);
      
      if (result.success) {
        // Update player money locally
        setPlayer(prev => ({
          ...prev,
          virtualMoney: prev.virtualMoney - amount,
          realMoney: prev.realMoney + result.amount,
          money: (prev.virtualMoney - amount) + prev.realMoney + result.amount
        }));
        
        toast({
          title: "Withdrawal Successful",
          description: `Withdrew $${result.amount} (Fee: $${result.fee})`,
        });
      }
    } catch (error) {
      console.error('Withdrawal failed:', error);
      toast({
        title: "Withdrawal Failed",
        description: error.response?.data?.detail || "Please try again later",
        variant: "destructive",
      });
    } finally {
      setIsProcessingPayment(false);
    }
  };

  const activePowerUps = player.powerUps?.filter(p => p.duration > 0) || [];

  return (
    <div className="w-80 space-y-4">
      {/* Player Stats */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-blue-500 text-white text-sm">
                {player.name?.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            {player.name}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">${player.score || 0}</div>
              <div className="text-sm text-gray-600">Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{player.kills || 0}</div>
              <div className="text-sm text-gray-600">Kills</div>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Size Progress</span>
              <span className="text-sm text-gray-600">{Math.round(10 + Math.sqrt((player.money || 0) / 10))}px</span>
            </div>
            <Progress value={Math.min(((player.money || 0) / 1000) * 100, 100)} className="h-2" />
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
              <div className="text-xl font-bold text-green-600">${player.virtualMoney || 0}</div>
              <div className="text-sm text-gray-600">Virtual</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-blue-600">${player.realMoney || 0}</div>
              <div className="text-sm text-gray-600">Real Money</div>
            </div>
          </div>
          
          <div className="space-y-2">
            <Button 
              onClick={() => setShowPaymentModal(true)}
              className="w-full bg-green-600 hover:bg-green-700"
              size="sm"
              disabled={isProcessingPayment}
            >
              <DollarSign className="w-4 h-4 mr-2" />
              {isProcessingPayment ? 'Processing...' : 'Add Money'}
            </Button>
            <Button 
              onClick={() => handleWithdraw(100)}
              variant="outline"
              className="w-full"
              size="sm"
              disabled={player.virtualMoney < 100 || isProcessingPayment}
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
            {leaderboard.slice(0, 5).map((playerEntry, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant={index === 0 ? "default" : "secondary"} className={
                    index === 0 ? "bg-yellow-500" : ""
                  }>
                    {playerEntry.rank}
                  </Badge>
                  <span className="text-sm font-medium">{playerEntry.name}</span>
                </div>
                <span className="text-sm text-gray-600">${playerEntry.score}</span>
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
              <span className="font-medium">{gameState.gameStats?.playersOnline || 0}</span>
            </div>
            <div className="flex justify-between">
              <span>Food Items:</span>
              <span className="font-medium">{gameState.gameStats?.foodItems || 0}</span>
            </div>
            <div className="flex justify-between">
              <span>Game Mode:</span>
              <span className="font-medium text-blue-600">{gameState.gameStats?.gameMode || 'Classic'}</span>
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
                    disabled={isProcessingPayment}
                  >
                    ${amount}
                  </Button>
                ))}
              </div>
              <div className="text-center">
                <Button 
                  onClick={() => setShowPaymentModal(false)} 
                  variant="secondary"
                  disabled={isProcessingPayment}
                >
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