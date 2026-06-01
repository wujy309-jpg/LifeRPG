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
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            
            CREATE TABLE IF NOT EXISTS check_ins (
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
            
            CREATE TABLE IF NOT EXISTS activity_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                activity_type TEXT,
                use_count INTEGER DEFAULT 0,
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
            ("quests", "completed_at", "TIMESTAMP"),
        ]
        
        for table, column, col_type in new_columns:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            except:
                pass  # 列已存在，忽略错误


def calculate_initial_stats(gender: str, age: int, height: float, weight: float, education: str, occupation: str) -> dict:
    """
    根据个人信息计算初始属性
    
    规则：
    - 每个属性初始值 = 50
    - 根据个人信息加分（可正可负）
    - 每个属性上限 100，下限 1
    - 总属性 = 五个属性平均值，范围 0-100
    """
    # 基础属性全部为 50
    strength = 50
    intelligence = 50
    agility = 50
    charisma = 50
    willpower = 50
    
    # ========== 性别影响 ==========
    if gender == "男":
        strength += 5      # 男性力量稍高
        agility += 3       # 敏捷稍高
        charisma -= 2      # 魅力稍低
    elif gender == "女":
        charisma += 5      # 女性魅力稍高
        agility += 3       # 敏捷稍高
        strength -= 2      # 力量稍低
    
    # ========== 年龄影响 ==========
    if age > 0:
        if age < 18:
            # 青少年：敏捷高，力量和意志低
            agility += 8
            intelligence += 5
            strength -= 8
            willpower -= 8
        elif age < 25:
            # 青年：平衡发展
            agility += 5
            strength += 3
            intelligence += 3
            charisma += 3
        elif age < 35:
            # 壮年：力量和智力高
            strength += 5
            intelligence += 5
            willpower += 5
        elif age < 50:
            # 中年：智力和意志高
            intelligence += 8
            willpower += 8
            charisma += 3
            agility -= 5
            strength -= 5
        else:
            # 老年：意志最高
            willpower += 12
            intelligence += 5
            charisma += 3
            agility -= 10
            strength -= 10
    
    # ========== 身高体重影响（BMI） ==========
    if height > 0 and weight > 0:
        height_m = height / 100
        bmi = weight / (height_m * height_m)
        
        if bmi < 18.5:
            # 偏瘦：敏捷高，力量低
            agility += 5
            strength -= 3
        elif bmi < 25:
            # 正常：平衡
            strength += 3
            agility += 3
        elif bmi < 30:
            # 偏胖：力量高，敏捷低
            strength += 5
            agility -= 5
        else:
            # 肥胖：力量高，敏捷和魅力低
            strength += 3
            agility -= 8
            charisma -= 5
        
        # 身高优势
        if height > 185:
            strength += 5
            charisma += 3
        elif height > 175:
            strength += 3
    
    # ========== 学历影响 ==========
    education_bonus = {
        "小学":   {"intelligence": -5, "willpower": -3},
        "初中":   {"intelligence": -2, "willpower": 0},
        "高中":   {"intelligence": 2, "willpower": 2},
        "大专":   {"intelligence": 5, "willpower": 3, "charisma": 2},
        "本科":   {"intelligence": 8, "willpower": 5, "charisma": 3},
        "硕士":   {"intelligence": 12, "willpower": 8, "charisma": 5},
        "博士":   {"intelligence": 18, "willpower": 12, "charisma": 5},
        "其他":   {"intelligence": 0, "willpower": 0}
    }
    
    if education in education_bonus:
        for attr, bonus in education_bonus[education].items():
            locals()[attr] += bonus
    
    # ========== 职业影响 ==========
    occupation_bonuses = {
        "学生":     {"intelligence": 5, "agility": 5, "charisma": 3},
        "程序员":   {"intelligence": 10, "willpower": 8, "agility": 3},
        "设计师":   {"intelligence": 8, "charisma": 8, "agility": 5},
        "教师":     {"intelligence": 8, "charisma": 8, "willpower": 5},
        "医生":     {"intelligence": 12, "willpower": 10, "charisma": 5},
        "律师":     {"intelligence": 10, "charisma": 10, "willpower": 5},
        "销售":     {"charisma": 12, "willpower": 8, "agility": 3},
        "工人":     {"strength": 10, "willpower": 8, "agility": 3},
        "运动员":   {"strength": 12, "agility": 12, "willpower": 8},
        "艺术家":   {"intelligence": 8, "charisma": 8, "agility": 5},
        "自由职业": {"willpower": 10, "charisma": 5, "agility": 5},
        "企业管理": {"charisma": 10, "intelligence": 8, "willpower": 8},
        "公务员":   {"willpower": 10, "charisma": 5, "intelligence": 5},
        "服务业":   {"charisma": 8, "agility": 5, "willpower": 3},
        "其他":     {"willpower": 3, "charisma": 3}
    }
    
    if occupation in occupation_bonuses:
        for attr, bonus in occupation_bonuses[occupation].items():
            locals()[attr] += bonus
    
    # ========== 确保属性在合理范围内（1-100） ==========
    strength = max(1, min(100, strength))
    intelligence = max(1, min(100, intelligence))
    agility = max(1, min(100, agility))
    charisma = max(1, min(100, charisma))
    willpower = max(1, min(100, willpower))
    
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO characters 
               (name, gender, age, height, weight, education, occupation,
                strength, intelligence, agility, charisma, willpower, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, gender, age, height, weight, education, occupation,
             stats["strength"], stats["intelligence"], stats["agility"], 
             stats["charisma"], stats["willpower"], now)
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO activity_logs 
               (character_id, activity_type, description, exp_gained, 
                gold_gained, attribute_changes, ai_feedback, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, activity_type, description, exp_gained,
             gold_gained, json.dumps(attribute_changes), ai_feedback, now)
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO equipment 
               (character_id, name, description, rarity, stat_bonuses, special_effect,
                use_desc, use_effect, use_bonus, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, name, description, rarity,
             json.dumps(stat_bonuses), special_effect,
             use_desc, use_effect, json.dumps(use_bonus), now)
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO titles (character_id, name, description, unlock_condition, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (character_id, name, description, unlock_condition, now)
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO quests 
               (character_id, title, description, quest_type, exp_reward, gold_reward, due_date, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, title, description, quest_type, exp_reward, gold_reward, due_date, now)
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
               SET status = 'active', completed_at = NULL
               WHERE character_id = ? 
               AND quest_type = 'daily' 
               AND status = 'completed' 
               AND completed_at IS NOT NULL
               AND DATE(completed_at) < ?""",
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE quests SET status = 'completed', completed_at = ? WHERE id = ?",
            (now, quest_id)
        )
        row = conn.execute(
            "SELECT * FROM quests WHERE id = ?",
            (quest_id,)
        ).fetchone()
        return dict(row) if row else None


# ============ 统计函数 ============

def get_activity_stats(character_id: int) -> dict:
    """获取活动统计数据"""
    with get_db() as conn:
        # 总活动次数
        total_count = conn.execute(
            "SELECT COUNT(*) as count FROM activity_logs WHERE character_id = ?",
            (character_id,)
        ).fetchone()["count"]
        
        # 今日活动次数
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = conn.execute(
            "SELECT COUNT(*) as count FROM activity_logs WHERE character_id = ? AND DATE(created_at) = ?",
            (character_id, today)
        ).fetchone()["count"]
        
        # 本周活动次数
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_count = conn.execute(
            "SELECT COUNT(*) as count FROM activity_logs WHERE character_id = ? AND DATE(created_at) >= ?",
            (character_id, week_ago)
        ).fetchone()["count"]
        
        # 总经验值和金币
        totals = conn.execute(
            "SELECT SUM(exp_gained) as total_exp, SUM(gold_gained) as total_gold FROM activity_logs WHERE character_id = ?",
            (character_id,)
        ).fetchone()
        
        # 活动类型统计
        type_stats = conn.execute(
            """SELECT activity_type, COUNT(*) as count 
               FROM activity_logs WHERE character_id = ? 
               GROUP BY activity_type ORDER BY count DESC""",
            (character_id,)
        ).fetchall()
        
        # 最常做的活动
        most_common = type_stats[0]["activity_type"] if type_stats else "无"
        
        # 连续登录天数
        consecutive_days = get_consecutive_days(character_id)
        
        return {
            "total_count": total_count,
            "today_count": today_count,
            "week_count": week_count,
            "total_exp": totals["total_exp"] or 0,
            "total_gold": totals["total_gold"] or 0,
            "type_stats": [dict(t) for t in type_stats],
            "most_common": most_common,
            "consecutive_days": consecutive_days
        }


def get_consecutive_days(character_id: int) -> int:
    """获取连续登录天数"""
    with get_db() as conn:
        # 获取所有活动日期（去重）
        dates = conn.execute(
            """SELECT DISTINCT DATE(created_at) as date 
               FROM activity_logs WHERE character_id = ? 
               ORDER BY date DESC""",
            (character_id,)
        ).fetchall()
        
        if not dates:
            return 0
        
        consecutive = 0
        current_date = datetime.now().date()
        
        for row in dates:
            activity_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
            if activity_date == current_date:
                consecutive += 1
                current_date -= timedelta(days=1)
            elif activity_date == current_date - timedelta(days=1):
                # 允许昨天没记录
                current_date = activity_date
                consecutive += 1
            else:
                break
        
        return consecutive


def get_activity_history(character_id: int, days: int = 30) -> list:
    """获取活动历史（按天统计）"""
    with get_db() as conn:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        history = conn.execute(
            """SELECT DATE(created_at) as date, 
                      COUNT(*) as count,
                      SUM(exp_gained) as exp,
                      SUM(gold_gained) as gold
               FROM activity_logs 
               WHERE character_id = ? AND DATE(created_at) >= ?
               GROUP BY DATE(created_at)
               ORDER BY date""",
            (character_id, start_date)
        ).fetchall()
        
        # 填充缺失的日期
        result = []
        current_date = datetime.now().date()
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        history_dict = {row["date"]: dict(row) for row in history}
        
        while current_date >= start:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in history_dict:
                result.append(history_dict[date_str])
            else:
                result.append({
                    "date": date_str,
                    "count": 0,
                    "exp": 0,
                    "gold": 0
                })
            current_date -= timedelta(days=1)
        
        return result


def get_attribute_history(character_id: int, days: int = 30) -> list:
    """获取属性变化历史"""
    with get_db() as conn:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # 获取属性变化记录
        logs = conn.execute(
            """SELECT attribute_changes, created_at
               FROM activity_logs 
               WHERE character_id = ? AND DATE(created_at) >= ?
               ORDER BY created_at""",
            (character_id, start_date)
        ).fetchall()
        
        # 当前属性值
        character = get_character(character_id)
        if not character:
            return []
        
        # 从当前属性反推历史
        current_stats = {
            "strength": character["strength"],
            "intelligence": character["intelligence"],
            "agility": character["agility"],
            "charisma": character["charisma"],
            "willpower": character["willpower"]
        }
        
        # 收集所有变化
        changes_by_date = {}
        for log in logs:
            date = datetime.strptime(log["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d") if log["created_at"] else None
            if date and log["attribute_changes"]:
                try:
                    changes = json.loads(log["attribute_changes"])
                    if date not in changes_by_date:
                        changes_by_date[date] = {}
                    for attr, value in changes.items():
                        changes_by_date[date][attr] = changes_by_date[date].get(attr, 0) + value
                except:
                    pass
        
        # 生成历史数据
        result = []
        stats = current_stats.copy()
        
        current_date = datetime.now().date()
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        while current_date >= start:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # 减去当天的变化
            if date_str in changes_by_date:
                for attr, value in changes_by_date[date_str].items():
                    if attr in stats:
                        stats[attr] -= value
            
            result.append({
                "date": date_str,
                **stats
            })
            
            current_date -= timedelta(days=1)
        
        result.reverse()
        return result


def get_weekly_activity_type_stats(character_id: int) -> dict:
    """获取本周各类型活动统计"""
    with get_db() as conn:
        # 获取本周的开始日期（周一）
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_start_str = week_start.strftime("%Y-%m-%d")
        
        type_stats = conn.execute(
            """SELECT activity_type, COUNT(*) as count
               FROM activity_logs 
               WHERE character_id = ? AND DATE(created_at) >= ?
               GROUP BY activity_type""",
            (character_id, week_start_str)
        ).fetchall()
        
        return {row["activity_type"]: row["count"] for row in type_stats}


def init_reality_tables():
    """初始化现实连接相关的表"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reality_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER DEFAULT 0,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'entertainment',
                cost INTEGER NOT NULL,
                icon TEXT DEFAULT ' ',
                is_custom BOOLEAN DEFAULT 0,
                times_redeemed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(character_id, name)
            );

            CREATE TABLE IF NOT EXISTS habit_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                duration_days INTEGER DEFAULT 21,
                cost INTEGER NOT NULL,
                reward_exp INTEGER DEFAULT 100,
                reward_gold INTEGER DEFAULT 50,
                status TEXT DEFAULT 'active',
                start_date DATE,
                end_date DATE,
                check_in_days INTEGER DEFAULT 0,
                last_check_in DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS immunity_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                cost INTEGER NOT NULL,
                uses_remaining INTEGER DEFAULT 1,
                card_type TEXT DEFAULT 'skip_task',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS penalty_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                penalty_type TEXT NOT NULL,
                description TEXT,
                gold_lost INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
        """)
        
        # 插入默认奖励模板
        default_rewards = [
            # 娱乐类
            ("看一集电视剧", "放松一下，追剧时间到！", "entertainment", 30, " "),
            ("玩30分钟游戏", "适度游戏益脑，沉迷游戏伤身", "entertainment", 50, " ️"),
            ("看一部电影", "光影世界，放松心情", "entertainment", 60, " "),
            ("刷30分钟短视频", "适当放松，别沉迷哦", "entertainment", 20, " "),
            ("唱KTV一小时", "释放压力，放声歌唱", "entertainment", 80, " "),
            ("打一局桌游", "动动脑子，享受乐趣", "entertainment", 40, " "),
            
            # 美食类
            ("吃一顿好的", "美食是最好的奖励", "food", 80, " "),
            ("喝一杯奶茶", "甜蜜的小确幸", "food", 20, " "),
            ("点一份外卖大餐", "今天不想做饭，犒劳自己", "food", 60, " "),
            ("去网红店打卡", "探索美食，记录生活", "food", 100, " ️"),
            ("买一份甜品", "生活需要一点甜", "food", 30, " "),
            
            # 休息类
            ("睡个懒觉", "明天多睡30分钟", "rest", 40, " ️"),
            ("泡个热水澡", "放松身心，洗去疲惫", "rest", 35, " "),
            ("做个面膜", "护肤时间，宠爱自己", "rest", 25, " "),
            ("冥想15分钟", "放空大脑，回归平静", "rest", 15, " "),
            ("早睡一小时", "今天提前休息，明天更有精神", "rest", 30, " ️"),
            
            # 学习类
            ("买一本想看的书", "知识就是力量", "education", 100, " "),
            ("看一个TED演讲", "开拓视野，获取灵感", "education", 30, " "),
            ("学习新技能30分钟", "投资自己，提升能力", "education", 50, " "),
            ("听一期播客", "碎片时间，充实大脑", "education", 20, " "),
            
            # 购物类
            ("逛街购物", "买买买！", "shopping", 150, " ️"),
            ("买一件新衣服", "换个风格，换个心情", "shopping", 200, " "),
            ("买一件小饰品", "点缀生活的小物件", "shopping", 80, " "),
            ("买一束花", "生活需要仪式感", "shopping", 50, " "),
            
            # 社交类
            ("请朋友喝咖啡", "社交也是一种充电", "social", 60, " ☕"),
            ("给家人打电话", "关心家人，传递温暖", "social", 15, " "),
            ("约朋友聚餐", "美食与友情不可辜负", "social", 120, " "),
            
            # 运动类
            ("买运动饮料", "补充能量，继续加油", "health", 15, " "),
            ("按摩30分钟", "放松肌肉，缓解疲劳", "health", 80, " "),
            ("买一双新运动鞋", "工欲善其事，必先利其器", "health", 250, " "),
        ]
        
        # 插入默认奖励（使用 INSERT OR IGNORE 避免重复）
        for name, desc, cat, cost, icon in default_rewards:
            conn.execute(
                "INSERT OR IGNORE INTO reality_rewards (character_id, name, description, category, cost, icon, is_custom) VALUES (0, ?, ?, ?, ?, ?, 0)",
                (name, desc, cat, cost, icon)
            )
        
        # 插入默认习惯挑战模板（character_id=0 表示模板）
        default_challenges = [
            # 健康类
            ("21天早起挑战", "每天7点前起床，养成早起习惯", 21, 50, 100, 50, " "),
            ("21天运动挑战", "每天运动30分钟，塑造健康体魄", 21, 60, 120, 60, " ️"),
            ("21天喝水挑战", "每天喝8杯水，保持健康", 21, 20, 40, 20, " "),
            ("21天不熬夜挑战", "每天11点前睡觉，规律作息", 21, 45, 90, 45, " "),
            ("14天健康饮食挑战", "拒绝垃圾食品，健康饮食", 14, 80, 160, 80, " "),
            ("21天拉伸挑战", "每天拉伸10分钟，改善体态", 21, 30, 60, 30, " "),
            ("7天不喝奶茶挑战", "戒掉奶茶，健康饮水", 7, 25, 50, 25, " "),
            
            # 学习类
            ("21天阅读挑战", "每天阅读30分钟，开拓视野", 21, 40, 80, 40, " "),
            ("21天学习挑战", "每天学习1小时，提升自我", 21, 70, 140, 70, " "),
            ("21天写日记挑战", "每天记录生活，反思成长", 21, 25, 50, 25, " "),
            ("21天背单词挑战", "每天背20个单词，扩充词汇", 21, 35, 70, 35, " "),
            ("21天编程挑战", "每天写代码30分钟，精进技能", 21, 80, 160, 80, " "),
            ("14天学一门新技能", "两周入门一项新技能", 14, 100, 200, 100, " "),
            
            # 心理类
            ("21天冥想挑战", "每天冥想10分钟，平静内心", 21, 30, 60, 30, " "),
            ("21天感恩挑战", "每天写下3件感恩的事", 21, 20, 40, 20, " "),
            ("21天不抱怨挑战", "保持积极心态，不抱怨", 21, 50, 100, 50, " "),
            ("7天数字断联", "每天手机使用不超过1小时", 7, 70, 140, 70, " "),
            
            # 生活类
            ("7天断舍离挑战", "每天扔掉一件不需要的东西", 7, 30, 60, 30, " "),
            ("30天存钱挑战", "每天存10元，养成储蓄习惯", 30, 100, 300, 100, " "),
            ("21天做饭挑战", "每天自己做一顿饭", 21, 60, 120, 60, " "),
            ("21天整理房间挑战", "每天整理一个角落", 21, 35, 70, 35, " "),
            ("14天极简生活挑战", "减少不必要的消费", 14, 80, 160, 80, " "),
            
            # 社交类
            ("21天社交挑战", "每天和一个朋友聊天", 21, 40, 80, 40, " "),
            ("7天帮助他人挑战", "每天做一件帮助他人的事", 7, 50, 100, 50, " "),
            ("21天赞美挑战", "每天真诚赞美一个人", 21, 25, 50, 25, " "),
        ]
        
        # 创建挑战模板表（如果不存在）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS challenge_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                duration_days INTEGER,
                cost INTEGER,
                reward_exp INTEGER,
                reward_gold INTEGER,
                icon TEXT
            )
        """)
        
        # 插入挑战模板（使用 INSERT OR IGNORE 避免重复）
        for name, desc, days, cost, exp, gold, icon in default_challenges:
            conn.execute(
                "INSERT OR IGNORE INTO challenge_templates (name, description, duration_days, cost, reward_exp, reward_gold, icon) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, desc, days, cost, exp, gold, icon)
            )


def get_reality_rewards(character_id: int) -> list:
    """获取可用的现实奖励"""
    with get_db() as conn:
        # 获取默认奖励和用户自定义奖励
        rewards = conn.execute(
            """SELECT * FROM reality_rewards 
               WHERE character_id = 0 OR character_id = ?
               ORDER BY cost ASC""",
            (character_id,)
        ).fetchall()
        return [dict(r) for r in rewards]


def add_custom_reward(character_id: int, name: str, description: str, cost: int, category: str = "custom") -> dict:
    """添加自定义奖励"""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO reality_rewards (character_id, name, description, category, cost, icon, is_custom) VALUES (?, ?, ?, ?, ?, ' ', 1)",
            (character_id, name, description, category, cost)
        )
        return {"id": cursor.lastrowid, "name": name, "cost": cost}


def redeem_reward(character_id: int, reward_id: int) -> dict:
    """兑换奖励"""
    with get_db() as conn:
        # 获取奖励信息
        reward = conn.execute("SELECT * FROM reality_rewards WHERE id = ?", (reward_id,)).fetchone()
        if not reward:
            return {"success": False, "error": "奖励不存在"}
        
        # 获取角色金币
        character = conn.execute("SELECT gold FROM characters WHERE id = ?", (character_id,)).fetchone()
        if not character:
            return {"success": False, "error": "角色不存在"}
        
        if character["gold"] < reward["cost"]:
            return {"success": False, "error": f"金币不足！需要{reward['cost']}金币，当前只有{character['gold']}金币"}
        
        # 扣除金币
        conn.execute(
            "UPDATE characters SET gold = gold - ? WHERE id = ?",
            (reward["cost"], character_id)
        )
        
        # 记录兑换次数
        conn.execute(
            "UPDATE reality_rewards SET times_redeemed = times_redeemed + 1 WHERE id = ?",
            (reward_id,)
        )
        
        return {
            "success": True,
            "reward_name": reward["name"],
            "cost": reward["cost"],
            "remaining_gold": character["gold"] - reward["cost"]
        }


def get_habit_challenges(character_id: int) -> list:
    """获取习惯挑战"""
    with get_db() as conn:
        challenges = conn.execute(
            "SELECT * FROM habit_challenges WHERE character_id = ? ORDER BY created_at DESC",
            (character_id,)
        ).fetchall()
        return [dict(c) for c in challenges]


def get_challenge_templates() -> list:
    """获取挑战模板"""
    with get_db() as conn:
        templates = conn.execute("SELECT * FROM challenge_templates ORDER BY cost ASC").fetchall()
        return [dict(t) for t in templates]


def create_habit_challenge(character_id: int, name: str, description: str, duration_days: int, cost: int, reward_exp: int = None, reward_gold: int = None) -> dict:
    """创建习惯挑战"""
    with get_db() as conn:
        # 检查金币
        character = conn.execute("SELECT gold FROM characters WHERE id = ?", (character_id,)).fetchone()
        if not character or character["gold"] < cost:
            return {"success": False, "error": "金币不足"}
        
        # 扣除金币
        conn.execute("UPDATE characters SET gold = gold - ? WHERE id = ?", (cost, character_id))
        
        # 计算奖励（如果没有指定，则根据成本计算）
        if reward_exp is None:
            reward_exp = cost * 2
        if reward_gold is None:
            reward_gold = cost
        
        # 创建挑战
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=duration_days)
        cursor = conn.execute(
            """INSERT INTO habit_challenges 
               (character_id, name, description, duration_days, cost, reward_exp, reward_gold, start_date, end_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, name, description, duration_days, cost, reward_exp, reward_gold, start_date, end_date)
        )
        
        return {"success": True, "challenge_id": cursor.lastrowid}


def check_in_challenge(character_id: int, challenge_id: int) -> dict:
    """习惯挑战打卡"""
    with get_db() as conn:
        challenge = conn.execute(
            "SELECT * FROM habit_challenges WHERE id = ? AND character_id = ?",
            (challenge_id, character_id)
        ).fetchone()
        
        if not challenge:
            return {"success": False, "error": "挑战不存在"}
        
        if challenge["status"] != "active":
            return {"success": False, "error": "挑战已结束"}
        
        today = datetime.now().date()
        if challenge["last_check_in"] == str(today):
            return {"success": False, "error": "今天已经打卡过了"}
        
        # 更新打卡
        new_check_in_days = challenge["check_in_days"] + 1
        conn.execute(
            "UPDATE habit_challenges SET check_in_days = ?, last_check_in = ? WHERE id = ?",
            (new_check_in_days, today, challenge_id)
        )
        
        # 检查是否完成
        if new_check_in_days >= challenge["duration_days"]:
            conn.execute(
                "UPDATE habit_challenges SET status = 'completed' WHERE id = ?",
                (challenge_id,)
            )
            # 给予奖励
            conn.execute(
                "UPDATE characters SET exp = exp + ?, gold = gold + ? WHERE id = ?",
                (challenge["reward_exp"], challenge["reward_gold"], character_id)
            )
            return {
                "success": True,
                "completed": True,
                "reward_exp": challenge["reward_exp"],
                "reward_gold": challenge["reward_gold"]
            }
        
        return {"success": True, "completed": False, "days_remaining": challenge["duration_days"] - new_check_in_days}


def get_immunity_cards(character_id: int) -> list:
    """获取免罪金牌"""
    with get_db() as conn:
        cards = conn.execute(
            "SELECT * FROM immunity_cards WHERE character_id = ? AND uses_remaining > 0",
            (character_id,)
        ).fetchall()
        return [dict(c) for c in cards]


def buy_immunity_card(character_id: int, card_type: str) -> dict:
    """购买免罪金牌"""
    card_configs = {
        "skip_task": {"name": "任务跳过卡", "desc": "跳过一个不想做的任务", "cost": 50, "icon": "⏭️"},
        "rest_day": {"name": "休息日卡", "desc": "允许一天不打卡不扣金币", "cost": 80, "icon": " ️"},
        "double_reward": {"name": "双倍奖励卡", "desc": "下次任务获得双倍奖励", "cost": 100, "icon": "✨"},
        "penalty_shield": {"name": "惩罚护盾", "desc": "抵挡一次金币惩罚", "cost": 60, "icon": " ️"},
    }
    
    config = card_configs.get(card_type)
    if not config:
        return {"success": False, "error": "未知的卡牌类型"}
    
    with get_db() as conn:
        character = conn.execute("SELECT gold FROM characters WHERE id = ?", (character_id,)).fetchone()
        if not character or character["gold"] < config["cost"]:
            return {"success": False, "error": "金币不足"}
        
        conn.execute("UPDATE characters SET gold = gold - ? WHERE id = ?", (config["cost"], character_id))
        conn.execute(
            "INSERT INTO immunity_cards (character_id, name, description, cost, card_type) VALUES (?, ?, ?, ?, ?)",
            (character_id, config["name"], config["desc"], config["cost"], card_type)
        )
        
        return {"success": True, "card_name": config["name"]}


def check_penalty(character_id: int) -> dict:
    """检查并执行惩罚机制"""
    with get_db() as conn:
        # 获取最近7天的活动记录
        seven_days_ago = (datetime.now() - timedelta(days=7)).date()
        activity_count = conn.execute(
            "SELECT COUNT(*) FROM activity_logs WHERE character_id = ? AND DATE(created_at) >= ?",
            (character_id, seven_days_ago)
        ).fetchone()[0]
        
        # 获取角色信息
        character = conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
        if not character:
            return {"penalty": False}
        
        # 检查是否有惩罚护盾
        shield = conn.execute(
            "SELECT id FROM immunity_cards WHERE character_id = ? AND card_type = 'penalty_shield' AND uses_remaining > 0",
            (character_id,)
        ).fetchone()
        
        # 如果7天内活动少于3次，触发惩罚
        if activity_count < 3:
            if shield:
                # 使用护盾
                conn.execute("UPDATE immunity_cards SET uses_remaining = uses_remaining - 1 WHERE id = ?", (shield["id"],))
                return {"penalty": False, "shield_used": True}
            
            # 扣除金币惩罚
            penalty_gold = min(50, character["gold"])
            if penalty_gold > 0:
                conn.execute("UPDATE characters SET gold = gold - ? WHERE id = ?", (penalty_gold, character_id))
                conn.execute(
                    "INSERT INTO penalty_log (character_id, penalty_type, description, gold_lost) VALUES (?, 'inactive', ?, ?)",
                    (character_id, f"连续7天活动不足3次，扣除{penalty_gold}金币", penalty_gold)
                )
                return {"penalty": True, "gold_lost": penalty_gold, "reason": "连续7天活动不足3次"}
        
        return {"penalty": False}


def get_penalty_history(character_id: int) -> list:
    """获取惩罚历史"""
    with get_db() as conn:
        history = conn.execute(
            "SELECT * FROM penalty_log WHERE character_id = ? ORDER BY created_at DESC LIMIT 20",
            (character_id,)
        ).fetchall()
        return [dict(h) for h in history]


# ============ 签到系统 ============

def check_in(character_id: int) -> dict:
    """
    每日签到
    
    规则：
    - 每天只能签到一次
    - 连续签到奖励递增
    - 基础奖励：10经验 + 5金币
    - 每连续一天：+5经验 + 3金币
    - 最高连续30天封顶
    """
    today = date.today().isoformat()
    
    with get_db() as conn:
        # 检查今天是否已签到
        existing = conn.execute(
            "SELECT * FROM check_ins WHERE character_id = ? AND check_in_date = ?",
            (character_id, today)
        ).fetchone()
        
        if existing:
            return {"success": False, "message": "今天已经签到过了！"}
        
        # 获取昨天的签到记录
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        last_checkin = conn.execute(
            "SELECT * FROM check_ins WHERE character_id = ? AND check_in_date = ?",
            (character_id, yesterday)
        ).fetchone()
        
        # 计算连续天数
        consecutive_days = 1
        if last_checkin:
            consecutive_days = last_checkin["consecutive_days"] + 1
        
        # 限制最大连续天数
        consecutive_days = min(consecutive_days, 30)
        
        # 计算奖励
        base_exp = 10
        base_gold = 5
        reward_exp = base_exp + (consecutive_days - 1) * 5
        reward_gold = base_gold + (consecutive_days - 1) * 3
        
        # 记录签到
        conn.execute(
            "INSERT INTO check_ins (character_id, check_in_date, consecutive_days, reward_exp, reward_gold) VALUES (?, ?, ?, ?, ?)",
            (character_id, today, consecutive_days, reward_exp, reward_gold)
        )
        
        # 给角色加奖励
        character = conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
        if character:
            new_exp = character["exp"] + reward_exp
            new_gold = character["gold"] + reward_gold
            
            # 检查升级
            from game_engine import check_level_up
            new_level, remaining_exp = check_level_up(new_exp, character["level"])
            
            conn.execute(
                "UPDATE characters SET exp = ?, gold = ?, level = ? WHERE id = ?",
                (remaining_exp, new_gold, new_level, character_id)
            )
        
        return {
            "success": True,
            "message": f"签到成功！连续签到{consecutive_days}天",
            "consecutive_days": consecutive_days,
            "reward_exp": reward_exp,
            "reward_gold": reward_gold
        }


def get_check_in_status(character_id: int) -> dict:
    """获取签到状态"""
    today = date.today().isoformat()
    
    with get_db() as conn:
        # 检查今天是否已签到
        today_checkin = conn.execute(
            "SELECT * FROM check_ins WHERE character_id = ? AND check_in_date = ?",
            (character_id, today)
        ).fetchone()
        
        # 获取连续签到天数
        consecutive_days = 0
        if today_checkin:
            consecutive_days = today_checkin["consecutive_days"]
        else:
            # 检查昨天的记录
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            yesterday_checkin = conn.execute(
                "SELECT * FROM check_ins WHERE character_id = ? AND check_in_date = ?",
                (character_id, yesterday)
            ).fetchone()
            if yesterday_checkin:
                consecutive_days = yesterday_checkin["consecutive_days"]
        
        # 获取本月签到记录
        month_start = date.today().replace(day=1).isoformat()
        month_checkins = conn.execute(
            "SELECT check_in_date FROM check_ins WHERE character_id = ? AND check_in_date >= ?",
            (character_id, month_start)
        ).fetchall()
        
        return {
            "checked_in_today": today_checkin is not None,
            "consecutive_days": consecutive_days,
            "month_checkins": [r["check_in_date"] for r in month_checkins]
        }


# ============ 活动模板 ============

def get_activity_templates(character_id: int) -> list:
    """获取活动模板列表"""
    with get_db() as conn:
        templates = conn.execute(
            "SELECT * FROM activity_templates WHERE character_id = ? ORDER BY use_count DESC",
            (character_id,)
        ).fetchall()
        return [dict(t) for t in templates]


def add_activity_template(character_id: int, name: str, description: str, activity_type: str = None) -> dict:
    """添加活动模板"""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO activity_templates (character_id, name, description, activity_type) VALUES (?, ?, ?, ?)",
            (character_id, name, description, activity_type)
        )
        return {"id": cursor.lastrowid, "name": name, "description": description}


def delete_activity_template(template_id: int) -> bool:
    """删除活动模板"""
    with get_db() as conn:
        conn.execute("DELETE FROM activity_templates WHERE id = ?", (template_id,))
        return True


def use_activity_template(template_id: int) -> dict:
    """使用活动模板（增加使用次数）"""
    with get_db() as conn:
        conn.execute(
            "UPDATE activity_templates SET use_count = use_count + 1 WHERE id = ?",
            (template_id,)
        )
        template = conn.execute(
            "SELECT * FROM activity_templates WHERE id = ?",
            (template_id,)
        ).fetchone()
        return dict(template) if template else None
