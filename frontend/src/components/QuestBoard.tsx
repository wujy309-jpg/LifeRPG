import { useState, useEffect } from 'react';
import { getQuests, completeQuest } from '../services/api';
import type { Quest } from '../services/api';
import './QuestBoard.css';

interface QuestBoardProps {
  characterId: number;
  onQuestComplete: () => void;
}

function QuestBoard({ characterId, onQuestComplete }: QuestBoardProps) {
  const [quests, setQuests] = useState<Quest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');
  const [completing, setCompleting] = useState<number | null>(null);

  useEffect(() => {
    loadQuests();
  }, [characterId]);

  const loadQuests = async () => {
    try {
      const data = await getQuests(characterId);
      setQuests(data);
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

  const filteredQuests = quests.filter(q => {
    if (filter === 'active') return q.status === 'active';
    if (filter === 'completed') return q.status === 'completed';
    return true;
  });

  const activeCount = quests.filter(q => q.status === 'active').length;
  const completedCount = quests.filter(q => q.status === 'completed').length;

  if (loading) {
    return <div className="loading">加载中...</div>;
  }

  return (
    <div className="quest-page">
      <header className="page-header">
        <h2>  任务板</h2>
        <div className="quest-stats">
          <span className="stat active">进行中: {activeCount}</span>
          <span className="stat completed">已完成: {completedCount}</span>
        </div>
      </header>

      {/* 筛选标签 */}
      <div className="filter-tabs">
        <button
          className={`tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          全部 ({quests.length})
        </button>
        <button
          className={`tab ${filter === 'active' ? 'active' : ''}`}
          onClick={() => setFilter('active')}
        >
          进行中 ({activeCount})
        </button>
        <button
          className={`tab ${filter === 'completed' ? 'active' : ''}`}
          onClick={() => setFilter('completed')}
        >
          已完成 ({completedCount})
        </button>
      </div>

      {/* 任务列表 */}
      <div className="quest-list">
        {filteredQuests.length > 0 ? (
          filteredQuests.map(quest => (
            <div key={quest.id} className={`quest-card ${quest.status}`}>
              <div className="quest-header">
                <div className="quest-type-badge">
                  {quest.quest_type === 'daily' ? '  每日' : '  主线'}
                </div>
                <h3 className="quest-title">{quest.title}</h3>
                {quest.status === 'completed' && (
                  <span className="completed-badge">✓ 已完成</span>
                )}
              </div>
              <p className="quest-description">{quest.description}</p>
              <div className="quest-footer">
                <div className="quest-rewards">
                  <span className="reward exp">⭐ +{quest.exp_reward} EXP</span>
                  <span className="reward gold">  +{quest.gold_reward}G</span>
                </div>
                {quest.status === 'active' && (
                  <button
                    className="complete-btn"
                    onClick={() => handleComplete(quest.id)}
                    disabled={completing === quest.id}
                  >
                    {completing === quest.id ? '完成中...' : '完成任务'}
                  </button>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <p className="empty-icon"> </p>
            <p>{filter === 'active' ? '没有进行中的任务' : filter === 'completed' ? '还没有完成任何任务' : '暂无任务'}</p>
            <p className="hint">记录活动来获取新任务吧！</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default QuestBoard;
