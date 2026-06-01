import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface AgentDashboardProps {
  characterId: number;
}

interface Notification {
  id: number;
  notification_type: string;
  title: string;
  content: string;
  priority: number;
  created_at: string;
  read: boolean;
}

interface Goal {
  id: number;
  title: string;
  description: string;
  goal_type: string;
  target_value: number;
  current_value: number;
  progress: number;
  status: string;
  deadline: string;
}

interface Task {
  id: number;
  title: string;
  description: string;
  task_type: string;
  priority: number;
  scheduled_date: string;
  scheduled_time: string;
  completed: boolean;
}

interface EmotionStats {
  emotion: string;
  count: number;
  avg_intensity: number;
}

interface UserProfile {
  personality: string;
  habits: string;
  preferences: string;
  activity_patterns: string;
  peak_hours: string;
  weakness: string;
  strength: string;
  motivation_style: string;
}

const AgentDashboard: React.FC<AgentDashboardProps> = ({ characterId }) => {
  const [activeTab, setActiveTab] = useState<'notifications' | 'goals' | 'tasks' | 'emotions' | 'profile'>('notifications');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [emotionStats, setEmotionStats] = useState<EmotionStats[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [characterId, activeTab]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      switch (activeTab) {
        case 'notifications':
          const notifRes = await axios.get(`/api/agent/notifications/${characterId}`);
          setNotifications(notifRes.data.notifications || []);
          break;
        case 'goals':
          const goalsRes = await axios.get(`/api/agent/goals/${characterId}`);
          setGoals(goalsRes.data.goals || []);
          break;
        case 'tasks':
          const tasksRes = await axios.get(`/api/agent/tasks/${characterId}`);
          setTasks(tasksRes.data.tasks || []);
          break;
        case 'emotions':
          const emotionRes = await axios.get(`/api/agent/emotion/${characterId}`);
          setEmotionStats(emotionRes.data.emotion_stats || []);
          break;
        case 'profile':
          const profileRes = await axios.get(`/api/agent/profile/${characterId}`);
          setProfile(profileRes.data);
          break;
      }
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const markNotificationRead = async (notificationId: number) => {
    try {
      await axios.post(`/api/agent/notifications/${notificationId}/read`);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
    } catch (error) {
      console.error('标记已读失败:', error);
    }
  };

  const completeTask = async (taskId: number) => {
    try {
      await axios.post(`/api/agent/tasks/${taskId}/complete`);
      setTasks(prev => 
        prev.map(t => t.id === taskId ? { ...t, completed: true } : t)
      );
    } catch (error) {
      console.error('完成任务失败:', error);
    }
  };

  const getNotificationIcon = (type: string) => {
    const icons: Record<string, string> = {
      'reminder': ' ',
      'summary': ' ',
      'encouragement': ' ',
      'suggestion': ' ',
      'warning': '⚠️',
      'achievement': ' '
    };
    return icons[type] || ' ';
  };

  const getGoalTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'fitness': '  健身',
      'learning': '  学习',
      'habit': '  习惯',
      'general': '  通用'
    };
    return labels[type] || type;
  };

  const getTaskTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'daily': '每日',
      'weekly': '每周',
      'one-time': '一次性'
    };
    return labels[type] || type;
  };

  const getEmotionEmoji = (emotion: string) => {
    const emojis: Record<string, string> = {
      'happy': ' ',
      'sad': ' ',
      'angry': ' ',
      'anxious': ' ',
      'excited': ' ',
      'neutral': ' '
    };
    return emojis[emotion] || '❓';
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
  };

  const renderNotifications = () => (
    <div>
      <h3 style={{ marginBottom: '15px', color: '#333' }}>  通知</h3>
      {notifications.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
          <div style={{ fontSize: '40px', marginBottom: '10px' }}> </div>
          <p>暂无通知</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {notifications.map(notif => (
            <div
              key={notif.id}
              style={{
                padding: '12px',
                background: notif.read ? '#f9f9f9' : '#fff',
                borderRadius: '8px',
                border: notif.read ? '1px solid #eee' : '1px solid #667eea',
                cursor: 'pointer',
                opacity: notif.read ? 0.7 : 1
              }}
              onClick={() => markNotificationRead(notif.id)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '20px' }}>{getNotificationIcon(notif.notification_type)}</span>
                <strong style={{ color: '#333' }}>{notif.title}</strong>
                <span style={{ 
                  marginLeft: 'auto', 
                  fontSize: '12px', 
                  color: '#999' 
                }}>
                  {formatDate(notif.created_at)}
                </span>
              </div>
              <p style={{ color: '#666', margin: 0, fontSize: '14px' }}>{notif.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderGoals = () => (
    <div>
      <h3 style={{ marginBottom: '15px', color: '#333' }}>  长期目标</h3>
      {goals.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
          <div style={{ fontSize: '40px', marginBottom: '10px' }}> </div>
          <p>还没有设置目标</p>
          <p style={{ fontSize: '12px' }}>在智能助手中创建目标</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {goals.map(goal => (
            <div
              key={goal.id}
              style={{
                padding: '15px',
                background: '#fff',
                borderRadius: '8px',
                border: '1px solid #eee'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div>
                  <span style={{ 
                    padding: '4px 8px', 
                    background: '#f0f0f0', 
                    borderRadius: '4px',
                    fontSize: '12px',
                    marginRight: '8px'
                  }}>
                    {getGoalTypeLabel(goal.goal_type)}
                  </span>
                  <strong style={{ color: '#333' }}>{goal.title}</strong>
                </div>
                <span style={{ 
                  color: goal.status === 'completed' ? '#52c41a' : '#667eea',
                  fontWeight: 'bold'
                }}>
                  {Math.round(goal.progress * 100)}%
                </span>
              </div>
              
              {goal.description && (
                <p style={{ color: '#666', fontSize: '14px', margin: '8px 0' }}>{goal.description}</p>
              )}
              
              {/* 进度条 */}
              <div style={{
                height: '8px',
                background: '#f0f0f0',
                borderRadius: '4px',
                overflow: 'hidden',
                marginBottom: '8px'
              }}>
                <div style={{
                  height: '100%',
                  width: `${goal.progress * 100}%`,
                  background: goal.status === 'completed' 
                    ? 'linear-gradient(90deg, #52c41a, #73d13d)' 
                    : 'linear-gradient(90deg, #667eea, #764ba2)',
                  borderRadius: '4px',
                  transition: 'width 0.3s ease'
                }} />
              </div>
              
              {goal.deadline && (
                <div style={{ fontSize: '12px', color: '#999' }}>
                  截止日期: {formatDate(goal.deadline)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderTasks = () => (
    <div>
      <h3 style={{ marginBottom: '15px', color: '#333' }}>✅ 任务计划</h3>
      {tasks.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
          <div style={{ fontSize: '40px', marginBottom: '10px' }}> </div>
          <p>暂无任务</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {tasks.map(task => (
            <div
              key={task.id}
              style={{
                padding: '12px',
                background: task.completed ? '#f9f9f9' : '#fff',
                borderRadius: '8px',
                border: '1px solid #eee',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                opacity: task.completed ? 0.6 : 1
              }}
            >
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => !task.completed && completeTask(task.id)}
                style={{ 
                  width: '18px', 
                  height: '18px',
                  cursor: task.completed ? 'default' : 'pointer'
                }}
              />
              
              <div style={{ flex: 1 }}>
                <div style={{ 
                  textDecoration: task.completed ? 'line-through' : 'none',
                  color: '#333',
                  fontWeight: task.completed ? 'normal' : 'bold'
                }}>
                  {task.title}
                </div>
                
                {task.description && (
                  <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                    {task.description}
                  </div>
                )}
              </div>
              
              <div style={{ textAlign: 'right' }}>
                <div style={{ 
                  fontSize: '12px', 
                  padding: '2px 6px',
                  background: '#f0f0f0',
                  borderRadius: '4px',
                  display: 'inline-block'
                }}>
                  {getTaskTypeLabel(task.task_type)}
                </div>
                
                {task.scheduled_time && (
                  <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                    {task.scheduled_time}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderEmotions = () => (
    <div>
      <h3 style={{ marginBottom: '15px', color: '#333' }}>   情绪统计</h3>
      {emotionStats.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
          <div style={{ fontSize: '40px', marginBottom: '10px' }}> </div>
          <p>暂无情绪数据</p>
          <p style={{ fontSize: '12px' }}>记录活动或对话时会自动分析情绪</p>
        </div>
      ) : (
        <div>
          <p style={{ color: '#666', marginBottom: '15px' }}>最近7天情绪分布</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {emotionStats.map(stat => (
              <div
                key={stat.emotion}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '10px',
                  background: '#fff',
                  borderRadius: '8px',
                  border: '1px solid #eee'
                }}
              >
                <span style={{ fontSize: '24px' }}>{getEmotionEmoji(stat.emotion)}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 'bold', color: '#333' }}>
                    {stat.emotion}
                  </div>
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    {stat.count}次 · 平均强度: {(stat.avg_intensity * 100).toFixed(0)}%
                  </div>
                </div>
                <div style={{
                  width: '100px',
                  height: '8px',
                  background: '#f0f0f0',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${(stat.count / Math.max(...emotionStats.map(s => s.count))) * 100}%`,
                    background: 'linear-gradient(90deg, #667eea, #764ba2)',
                    borderRadius: '4px'
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderProfile = () => (
    <div>
      <h3 style={{ marginBottom: '15px', color: '#333' }}>  用户画像</h3>
      {!profile ? (
        <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
          <div style={{ fontSize: '40px', marginBottom: '10px' }}> </div>
          <p>正在分析你的行为模式...</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {/* 行为模式 */}
          <div style={{
            padding: '15px',
            background: '#fff',
            borderRadius: '8px',
            border: '1px solid #eee'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#333' }}> </h4>
            <p style={{ color: '#666', fontSize: '14px' }}>
              {profile.activity_patterns ? 
                JSON.parse(profile.activity_patterns).length > 0 ?
                  '已分析你的活动模式，正在学习你的习惯...' :
                  '还没有足够的数据来分析你的模式' :
                '正在收集数据...'
              }
            </p>
          </div>

          {/* 高效时段 */}
          <div style={{
            padding: '15px',
            background: '#fff',
            borderRadius: '8px',
            border: '1px solid #eee'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>⏰ 高效时段</h4>
            <p style={{ color: '#666', fontSize: '14px' }}>
              {profile.peak_hours ? 
                JSON.parse(profile.peak_hours).length > 0 ?
                  '已识别你的高效时段' :
                  '还在分析你的活跃时间...' :
                '正在收集数据...'
              }
            </p>
          </div>

          {/* 习惯统计 */}
          <div style={{
            padding: '15px',
            background: '#fff',
            borderRadius: '8px',
            border: '1px solid #eee'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>   习惯统计</h4>
            <p style={{ color: '#666', fontSize: '14px' }}>
              {profile.habits ? 
                Object.keys(JSON.parse(profile.habits)).length > 0 ?
                  `已记录 ${Object.keys(JSON.parse(profile.habits)).length} 种活动习惯` :
                  '开始记录活动后会自动统计习惯' :
                '正在收集数据...'
              }
            </p>
          </div>

          {/* 激励风格 */}
          <div style={{
            padding: '15px',
            background: '#fff',
            borderRadius: '8px',
            border: '1px solid #eee'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>  激励风格</h4>
            <p style={{ color: '#666', fontSize: '14px' }}>
              {profile.motivation_style === 'balanced' ? '平衡型' :
               profile.motivation_style === 'challenging' ? '挑战型' :
               profile.motivation_style === 'supportive' ? '支持型' : '平衡型'}
            </p>
          </div>
        </div>
      )}
    </div>
  );

  const tabs = [
    { key: 'notifications', label: '  通知', count: notifications.filter(n => !n.read).length },
    { key: 'goals', label: '  目标', count: goals.filter(g => g.status === 'active').length },
    { key: 'tasks', label: '✅ 任务', count: tasks.filter(t => !t.completed).length },
    { key: 'emotions', label: '   情绪' },
    { key: 'profile', label: '  画像' }
  ];

  return (
    <div style={{
      background: '#f5f5f5',
      borderRadius: '12px',
      padding: '20px',
      minHeight: '500px'
    }}>
      {/* 标签页 */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '20px',
        flexWrap: 'wrap'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === tab.key 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : '#fff',
              color: activeTab === tab.key ? 'white' : '#333',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: activeTab === tab.key ? '0 2px 8px rgba(102,126,234,0.4)' : 'none'
            }}
          >
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span style={{
                background: activeTab === tab.key ? 'rgba(255,255,255,0.3)' : '#667eea',
                color: 'white',
                padding: '2px 6px',
                borderRadius: '10px',
                fontSize: '12px',
                minWidth: '18px',
                textAlign: 'center'
              }}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* 内容区域 */}
      <div style={{
        background: '#fff',
        borderRadius: '8px',
        padding: '20px',
        minHeight: '400px'
      }}>
        {isLoading ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px',
            color: '#999'
          }}>
            <div style={{ fontSize: '40px', marginBottom: '10px', animation: 'spin 1s linear infinite' }}>⏳</div>
            <p>加载中...</p>
            <style>{`
              @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        ) : (
          <>
            {activeTab === 'notifications' && renderNotifications()}
            {activeTab === 'goals' && renderGoals()}
            {activeTab === 'tasks' && renderTasks()}
            {activeTab === 'emotions' && renderEmotions()}
            {activeTab === 'profile' && renderProfile()}
          </>
        )}
      </div>
    </div>
  );
};

export default AgentDashboard;