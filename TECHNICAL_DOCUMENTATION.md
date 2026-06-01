# LifeRPG 技术文档

## 项目概述

LifeRPG 是一个生活游戏化系统，将用户的日常活动转化为RPG游戏体验。通过记录活动获得经验值、金币、装备和称号，激励用户建立健康的生活习惯。

### 核心特性
- **五维属性系统**：力量、智力、敏捷、魅力、意志
- **经验值与等级**：基于指数增长模型的升级系统
- **装备系统**：60+种贴近现实的物品，支持稀有度分级
- **任务系统**：每日、每周、挑战、成就四类任务
- **AI集成**：支持多种AI提供商（Ollama、OpenAI、Claude、DeepSeek）
- **现实商城**：金币兑换现实奖励、习惯挑战、免罪金牌

## 技术架构

### 整体架构
```
┌────────────────-frontend (React + TypeScript)────────────────┐
│                    ↕ HTTP/REST API                           │
└────────────────backend (Python + FastAPI)────────────────────┘
                    ↕ SQLite + JSON配置
              ┌─────────────────┐
              │   数据存储层     │
              └─────────────────┘
```

### 技术栈

#### 后端
- **Python 3.8+**
- **FastAPI 0.109.0**：高性能异步Web框架
- **SQLite**：轻量级关系数据库
- **Pydantic 2.5.3**：数据验证和序列化
- **Uvicorn 0.27.0**：ASGI服务器
- **HTTPX 0.26.0**：异步HTTP客户端（用于AI API调用）

#### 前端
- **React 19.2.6**：用户界面库
- **TypeScript 6.0.2**：类型安全的JavaScript超集
- **Vite 8.0.12**：下一代前端构建工具
- **React Router 7.15.1**：客户端路由
- **Axios 1.16.1**：HTTP客户端

#### AI集成
- **多提供商支持**：Ollama、OpenAI、Claude、DeepSeek、自定义
- **异步处理**：支持30秒超时降级到本地逻辑
- **智能分析**：AI自动判断活动类型和属性变化

## 系统设计

### 1. 数据库设计

#### 核心表结构

**characters（角色表）**
```sql
CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    level INTEGER DEFAULT 1,
    exp INTEGER DEFAULT 0,
    gold INTEGER DEFAULT 0,
    strength INTEGER DEFAULT 10,
    intelligence INTEGER DEFAULT 10,
    agility INTEGER DEFAULT 10,
    charisma INTEGER DEFAULT 10,
    willpower INTEGER DEFAULT 10,
    gender TEXT DEFAULT '',
    age INTEGER DEFAULT 0,
    height REAL DEFAULT 0,
    weight REAL DEFAULT 0,
    education TEXT DEFAULT '',
    occupation TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**activity_logs（活动日志表）**
```sql
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    description TEXT,
    exp_gained INTEGER DEFAULT 0,
    gold_gained INTEGER DEFAULT 0,
    attribute_changes TEXT DEFAULT '{}',
    ai_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id)
);
```

**equipment（装备表）**
```sql
CREATE TABLE equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    rarity TEXT DEFAULT '普通',
    stat_bonuses TEXT DEFAULT '{}',
    special_effect TEXT,
    use_desc TEXT DEFAULT '使用物品',
    use_effect TEXT DEFAULT '感觉不错',
    use_bonus TEXT DEFAULT '{}',
    equipped BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id)
);
```

**titles（称号表）**
```sql
CREATE TABLE titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    unlock_condition TEXT,
    equipped BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id)
);
```

**quests（任务表）**
```sql
CREATE TABLE quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    quest_type TEXT DEFAULT 'daily',
    exp_reward INTEGER DEFAULT 0,
    gold_reward INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    due_date DATE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id)
);
```

**check_ins（签到表）**
```sql
CREATE TABLE check_ins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    check_in_date DATE NOT NULL,
    consecutive_days INTEGER DEFAULT 1,
    reward_exp INTEGER DEFAULT 0,
    reward_gold INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id),
    UNIQUE(character_id, check_in_date)
);
```

**activity_templates（活动模板表）**
```sql
CREATE TABLE activity_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    activity_type TEXT,
    use_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id)
);
```

### 2. 游戏引擎设计

#### 属性系统
- **五维属性**：力量、智力、敏捷、魅力、意志
- **属性范围**：1-100（硬上限）
- **初始值**：50（基础值）+ 个人信息调整
- **成长曲线**：对数衰减模型，属性越高提升越难

#### 经验值系统
```python
def exp_for_level(level: int) -> int:
    return int(100 * (1.5 ** (level - 1)))

def check_level_up(exp: int, level: int) -> tuple[int, int]:
    while exp >= exp_for_level(level):
        exp -= exp_for_level(level)
        level += 1
    return level, exp
```

#### 活动分类
- **学习**：智力为主，意志为辅
- **运动**：力量为主，敏捷为辅
- **编程**：智力为主，意志为辅
- **社交**：魅力为主
- **工作**：意志为主，智力为辅
- **创作**：智力为主，魅力为辅
- **生活**：意志为主
- **休息**：意志为主

#### 装备系统
- **稀有度**：普通（50%）、稀有（30%）、史诗（15%）、传说（5%）
- **属性加成**：+1~15（根据稀有度）
- **使用效果**：消耗装备获得临时属性提升

### 3. AI服务设计

#### 多提供商架构
```python
PROVIDERS = {
    "ollama": {
        "name": "Ollama (本地)",
        "base_url": "http://localhost:11434",
        "model": "gemma4:latest"
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo"
    },
    "claude": {
        "name": "Claude",
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-3-sonnet-20240229"
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat"
    }
}
```

#### AI响应处理
1. **超时处理**：30秒超时自动降级到本地逻辑
2. **错误处理**：AI失败时使用本地分类和计算
3. **智能分析**：AI自动判断活动类型、属性变化、装备生成

## API文档

### 角色API

#### 获取所有角色
```
GET /api/characters
```
**响应**：
```json
{
    "characters": [...],
    "count": 3,
    "max_count": 3
}
```

#### 创建角色
```
POST /api/character
```
**请求体**：
```json
{
    "name": "角色名",
    "gender": "男",
    "age": 25,
    "height": 175.5,
    "weight": 70.0,
    "education": "本科",
    "occupation": "程序员"
}
```

#### 获取角色详情
```
GET /api/character/{character_id}
```

#### 获取角色完整信息
```
GET /api/character/{character_id}/full
```
**响应**：
```json
{
    "character": {...},
    "equipment": [...],
    "titles": [...],
    "active_quests": [...],
    "recent_activities": [...],
    "next_level_exp": 150,
    "level_title": "初级勇者"
}
```

### 活动API

#### 记录活动
```
POST /api/activity/{character_id}
```
**请求体**：
```json
{
    "description": "跑步30分钟",
    "activity_type": "运动"  // 可选，AI自动判断
}
```
**响应**：
```json
{
    "activity_log": {...},
    "character": {...},
    "level_up": false,
    "new_level": null,
    "equipment_found": {...},
    "title_earned": {...},
    "quest_generated": {...},
    "ai_comment": "你这运动量，连你家狗都自愧不如了"
}
```

#### 获取活动记录
```
GET /api/activities/{character_id}?limit=20
```

### 装备API

#### 获取装备列表
```
GET /api/equipment/{character_id}
```

#### 使用装备
```
POST /api/equipment/{equipment_id}/use
```

### 任务API

#### 获取任务列表
```
GET /api/quests/{character_id}?status=active
```

#### 获取所有类型任务
```
GET /api/quests/{character_id}/all
```

#### 完成任务
```
POST /api/quests/{quest_id}/complete
```

### 签到API

#### 每日签到
```
POST /api/checkin/{character_id}
```

#### 获取签到状态
```
GET /api/checkin/status/{character_id}
```

### 活动模板API

#### 获取模板列表
```
GET /api/templates/{character_id}
```

#### 添加模板
```
POST /api/templates/{character_id}
```
**请求体**：
```json
{
    "name": "晨跑",
    "description": "早上跑步30分钟",
    "activity_type": "运动"
}
```

#### 使用模板
```
POST /api/templates/use/{template_id}
```

### 现实商城API

#### 获取现实奖励
```
GET /api/reality/rewards/{character_id}
```

#### 兑换奖励
```
POST /api/reality/rewards/{character_id}/redeem/{reward_id}
```

#### 获取习惯挑战
```
GET /api/reality/challenges/{character_id}
```

#### 创建习惯挑战
```
POST /api/reality/challenges/{character_id}/create
```

#### 习惯挑战打卡
```
POST /api/reality/challenges/{challenge_id}/checkin/{character_id}
```

#### 获取免罪金牌
```
GET /api/reality/cards/{character_id}
```

#### 购买免罪金牌
```
POST /api/reality/cards/{character_id}/buy
```

### AI配置API

#### 获取AI提供商配置
```
GET /api/ai/providers
```

#### 切换AI提供商
```
POST /api/ai/switch/{provider_name}
```

#### 更新AI配置
```
POST /api/ai/config/{provider_name}
```
**请求体**：
```json
{
    "api_key": "sk-...",
    "model": "gpt-4",
    "base_url": "https://api.openai.com/v1"
}
```

#### 测试AI连接
```
POST /api/ai/test/{provider_name}
```

### 统计API

#### 获取角色统计
```
GET /api/stats/{character_id}
```

#### 获取活动历史
```
GET /api/stats/{character_id}/history?days=30
```

#### 获取属性变化历史
```
GET /api/stats/{character_id}/attributes?days=30
```

### 数据导出API

#### 导出数据
```
GET /api/export/{character_id}?format=json
```
支持格式：`json`、`csv`

## 前端架构

### 组件结构
```
src/
├── App.tsx              # 主应用组件
├── Stats.tsx            # 数据统计页
├── components/
│   ├── Dashboard.tsx        # 仪表盘
│   ├── ActivityLog.tsx      # 活动记录
│   ├── ActivityTemplates.tsx # 活动模板
│   ├── CharacterSheet.tsx   # 角色属性
│   ├── Inventory.tsx        # 装备背包
│   ├── QuestBoard.tsx       # 任务板
│   ├── CharacterManager.tsx # 角色管理
│   ├── AISettings.tsx       # AI设置
│   ├── RealityShop.tsx      # 现实商城
│   ├── DailyCheckIn.tsx     # 每日签到
│   ├── DataExport.tsx       # 数据导出
│   ├── GameIcons.tsx        # RPG图标
│   ├── PixelCharacter.tsx   # 像素角色
│   ├── RadarChart.tsx       # 雷达图
│   ├── Calendar.tsx         # 日历
│   ├── ThemeSwitcher.tsx    # 主题切换
│   └── TimeDisplay.tsx      # 时间显示
├── services/
│   └── api.ts           # API服务层
└── utils/
    └── ...              # 工具函数
```

### 状态管理
- **本地状态**：使用React useState管理组件状态
- **API调用**：使用Axios进行HTTP请求
- **路由管理**：使用React Router进行页面导航

### UI设计
- **RPG风格**：像素风格图标和边框
- **响应式设计**：适配不同屏幕尺寸
- **动画效果**：升级特效、属性变化动画、雷达图动画

## 部署指南

### 环境要求
- **Python 3.8+**
- **Node.js 18+**
- **AI服务**（可选）：Ollama、OpenAI API、Claude API、DeepSeek API

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/wujy309-jpg/LifeRPG.git
cd LifeRPG
```

2. **配置AI服务**
```bash
copy backend\config.example.json backend\config.json
# 编辑 config.json 配置AI提供商
```

3. **运行安装脚本**
```bash
install.bat
```

4. **启动系统**
```bash
start.bat
```

### 手动启动

#### 后端
```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### 前端
```bash
cd frontend
npm install
npm run dev
```

### 生产环境部署

#### 构建前端
```bash
cd frontend
npm run build
```

#### 启动后端
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 查看应用。

## 配置说明

### AI配置文件 (backend/config.json)
```json
{
    "ai_provider": "ollama",
    "providers": {
        "ollama": {
            "name": "Ollama (本地)",
            "base_url": "http://localhost:11434",
            "model": "gemma4:latest",
            "api_key": null
        },
        "openai": {
            "name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo",
            "api_key": "sk-your-api-key"
        }
    }
}
```

### 游戏配置

#### 属性配置
- **初始属性**：50（基础值）
- **属性上限**：100
- **软上限**：75（超过后提升速度减半）

#### 经验值公式
```python
EXP(n) = 100 × 1.5^(n-1)
```

#### 属性成长曲线
| 属性区间 | 提升概率 | 最大提升 |
|----------|----------|----------|
| 40-55    | 80%      | +3       |
| 56-65    | 60%      | +2       |
| 66-75    | 40%      | +2       |
| 76-85    | 30%      | +1       |
| 86-95    | 20%      | +1       |
| 96-100   | 10%      | +1       |

## 测试

### 运行测试
```bash
# 后端测试
python test.py
python test_activity.py
python test_rules.py

# 前端测试
cd frontend
npm run lint
```

### 测试覆盖
- **单元测试**：游戏引擎核心逻辑
- **集成测试**：API端点功能
- **端到端测试**：用户流程验证

## 性能优化

### 后端优化
- **数据库索引**：为常用查询字段添加索引
- **连接池**：使用SQLite连接池
- **异步处理**：AI调用使用异步IO
- **缓存**：静态数据缓存

### 前端优化
- **代码分割**：使用React.lazy进行路由级代码分割
- **图片优化**：压缩和懒加载图片
- **缓存策略**：合理设置HTTP缓存头
- **打包优化**：使用Vite进行生产环境优化

## 安全考虑

### 数据安全
- **输入验证**：使用Pydantic进行严格的数据验证
- **SQL注入防护**：使用参数化查询
- **XSS防护**：React自动转义HTML
- **CORS配置**：限制允许的源

### API安全
- **API密钥管理**：API密钥加密存储
- **速率限制**：防止API滥用
- **错误处理**：不暴露敏感信息

## 监控与日志

### 日志记录
- **访问日志**：记录API请求
- **错误日志**：记录异常和错误
- **性能日志**：记录响应时间

### 监控指标
- **系统状态**：CPU、内存、磁盘使用率
- **API性能**：响应时间、错误率
- **用户行为**：活动记录频率、任务完成率

## 扩展性

### 水平扩展
- **负载均衡**：使用Nginx进行负载均衡
- **数据库分片**：按用户ID分片
- **缓存层**：添加Redis缓存层

### 功能扩展
- **插件系统**：支持自定义插件
- **API版本控制**：支持多版本API
- **国际化**：支持多语言

## 故障排除

### 常见问题

#### AI响应慢
- 检查AI服务状态
- 调整超时时间
- 使用更小的模型

#### 数据库锁定
- 检查并发连接数
- 优化查询语句
- 使用WAL模式

#### 前端构建失败
- 清除node_modules重新安装
- 检查Node.js版本
- 更新依赖包

## 更新日志

### v1.6.0 (2026-06-01)
- 新增每日签到系统
- 新增活动模板功能
- 新增数据统计页面
- 新增数据导出功能
- 新增日历组件
- 新增主题切换功能
- 修复任务完成按钮BUG
- 优化角色属性展示
- 优化像素角色动画

### v1.5.0 (2026-05-30)
- 新增现实商城系统
- 新增活动反馈弹窗
- 新增AI幽默评论功能

### v1.4.0 (2026-05-29)
- 新增任务多样性
- 任务界面新增标签页切换
- 新增任务类型颜色标识

### v1.3.0 (2026-05-29)
- 新增角色管理系统
- 新增个人信息系统
- 新增装备使用效果
- 新增智能属性分析

### v1.2.0 (2026-05-29)
- 新增多AI提供商支持
- 新增AI设置界面
- 新增API Key管理功能

### v1.1.0 (2026-05-28)
- 新增属性成长曲线系统
- 新增升级特效动画
- 新增属性变化动画

### v1.0.0 (2026-05-28)
- 初始版本发布
- 五维属性系统
- 经验值与等级系统
- 装备与称号系统
- 任务系统

## 贡献指南

### 开发流程
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

### 代码规范
- **Python**：遵循PEP 8规范
- **TypeScript**：使用ESLint进行代码检查
- **Git**：使用语义化提交信息

### 测试要求
- 新功能必须包含测试
- 修复BUG必须包含回归测试
- 保持测试覆盖率

## 许可证

MIT License

## 联系方式

- **GitHub**：https://github.com/wujy309-jpg/LifeRPG
- **问题反馈**：GitHub Issues

---

*本文档由 LifeRPG 开发团队维护，最后更新：2026-06-01*