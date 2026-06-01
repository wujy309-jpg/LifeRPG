import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime, timedelta, date

DB_PATH = "liferpg.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_agent_tables():
    """初始化智能体相关表"""
    with get_db() as conn:
        conn.executescript("""
            -- 用户画像表
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL UNIQUE,
                personality TEXT DEFAULT '{}',  -- 性格特征
                habits TEXT DEFAULT '{}',  -- 习惯模式
                preferences TEXT DEFAULT '{}',  -- 偏好设置
                activity_patterns TEXT DEFAULT '{}',  -- 活动模式
                peak_hours TEXT DEFAULT '[]',  -- 高效时段
                weakness TEXT DEFAULT '[]',  -- 弱项属性
                strength TEXT DEFAULT '[]',  -- 强项属性
                motivation_style TEXT DEFAULT 'balanced',  -- 激励风格
                last_active TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 行为记忆表
            CREATE TABLE IF NOT EXISTS behavior_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                memory_type TEXT NOT NULL,  -- episodic(事件)/semantic(知识)/procedural(程序)
                content TEXT NOT NULL,  -- 记忆内容
                context TEXT DEFAULT '{}',  -- 上下文信息
                importance REAL DEFAULT 0.5,  -- 重要性(0-1)
                emotion TEXT DEFAULT 'neutral',  -- 情绪标签
                related_activity TEXT,  -- 关联活动
                access_count INTEGER DEFAULT 0,  -- 访问次数
                last_accessed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 对话历史表
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,  -- 会话ID
                role TEXT NOT NULL,  -- user/assistant/system
                content TEXT NOT NULL,  -- 消息内容
                intent TEXT,  -- 意图识别
                emotion TEXT,  -- 情绪状态
                context TEXT DEFAULT '{}',  -- 上下文
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 长期目标表
            CREATE TABLE IF NOT EXISTS long_term_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                goal_type TEXT DEFAULT 'general',  -- fitness/learning/habit/general
                target_value REAL,  -- 目标值
                current_value REAL DEFAULT 0,  -- 当前值
                unit TEXT DEFAULT '',  -- 单位
                deadline DATE,  -- 截止日期
                milestones TEXT DEFAULT '[]',  -- 里程碑
                status TEXT DEFAULT 'active',  -- active/completed/abandoned
                progress REAL DEFAULT 0,  -- 进度(0-1)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 任务计划表
            CREATE TABLE IF NOT EXISTS task_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                goal_id INTEGER,  -- 关联目标
                title TEXT NOT NULL,
                description TEXT,
                task_type TEXT DEFAULT 'daily',  -- daily/weekly/one-time
                priority INTEGER DEFAULT 5,  -- 优先级(1-10)
                scheduled_date DATE,
                scheduled_time TEXT,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                recurrence TEXT DEFAULT '{}',  -- 重复规则
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id),
                FOREIGN KEY (goal_id) REFERENCES long_term_goals(id)
            );
            
            -- 推送通知表
            CREATE TABLE IF NOT EXISTS push_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,  -- reminder/encouragement/warning/suggestion
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                priority INTEGER DEFAULT 5,  -- 优先级(1-10)
                scheduled_time TIMESTAMP,
                sent BOOLEAN DEFAULT 0,
                sent_at TIMESTAMP,
                read BOOLEAN DEFAULT 0,
                read_at TIMESTAMP,
                action_url TEXT,  -- 点击跳转
                context TEXT DEFAULT '{}',  -- 上下文
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 情绪记录表
            CREATE TABLE IF NOT EXISTS emotion_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                emotion TEXT NOT NULL,  -- happy/sad/angry/anxious/excited/neutral
                intensity REAL DEFAULT 0.5,  -- 强度(0-1)
                trigger TEXT,  -- 触发因素
                activity_context TEXT,  -- 活动上下文
                detected_from TEXT DEFAULT 'text',  -- 检测来源(text/activity/time)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 工具调用记录表
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                tool_name TEXT NOT NULL,  -- 工具名称
                input_params TEXT DEFAULT '{}',  -- 输入参数
                output_result TEXT,  -- 输出结果
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                execution_time REAL,  -- 执行时间(秒)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 决策日志表
            CREATE TABLE IF NOT EXISTS decision_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                decision_type TEXT NOT NULL,  -- suggestion/reminder/plan/feedback
                context TEXT DEFAULT '{}',  -- 决策上下文
                options TEXT DEFAULT '[]',  -- 可选方案
                chosen_option TEXT,  -- 选择的方案
                reasoning TEXT,  -- 决策理由
                outcome TEXT,  -- 结果反馈
                confidence REAL DEFAULT 0.5,  -- 置信度(0-1)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 智能体配置表
            CREATE TABLE IF NOT EXISTS agent_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL UNIQUE,
                proactive_enabled BOOLEAN DEFAULT 1,  -- 主动推送开关
                notification_preferences TEXT DEFAULT '{}',  -- 通知偏好
                interaction_style TEXT DEFAULT 'balanced',  -- 交互风格
                autonomy_level TEXT DEFAULT 'medium',  -- 自主程度(low/medium/high)
                learning_enabled BOOLEAN DEFAULT 1,  -- 学习开关
                privacy_level TEXT DEFAULT 'normal',  -- 隐私级别
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            -- 创建索引
            CREATE INDEX IF NOT EXISTS idx_behavior_memories_character 
                ON behavior_memories(character_id);
            CREATE INDEX IF NOT EXISTS idx_conversation_history_character 
                ON conversation_history(character_id);
            CREATE INDEX IF NOT EXISTS idx_conversation_history_session 
                ON conversation_history(session_id);
            CREATE INDEX IF NOT EXISTS idx_push_notifications_character 
                ON push_notifications(character_id);
            CREATE INDEX IF NOT EXISTS idx_emotion_logs_character 
                ON emotion_logs(character_id);
            CREATE INDEX IF NOT EXISTS idx_long_term_goals_character 
                ON long_term_goals(character_id);
            CREATE INDEX IF NOT EXISTS idx_task_plans_character 
                ON task_plans(character_id);
        """)
        
        print("智能体数据库表初始化完成")


# ==================== 用户画像操作 ====================

def get_or_create_user_profile(character_id: int) -> dict:
    """获取或创建用户画像"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM user_profiles WHERE character_id = ?",
            (character_id,)
        ).fetchone()
        
        if row:
            return dict(row)
        
        # 创建新的用户画像
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """INSERT INTO user_profiles (character_id, created_at, updated_at)
               VALUES (?, ?, ?)""",
            (character_id, now, now)
        )
        row = conn.execute(
            "SELECT * FROM user_profiles WHERE character_id = ?",
            (character_id,)
        ).fetchone()
        return dict(row)


def update_user_profile(character_id: int, **kwargs) -> dict:
    """更新用户画像"""
    with get_db() as conn:
        kwargs['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [character_id]
        conn.execute(
            f"UPDATE user_profiles SET {set_clause} WHERE character_id = ?",
            values
        )
        return get_or_create_user_profile(character_id)


# ==================== 行为记忆操作 ====================

def add_behavior_memory(character_id: int, memory_type: str, content: str,
                       context: dict = None, importance: float = 0.5,
                       emotion: str = 'neutral', related_activity: str = None) -> dict:
    """添加行为记忆"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO behavior_memories 
               (character_id, memory_type, content, context, importance, 
                emotion, related_activity, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, memory_type, content, 
             json.dumps(context or {}), importance, emotion, related_activity, now)
        )
        return {"id": cursor.lastrowid, "character_id": character_id, "content": content}


def get_behavior_memories(character_id: int, memory_type: str = None, 
                         limit: int = 50) -> list:
    """获取行为记忆"""
    with get_db() as conn:
        if memory_type:
            rows = conn.execute(
                """SELECT * FROM behavior_memories 
                   WHERE character_id = ? AND memory_type = ?
                   ORDER BY importance DESC, created_at DESC LIMIT ?""",
                (character_id, memory_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM behavior_memories 
                   WHERE character_id = ?
                   ORDER BY importance DESC, created_at DESC LIMIT ?""",
                (character_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]


def search_memories(character_id: int, query: str, limit: int = 10) -> list:
    """搜索记忆"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM behavior_memories 
               WHERE character_id = ? AND content LIKE ?
               ORDER BY importance DESC, created_at DESC LIMIT ?""",
            (character_id, f"%{query}%", limit)
        ).fetchall()
        return [dict(r) for r in rows]


def update_memory_access(memory_id: int):
    """更新记忆访问次数"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """UPDATE behavior_memories 
               SET access_count = access_count + 1, last_accessed = ?
               WHERE id = ?""",
            (now, memory_id)
        )


# ==================== 对话历史操作 ====================

def add_conversation(character_id: int, session_id: str, role: str, 
                    content: str, intent: str = None, emotion: str = None,
                    context: dict = None) -> dict:
    """添加对话记录"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO conversation_history 
               (character_id, session_id, role, content, intent, emotion, context, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, session_id, role, content, intent, emotion,
             json.dumps(context or {}), now)
        )
        return {"id": cursor.lastrowid, "character_id": character_id, "role": role}


def get_conversation_history(character_id: int, session_id: str = None,
                            limit: int = 50) -> list:
    """获取对话历史"""
    with get_db() as conn:
        if session_id:
            rows = conn.execute(
                """SELECT * FROM conversation_history 
                   WHERE character_id = ? AND session_id = ?
                   ORDER BY created_at ASC LIMIT ?""",
                (character_id, session_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM conversation_history 
                   WHERE character_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (character_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]


def get_recent_conversations(character_id: int, hours: int = 24) -> list:
    """获取最近的对话"""
    with get_db() as conn:
        cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute(
            """SELECT * FROM conversation_history 
               WHERE character_id = ? AND created_at >= ?
               ORDER BY created_at ASC""",
            (character_id, cutoff)
        ).fetchall()
        return [dict(r) for r in rows]


# ==================== 长期目标操作 ====================

def create_long_term_goal(character_id: int, title: str, description: str = "",
                         goal_type: str = "general", target_value: float = None,
                         unit: str = "", deadline: str = None) -> dict:
    """创建长期目标"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO long_term_goals 
               (character_id, title, description, goal_type, target_value, 
                unit, deadline, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, title, description, goal_type, target_value,
             unit, deadline, now, now)
        )
        goal_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM long_term_goals WHERE id = ?",
            (goal_id,)
        ).fetchone()
        return dict(row)


def get_long_term_goals(character_id: int, status: str = "active") -> list:
    """获取长期目标"""
    with get_db() as conn:
        if status:
            rows = conn.execute(
                """SELECT * FROM long_term_goals 
                   WHERE character_id = ? AND status = ?
                   ORDER BY created_at DESC""",
                (character_id, status)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM long_term_goals 
                   WHERE character_id = ?
                   ORDER BY created_at DESC""",
                (character_id,)
            ).fetchall()
        return [dict(r) for r in rows]


def update_goal_progress(goal_id: int, current_value: float, progress: float) -> dict:
    """更新目标进度"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "completed" if progress >= 1.0 else "active"
        conn.execute(
            """UPDATE long_term_goals 
               SET current_value = ?, progress = ?, status = ?, updated_at = ?
               WHERE id = ?""",
            (current_value, progress, status, now, goal_id)
        )
        row = conn.execute(
            "SELECT * FROM long_term_goals WHERE id = ?",
            (goal_id,)
        ).fetchone()
        return dict(row)


# ==================== 任务计划操作 ====================

def create_task_plan(character_id: int, title: str, description: str = "",
                    goal_id: int = None, task_type: str = "daily",
                    priority: int = 5, scheduled_date: str = None,
                    scheduled_time: str = None, recurrence: dict = None) -> dict:
    """创建任务计划"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO task_plans 
               (character_id, goal_id, title, description, task_type, 
                priority, scheduled_date, scheduled_time, recurrence, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, goal_id, title, description, task_type,
             priority, scheduled_date, scheduled_time, 
             json.dumps(recurrence or {}), now)
        )
        task_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM task_plans WHERE id = ?",
            (task_id,)
        ).fetchone()
        return dict(row)


def get_task_plans(character_id: int, date: str = None, completed: bool = None) -> list:
    """获取任务计划"""
    with get_db() as conn:
        query = "SELECT * FROM task_plans WHERE character_id = ?"
        params = [character_id]
        
        if date:
            query += " AND scheduled_date = ?"
            params.append(date)
        
        if completed is not None:
            query += " AND completed = ?"
            params.append(1 if completed else 0)
        
        query += " ORDER BY priority DESC, scheduled_time ASC"
        
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def complete_task_plan(task_id: int) -> dict:
    """完成任务计划"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """UPDATE task_plans 
               SET completed = 1, completed_at = ?
               WHERE id = ?""",
            (now, task_id)
        )
        row = conn.execute(
            "SELECT * FROM task_plans WHERE id = ?",
            (task_id,)
        ).fetchone()
        return dict(row)


# ==================== 推送通知操作 ====================

def create_notification(character_id: int, notification_type: str, title: str,
                       content: str, priority: int = 5, scheduled_time: str = None,
                       action_url: str = None, context: dict = None) -> dict:
    """创建推送通知"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO push_notifications 
               (character_id, notification_type, title, content, priority,
                scheduled_time, action_url, context, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, notification_type, title, content, priority,
             scheduled_time or now, action_url, json.dumps(context or {}), now)
        )
        notification_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM push_notifications WHERE id = ?",
            (notification_id,)
        ).fetchone()
        return dict(row)


def get_pending_notifications(character_id: int) -> list:
    """获取待发送的通知"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute(
            """SELECT * FROM push_notifications 
               WHERE character_id = ? AND sent = 0 AND scheduled_time <= ?
               ORDER BY priority DESC, scheduled_time ASC""",
            (character_id, now)
        ).fetchall()
        return [dict(r) for r in rows]


def mark_notification_sent(notification_id: int):
    """标记通知已发送"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE push_notifications SET sent = 1, sent_at = ? WHERE id = ?",
            (now, notification_id)
        )


def mark_notification_read(notification_id: int):
    """标记通知已读"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE push_notifications SET read = 1, read_at = ? WHERE id = ?",
            (now, notification_id)
        )


def get_unread_notifications(character_id: int, limit: int = 20) -> list:
    """获取未读通知"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM push_notifications 
               WHERE character_id = ? AND read = 0 AND sent = 1
               ORDER BY created_at DESC LIMIT ?""",
            (character_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]


# ==================== 情绪记录操作 ====================

def log_emotion(character_id: int, emotion: str, intensity: float = 0.5,
               trigger: str = None, activity_context: str = None,
               detected_from: str = "text") -> dict:
    """记录情绪"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO emotion_logs 
               (character_id, emotion, intensity, trigger, activity_context, 
                detected_from, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (character_id, emotion, intensity, trigger, activity_context,
             detected_from, now)
        )
        return {"id": cursor.lastrowid, "emotion": emotion, "intensity": intensity}


def get_recent_emotions(character_id: int, hours: int = 24) -> list:
    """获取最近的情绪记录"""
    with get_db() as conn:
        cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute(
            """SELECT * FROM emotion_logs 
               WHERE character_id = ? AND created_at >= ?
               ORDER BY created_at DESC""",
            (character_id, cutoff)
        ).fetchall()
        return [dict(r) for r in rows]


def get_emotion_stats(character_id: int, days: int = 7) -> dict:
    """获取情绪统计"""
    with get_db() as conn:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute(
            """SELECT emotion, COUNT(*) as count, AVG(intensity) as avg_intensity
               FROM emotion_logs 
               WHERE character_id = ? AND created_at >= ?
               GROUP BY emotion
               ORDER BY count DESC""",
            (character_id, cutoff)
        ).fetchall()
        return [dict(r) for r in rows]


# ==================== 工具调用操作 ====================

def log_tool_call(character_id: int, tool_name: str, input_params: dict,
                 output_result: str = None, success: bool = True,
                 error_message: str = None, execution_time: float = None) -> dict:
    """记录工具调用"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO tool_calls 
               (character_id, tool_name, input_params, output_result, 
                success, error_message, execution_time, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, tool_name, json.dumps(input_params), output_result,
             1 if success else 0, error_message, execution_time, now)
        )
        return {"id": cursor.lastrowid, "tool_name": tool_name}


def get_tool_calls(character_id: int, tool_name: str = None, limit: int = 50) -> list:
    """获取工具调用记录"""
    with get_db() as conn:
        if tool_name:
            rows = conn.execute(
                """SELECT * FROM tool_calls 
                   WHERE character_id = ? AND tool_name = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (character_id, tool_name, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM tool_calls 
                   WHERE character_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (character_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]


# ==================== 决策日志操作 ====================

def log_decision(character_id: int, decision_type: str, context: dict,
                options: list, chosen_option: str, reasoning: str,
                confidence: float = 0.5) -> dict:
    """记录决策"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO decision_logs 
               (character_id, decision_type, context, options, chosen_option,
                reasoning, confidence, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, decision_type, json.dumps(context),
             json.dumps(options), chosen_option, reasoning, confidence, now)
        )
        return {"id": cursor.lastrowid, "decision_type": decision_type}


def get_decision_logs(character_id: int, decision_type: str = None, limit: int = 50) -> list:
    """获取决策日志"""
    with get_db() as conn:
        if decision_type:
            rows = conn.execute(
                """SELECT * FROM decision_logs 
                   WHERE character_id = ? AND decision_type = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (character_id, decision_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM decision_logs 
                   WHERE character_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (character_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]


def update_decision_outcome(decision_id: int, outcome: str):
    """更新决策结果"""
    with get_db() as conn:
        conn.execute(
            "UPDATE decision_logs SET outcome = ? WHERE id = ?",
            (outcome, decision_id)
        )


# ==================== 智能体配置操作 ====================

def get_agent_config(character_id: int) -> dict:
    """获取智能体配置"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM agent_config WHERE character_id = ?",
            (character_id,)
        ).fetchone()
        
        if row:
            return dict(row)
        
        # 创建默认配置
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """INSERT INTO agent_config (character_id, created_at, updated_at)
               VALUES (?, ?, ?)""",
            (character_id, now, now)
        )
        row = conn.execute(
            "SELECT * FROM agent_config WHERE character_id = ?",
            (character_id,)
        ).fetchone()
        return dict(row)


def update_agent_config(character_id: int, **kwargs) -> dict:
    """更新智能体配置"""
    with get_db() as conn:
        kwargs['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [character_id]
        conn.execute(
            f"UPDATE agent_config SET {set_clause} WHERE character_id = ?",
            values
        )
        return get_agent_config(character_id)


if __name__ == "__main__":
    init_agent_tables()
    print("智能体数据库初始化完成")