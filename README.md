# LifeRPG - 生活游戏化系统

把你的日常生活变成一场RPG冒险！记录活动获得经验值、金币、装备和称号。

## 功能特色

-   **经验值系统** - 记录活动获得EXP，升级解锁新头衔
-   **金币奖励** - 完成任务赚取金币
-   **五维属性** - 力量/智力/敏捷/魅力/意志
-   **装备收集** - AI生成创意装备（普通/稀有/史诗/传说）
-   **趣味称号** - 如"凌晨两点还在Debug的人"
-   **每日任务** - AI智能生成个性化任务
-   **AI评价** - 幽默的活动反馈
-  ️ **多AI支持** - 支持Ollama、OpenAI、Claude、DeepSeek等多种AI提供商

## 快速开始

### 前置要求

1. **Python 3.8+**
2. **Node.js 18+**
3. **AI服务**（任选其一）：
   - **Ollama**（本地运行，免费）
   - **OpenAI API**（需要API Key）
   - **Claude API**（需要API Key）
   - **DeepSeek API**（需要API Key）

### 安装步骤

1. 克隆或下载项目
2. 运行安装脚本：
   ```bash
   install.bat
   ```

### 启动系统

```bash
start.bat
```

访问 http://localhost:8000

## AI配置指南

### 方式一：使用Ollama（本地，免费）

1. 安装Ollama：
   ```bash
   # Windows
   winget install Ollama.Ollama
   
   # 或访问 https://ollama.ai 下载
   ```

2. 安装模型：
   ```bash
   ollama pull qwen2.5:7b
   ```

3. 启动系统后，在"AI 设置"中选择"Ollama (本地)"

### 方式二：使用OpenAI API

1. 获取API Key：访问 https://platform.openai.com/api-keys
2. 启动系统后，点击侧边栏的"⚙️ AI 设置"
3. 选择"OpenAI"，点击"配置"
4. 输入你的API Key和模型名称（如 `gpt-3.5-turbo`）
5. 点击"保存"并"测试"连接

### 方式三：使用Claude API

1. 获取API Key：访问 https://console.anthropic.com/
2. 在"AI 设置"中选择"Claude"
3. 输入API Key和模型名称（如 `claude-3-sonnet-20240229`）

### 方式四：使用DeepSeek API

1. 获取API Key：访问 https://platform.deepseek.com/
2. 在"AI 设置"中选择"DeepSeek"
3. 输入API Key（DeepSeek使用OpenAI兼容接口）

### 方式五：自定义AI提供商

支持任何OpenAI兼容的API接口：
1. 在"AI 设置"中选择"自定义"
2. 输入API Base URL、模型名称和API Key

## 手动启动

### 后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 前端开发模式

```bash
cd frontend
npm install
npm run dev
```

## 技术栈

- **后端**: Python + FastAPI + SQLite
- **前端**: React + TypeScript + Vite
- **AI**: 支持多种AI提供商（Ollama/OpenAI/Claude/DeepSeek）

## API 文档

启动后访问 http://localhost:8000/docs

## 项目结构

```
LifeRPG/
├── backend/
│   ├── main.py          # FastAPI 主程序
│   ├── database.py      # 数据库操作
│   ├── game_engine.py   # 游戏逻辑引擎
│   ├── ai_service.py    # AI服务（支持多提供商）
│   ├── config.json      # AI配置文件
│   ├── models.py        # 数据模型
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ActivityLog.tsx
│   │   │   ├── CharacterSheet.tsx
│   │   │   ├── Inventory.tsx
│   │   │   ├── QuestBoard.tsx
│   │   │   └── AISettings.tsx  # AI设置界面
│   │   └── services/api.ts
│   └── package.json
├── install.bat
└── start.bat
```

## AI配置文件说明

`backend/config.json` 文件结构：

```json
{
  "ai_provider": "ollama",  // 当前使用的AI提供商
  "providers": {
    "ollama": {
      "name": "Ollama (本地)",
      "base_url": "http://localhost:11434",
      "model": "qwen2.5:7b",
      "api_key": null
    },
    "openai": {
      "name": "OpenAI",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-3.5-turbo",
      "api_key": "sk-..."
    }
  }
}
```

## 常见问题

### Q: 如何切换AI提供商？
A: 点击侧边栏的"⚙️ AI 设置"按钮，选择你想要的AI提供商，点击"配置"输入API Key，然后点击"测试"验证连接。

### Q: AI响应很慢怎么办？
A: 
- 本地Ollama：尝试使用更小的模型（如 `qwen2.5:7b`）
- 云端API：检查网络连接，或尝试其他AI提供商

### Q: 如何获取API Key？
A: 
- OpenAI: https://platform.openai.com/api-keys
- Claude: https://console.anthropic.com/
- DeepSeek: https://platform.deepseek.com/

### Q: 可以同时使用多个AI吗？
A: 目前只能同时使用一个AI提供商，但你可以随时在设置中切换。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.2.0 (2026-05-29)
- 新增多AI提供商支持（OpenAI、Claude、DeepSeek）
- 新增AI设置界面，支持一键切换AI
- 新增API Key管理功能
- 新增连接测试功能

### v1.1.0 (2026-05-28)
- 新增属性成长曲线系统（对数衰减模型）
- 新增升级特效动画
- 新增属性变化动画
- 优化雷达图动画效果

### v1.0.0 (2026-05-28)
- 初始版本发布
- 五维属性系统
- 经验值与等级系统
- 装备与称号系统
- 任务系统