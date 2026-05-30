import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime, timedelta

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
                character_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'entertainment',
                cost INTEGER NOT NULL,
                icon TEXT DEFAULT ' ',
                is_custom BOOLEAN DEFAULT 0,
                times_redeemed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );

            CREATE TABLE IF NOT EXISTS immunity_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                cost INTEGER NOT NULL,
                uses_remaining INTEGER DEFAULT 1,
                card_type TEXT DEFAULT 'skip_task',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
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
            ("看一集电视剧", "放松一下，追剧时间到！", "entertainment", 30, " "),
            ("玩30分钟游戏", "适度游戏益脑，沉迷游戏伤身", "entertainment", 50, " ️",
            ("吃一顿好的", "美食是最好的奖励", "food", 80, " "),
            ("睡个懒觉", "明天多睡30分钟", "rest", 40, " ️"),
            ("买一本想看的书", "知识就是力量", "education", 100, " "),
            ("看一部电影", "光影世界，放松心情", "entertainment", 60, " "),
            ("喝一杯奶茶", "甜蜜的小确幸", "food", 20, " "),
            ("逛街购物", "买买买！", "shopping", 150, " ️"),
        ]
        
        # 检查是否已有默认奖励
        count = conn.execute("SELECT COUNT(*) FROM reality_rewards WHERE is_custom = 0").fetchone()[0]
        if count == 0:
            for name, desc, cat, cost, icon in default_rewards:
                conn.execute(
                    "INSERT INTO reality_rewards (character_id, name, description, category, cost, icon, is_custom) VALUES (0, ?, ?, ?, ?, ?, 0)",
                    (name, desc, cat, cost, icon)
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


def create_habit_challenge(character_id: int, name: str, description: str, duration_days: int, cost: int) -> dict:
    """创建习惯挑战"""
    with get_db() as conn:
        # 检查金币
        character = conn.execute("SELECT gold FROM characters WHERE id = ?", (character_id,)).fetchone()
        if not character or character["gold"] < cost:
            return {"success": False, "error": "金币不足"}
        
        # 扣除金币
        conn.execute("UPDATE characters SET gold = gold - ? WHERE id = ?", (cost, character_id))
        
        # 创建挑战
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=duration_days)
        cursor = conn.execute(
            """INSERT INTO habit_challenges 
               (character_id, name, description, duration_days, cost, start_date, end_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (character_id, name, description, duration_days, cost, start_date, end_date)
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
