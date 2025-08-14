import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Separator } from './ui/separator';
import { shopAPI } from '../services/api';
import { toast } from '../hooks/use-toast';
import { 
  ShoppingBag, 
  Crown, 
  Zap, 
  Shield, 
  Palette, 
  Star,
  Coins,
  DollarSign,
  Package
} from 'lucide-react';

const Shop = ({ player, setPlayer, onClose }) => {
  const [shopItems, setShopItems] = useState([]);
  const [playerInventory, setPlayerInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    loadShopData();
  }, [player.id]);

  const loadShopData = async () => {
    try {
      setLoading(true);
      const [itemsResponse, inventoryResponse] = await Promise.all([
        shopAPI.getItems(),
        shopAPI.getInventory(player.id)
      ]);
      
      setShopItems(itemsResponse.items);
      setPlayerInventory(inventoryResponse.inventory);
    } catch (error) {
      console.error('Failed to load shop data:', error);
      toast({
        title: "Error",
        description: "Failed to load shop data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (item) => {
    try {
      const response = await shopAPI.purchaseItem(player.id, item.id, 1);
      
      // Update player balance
      if (item.currency === 'virtual') {
        setPlayer(prev => ({
          ...prev,
          virtualMoney: response.newBalance
        }));
      } else {
        setPlayer(prev => ({
          ...prev,
          realMoney: response.newBalance
        }));
      }
      
      toast({
        title: "Purchase Successful!",
        description: response.message,
      });
      
      // Reload inventory
      loadShopData();
      
    } catch (error) {
      console.error('Purchase failed:', error);
      toast({
        title: "Purchase Failed",
        description: error.response?.data?.detail || "Purchase failed",
        variant: "destructive",
      });
    }
  };

  const handleEquip = async (item) => {
    try {
      await shopAPI.equipItem(player.id, item.itemId);
      
      toast({
        title: "Item Equipped!",
        description: `${item.itemName} is now equipped`,
      });
      
      // Reload inventory
      loadShopData();
      
    } catch (error) {
      console.error('Equip failed:', error);
      toast({
        title: "Equip Failed",
        description: "Failed to equip item",
        variant: "destructive",
      });
    }
  };

  const getRarityColor = (rarity) => {
    const colors = {
      common: 'bg-gray-100 text-gray-800',
      rare: 'bg-blue-100 text-blue-800',
      epic: 'bg-purple-100 text-purple-800',
      legendary: 'bg-orange-100 text-orange-800'
    };
    return colors[rarity] || colors.common;
  };

  const getCategoryIcon = (category) => {
    const icons = {
      skins: <Palette className="w-4 h-4" />,
      powerups: <Zap className="w-4 h-4" />,
      boosts: <Shield className="w-4 h-4" />,
      premium: <Crown className="w-4 h-4" />
    };
    return icons[category] || <Package className="w-4 h-4" />;
  };

  const filteredItems = shopItems.filter(item => 
    selectedCategory === 'all' || item.category === selectedCategory
  );

  const isItemOwned = (itemId) => {
    return playerInventory.some(invItem => invItem.itemId === itemId);
  };

  const canAfford = (item) => {
    if (item.currency === 'virtual') {
      return player.virtualMoney >= item.price;
    } else {
      return player.realMoney >= item.price;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <ShoppingBag className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold">MoneyAgar Shop</h1>
            <p className="text-gray-600">Enhance your gameplay with skins, power-ups and more!</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-green-100 rounded-lg">
            <Coins className="w-5 h-5 text-green-600" />
            <span className="font-semibold text-green-800">${player.virtualMoney}</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-blue-100 rounded-lg">
            <DollarSign className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-blue-800">${player.realMoney}</span>
          </div>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>

      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">All Items</TabsTrigger>
          <TabsTrigger value="skins">Skins</TabsTrigger>
          <TabsTrigger value="powerups">Power-ups</TabsTrigger>
          <TabsTrigger value="boosts">Boosts</TabsTrigger>
          <TabsTrigger value="premium">Premium</TabsTrigger>
        </TabsList>

        <TabsContent value={selectedCategory} className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredItems.map((item) => {
              const owned = isItemOwned(item.id);
              const affordable = canAfford(item);
              
              return (
                <Card key={item.id} className="relative overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(item.category)}
                        <CardTitle className="text-lg">{item.name}</CardTitle>
                      </div>
                      <Badge className={getRarityColor(item.rarity)}>
                        {item.rarity}
                      </Badge>
                    </div>
                    <CardDescription className="text-sm">
                      {item.description}
                    </CardDescription>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="space-y-4">
                      {/* Effects */}
                      {Object.keys(item.effects).length > 0 && (
                        <div className="space-y-2">
                          <h4 className="font-medium text-sm text-gray-700">Effects:</h4>
                          <div className="space-y-1">
                            {Object.entries(item.effects).map(([key, value]) => (
                              <div key={key} className="flex justify-between text-xs">
                                <span className="capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                                <span className="font-medium">
                                  {typeof value === 'number' && key.includes('Multiplier') 
                                    ? `${(value * 100)}%` 
                                    : String(value)
                                  }
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <Separator />
                      
                      {/* Price and Purchase */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {item.currency === 'virtual' ? (
                            <Coins className="w-4 h-4 text-green-600" />
                          ) : (
                            <DollarSign className="w-4 h-4 text-blue-600" />
                          )}
                          <span className="font-bold text-lg">
                            ${item.price}
                          </span>
                          {!item.isPermanent && (
                            <span className="text-xs text-gray-500">
                              ({Math.floor(item.duration / 3600)}h)
                            </span>
                          )}
                        </div>
                        
                        {owned ? (
                          <Badge variant="secondary">Owned</Badge>
                        ) : (
                          <Button
                            size="sm"
                            onClick={() => handlePurchase(item)}
                            disabled={!affordable}
                            className={affordable ? '' : 'opacity-50 cursor-not-allowed'}
                          >
                            {affordable ? 'Buy Now' : 'Not Enough Money'}
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
          
          {filteredItems.length === 0 && (
            <div className="text-center py-12">
              <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No items found</h3>
              <p className="text-gray-500">Try selecting a different category</p>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Inventory Section */}
      {playerInventory.length > 0 && (
        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Package className="w-6 h-6" />
            Your Inventory
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {playerInventory.map((item) => (
              <Card key={item.id} className="relative">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{item.itemName}</h3>
                    {item.isEquipped && (
                      <Badge variant="secondary">
                        <Star className="w-3 h-3 mr-1" />
                        Equipped
                      </Badge>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-3 capitalize">
                    {item.category} • {item.subcategory}
                  </p>
                  
                  {!item.isEquipped && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEquip(item)}
                      className="w-full"
                    >
                      Equip
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Shop;