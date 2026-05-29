import math
import random
from typing import Optional, Tuple, Dict, List
from datetime import datetime, timedelta


# ============================================
# LifeRPG 游戏引擎 v2.0
# 基于 RULES.md 规范实现
# ============================================


# ============ 属性配置 ============

# 五维属性定义
ATTRIBUTES = {
    "strength": {"name": "力量", "icon": " ", "desc": "身体素质、运动能力、体力"},
    "intelligence": {"name": "智力", "icon": " ", "desc": "学习能力、逻辑思维、知识储备"},
    "agility": {"name": "敏捷", "icon": " ", "desc": "反应速度、灵活性、协调性"},
    "charisma": {"name": "魅力", "icon": " ", "desc": "社交能力、领导力、表达能力"},
    "willpower": {"name": "意志", "icon": " ️", "desc": "毅力、自控力、专注力、决心"},
}

# 属性等级定义
ATTRIBUTE_LEVELS = [
    (1, 5, "薄弱"),
    (6, 10, "普通"),
    (11, 15, "良好"),
    (16, 20, "优秀"),
    (21, 25, "精英"),
    (26, 30, "大师"),
    (31, 100, "传说"),
]

# 属性上限
ATTRIBUTE_SOFT_CAP = 50  # 超过后提升速度减半
ATTRIBUTE_HARD_CAP = 100
ATTRIBUTE_INITIAL = 10

# 属性成长曲线配置
# 使用对数衰减模型，属性越高提升越难
ATTRIBUTE_GROWTH_CONFIG = {
    # 属性区间: (基础概率, 最大提升值)
    (1, 20): (1.0, 2),      # 初期：容易提升，最多+2
    (21, 40): (0.7, 2),     # 中期：概率降低
    (41, 60): (0.4, 1),     # 后期：很难提升
    (61, 80): (0.2, 1),     # 高级：极难提升
    (81, 100): (0.1, 1),    # 大师：每次+1都很难
}


# ============ 活动配置 ============

ACTIVITY_CONFIG = {
    "学习": {
        "base_exp": 30,
        "base_gold": 10,
        "primary_attr": "intelligence",
        "secondary_attr": "willpower",
        "keywords": ["上课", "看书", "学习", "复习", "做题", "写作业", "考试", "读书", "背单词", "练习"]
    },
    "运动": {
        "base_exp": 35,
        "base_gold": 12,
        "primary_attr": "strength",
        "secondary_attr": "agility",
        "keywords": ["健身", "跑步", "游泳", "打球", "运动", "锻炼", "瑜伽", "骑车", "爬山", "跳绳"]
    },
    "编程": {
        "base_exp": 40,
        "base_gold": 15,
        "primary_attr": "intelligence",
        "secondary_attr": "willpower",
        "keywords": ["写代码", "编程", "debug", "开发", "coding", "程序", "算法", "前端", "后端", "数据库"]
    },
    "社交": {
        "base_exp": 20,
        "base_gold": 8,
        "primary_attr": "charisma",
        "secondary_attr": None,
        "keywords": ["聚会", "聊天", "社交", "约会", "聚餐", "团建", "交流", "认识", "朋友", "派对"]
    },
    "工作": {
        "base_exp": 35,
        "base_gold": 20,
        "primary_attr": "willpower",
        "secondary_attr": "intelligence",
        "keywords": ["上班", "工作", "开会", "加班", "出差", "项目", "报告", "方案", "策划", "汇报"]
    },
    "创作": {
        "base_exp": 30,
        "base_gold": 12,
        "primary_attr": "intelligence",
        "secondary_attr": "charisma",
        "keywords": ["画画", "写作", "设计", "创作", "音乐", "摄影", "视频", "文章", "绘画", "编曲"]
    },
    "生活": {
        "base_exp": 15,
        "base_gold": 5,
        "primary_attr": "willpower",
        "secondary_attr": None,
        "keywords": ["做饭", "打扫", "整理", "购物", "洗衣", "清洁", "收拾", "家务", "买菜", "烹饪"]
    },
    "休息": {
        "base_exp": 10,
        "base_gold": 3,
        "primary_attr": "willpower",
        "secondary_attr": None,
        "keywords": ["睡觉", "午休", "休息", "放松", "冥想", "发呆", "散步", "泡澡", "按摩", "听音乐"]
    },
}


# ============ 等级系统 ============

def exp_for_level(level: int) -> int:
    """计算升级所需经验"""
    return int(100 * (1.5 ** (level - 1)))


def check_level_up(exp: int, level: int) -> Tuple[int, int]:
    """检查是否升级，返回 (新等级, 剩余经验)"""
    while exp >= exp_for_level(level):
        exp -= exp_for_level(level)
        level += 1
    return level, exp


def get_level_title(level: int) -> str:
    """根据等级获取头衔"""
    if level < 5:
        return "新手冒险者"
    elif level < 10:
        return "初级勇者"
    elif level < 20:
        return "中级战士"
    elif level < 30:
        return "高级英雄"
    elif level < 50:
        return "传奇大师"
    else:
        return "不朽传说"


def get_level_rewards(level: int) -> Dict:
    """获取升级奖励"""
    return {
        "attribute_points": 3,
        "gold": level * 10,
        "unlock_title": level % 10 == 0
    }


# ============ 属性系统 ============

def get_attribute_level(value: int) -> str:
    """获取属性等级名称"""
    for min_val, max_val, name in ATTRIBUTE_LEVELS:
        if min_val <= value <= max_val:
            return name
    return "传说"


def calculate_attribute_gain(current_value: int, base_gain: int = 1) -> Tuple[int, bool]:
    """
    计算属性提升（使用对数衰减模型）
    
    返回: (实际提升值, 是否成功提升)
    
    成长曲线:
    - 1-20:  容易提升，100%概率，最多+2
    - 21-40: 中等难度，70%概率
    - 41-60: 困难，40%概率
    - 61-80: 极难，20%概率
    - 81-100: 大师级，10%概率
    """
    if current_value >= ATTRIBUTE_HARD_CAP:
        return 0, False
    
    # 找到当前属性区间的配置
    prob = 0.1
    max_gain = 1
    for (min_val, max_val), (p, mg) in ATTRIBUTE_GROWTH_CONFIG.items():
        if min_val <= current_value <= max_val:
            prob = p
            max_gain = mg
            break
    
    # 随机决定是否提升
    if random.random() > prob:
        return 0, False
    
    # 计算实际提升值
    # 属性越高，越难获得最大提升
    value_factor = 1 - (current_value / ATTRIBUTE_HARD_CAP) * 0.5
    actual_max = max(1, int(max_gain * value_factor))
    
    gain = random.randint(1, actual_max)
    
    # 确保不超过上限
    if current_value + gain > ATTRIBUTE_HARD_CAP:
        gain = ATTRIBUTE_HARD_CAP - current_value
    
    return gain, True


def get_growth_probability(current_value: int) -> float:
    """获取当前属性的提升概率"""
    for (min_val, max_val), (prob, _) in ATTRIBUTE_GROWTH_CONFIG.items():
        if min_val <= current_value <= max_val:
            return prob
    return 0.1


def classify_activity(description: str) -> str:
    """根据描述自动分类活动类型"""
    desc_lower = description.lower()
    for activity_type, config in ACTIVITY_CONFIG.items():
        for keyword in config["keywords"]:
            if keyword in desc_lower:
                return activity_type
    return "其他"


# ============ 收益计算 ============

def calculate_exp_gain(
    activity_type: str,
    description: str,
    level: int,
    consecutive_days: int = 1
) -> int:
    """
    计算经验值收益
    
    公式:
    基础收益 = 活动基础EXP
    随机波动 = 基础 × random(0.8, 1.2)
    详情奖励 = min(描述长度 / 10, 5)
    等级缩放 = 1 + (等级 - 1) × 0.05
    连击加成 = 1 + (连续天数 - 1) × 0.1 (最高 +100%)
    
    最终EXP = (随机波动 + 详情奖励) × 等级缩放 × 连击加成
    """
    config = ACTIVITY_CONFIG.get(activity_type, ACTIVITY_CONFIG["工作"])
    
    # 基础收益
    base = config["base_exp"]
    
    # 随机波动 ±20%
    variation = base * random.uniform(0.8, 1.2)
    
    # 详情奖励（每10个字符+1，最高+5）
    detail_bonus = min(len(description) // 10, 5)
    
    # 等级缩放
    level_scale = 1 + (level - 1) * 0.05
    
    # 连击加成（每天+10%，最高+100%）
    streak_bonus = 1 + min(consecutive_days - 1, 10) * 0.1
    
    # 时间加成
    hour = datetime.now().hour
    time_bonus = 1.0
    if 0 <= hour < 6:  # 凌晨活动 +20%
        time_bonus = 1.2
    
    # 最终计算
    exp = int((variation + detail_bonus) * level_scale * streak_bonus * time_bonus)
    
    return max(exp, 5)  # 最少5经验


def calculate_gold_gain(
    activity_type: str,
    level: int,
    consecutive_days: int = 1
) -> int:
    """
    计算金币收益
    
    公式:
    基础收益 = 活动基础Gold
    随机波动 = 基础 × random(0.8, 1.2)
    等级缩放 = 1 + (等级 - 1) × 0.03
    
    最终Gold = 随机波动 × 等级缩放
    """
    config = ACTIVITY_CONFIG.get(activity_type, ACTIVITY_CONFIG["工作"])
    
    # 基础收益
    base = config["base_gold"]
    
    # 随机波动 ±20%
    variation = base * random.uniform(0.8, 1.2)
    
    # 等级缩放
    level_scale = 1 + (level - 1) * 0.03
    
    # 周末加成
    is_weekend = datetime.now().weekday() >= 5
    weekend_bonus = 1.2 if is_weekend else 1.0
    
    # 最终计算
    gold = int(variation * level_scale * weekend_bonus)
    
    return max(gold, 1)  # 最少1金币


def calculate_attribute_changes(
    activity_type: str,
    current_stats: Dict[str, int]
) -> Dict[str, int]:
    """
    计算属性变化
    
    规则（基于成长曲线）:
    - 主属性: 根据当前值有概率提升
    - 副属性: 较低概率提升
    - 额外属性: 极低概率提升
    """
    config = ACTIVITY_CONFIG.get(activity_type, ACTIVITY_CONFIG["工作"])
    changes = {}
    
    # 主属性（最高概率）
    primary = config["primary_attr"]
    if primary:
        current = current_stats.get(primary, 10)
        gain, success = calculate_attribute_gain(current)
        if success and gain > 0:
            changes[primary] = gain
    
    # 副属性（中等概率）
    secondary = config["secondary_attr"]
    if secondary and random.random() > 0.5:
        current = current_stats.get(secondary, 10)
        gain, success = calculate_attribute_gain(current)
        if success and gain > 0:
            changes[secondary] = gain
    
    # 额外属性（10%概率）
    if random.random() > 0.9:
        extra_attrs = [a for a in ATTRIBUTES.keys() if a not in changes]
        if extra_attrs:
            extra = random.choice(extra_attrs)
            current = current_stats.get(extra, 10)
            gain, success = calculate_attribute_gain(current)
            if success and gain > 0:
                changes[extra] = gain
    
    return changes


# ============ 装备系统 ============

# 装备稀有度配置
RARITY_CONFIG = {
    "普通": {"color": "#9d9d9d", "weight": 50, "stat_range": (1, 2)},
    "稀有": {"color": "#0070dd", "weight": 30, "stat_range": (3, 5)},
    "史诗": {"color": "#a335ee", "weight": 15, "stat_range": (6, 8)},
    "传说": {"color": "#ff8000", "weight": 5, "stat_range": (10, 15)},
}

# 装备池
EQUIPMENT_POOL = {
    "学习": [
        {"name": "学霸眼镜", "desc": "戴上后看书效率+50%", "rarity": "稀有", "bonus": {"intelligence": 3}},
        {"name": "知识之书", "desc": "蕴含无穷智慧的古籍", "rarity": "史诗", "bonus": {"intelligence": 6}},
        {"name": "专注护目镜", "desc": "减少99%的分心概率", "rarity": "稀有", "bonus": {"willpower": 3}},
        {"name": "速记笔", "desc": "写字速度翻倍", "rarity": "普通", "bonus": {"intelligence": 1}},
        {"name": "记忆面包", "desc": "吃下就能记住知识", "rarity": "传说", "bonus": {"intelligence": 10}},
    ],
    "运动": [
        {"name": "疾风跑鞋", "desc": "穿上后跑步速度+30%", "rarity": "稀有", "bonus": {"agility": 3}},
        {"name": "力量护腕", "desc": "隐藏的力量加成", "rarity": "稀有", "bonus": {"strength": 3}},
        {"name": "能量饮料(无限)", "desc": "永不枯竭的能量来源", "rarity": "传说", "bonus": {"strength": 10}},
        {"name": "运动手环", "desc": "记录每一次突破", "rarity": "普通", "bonus": {"agility": 1}},
        {"name": "筋膜枪", "desc": "快速恢复肌肉疲劳", "rarity": "史诗", "bonus": {"strength": 5}},
    ],
    "编程": [
        {"name": "机械键盘(RGB)", "desc": "打字速度+40%，bug率-20%", "rarity": "稀有", "bonus": {"intelligence": 3}},
        {"name": "Stack Overflow权杖", "desc": "可召唤全球程序员的帮助", "rarity": "传说", "bonus": {"intelligence": 12}},
        {"name": "调试放大镜", "desc": "一眼看穿所有bug", "rarity": "史诗", "bonus": {"intelligence": 6}},
        {"name": "代码咖啡杯", "desc": "咖啡因无限续杯", "rarity": "稀有", "bonus": {"willpower": 3}},
        {"name": "程序员格子衫", "desc": "传说中的编程圣衣", "rarity": "史诗", "bonus": {"intelligence": 5}},
    ],
    "社交": [
        {"name": "魅力项链", "desc": "社交魅力+50%", "rarity": "稀有", "bonus": {"charisma": 3}},
        {"name": "破冰笑话集", "desc": "永远不会冷场", "rarity": "普通", "bonus": {"charisma": 1}},
        {"name": "读心术眼镜", "desc": "看穿对方真实想法", "rarity": "传说", "bonus": {"charisma": 10}},
        {"name": "社交达人徽章", "desc": "人见人爱的证明", "rarity": "史诗", "bonus": {"charisma": 6}},
    ],
    "工作": [
        {"name": "效率手环", "desc": "工作效率+30%", "rarity": "稀有", "bonus": {"willpower": 3}},
        {"name": "时间管理沙漏", "desc": "每天多出2小时", "rarity": "史诗", "bonus": {"willpower": 6}},
        {"name": "升职加薪符", "desc": "隐藏的幸运加成", "rarity": "稀有", "bonus": {"charisma": 3}},
        {"name": "老板看不见斗篷", "desc": "摸鱼神器", "rarity": "传说", "bonus": {"agility": 10}},
    ],
    "其他": [
        {"name": "神秘徽章", "desc": "来历不明但感觉很厉害", "rarity": "普通", "bonus": {"strength": 1}},
        {"name": "幸运草", "desc": "今天运气不错", "rarity": "普通", "bonus": {"charisma": 1}},
        {"name": "时光碎片", "desc": "记录这一刻的纪念品", "rarity": "稀有", "bonus": {"intelligence": 2}},
        {"name": "全能水晶", "desc": "蕴含所有属性的力量", "rarity": "传说", "bonus": {"strength": 3, "intelligence": 3, "agility": 3, "charisma": 3, "willpower": 3}},
    ],
}


def roll_rarity(level: int) -> str:
    """根据等级随机选择稀有度"""
    # 等级越高，高稀有度概率越高
    level_bonus = level * 0.5
    
    weights = {
        "普通": max(50 - level_bonus, 20),
        "稀有": 30,
        "史诗": 15 + level_bonus * 0.3,
        "传说": 5 + level_bonus * 0.2,
    }
    
    rarities = list(weights.keys())
    weights_list = list(weights.values())
    
    return random.choices(rarities, weights=weights_list, k=1)[0]


def generate_equipment(activity_type: str, level: int) -> Optional[Dict]:
    """生成装备"""
    # 30%概率获得装备
    if random.random() > 0.3:
        return None
    
    # 选择装备池
    pool = EQUIPMENT_POOL.get(activity_type, EQUIPMENT_POOL["其他"])
    
    # 随机选择装备
    equipment = random.choice(pool)
    
    # 根据等级调整稀有度
    rarity = roll_rarity(level)
    
    # 如果随机稀有度比装备默认稀有度高，使用随机稀有度
    rarity_order = ["普通", "稀有", "史诗", "传说"]
    if rarity_order.index(rarity) > rarity_order.index(equipment["rarity"]):
        equipment = equipment.copy()
        equipment["rarity"] = rarity
    
    # 根据稀有度调整属性加成
    stat_min, stat_max = RARITY_CONFIG[equipment["rarity"]]["stat_range"]
    adjusted_bonus = {}
    for attr, base_value in equipment.get("bonus", {}).items():
        # 基础值 + 随机波动
        adjusted_value = base_value + random.randint(0, stat_max - stat_min)
        adjusted_bonus[attr] = min(adjusted_value, stat_max)
    
    return {
        "name": equipment["name"],
        "description": equipment["desc"],
        "rarity": equipment["rarity"],
        "stat_bonuses": adjusted_bonus,
        "special_effect": None
    }


# ============ 称号系统 ============

# 称号池
TITLE_POOL = {
    # 时间称号
    "time": [
        {"name": "凌晨战士", "desc": "在凌晨依然奋斗的人", "condition": "0-6点记录活动"},
        {"name": "熬夜冠军", "desc": "睡眠是什么？能吃吗？", "condition": "0-6点记录活动"},
        {"name": "早起鸟儿", "desc": "比太阳起得还早", "condition": "6-8点记录活动"},
        {"name": "夜猫子", "desc": "夜晚才是我的主场", "condition": "22-24点记录活动"},
    ],
    # 活动称号
    "学习": [
        {"name": "学霸附体", "desc": "今天学习状态爆表", "condition": "记录学习活动"},
        {"name": "知识收割机", "desc": "疯狂吸收知识中", "condition": "记录学习活动"},
        {"name": "图书馆常客", "desc": "书山有路勤为径", "condition": "记录10次学习"},
    ],
    "运动": [
        {"name": "健身狂人", "desc": "汗水就是我的勋章", "condition": "记录运动活动"},
        {"name": "钢铁之躯", "desc": "身体就是最好的武器", "condition": "记录运动活动"},
        {"name": "马拉松选手", "desc": "坚持就是胜利", "condition": "记录10次运动"},
    ],
    "编程": [
        {"name": "凌晨两点还在Debug的人", "desc": "代码就是我的生命", "condition": "记录编程活动"},
        {"name": "Bug猎人", "desc": "专门捕猎野生Bug", "condition": "记录编程活动"},
        {"name": "键盘侠", "desc": "用代码改变世界", "condition": "记录10次编程"},
        {"name": "全栈战士", "desc": "前后端通吃", "condition": "记录20次编程"},
    ],
    "社交": [
        {"name": "社交蝴蝶", "desc": "人见人爱花见花开", "condition": "记录社交活动"},
        {"name": "破冰专家", "desc": "没有我暖不了的场", "condition": "记录社交活动"},
    ],
    "工作": [
        {"name": "职场战士", "desc": "打工是不可能打工的...真香", "condition": "记录工作活动"},
        {"name": "加班达人", "desc": "老板看了都感动", "condition": "记录工作活动"},
    ],
    # 成就称号
    "achievement": [
        {"name": "连续登录", "desc": "坚持就是胜利", "condition": "连续7天记录"},
        {"name": "百小时", "desc": "时间的朋友", "condition": "累计100小时活动"},
        {"name": "全能战士", "desc": "均衡发展", "condition": "五项属性均15+"},
        {"name": "不朽传说", "desc": "登峰造极", "condition": "达到50级"},
    ],
}


def generate_title(
    activity_type: str,
    description: str,
    stats: Dict[str, int],
    consecutive_days: int = 1,
    total_activities: int = 0
) -> Optional[Dict]:
    """生成称号"""
    # 20%概率获得称号
    if random.random() > 0.2:
        return None
    
    candidates = []
    
    # 时间称号
    hour = datetime.now().hour
    if 0 <= hour < 6:
        candidates.extend([t for t in TITLE_POOL["time"] if "0-6" in t["condition"]])
    elif 6 <= hour < 8:
        candidates.extend([t for t in TITLE_POOL["time"] if "6-8" in t["condition"]])
    elif 22 <= hour < 24:
        candidates.extend([t for t in TITLE_POOL["time"] if "22-24" in t["condition"]])
    
    # 活动称号
    if activity_type in TITLE_POOL:
        candidates.extend(TITLE_POOL[activity_type])
    
    # 成就称号
    if consecutive_days >= 7:
        candidates.append(TITLE_POOL["achievement"][0])
    
    # 全能战士
    if all(v >= 15 for v in stats.values()):
        candidates.append(TITLE_POOL["achievement"][2])
    
    if not candidates:
        return None
    
    return random.choice(candidates)


# ============ 任务系统 ============

DAILY_QUESTS = [
    {
        "title": "今日学习任务",
        "description": "学习30分钟，阅读一本书的章节",
        "quest_type": "daily",
        "exp_base": 30,
        "gold_base": 10,
        "target_attr": "intelligence"
    },
    {
        "title": "运动挑战",
        "description": "完成20分钟的有氧运动",
        "quest_type": "daily",
        "exp_base": 35,
        "gold_base": 12,
        "target_attr": "strength"
    },
    {
        "title": "代码练习",
        "description": "解决一道算法题或写一个小项目",
        "quest_type": "daily",
        "exp_base": 40,
        "gold_base": 15,
        "target_attr": "intelligence"
    },
    {
        "title": "社交任务",
        "description": "和一个朋友聊天或帮助一个人",
        "quest_type": "daily",
        "exp_base": 20,
        "gold_base": 8,
        "target_attr": "charisma"
    },
    {
        "title": "生活整理",
        "description": "整理房间或做一顿健康的饭菜",
        "quest_type": "daily",
        "exp_base": 15,
        "gold_base": 5,
        "target_attr": "willpower"
    },
    {
        "title": "创意挑战",
        "description": "写一篇文章或画一幅画",
        "quest_type": "daily",
        "exp_base": 30,
        "gold_base": 12,
        "target_attr": "intelligence"
    },
]


def generate_quests(character_level: int, character_stats: Dict[str, int]) -> List[Dict]:
    """生成每日任务（3个）"""
    # 找出最弱属性
    weakest_attr = min(character_stats, key=character_stats.get)
    
    # 优先推荐针对最弱属性的任务
    priority_quests = [q for q in DAILY_QUESTS if q["target_attr"] == weakest_attr]
    other_quests = [q for q in DAILY_QUESTS if q["target_attr"] != weakest_attr]
    
    # 选择3个任务
    selected = []
    
    # 至少一个针对最弱属性的任务
    if priority_quests:
        selected.append(random.choice(priority_quests))
    
    # 填充剩余位置
    random.shuffle(other_quests)
    while len(selected) < 3 and other_quests:
        quest = other_quests.pop()
        if quest not in selected:
            selected.append(quest)
    
    # 计算奖励（基于等级）
    result = []
    for quest in selected:
        result.append({
            "title": quest["title"],
            "description": quest["description"],
            "quest_type": quest["quest_type"],
            "exp_reward": quest["exp_base"] + character_level * 5,
            "gold_reward": quest["gold_base"] + character_level * 2,
        })
    
    return result


# ============ 装备效果 ============

def get_rarity_color(rarity: str) -> str:
    """获取稀有度颜色"""
    return RARITY_CONFIG.get(rarity, {}).get("color", "#9d9d9d")


def calculate_total_stats(character_stats: Dict[str, int], equipment: List[Dict]) -> Dict[str, int]:
    """计算包含装备加成的总属性"""
    total = character_stats.copy()
    
    for equip in equipment:
        if equip.get("equipped") and equip.get("stat_bonuses"):
            bonuses = equip["stat_bonuses"]
            if isinstance(bonuses, str):
                import json
                bonuses = json.loads(bonuses)
            for attr, value in bonuses.items():
                if attr in total:
                    total[attr] += value
    
    return total


# ============ 统计函数 ============

def get_attribute_progress(value: int) -> Dict:
    """获取属性进度信息"""
    level_name = get_attribute_level(value)
    next_threshold = None
    
    for min_val, max_val, name in ATTRIBUTE_LEVELS:
        if value < min_val:
            next_threshold = min_val
            break
    
    progress = 0
    if next_threshold:
        current_min = max(1, value - 5)
        progress = (value - current_min) / (next_threshold - current_min) * 100
    
    return {
        "value": value,
        "level": level_name,
        "next_threshold": next_threshold,
        "progress": min(progress, 100)
    }
