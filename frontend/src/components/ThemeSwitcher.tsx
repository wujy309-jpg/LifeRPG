import { useState, useEffect } from 'react';
import './ThemeSwitcher.css';

type Theme = 'dark' | 'light' | 'pixel';

interface ThemeSwitcherProps {
  onClose: () => void;
}

export default function ThemeSwitcher({ onClose }: ThemeSwitcherProps) {
  const [currentTheme, setCurrentTheme] = useState<Theme>(() => {
    return (localStorage.getItem('liferpg_theme') as Theme) || 'dark';
  });

  useEffect(() => {
    applyTheme(currentTheme);
  }, [currentTheme]);

  const applyTheme = (theme: Theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('liferpg_theme', theme);
  };

  const handleThemeChange = (theme: Theme) => {
    setCurrentTheme(theme);
  };

  const themes = [
    {
      id: 'dark' as Theme,
      name: '暗黑风格',
      description: '经典RPG暗黑主题',
      icon: ' ',
      preview: 'linear-gradient(135deg, #0a0a0f, #1a1a24)'
    },
    {
      id: 'light' as Theme,
      name: '明亮风格',
      description: '清爽明亮主题',
      icon: '☀️',
      preview: 'linear-gradient(135deg, #f5f5f5, #ffffff)'
    },
    {
      id: 'pixel' as Theme,
      name: '像素风格',
      description: '复古像素游戏主题',
      icon: ' ',
      preview: 'linear-gradient(135deg, #1a1a2e, #16213e)'
    }
  ];

  return (
    <div className="theme-switcher-overlay">
      <div className="theme-switcher-modal">
        <div className="modal-header">
          <h2>  主题设置</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-content">
          <p className="theme-hint">选择你喜欢的主题风格</p>
          
          <div className="theme-grid">
            {themes.map(theme => (
              <div
                key={theme.id}
                className={`theme-card ${currentTheme === theme.id ? 'active' : ''}`}
                onClick={() => handleThemeChange(theme.id)}
              >
                <div className="theme-preview" style={{ background: theme.preview }}>
                  <span className="theme-icon">{theme.icon}</span>
                </div>
                <div className="theme-info">
                  <h3>{theme.name}</h3>
                  <p>{theme.description}</p>
                </div>
                {currentTheme === theme.id && (
                  <div className="active-badge">当前使用</div>
                )}
              </div>
            ))}
          </div>

          <div className="theme-footer">
            <p className="theme-note">主题设置会自动保存到本地</p>
          </div>
        </div>
      </div>
    </div>
  );
}