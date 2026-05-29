import { useState, useEffect } from 'react';
import { getEquipment, useEquipment } from '../services/api';
import type { Equipment } from '../services/api';
import './Inventory.css';

interface InventoryProps {
  characterId: number;
}

function Inventory({ characterId }: InventoryProps) {
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<Equipment | null>(null);
  const [useMessage, setUseMessage] = useState<string | null>(null);

  useEffect(() => {
    loadEquipment();
  }, [characterId]);

  const loadEquipment = async () => {
    try {
      const data = await getEquipment(characterId);
      setEquipment(data);
    } catch (e) {
      console.error('加载装备失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const getRarityColor = (rarity: string) => {
    const colors: Record<string, string> = {
      '普通': '#9d9d9d',
      '稀有': '#0070dd',
      '史诗': '#a335ee',
      '传说': '#ff8000'
    };
    return colors[rarity] || '#9d9d9d';
  };

  const getRarityBorder = (rarity: string) => {
    const colors: Record<string, string> = {
      '普通': '1px solid #9d9d9d33',
      '稀有': '1px solid #0070dd33',
      '史诗': '1px solid #a335ee33',
      '传说': '2px solid #ff800055'
    };
    return colors[rarity] || '1px solid #9d9d9d33';
  };

  const handleUseItem = async (item: Equipment) => {
    try {
      const result = await useEquipment(item.id);
      setUseMessage(result.message);
      setSelectedItem(null);
      loadEquipment(); // 重新加载装备列表
      
      // 3秒后清除消息
      setTimeout(() => setUseMessage(null), 3000);
    } catch (e) {
      console.error('使用装备失败:', e);
      setUseMessage('使用失败');
      setTimeout(() => setUseMessage(null), 3000);
    }
  };

  const rarityCounts = equipment.reduce((acc, item) => {
    acc[item.rarity] = (acc[item.rarity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return <div className="loading">加载中...</div>;
  }

  return (
    <div className="inventory-page">
      <header className="page-header">
        <h2>   装备背包</h2>
        <p className="equip-count">共 {equipment.length} 件装备</p>
      </header>

      {/* 使用消息提示 */}
      {useMessage && (
        <div className="use-message">
          ✨ {useMessage}
        </div>
      )}

      {/* 稀有度统计 */}
      <div className="rarity-stats">
        {Object.entries(rarityCounts).map(([rarity, count]) => (
          <div key={rarity} className="rarity-stat" style={{ borderColor: getRarityColor(rarity) }}>
            <span className="rarity-name" style={{ color: getRarityColor(rarity) }}>{rarity}</span>
            <span className="rarity-count">{count}</span>
          </div>
        ))}
      </div>

      <div className="inventory-content">
        {/* 装备网格 */}
        <div className="equipment-grid">
          {equipment.length > 0 ? (
            equipment.map(item => (
              <div
                key={item.id}
                className={`equipment-card ${selectedItem?.id === item.id ? 'selected' : ''}`}
                style={{ border: getRarityBorder(item.rarity) }}
                onClick={() => setSelectedItem(item)}
              >
                <div className="card-glow" style={{ backgroundColor: getRarityColor(item.rarity) }}></div>
                <div className="card-content">
                  <span className="item-rarity" style={{ color: getRarityColor(item.rarity) }}>
                    [{item.rarity}]
                  </span>
                  <h4 className="item-name">{item.name}</h4>
                  {item.equipped && <span className="equipped-tag">已装备</span>}
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <p className="empty-icon"> </p>
              <p>背包空空如也</p>
              <p className="hint">记录活动来获取装备吧！</p>
            </div>
          )}
        </div>

        {/* 装备详情 */}
        {selectedItem && (
          <div className="equipment-detail">
            <div className="detail-header" style={{ borderColor: getRarityColor(selectedItem.rarity) }}>
              <span className="detail-rarity" style={{ color: getRarityColor(selectedItem.rarity) }}>
                [{selectedItem.rarity}]
              </span>
              <h3 className="detail-name">{selectedItem.name}</h3>
            </div>
            <div className="detail-body">
              <p className="detail-desc">{selectedItem.description}</p>
              
              {/* 使用效果 */}
              {selectedItem.use_desc && (
                <div className="use-effect">
                  <span className="use-label">使用方式:</span>
                  <span className="use-text">{selectedItem.use_desc}</span>
                </div>
              )}
              {selectedItem.use_effect && (
                <div className="use-effect">
                  <span className="use-label">使用效果:</span>
                  <span className="use-text">{selectedItem.use_effect}</span>
                </div>
              )}
              
              {selectedItem.special_effect && (
                <div className="special-effect">
                  <span className="effect-label">特殊效果:</span>
                  <span className="effect-text">{selectedItem.special_effect}</span>
                </div>
              )}
              {selectedItem.stat_bonuses && selectedItem.stat_bonuses !== '{}' && (
                <div className="stat-bonuses">
                  <span className="bonus-label">属性加成:</span>
                  <div className="bonus-list">
                    {Object.entries(JSON.parse(selectedItem.stat_bonuses)).map(([stat, value]) => (
                      <span key={stat} className="bonus-item">
                        {stat}: +{value as number}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {/* 使用按钮 */}
              <button 
                className="use-btn"
                onClick={() => handleUseItem(selectedItem)}
              >
                使用物品
              </button>
              
              <div className="detail-meta">
                <span>获得时间: {new Date(selectedItem.created_at).toLocaleDateString('zh-CN')}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Inventory;
