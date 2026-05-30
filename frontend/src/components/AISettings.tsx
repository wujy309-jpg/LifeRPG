import { useState, useEffect } from 'react';
import { getAIProviders, switchAIProvider, updateAIConfig, testAIConnection } from '../services/api';
import type { AIProvider, AIProvidersResponse } from '../services/api';
import './AISettings.css';

interface AISettingsProps {
  onClose: () => void;
}

export default function AISettings({ onClose }: AISettingsProps) {
  const [providers, setProviders] = useState<Record<string, AIProvider>>({});
  const [currentProvider, setCurrentProvider] = useState('ollama');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // 编辑状态
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    api_key: '',
    base_url: '',
    model: ''
  });

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const data: AIProvidersResponse = await getAIProviders();
      setProviders(data.providers);
      setCurrentProvider(data.current_provider);
    } catch (e) {
      console.error('加载AI配置失败:', e);
      setMessage({ type: 'error', text: '加载配置失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchProvider = async (providerName: string) => {
    try {
      setSaving(true);
      await switchAIProvider(providerName);
      setCurrentProvider(providerName);
      setMessage({ type: 'success', text: `已切换到 ${providers[providerName]?.name || providerName}` });
      setTimeout(() => setMessage(null), 3000);
    } catch (e) {
      console.error('切换失败:', e);
      setMessage({ type: 'error', text: '切换失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleEditProvider = (providerName: string) => {
    const provider = providers[providerName];
    setEditingProvider(providerName);
    setEditForm({
      api_key: '',
      base_url: provider?.base_url || '',
      model: provider?.model || ''
    });
  };

  const handleSaveConfig = async () => {
    if (!editingProvider) return;
    
    try {
      setSaving(true);
      const updates: Partial<AIProvider> = {};
      
      if (editForm.base_url) updates.base_url = editForm.base_url;
      if (editForm.model) updates.model = editForm.model;
      if (editForm.api_key) updates.api_key = editForm.api_key;
      
      await updateAIConfig(editingProvider, updates);
      setMessage({ type: 'success', text: '配置已保存' });
      setEditingProvider(null);
      loadProviders(); // 重新加载配置
      setTimeout(() => setMessage(null), 3000);
    } catch (e) {
      console.error('保存失败:', e);
      setMessage({ type: 'error', text: '保存失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async (providerName: string) => {
    try {
      setTesting(providerName);
      const result = await testAIConnection(providerName);
      if (result.connected) {
        setMessage({ type: 'success', text: `${providerName} 连接成功` });
      } else {
        setMessage({ type: 'error', text: `${providerName} 连接失败: ${result.error || '未知错误'}` });
      }
      setTimeout(() => setMessage(null), 5000);
    } catch (e) {
      console.error('测试失败:', e);
      setMessage({ type: 'error', text: '连接测试失败' });
    } finally {
      setTesting(null);
    }
  };

  const getProviderIcon = (providerName: string) => {
    const icons: Record<string, string> = {
      ollama: ' ',
      openai: ' ',
      claude: ' ',
      deepseek: ' ',
      mimo: ' ',
      custom: '⚙️'
    };
    return icons[providerName] || ' ';
  };

  if (loading) {
    return (
      <div className="ai-settings-overlay">
        <div className="ai-settings-modal">
          <div className="loading-spinner"></div>
          <p>加载AI配置...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="ai-settings-overlay">
      <div className="ai-settings-modal">
        <div className="ai-settings-header">
          <h2>⚙️ AI 设置</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        {message && (
          <div className={`ai-message ${message.type}`}>
            {message.text}
          </div>
        )}
        
        <div className="ai-providers-list">
          <h3>选择AI提供商</h3>
          <div className="providers-grid">
            {Object.entries(providers).map(([name, provider]) => (
              <div 
                key={name} 
                className={`provider-card ${currentProvider === name ? 'active' : ''}`}
                onClick={() => handleSwitchProvider(name)}
              >
                <div className="provider-icon">{getProviderIcon(name)}</div>
                <div className="provider-info">
                  <h4>{provider.name}</h4>
                  <p className="provider-model">{provider.model}</p>
                  {provider.api_key_set && (
                    <span className="api-key-badge">API Key 已设置</span>
                  )}
                </div>
                {currentProvider === name && (
                  <div className="active-badge">当前使用</div>
                )}
                <div className="provider-actions">
                  <button 
                    className="edit-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditProvider(name);
                    }}
                  >
                    配置
                  </button>
                  <button 
                    className="test-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTestConnection(name);
                    }}
                    disabled={testing === name}
                  >
                    {testing === name ? '测试中...' : '测试'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {editingProvider && (
          <div className="edit-modal">
            <h3>配置 {providers[editingProvider]?.name}</h3>
            <div className="edit-form">
              <div className="form-group">
                <label>API Base URL</label>
                <input
                  type="text"
                  value={editForm.base_url}
                  onChange={(e) => setEditForm({ ...editForm, base_url: e.target.value })}
                  placeholder="https://api.openai.com/v1"
                />
              </div>
              <div className="form-group">
                <label>模型名称</label>
                <input
                  type="text"
                  value={editForm.model}
                  onChange={(e) => setEditForm({ ...editForm, model: e.target.value })}
                  placeholder="gpt-3.5-turbo"
                />
              </div>
              <div className="form-group">
                <label>API Key</label>
                <input
                  type="password"
                  value={editForm.api_key}
                  onChange={(e) => setEditForm({ ...editForm, api_key: e.target.value })}
                  placeholder="sk-... (留空表示不修改)"
                />
                <small>留空表示不修改现有API Key</small>
              </div>
              <div className="form-actions">
                <button 
                  className="save-btn"
                  onClick={handleSaveConfig}
                  disabled={saving}
                >
                  {saving ? '保存中...' : '保存'}
                </button>
                <button 
                  className="cancel-btn"
                  onClick={() => setEditingProvider(null)}
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        )}
        
        <div className="ai-settings-footer">
          <p className="tip">
            💡 提示：切换AI提供商后，系统会自动使用新的AI进行活动分析和反馈生成。
          </p>
        </div>
      </div>
    </div>
  );
}