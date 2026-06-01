import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';

interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  intent?: string;
  emotion?: string;
  created_at: string;
}

interface AgentChatProps {
  characterId: number;
}

const AgentChat: React.FC<AgentChatProps> = ({ characterId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 拖动相关状态
  const [position, setPosition] = useState(() => {
    const saved = localStorage.getItem('agent_chat_position');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return { x: window.innerWidth - 80, y: window.innerHeight - 80 };
      }
    }
    return { x: window.innerWidth - 80, y: window.innerHeight - 80 };
  });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hasMoved, setHasMoved] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // 保存位置到localStorage
  useEffect(() => {
    localStorage.setItem('agent_chat_position', JSON.stringify(position));
  }, [position]);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 加载历史对话
  useEffect(() => {
    if (isOpen && characterId) {
      loadHistory();
    }
  }, [isOpen, characterId]);

  const loadHistory = async () => {
    try {
      const response = await axios.get(`/api/agent/sessions/${characterId}`);
      const sessions = response.data.sessions || [];
      
      if (sessions.length > 0) {
        const latestSession = sessions[0];
        setSessionId(latestSession.session_id);
        setMessages(latestSession.messages || []);
      }
    } catch (error) {
      console.error('加载对话历史失败:', error);
    }
  };

  // 拖动开始
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    setHasMoved(false);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    });
  }, [position]);

  // 拖动中
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      
      setHasMoved(true);
      
      const newX = e.clientX - dragStart.x;
      const newY = e.clientY - dragStart.y;
      
      // 限制在窗口范围内
      const buttonSize = 60;
      const minX = 0;
      const minY = 0;
      const maxX = window.innerWidth - buttonSize;
      const maxY = window.innerHeight - buttonSize;
      
      setPosition({
        x: Math.max(minX, Math.min(maxX, newX)),
        y: Math.max(minY, Math.min(maxY, newY))
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragStart]);

  // 触摸拖动支持
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0];
    setIsDragging(true);
    setHasMoved(false);
    setDragStart({
      x: touch.clientX - position.x,
      y: touch.clientY - position.y
    });
  }, [position]);

  useEffect(() => {
    const handleTouchMove = (e: TouchEvent) => {
      if (!isDragging) return;
      
      e.preventDefault();
      setHasMoved(true);
      
      const touch = e.touches[0];
      const newX = touch.clientX - dragStart.x;
      const newY = touch.clientY - dragStart.y;
      
      const buttonSize = 60;
      const minX = 0;
      const minY = 0;
      const maxX = window.innerWidth - buttonSize;
      const maxY = window.innerHeight - buttonSize;
      
      setPosition({
        x: Math.max(minX, Math.min(maxX, newX)),
        y: Math.max(minY, Math.min(maxY, newY))
      });
    };

    const handleTouchEnd = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('touchmove', handleTouchMove, { passive: false });
      document.addEventListener('touchend', handleTouchEnd);
    }

    return () => {
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [isDragging, dragStart]);

  // 点击按钮（只有在没有拖动时才触发）
  const handleClick = () => {
    if (!hasMoved) {
      setIsOpen(!isOpen);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: inputValue,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post(`/api/agent/chat/${characterId}`, {
        message: inputValue,
        session_id: sessionId
      });

      const data = response.data;
      
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        intent: data.intent,
        emotion: data.emotion?.emotion,
        created_at: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('发送消息失败:', error);
      
      const errorMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '抱歉，发生了错误。请稍后再试。',
        created_at: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getIntentLabel = (intent?: string) => {
    const labels: Record<string, string> = {
      'record_activity': '记录活动',
      'check_status': '查看状态',
      'get_suggestion': '获取建议',
      'check_quests': '查看任务',
      'view_equipment': '查看装备',
      'emotional_support': '情感支持',
      'general_chat': '聊天'
    };
    return intent ? labels[intent] || intent : '';
  };

  const getEmotionEmoji = (emotion?: string) => {
    const emojis: Record<string, string> = {
      'happy': ' ',
      'sad': ' ',
      'angry': ' ',
      'anxious': ' ',
      'excited': ' ',
      'neutral': ' '
    };
    return emotion ? emojis[emotion] || ' ' : ' ';
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // 计算聊天窗口位置（在按钮上方）
  const getChatPosition = () => {
    const chatWidth = 400;
    const chatHeight = 500;
    const offset = 80;
    
    let x = position.x - chatWidth + 60;
    let y = position.y - chatHeight - offset;
    
    // 确保不超出屏幕
    if (x < 10) x = 10;
    if (x + chatWidth > window.innerWidth - 10) x = window.innerWidth - chatWidth - 10;
    if (y < 10) y = position.y + offset;
    
    return { x, y };
  };

  const chatPos = getChatPosition();

  return (
    <>
      {/* 悬浮按钮 */}
      <button
        ref={buttonRef}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        onClick={handleClick}
        style={{
          position: 'fixed',
          left: `${position.x}px`,
          top: `${position.y}px`,
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          border: 'none',
          cursor: isDragging ? 'grabbing' : 'grab',
          fontSize: '24px',
          boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: isDragging ? 'none' : 'box-shadow 0.2s',
          userSelect: 'none',
          touchAction: 'none'
        }}
        onMouseEnter={(e) => {
          if (!isDragging) {
            e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.4)';
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = '0 4px 15px rgba(0,0,0,0.3)';
        }}
      >
        {isOpen ? '✕' : ' '}
      </button>

      {/* 拖动提示 */}
      {isDragging && !hasMoved && (
        <div style={{
          position: 'fixed',
          left: `${position.x + 70}px`,
          top: `${position.y + 10}px`,
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          whiteSpace: 'nowrap',
          zIndex: 1001
        }}>
          拖动移动位置
        </div>
      )}

      {/* 聊天窗口 */}
      {isOpen && (
        <div style={{
          position: 'fixed',
          left: `${chatPos.x}px`,
          top: `${chatPos.y}px`,
          width: '400px',
          height: '500px',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 1001,
          overflow: 'hidden'
        }}>
          {/* 头部 */}
          <div style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '15px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            cursor: 'default'
          }}>
            <span style={{ fontSize: '24px' }}> </span>
            <div>
              <div style={{ fontWeight: 'bold', fontSize: '16px' }}>LifeRPG 智能助手</div>
              <div style={{ fontSize: '12px', opacity: 0.8 }}>随时为你服务</div>
            </div>
          </div>

          {/* 消息列表 */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '15px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {messages.length === 0 && (
              <div style={{
                textAlign: 'center',
                color: '#999',
                padding: '40px 20px'
              }}>
                <div style={{ fontSize: '40px', marginBottom: '10px' }}> </div>
                <p>你好！我是你的智能助手</p>
                <p style={{ fontSize: '12px' }}>有什么可以帮你的吗？</p>
              </div>
            )}
            
            {messages.map((msg, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <div style={{
                  maxWidth: '80%',
                  padding: '10px 14px',
                  borderRadius: '12px',
                  background: msg.role === 'user' 
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                    : '#f0f0f0',
                  color: msg.role === 'user' ? 'white' : '#333',
                  position: 'relative'
                }}>
                  {msg.role === 'assistant' && msg.intent && (
                    <div style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      background: 'rgba(0,0,0,0.1)',
                      borderRadius: '4px',
                      marginBottom: '6px',
                      display: 'inline-block'
                    }}>
                      {getIntentLabel(msg.intent)}
                    </div>
                  )}
                  
                  <div style={{ 
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.5'
                  }}>
                    {msg.role === 'assistant' && msg.emotion && (
                      <span style={{ marginRight: '6px' }}>
                        {getEmotionEmoji(msg.emotion)}
                      </span>
                    )}
                    {msg.content}
                  </div>
                  
                  <div style={{
                    fontSize: '10px',
                    opacity: 0.6,
                    marginTop: '4px',
                    textAlign: 'right'
                  }}>
                    {formatTime(msg.created_at)}
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div style={{
                display: 'flex',
                justifyContent: 'flex-start'
              }}>
                <div style={{
                  padding: '10px 14px',
                  borderRadius: '12px',
                  background: '#f0f0f0'
                }}>
                  <div style={{
                    display: 'flex',
                    gap: '4px',
                    alignItems: 'center'
                  }}>
                    <span style={{ 
                      animation: 'pulse 1.5s infinite',
                      animationDelay: '0s' 
                    }}>●</span>
                    <span style={{ 
                      animation: 'pulse 1.5s infinite',
                      animationDelay: '0.3s' 
                    }}>●</span>
                    <span style={{ 
                      animation: 'pulse 1.5s infinite',
                      animationDelay: '0.6s' 
                    }}>●</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* 输入框 */}
          <div style={{
            padding: '12px',
            borderTop: '1px solid #eee',
            display: 'flex',
            gap: '8px'
          }}>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入消息..."
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '10px 14px',
                borderRadius: '8px',
                border: '1px solid #ddd',
                outline: 'none',
                fontSize: '14px'
              }}
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !inputValue.trim()}
              style={{
                padding: '10px 16px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading || !inputValue.trim() ? 0.5 : 1,
                fontSize: '14px'
              }}
            >
              发送
            </button>
          </div>
        </div>
      )}

      {/* CSS动画 */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }
      `}</style>
    </>
  );
};

export default AgentChat;