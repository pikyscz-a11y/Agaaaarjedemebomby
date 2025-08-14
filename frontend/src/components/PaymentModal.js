import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { DollarSign, CreditCard, X } from 'lucide-react';
import { paymentAPI } from '../services/api';
import { toast } from '../hooks/use-toast';

const PaymentModal = ({ player, setPlayer, onClose }) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAddMoney = async (amount) => {
    if (isProcessing || !player.id) return;
    
    setIsProcessing(true);
    try {
      const result = await paymentAPI.addMoney(player.id, amount);
      
      if (result.success) {
        // Update player money locally
        setPlayer(prev => ({
          ...prev,
          realMoney: prev.realMoney + amount,
          money: prev.money + amount
        }));
        
        toast({
          title: "Payment Successful",
          description: `Added $${amount} to your account`,
        });
        
        onClose();
      }
    } catch (error) {
      console.error('Payment failed:', error);
      toast({
        title: "Payment Failed",
        description: "Please try again later",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-96 max-w-md bg-white">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            Add Real Money
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            disabled={isProcessing}
          >
            <X className="w-4 h-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center mb-4">
            <p className="text-sm text-gray-600">
              Current Balance: <span className="font-semibold">${player.realMoney}</span>
            </p>
          </div>
          
          <div className="grid grid-cols-3 gap-2">
            {[10, 25, 50, 100, 200, 500].map(amount => (
              <Button
                key={amount}
                onClick={() => handleAddMoney(amount)}
                variant="outline"
                className="h-12 flex flex-col items-center justify-center"
                disabled={isProcessing}
              >
                <DollarSign className="w-4 h-4 mb-1" />
                ${amount}
              </Button>
            ))}
          </div>
          
          <div className="text-center space-y-2">
            <Button 
              onClick={onClose} 
              variant="secondary"
              disabled={isProcessing}
              className="w-full"
            >
              Cancel
            </Button>
            <div className="text-xs text-gray-500">
              * This is a demo. No real money will be charged.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentModal;