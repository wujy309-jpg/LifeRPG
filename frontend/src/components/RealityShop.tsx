import { useState, useEffect } from 'react';
import { 
  getRealityRewards, addCustomReward, redeemReward,
  getHabitChallenges, createHabitChallenge, checkInChallenge,
  getImmunityCards, buyImmunityCard, checkPenalty, getPenaltyHistory
} from '../services/api';
import type { RealityReward, HabitChallenge, ImmunityCard } from '../services/api';
import './RealityShop.css';

interface RealityShopProps {
  characterId: number;
  onRefresh: () => void;
}

export default function RealityShop({ characterId, onRefresh }: RealityShopProps) {
  const [activeTab, setActiveTab] = useState<'rewards' | 'challenges' | 'cards' | 'penalty'>('rewards');
  const [rewards, setRewards] = useState<RealityReward[]>([]);
  const [challenges, setChallenges] = useState<HabitChallenge[]>([]);
  const [cards, setCards] = useState<ImmunityCard[]>([]);
  const [gold, setGold] = useState(0);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [showAddReward, setShowAddReward] = useState(false);
  const [showCreateChallenge, setShowCreateChallenge] = useState(false);
  const [penaltyInfo, setPenaltyInfo] = useState<any>(null);
  const [penaltyHistory, setPenaltyHistory] = useState<any[]>([]);

  // 新奖励表单
  const [newReward, setNewReward] = useState({name: '', description: '', cost: 50});
  // 新挑战表单
  const [newChallenge, setNewChallenge] = useState({name: '', description: '', duration_days: 21, cost: 50});

  useEffect(() => {
    loadData();
  }, [characterId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [rewardsData, challengesData, cardsData, penaltyData, historyData] = await Promise.all([
        getRealityRewards(characterId),
        getHabitChallenges(characterId),
        getImmunityCards(characterId),
        checkPenalty(characterId),
        getPenaltyHistory(characterId)
      ]);
      setRewards(rewardsData.rewards);
      setGold(rewardsData.gold);
      setChallenges(challengesData.challenges);
      setCards(cardsData.cards);
      setPenaltyInfo(penaltyData);
      setPenaltyHistory(historyData.history);
    } catch (e) {
      console.error('加载数据失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({type, text});
    setTimeout(() => setMessage(null), 3000);
  };

  const handleRedeemReward = async (rewardId: number) => {
    try {
      const result = await redeemReward(characterId, rewardId);
      showMessage('success', `兑换成功！获得「${result.reward_name}」，剩余${result.remaining_gold}金币`);
      loadData();
      onRefresh();
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail || '兑换失败');
    }
  };

  const handleAddReward = async () => {
    if (!newReward.name) {
      showMessage('error', '请输入奖励名称');
      return;
    }
    try {
      await addCustomReward(characterId, newReward);
      showMessage('success', '添加成功！');
      setNewReward({name: '', description: '', cost: 50});
      setShowAddReward(false);
      loadData();
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail || '添加失败');
    }
  };

  const handleCreateChallenge = async () => {
    if (!newChallenge.name) {
      showMessage('error', '请输入挑战名称');
      return;
    }
    try {
      await createHabitChallenge(characterId, newChallenge);
      showMessage('success', '挑战创建成功！');
      setNewChallenge({name: '', description: '', duration_days: 21, cost: 50});
      setShowCreateChallenge(false);
      loadData();
      onRefresh();
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail || '创建失败');
    }
  };

  const handleCheckIn = async (challengeId: number) => {
    try {
      const result = await checkInChallenge(characterId, challengeId);
      if (result.completed) {
        showMessage('success', `挑战完成！获得${result.reward_exp}经验，${result.reward_gold}金币`);
      } else {
        showMessage('success', `打卡成功！还剩${result.days_remaining}天`);
      }
      loadData();
      onRefresh();
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail || '打卡失败');
    }
  };

  const handleBuyCard = async (cardType: string) => {
    try {
      const result = await buyImmunityCard(characterId, cardType);
      showMessage('success', `购买成功！获得「${result.card_name}」`);
      loadData();
      onRefresh();
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail || '购买失败');
    }
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      entertainment: ' ',
      food: ' ',
      rest: ' ️',
      education: ' ',
      shopping: ' ️',
      custom: '✨'
    };
    return icons[category] || ' ';
  };

  const getCardTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      skip_task: '⏭️',
      rest_day: ' ️',
      double_reward: '✨',
      penalty_shield: ' ️'
    };
    return icons[type] || ' ';
  };

  if (loading) {
    return <div className="loading">加载中...</div>;
  }

  return (
    <div className="reality-shop">
      <header className="page-header">
        <h2>  现实商城</h2>
        <p>用金币兑换现实奖励，让游戏与生活连接！</p>
        <div className="gold-display">
          <span className="gold-icon"> </span>
          <span className="gold-amount">{gold}</span>
        </div>
      </header>

      {message && (
        <div className={`message ${message.type}`}>
          {message.type === 'success' ? '✅' : '❌'} {message.text}
        </div>
      )}

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'rewards' ? 'active' : ''}`}
          onClick={() => setActiveTab('rewards')}
        >
            现实奖励
        </button>
        <button 
          className={`tab ${activeTab === 'challenges' ? 'active' : ''}`}
          onClick={() => setActiveTab('challenges')}
        >
            习惯挑战
        </button>
        <button 
          className={`tab ${activeTab === 'cards' ? 'active' : ''}`}
          onClick={() => setActiveTab('cards')}
        >
            免罪金牌
        </button>
        <button 
          className={`tab ${activeTab === 'penalty' ? 'active' : ''}`}
          onClick={() => setActiveTab('penalty')}
        >
            惩罚机制
        </button>
      </div>

      {/* 现实奖励 */}
      {activeTab === 'rewards' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>兑换奖励</h3>
            <button className="add-btn" onClick={() => setShowAddReward(true)}>+ 自定义奖励</button>
          </div>
          
          <div className="rewards-grid">
            {rewards.map(reward => (
              <div key={reward.id} className="reward-card">
                <div className="reward-icon">{reward.icon || getCategoryIcon(reward.category)}</div>
                <div className="reward-info">
                  <h4>{reward.name}</h4>
                  <p>{reward.description}</p>
                  <div className="reward-cost">
                    <span className="cost-icon"> </span>
                    <span className="cost-amount">{reward.cost}</span>
                  </div>
                </div>
                <button 
                  className="redeem-btn"
                  onClick={() => handleRedeemReward(reward.id)}
                  disabled={gold < reward.cost}
                >
                  兑换
                </button>
              </div>
            ))}
          </div>

          {showAddReward && (
            <div className="modal-overlay" onClick={() => setShowAddReward(false)}>
              <div className="modal" onClick={e => e.stopPropagation()}>
                <h3>添加自定义奖励</h3>
                <div className="form-group">
                  <label>奖励名称</label>
                  <input 
                    type="text" 
                    value={newReward.name}
                    onChange={e => setNewReward({...newReward, name: e.target.value})}
                    placeholder="例如：看一集电视剧"
                  />
                </div>
                <div className="form-group">
                  <label>描述</label>
                  <input 
                    type="text" 
                    value={newReward.description}
                    onChange={e => setNewReward({...newReward, description: e.target.value})}
                    placeholder="可选描述"
                  />
                </div>
                <div className="form-group">
                  <label>花费金币</label>
                  <input 
                    type="number" 
                    value={newReward.cost}
                    onChange={e => setNewReward({...newReward, cost: parseInt(e.target.value) || 0})}
                    min="1"
                  />
                </div>
                <div className="modal-actions">
                  <button className="cancel-btn" onClick={() => setShowAddReward(false)}>取消</button>
                  <button className="confirm-btn" onClick={handleAddReward}>添加</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 习惯挑战 */}
      {activeTab === 'challenges' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>进行中的挑战</h3>
            <button className="add-btn" onClick={() => setShowCreateChallenge(true)}>+ 创建挑战</button>
          </div>

          {challenges.length === 0 ? (
            <div className="empty-state">
              <p>还没有进行中的挑战</p>
              <p>创建一个21天习惯挑战吧！</p>
            </div>
          ) : (
            <div className="challenges-list">
              {challenges.map(challenge => (
                <div key={challenge.id} className={`challenge-card ${challenge.status}`}>
                  <div className="challenge-header">
                    <h4>{challenge.name}</h4>
                    <span className={`status-badge ${challenge.status}`}>
                      {challenge.status === 'active' ? '进行中' : challenge.status === 'completed' ? '已完成' : '已失败'}
                    </span>
                  </div>
                  <p className="challenge-desc">{challenge.description}</p>
                  <div className="challenge-progress">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{width: `${(challenge.check_in_days / challenge.duration_days) * 100}%`}}
                      />
                    </div>
                    <span className="progress-text">
                      {challenge.check_in_days}/{challenge.duration_days}天
                    </span>
                  </div>
                  <div className="challenge-rewards">
                    <span>奖励: +{challenge.reward_exp}EXP</span>
                    <span>+{challenge.reward_gold} </span>
                  </div>
                  {challenge.status === 'active' && (
                    <button 
                      className="checkin-btn"
                      onClick={() => handleCheckIn(challenge.id)}
                      disabled={challenge.last_check_in === new Date().toISOString().split('T')[0]}
                    >
                      {challenge.last_check_in === new Date().toISOString().split('T')[0] ? '今日已打卡' : '打卡'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {showCreateChallenge && (
            <div className="modal-overlay" onClick={() => setShowCreateChallenge(false)}>
              <div className="modal" onClick={e => e.stopPropagation()}>
                <h3>创建习惯挑战</h3>
                <div className="form-group">
                  <label>挑战名称</label>
                  <input 
                    type="text" 
                    value={newChallenge.name}
                    onChange={e => setNewChallenge({...newChallenge, name: e.target.value})}
                    placeholder="例如：21天早起挑战"
                  />
                </div>
                <div className="form-group">
                  <label>描述</label>
                  <input 
                    type="text" 
                    value={newChallenge.description}
                    onChange={e => setNewChallenge({...newChallenge, description: e.target.value})}
                    placeholder="挑战描述"
                  />
                </div>
                <div className="form-group">
                  <label>持续天数</label>
                  <input 
                    type="number" 
                    value={newChallenge.duration_days}
                    onChange={e => setNewChallenge({...newChallenge, duration_days: parseInt(e.target.value) || 21})}
                    min="7"
                    max="100"
                  />
                </div>
                <div className="form-group">
                  <label>投入金币</label>
                  <input 
                    type="number" 
                    value={newChallenge.cost}
                    onChange={e => setNewChallenge({...newChallenge, cost: parseInt(e.target.value) || 50})}
                    min="10"
                  />
                </div>
                <p className="form-hint">投入的金币越多，完成时获得的奖励越丰厚！</p>
                <div className="modal-actions">
                  <button className="cancel-btn" onClick={() => setShowCreateChallenge(false)}>取消</button>
                  <button className="confirm-btn" onClick={handleCreateChallenge}>创建</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 免罪金牌 */}
      {activeTab === 'cards' && (
        <div className="tab-content">
          <h3>购买免罪金牌</h3>
          <div className="cards-grid">
            <div className="card-item">
              <div className="card-icon">⏭️</div>
              <h4>任务跳过卡</h4>
              <p>跳过一个不想做的任务</p>
              <div className="card-cost">
                <span className="cost-icon"> </span>
                <span>50</span>
              </div>
              <button onClick={() => handleBuyCard('skip_task')} disabled={gold < 50}>购买</button>
            </div>
            <div className="card-item">
              <div className="card-icon"> ️</div>
              <h4>休息日卡</h4>
              <p>允许一天不打卡不扣金币</p>
              <div className="card-cost">
                <span className="cost-icon"> </span>
                <span>80</span>
              </div>
              <button onClick={() => handleBuyCard('rest_day')} disabled={gold < 80}>购买</button>
            </div>
            <div className="card-item">
              <div className="card-icon">✨</div>
              <h4>双倍奖励卡</h4>
              <p>下次任务获得双倍奖励</p>
              <div className="card-cost">
                <span className="cost-icon"> </span>
                <span>100</span>
              </div>
              <button onClick={() => handleBuyCard('double_reward')} disabled={gold < 100}>购买</button>
            </div>
            <div className="card-item">
              <div className="card-icon"> ️</div>
              <h4>惩罚护盾</h4>
              <p>抵挡一次金币惩罚</p>
              <div className="card-cost">
                <span className="cost-icon"> </span>
                <span>60</span>
              </div>
              <button onClick={() => handleBuyCard('penalty_shield')} disabled={gold < 60}>购买</button>
            </div>
          </div>

          <h3>我的卡牌</h3>
          {cards.length === 0 ? (
            <div className="empty-state">
              <p>还没有卡牌，快去购买吧！</p>
            </div>
          ) : (
            <div className="my-cards">
              {cards.map(card => (
                <div key={card.id} className="my-card">
                  <span className="card-icon">{getCardTypeIcon(card.card_type)}</span>
                  <span className="card-name">{card.name}</span>
                  <span className="card-uses">剩余{card.uses_remaining}次</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 惩罚机制 */}
      {activeTab === 'penalty' && (
        <div className="tab-content">
          <h3>惩罚规则</h3>
          <div className="penalty-rules">
            <div className="rule-card">
              <h4>  活跃度惩罚</h4>
              <p>连续7天活动不足3次，将扣除50金币</p>
              <p className="rule-tip">保持活跃，记录每日活动！</p>
            </div>
            <div className="rule-card">
              <h4> ️ 惩罚护盾</h4>
              <p>购买「惩罚护盾」可以抵挡一次惩罚</p>
              <p className="rule-tip">提前准备，有备无患！</p>
            </div>
          </div>

          {penaltyInfo && (
            <div className="penalty-status">
              <h4>当前状态</h4>
              {penaltyInfo.penalty ? (
                <div className="penalty-alert">
                  <p>⚠️ 触发惩罚：扣除{penaltyInfo.gold_lost}金币</p>
                  <p>原因：{penaltyInfo.reason}</p>
                </div>
              ) : penaltyInfo.shield_used ? (
                <div className="shield-alert">
                  <p> ️ 使用了惩罚护盾，免除本次惩罚</p>
                </div>
              ) : (
                <div className="safe-alert">
                  <p>✅ 状态正常，继续保持活跃！</p>
                </div>
              )}
            </div>
          )}

          <h3>惩罚历史</h3>
          {penaltyHistory.length === 0 ? (
            <div className="empty-state">
              <p>暂无惩罚记录</p>
            </div>
          ) : (
            <div className="penalty-history">
              {penaltyHistory.map((record, index) => (
                <div key={index} className="history-item">
                  <span className="history-icon"> </span>
                  <span className="history-desc">{record.description}</span>
                  <span className="history-gold">-{record.gold_lost} </span>
                  <span className="history-date">{new Date(record.created_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
