import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime

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


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS characters (
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

            CREATE TABLE IF NOT EXISTS activity_logs (
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

            CREATE TABLE IF NOT EXISTS equipment (
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

            CREATE TABLE IF NOT EXISTS titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                unlock_condition TEXT,
                equipped BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );

            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                quest_type TEXT DEFAULT 'daily',
                exp_reward INTEGER DEFAULT 0,
                gold_reward INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
        """)
        
        # 添加新列（如果不存在）
        new_columns = [
            ("characters", "gender", "TEXT DEFAULT ''"),
            ("characters", "age", "INTEGER DEFAULT 0"),
            ("characters", "height", "REAL DEFAULT 0"),
            ("characters", "weight", "REAL DEFAULT 0"),
            ("characters", "education", "TEXT DEFAULT ''"),
            ("characters", "occupation", "TEXT DEFAULT ''"),
            ("equipment", "use_desc", "TEXT DEFAULT '使用物品'"),
            ("equipment", "use_effect", "TEXT DEFAULT '感觉不错'"),
            ("equipment", "use_bonus", "TEXT DEFAULT '{}'"),
        ]
        
        for table, column, col_type in new_columns:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            except:
                pass  # 列已存在，忽略错误


def calculate_initial_stats(gender: str, age: int, height: float, weight: float, education: str, occupation: str) -> dict:
    """根据个人信息计算初始属性"""
    # 基础属性
    strength = 10
    intelligence = 10
    agility = 10
    charisma = 10
    willpower = 10
    
    # 性别影响（轻微）
    if gender == "男":
        strength += 2
        agility += 1
    elif gender == "女":
        charisma += 2
        agility += 1
    
    # 年龄影响
    if age > 0:
        if age < 18:
            # 年轻：敏捷高，力量低
            agility += 3
            strength -= 2
            intelligence += 1
        elif age < 25:
            # 青年：平衡发展
            agility += 2
            strength += 1
            intelligence += 1
        elif age < 35:
            # 壮年：力量和智力高
            strength += 2
            intelligence += 2
            willpower += 1
        elif age < 50:
            # 中年：智力和意志高
            intelligence += 3
            willpower += 2
            agility -= 1
        else:
            # 老年：意志高，敏捷低
            willpower += 4
            intelligence += 2
            agility -= 2
            strength -= 2
    
    # 身高体重影响（BMI相关）
    if height > 0 and weight > 0:
        height_m = height / 100
        bmi = weight / (height_m * height_m)
        
        if bmi < 18.5:
            # 偏瘦：敏捷高，力量低
            agility += 2
            strength -= 1
        elif bmi < 25:
            # 正常：平衡
            strength += 1
            agility += 1
        elif bmi < 30:
            # 偏胖：力量高，敏捷低
            strength += 2
            agility -= 1
        else:
            # 肥胖：力量高，敏捷低
            strength += 1
            agility -= 2
        
        # 身高优势
        if height > 175:
            strength += 1
            agility += 1
        elif height > 185:
            strength += 2
            charisma += 1
    
    # 学历影响
    education_bonus = {
        "小学": {"intelligence": 1},
        "初中": {"intelligence": 2},
        "高中": {"intelligence": 3, "willpower": 1},
        "大专": {"intelligence": 4, "willpower": 2},
        "本科": {"intelligence": 5, "willpower": 2, "charisma": 1},
        "硕士": {"intelligence": 7, "willpower": 3, "charisma": 2},
        "博士": {"intelligence": 9, "willpower": 4, "charisma": 2},
        "其他": {"intelligence": 1}
    }
    
    if education in education_bonus:
        for attr, bonus in education_bonus[education].items():
            locals()[attr] += bonus
    
    # 职业影响
    occupation_bonuses = {
        "学生": {"intelligence": 3, "agility": 1},
        "程序员": {"intelligence": 4, "willpower": 2},
        "设计师": {"intelligence": 3, "charisma": 2, "agility": 1},
        "教师": {"intelligence": 3, "charisma": 3},
        "医生": {"intelligence": 5, "willpower": 3},
        "律师": {"intelligence": 4, "charisma": 3},
        "销售": {"charisma": 4, "willpower": 2},
        "工人": {"strength": 4, "willpower": 2},
        "运动员": {"strength": 5, "agility": 4},
        "艺术家": {"intelligence": 3, "charisma": 3, "agility": 1},
        "自由职业": {"willpower": 3, "charisma": 2},
        "企业管理": {"charisma": 4, "intelligence": 2, "willpower": 2},
        "公务员": {"willpower": 3, "charisma": 2},
        "服务业": {"charisma": 3, "agility": 2},
        "其他": {"willpower": 1}
    }
    
    if occupation in occupation_bonuses:
        for attr, bonus in occupation_bonuses[occupation].items():
            locals()[attr] += bonus
    
    # 确保属性在合理范围内
    strength = max(5, min(20, strength))
    intelligence = max(5, min(20, intelligence))
    agility = max(5, min(20, agility))
    charisma = max(5, min(20, charisma))
    willpower = max(5, min(20, willpower))
    
    return {
        "strength": strength,
        "intelligence": intelligence,
        "agility": agility,
        "charisma": charisma,
        "willpower": willpower
    }


def create_character(name: str, gender: str = "", age: int = 0, height: float = 0, 
                     weight: float = 0, education: str = "", occupation: str = "") -> dict:
    # 计算初始属性
    stats = calculate_initial_stats(gender, age, height, weight, education, occupation)
    
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO characters 
               (name, gender, age, height, weight, education, occupation,
                strength, intelligence, agility, charisma, willpower)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, gender, age, height, weight, education, occupation,
             stats["strength"], stats["intelligence"], stats["agility"], 
             stats["charisma"], stats["willpower"])
        )
        conn.commit()
        character_id = cursor.lastrowid
        return get_character(character_id)


def get_character(character_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM characters WHERE id = ?",
            (character_id,)
        ).fetchone()
        if row:
            return dict(row)
    return None


def get_all_characters() -> list:
    """获取所有角色"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM characters ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_character_count() -> int:
    """获取角色数量"""
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) as count FROM characters").fetchone()
        return row["count"] if row else 0


def delete_character(character_id: int) -> bool:
    """删除角色及其相关数据"""
    with get_db() as conn:
        # 删除角色的装备
        conn.execute("DELETE FROM equipment WHERE character_id = ?", (character_id,))
        # 删除角色的称号
        conn.execute("DELETE FROM titles WHERE character_id = ?", (character_id,))
        # 删除角色的任务
        conn.execute("DELETE FROM quests WHERE character_id = ?", (character_id,))
        # 删除角色的活动日志
        conn.execute("DELETE FROM activity_logs WHERE character_id = ?", (character_id,))
        # 删除角色
        cursor = conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
        return cursor.rowcount > 0


def update_character(character_id: int, **kwargs) -> dict:
    with get_db() as conn:
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [character_id]
        conn.execute(
            f"UPDATE characters SET {set_clause} WHERE id = ?",
            values
        )
        return get_character(character_id)


def add_activity_log(character_id: int, activity_type: str, description: str,
                    exp_gained: int, gold_gained: int,
                    attribute_changes: dict, ai_feedback: str = None) -> dict:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO activity_logs 
               (character_id, activity_type, description, exp_gained, 
                gold_gained, attribute_changes, ai_feedback)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (character_id, activity_type, description, exp_gained,
             gold_gained, json.dumps(attribute_changes), ai_feedback)
        )
        row = conn.execute(
            "SELECT * FROM activity_logs WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


def get_activity_logs(character_id: int, limit: int = 20) -> list:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM activity_logs 
               WHERE character_id = ? 
               ORDER BY created_at DESC LIMIT ?""",
            (character_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def add_equipment(character_id: int, name: str, description: str,
                  rarity: str, stat_bonuses: dict, special_effect: str = None,
                  use_desc: str = "使用物品", use_effect: str = "感觉不错",
                  use_bonus: dict = None) -> dict:
    if use_bonus is None:
        use_bonus = {}
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO equipment 
               (character_id, name, description, rarity, stat_bonuses, special_effect,
                use_desc, use_effect, use_bonus)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, name, description, rarity,
             json.dumps(stat_bonuses), special_effect,
             use_desc, use_effect, json.dumps(use_bonus))
        )
        row = conn.execute(
            "SELECT * FROM equipment WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


def get_equipment(character_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM equipment WHERE character_id = ? ORDER BY created_at DESC",
            (character_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_title(character_id: int, name: str, description: str,
              unlock_condition: str = None) -> dict:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO titles (character_id, name, description, unlock_condition)
               VALUES (?, ?, ?, ?)""",
            (character_id, name, description, unlock_condition)
        )
        row = conn.execute(
            "SELECT * FROM titles WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


def get_titles(character_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM titles WHERE character_id = ? ORDER BY created_at DESC",
            (character_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_quest(character_id: int, title: str, description: str,
              quest_type: str, exp_reward: int, gold_reward: int,
              due_date: str = None) -> dict:
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO quests 
               (character_id, title, description, quest_type, exp_reward, gold_reward, due_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (character_id, title, description, quest_type, exp_reward, gold_reward, due_date)
        )
        row = conn.execute(
            "SELECT * FROM quests WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


def get_quests(character_id: int, status: str = None) -> list:
    with get_db() as conn:
        # 每日任务刷新：将昨天及以前完成的每日任务重置为活跃状态
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute(
            """UPDATE quests 
               SET status = 'active' 
               WHERE character_id = ? 
               AND quest_type = 'daily' 
               AND status = 'completed' 
               AND DATE(created_at) < ?""",
            (character_id, today)
        )
        
        if status:
            rows = conn.execute(
                "SELECT * FROM quests WHERE character_id = ? AND status = ? ORDER BY created_at DESC",
                (character_id, status)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM quests WHERE character_id = ? ORDER BY created_at DESC",
                (character_id,)
            ).fetchall()
        return [dict(r) for r in rows]


def complete_quest(quest_id: int) -> dict:
    with get_db() as conn:
        conn.execute(
            "UPDATE quests SET status = 'completed' WHERE id = ?",
            (quest_id,)
        )
        row = conn.execute(
            "SELECT * FROM quests WHERE id = ?",
            (quest_id,)
        ).fetchone()
        return dict(row) if row else None
