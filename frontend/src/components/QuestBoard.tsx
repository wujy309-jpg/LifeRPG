import { useState, useEffect } from 'react';
import { getQuests, getAllQuests, completeQuest } from '../services/api';
import type { Quest, AllQuestsResponse } from '../services/api';
import './QuestBoard.css';

interface QuestBoardProps {
  characterId: number;
  onQuestComplete: () => void;
}

function QuestBoard({ characterId, onQuestComplete }: QuestBoardProps) {
  const [quests, setQuests] = useState<Quest[]>([]);
  const [allQuests, setAllQuests] = useState<AllQuestsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'active' | 'daily' | 'weekly' | 'challenge'>('active');
  const [completing, setCompleting] = useState<number | null>(null);

  useEffect(() => {
    loadQuests();
  }, [characterId]);

  const loadQuests = async () => {
    try {
      const [questsData, allQuestsData] = await Promise.all([
        getQuests(characterId),
        getAllQuests(characterId)
      ]);
      setQuests(questsData);
      setAllQuests(allQuestsData);
    } catch (e) {
      console.error('加载任务失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (questId: number) => {
    setCompleting(questId);
    try {
      await completeQuest(questId);
      await loadQuests();
      onQuestComplete();
    } catch (e) {
      console.error('完成任务失败:', e);
      alert('操作失败，请重试');
    } finally {
      setCompleting(null);
    }
  };

  const activeQuests = quests.filter(q => q.status === 'active');

  const getQuestTypeIcon = (type: string) => {
    switch (type) {
      case 'daily': return '  ';
      case 'weekly': return '  ';
      case 'challenge': return '⚔️';
      case 'achievement': return ' ';
      default: return '  ';
    }
  };

  const getQuestTypeLabel = (type: string) => {
    switch (type) {
      case 'daily': return '每日';
      case 'weekly': return '每周';
      case 'challenge': return '挑战';
      case 'achievement': return '成就';
      default: return '任务';
    }
  };

  const getQuestTypeColor = (type: string) => {
    switch (type) {
      case 'daily': return '#4ade80';
      case 'weekly': return '#3b82f6';
      case 'challenge': return '#f59e0b';
      case 'achievement': return '#a855f7';
      default: return '#8888a0';
    }
  };

  if (loading) {
    return <div className="loading">加载中...</div>;
  }

  return (
    <div className="quest-page">
      <header className="page-header">
        <h2>  任务板</h2>
        <div className="quest-stats">
          <span className="stat active">进行中: {activeQuests.length}</span>
          <span className="stat completed">今日完成: {allQuests?.completed_today || 0}</span>
        </div>
      </header>

      {/* 任务标签页 */}
      <div className="quest-tabs">
        <button
          className={`tab ${activeTab === 'active' ? 'active' : ''}`}
          onClick={() => setActiveTab('active')}
        >
            进行中 ({activeQuests.length})
        </button>
        <button
          className={`tab ${activeTab === 'daily' ? 'active' : ''}`}
          onClick={() => setActiveTab('daily')}
        >
             每日任务
        </button>
        <button
          className={`tab ${activeTab === 'weekly' ? 'active' : ''}`}
          onClick={() => setActiveTab('weekly')}
        >
             每周任务
        </button>
        <button
          className={`tab ${activeTab === 'challenge' ? 'active' : ''}`}
          onClick={() => setActiveTab('challenge')}
        >
           ⚔️ 挑战任务
        </button>
      </div>

      {/* 任务列表 */}
      <div className="quest-content">
        {activeTab === 'active' ? (
          // 显示进行中的任务
          <div className="quest-list">
            {activeQuests.length > 0 ? (
              activeQuests.map(quest => (
                <div key={quest.id} className="quest-card active">
                  <div className="quest-header">
                    <div 
                      className="quest-type-badge"
                      style={{ backgroundColor: getQuestTypeColor(quest.quest_type) + '20', color: getQuestTypeColor(quest.quest_type) }}
                    >
                      {getQuestTypeIcon(quest.quest_type)} {getQuestTypeLabel(quest.quest_type)}
                    </div>
                    <h3 className="quest-title">{quest.title}</h3>
                  </div>
                  <p className="quest-description">{quest.description}</p>
                  <div className="quest-footer">
                    <div className="quest-rewards">
                      <span className="reward exp">⭐ +{quest.exp_reward} EXP</span>
                      <span className="reward gold">  +{quest.gold_reward}G</span>
                    </div>
                    <button
                      className="complete-btn"
                      onClick={() => handleComplete(quest.id)}
                      disabled={completing === quest.id}
                    >
                      {completing === quest.id ? '完成中...' : '完成任务'}
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <p className="empty-icon"> </p>
                <p>没有进行中的任务</p>
                <p className="hint">查看其他标签页获取新任务！</p>
              </div>
            )}
          </div>
        ) : (
          // 显示可用任务
          <div className="quest-list">
            {allQuests?.available_quests[activeTab as keyof typeof allQuests.available_quests]?.map((quest, index) => (
              <div key={index} className="quest-card available">
                <div className="quest-header">
                  <div 
                    className="quest-type-badge"
                    style={{ backgroundColor: getQuestTypeColor(quest.quest_type || activeTab) + '20', color: getQuestTypeColor(quest.quest_type || activeTab) }}
                  >
                    {getQuestTypeIcon(quest.quest_type || activeTab)} {getQuestTypeLabel(quest.quest_type || activeTab)}
                  </div>
                  <h3 className="quest-title">{quest.title}</h3>
                </div>
                <p className="quest-description">{quest.description}</p>
                <div className="quest-footer">
                  <div className="quest-rewards">
                    <span className="reward exp">⭐ +{quest.exp_reward} EXP</span>
                    <span className="reward gold">  +{quest.gold_reward}G</span>
                  </div>
                  <span className="quest-hint">记录活动自动接取</span>
                </div>
              </div>
            )) || (
              <div className="empty-state">
                <p className="empty-icon"> </p>
                <p>暂无可用任务</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 任务说明 */}
      <div className="quest-guide">
        <h3>  任务说明</h3>
        <ul>
          <li><strong>  每日任务</strong>：每天刷新，完成获得基础奖励</li>
          <li><strong>  每周任务</strong>：每周刷新，奖励更丰厚</li>
          <li><strong>⚔️ 挑战任务</strong>：高难度任务，奖励最高</li>
          <li><strong>  成就任务</strong>：一次性任务，记录里程碑</li>
        </ul>
      </div>
    </div>
  );
}

export default QuestBoard;