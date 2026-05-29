import { useState } from 'react';
import { logActivity } from '../services/api';
import type { GameFeedback } from '../services/api';
import './ActivityLog.css';

interface ActivityLogProps {
  characterId: number;
  onActivityLogged: () => void;
}

function ActivityLog({ characterId, onActivityLogged }: ActivityLogProps) {
  const [description, setDescription] = useState('');
  const [feedback, setFeedback] = useState<GameFeedback | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!description.trim()) return;
    setSubmitting(true);
    try {
      const result = await logActivity(characterId, description);
      setFeedback(result);
      setDescription('');
      onActivityLogged();
    } catch (e) {
      console.error('记录失败:', e);
      alert('记录失败，请重试');
    } finally {
      setSubmitting(false);
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

  const activityPresets = [
    { icon: ' ', label: '学习', desc: '去上课/看书/复习' },
    { icon: ' ️', label: '运动', desc: '健身/跑步/打球' },
    { icon: ' ', label: '编程', desc: '写代码/Debug' },
    { icon: ' ', label: '社交', desc: '聚会/聊天' },
    { icon: ' ', label: '工作', desc: '上班/开会' },
    { icon: ' ', label: '创作', desc: '画画/写作/设计' },
    { icon: ' ', label: '生活', desc: '做饭/打扫' },
    { icon: ' ', label: '休息', desc: '睡觉/放松' },
  ];

  return (
    <div className="activity-page">
      <header className="page-header">
        <h2>✏️ 记录活动</h2>
        <p>告诉我你今天做了什么，获得经验值和奖励！</p>
      </header>

      <div className="input-section">
        <textarea
          className="activity-input"
          placeholder="详细描述你做了什么...&#10;&#10;例如：&#10;- 在图书馆看了3小时高数&#10;- 去健身房练了胸和三头&#10;- 用React写了一个Todo应用"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={5}
        />
        <button
          className="submit-btn"
          onClick={handleSubmit}
          disabled={submitting || !description.trim()}
        >
          {submitting ? 'AI 分析中...' : '提交记录'}
        </button>
      </div>

      <div className="presets-section">
        <h3>快速选择</h3>
        <div className="presets-grid">
          {activityPresets.map((preset) => (
            <button
              key={preset.label}
              className="preset-btn"
              onClick={() => setDescription(preset.desc)}
            >
              <span className="preset-icon">{preset.icon}</span>
              <span className="preset-label">{preset.label}</span>
            </button>
          ))}
        </div>
      </div>

      {feedback && (
        <div className="feedback-section">
          <h3> 活动反馈</h3>
          <div className="feedback-card">
            <div className="gains-row">
              <div className="gain-item exp">
                <span className="gain-icon">⭐</span>
                <span className="gain-label">经验值</span>
                <span className="gain-value">+{feedback.activity_log.exp_gained}</span>
              </div>
              <div className="gain-item gold">
                <span className="gain-icon"> </span>
                <span className="gain-label">金币</span>
                <span className="gain-value">+{feedback.activity_log.gold_gained}</span>
              </div>
            </div>

            {feedback.level_up && (
              <div className="level-up-alert">
                <span> </span> 恭喜升级！达到 Lv.{feedback.new_level}
              </div>
            )}

            {feedback.equipment_found && (
              <div className="reward-card equipment" style={{ borderColor: getRarityColor(feedback.equipment_found.rarity) }}>
                <h4>  获得装备</h4>
                <p className="reward-name" style={{ color: getRarityColor(feedback.equipment_found.rarity) }}>
                  [{feedback.equipment_found.rarity}] {feedback.equipment_found.name}
                </p>
                <p className="reward-desc">{feedback.equipment_found.description}</p>
              </div>
            )}

            {feedback.title_earned && (
              <div className="reward-card title">
                <h4>  获得称号</h4>
                <p className="reward-name">「{feedback.title_earned.name}」</p>
                <p className="reward-desc">{feedback.title_earned.description}</p>
              </div>
            )}

            {feedback.quest_generated && (
              <div className="reward-card quest">
                <h4>  新任务</h4>
                <p className="reward-name">{feedback.quest_generated.title}</p>
                <p className="reward-desc">{feedback.quest_generated.description}</p>
                <div className="quest-rewards">
                  <span>+{feedback.quest_generated.exp_reward} EXP</span>
                  <span>+{feedback.quest_generated.gold_reward}G</span>
                </div>
              </div>
            )}

            {feedback.ai_comment && (
              <div className="ai-comment-box">
                <p className="comment-label">  AI 评价</p>
                <p className="comment-content">{feedback.ai_comment}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ActivityLog;
