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

# 属性等级定义（按 0-100 范围划分）
ATTRIBUTE_LEVELS = [
    (1, 30, "薄弱"),
    (31, 45, "普通"),
    (46, 60, "良好"),
    (61, 75, "优秀"),
    (76, 85, "精英"),
    (86, 95, "大师"),
    (96, 100, "传说"),
]

# 属性上限
ATTRIBUTE_SOFT_CAP = 75  # 超过后提升速度减半
ATTRIBUTE_HARD_CAP = 100
ATTRIBUTE_INITIAL = 50   # 初始属性基础值

# 属性成长曲线配置
# 使用对数衰减模型，属性越高提升越难
# 初始约50-65，提升到100需要长期积累
ATTRIBUTE_GROWTH_CONFIG = {
    # 属性区间: (基础概率, 最大提升值)
    (40, 55): (0.8, 3),     # 初期：容易提升，最多+3
    (56, 65): (0.6, 2),     # 中前期：概率降低，最多+2
    (66, 75): (0.4, 2),     # 中期：较难提升
    (76, 85): (0.3, 1),     # 中后期：很难提升
    (86, 95): (0.2, 1),     # 高级：极难提升
    (96, 100): (0.1, 1),    # 大师：每次+1都很难
}


# ============ 属性下限 ============
ATTRIBUTE_MIN = 10  # 属性最低值，不能降到10以下

# ============ 负面活动配置 ============
NEGATIVE_ACTIVITIES = {
    "沉迷游戏": {
        "keywords": ["打游戏", "玩游戏", "游戏一上午", "游戏一下午", "游戏几小时", "王者荣耀", "吃鸡", "LOL", "原神", "崩铁", "steam", "游戏停不下来"],
        "penalty": {"willpower": -2},
        "exp": 5,
        "gold": 2,
        "severity": "high"  # high: 3小时+, medium: 1-3小时, low: <1小时
    },
    "刷短视频": {
        "keywords": ["刷抖音", "刷视频", "刷短视频", "抖音", "快手", "B站", "小红书", "刷手机", "停不下来"],
        "penalty": {"willpower": -1},
        "exp": 5,
        "gold": 2,
        "severity": "medium"
    },
    "熬夜": {
        "keywords": ["熬夜", "通宵", "晚睡", "凌晨", "不睡觉"],
        "penalty": {"willpower": -1, "strength": -1},
        "exp": 3,
        "gold": 1,
        "severity": "high"
    },
    "拖延偷懒": {
        "keywords": ["拖延", "偷懒", "摸鱼", "无所事事", "发呆一整天", "啥也没干", "浪费时间"],
        "penalty": {"willpower": -2},
        "exp": 2,
        "gold": 1,
        "severity": "high"
    },
    "不健康饮食": {
        "keywords": ["垃圾食品", "暴饮暴食", "吃太多", "零食", "奶茶", "炸鸡", "外卖"],
        "penalty": {"strength": -1},
        "exp": 3,
        "gold": 1,
        "severity": "low"
    },
    "过度社交": {
        "keywords": ["水群", "聊天几小时", "无意义社交", "闲聊"],
        "penalty": {"willpower": -1},
        "exp": 3,
        "gold": 1,
        "severity": "medium"
    },
}

def classify_negative_activity(description: str) -> Optional[Dict]:
    """识别负面活动，返回负面活动配置或None"""
    import re
    desc_lower = description.lower()
    
    for activity_name, config in NEGATIVE_ACTIVITIES.items():
        # 先尝试精确匹配
        matched = False
        for keyword in config["keywords"]:
            if keyword in desc_lower:
                matched = True
                break
        
        # 如果精确匹配失败，尝试模式匹配
        if not matched:
            # 定义模式匹配规则
            pattern_rules = {
                "沉迷游戏": [r"打.{0,3}游戏", r"玩.{0,3}游戏", r"游戏.{0,5}", r"打.{0,3}王者", r"打.{0,3}吃鸡"],
                "刷短视频": [r"刷.{0,3}视频", r"刷.{0,3}抖音", r"看.{0,3}视频"],
                "熬夜": [r"熬.{0,3}夜", r"通.{0,3}宵", r"晚.{0,3}睡", r"凌晨.{0,5}不睡"],
                "拖延偷懒": [r"拖.{0,3}延", r"偷.{0,3}懒", r"摸.{0,3}鱼", r"浪费.{0,5}时间"],
                "不健康饮食": [r"吃.{0,3}垃圾食品", r"暴.{0,3}饮暴.{0,3}食", r"吃.{0,3}太多"],
                "过度社交": [r"水.{0,3}群", r"聊.{0,5}小时", r"闲.{0,3}聊"],
            }
            
            patterns = pattern_rules.get(activity_name, [])
            for pattern in patterns:
                if re.search(pattern, desc_lower):
                    matched = True
                    break
        
        if matched:
            # 根据描述中的时间信息调整惩罚程度
            penalty = config["penalty"].copy()
            exp = config["exp"]
            gold = config["gold"]
            
            # 检测时间长度关键词
            time_indicators = {
                "high": ["一上午", "一下午", "一整天", "几小时", "3小时", "4小时", "5小时", "6小时", "半天"],
                "medium": ["1小时", "2小时", "一会", "一会儿"],
                "low": ["一会", "半小时", "30分钟"]
            }
            
            severity = config["severity"]
            for level, indicators in time_indicators.items():
                for indicator in indicators:
                    if indicator in desc_lower:
                        severity = level
                        break
            
            # 根据严重程度调整惩罚
            if severity == "high":
                penalty = {k: v * 2 for k, v in penalty.items()}
                exp = max(exp - 3, 1)
                gold = max(gold - 1, 1)
            elif severity == "low":
                penalty = {k: int(v * 0.5) for k, v in penalty.items()}
                penalty = {k: max(v, -1) for k, v in penalty.items()}
            
            return {
                "activity_type": activity_name,
                "penalty": penalty,
                "exp": exp,
                "gold": gold,
                "severity": severity
            }
    
    return None

def apply_attribute_penalty(current_value: int, penalty: int) -> int:
    """应用属性惩罚，确保不低于最低值"""
    new_value = current_value + penalty
    return max(new_value, ATTRIBUTE_MIN)


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

# 装备池（贴近现实生活的物品）
EQUIPMENT_POOL = {
    "学习": [
        {"name": "学霸眼镜", "desc": "戴上后看书效率+50%", "rarity": "稀有", "bonus": {"intelligence": 3}, "use_desc": "擦干净镜片戴上", "use_effect": "视野清晰，专注力提升", "use_bonus": {"intelligence": 0.3}},
        {"name": "知识之书", "desc": "蕴含无穷智慧的古籍", "rarity": "史诗", "bonus": {"intelligence": 6}, "use_desc": "翻开阅读一章", "use_effect": "知识涌入脑海", "use_bonus": {"intelligence": 0.5}},
        {"name": "专注护目镜", "desc": "减少99%的分心概率", "rarity": "稀有", "bonus": {"willpower": 3}, "use_desc": "戴上护目镜开始学习", "use_effect": "世界安静了，只有知识", "use_bonus": {"willpower": 0.3}},
        {"name": "速记笔", "desc": "写字速度翻倍", "rarity": "普通", "bonus": {"intelligence": 1}, "use_desc": "用笔记录重点", "use_effect": "笔记工整，记忆加深", "use_bonus": {"intelligence": 0.1}},
        {"name": "记忆面包", "desc": "吃下就能记住知识", "rarity": "传说", "bonus": {"intelligence": 10}, "use_desc": "吃下面包", "use_effect": "知识点自动记忆", "use_bonus": {"intelligence": 1.0}},
        {"name": "荧光笔套装", "desc": "重点一目了然", "rarity": "普通", "bonus": {"intelligence": 1}, "use_desc": "标记重点内容", "use_effect": "重点突出，复习更高效", "use_bonus": {"intelligence": 0.1}},
        {"name": "隔音耳塞", "desc": "屏蔽外界干扰", "rarity": "稀有", "bonus": {"willpower": 2}, "use_desc": "戴上耳塞", "use_effect": "世界清静了", "use_bonus": {"willpower": 0.2}},
    ],
    "运动": [
        {"name": "毛巾", "desc": "运动后擦汗必备", "rarity": "普通", "bonus": {"strength": 1}, "use_desc": "运动后擦干汗水", "use_effect": "更清爽了", "use_bonus": {"charisma": 0.1}},
        {"name": "疾风跑鞋", "desc": "穿上后跑步速度+30%", "rarity": "稀有", "bonus": {"agility": 3}, "use_desc": "系好鞋带出发", "use_effect": "脚步轻盈，速度提升", "use_bonus": {"agility": 0.3}},
        {"name": "力量护腕", "desc": "隐藏的力量加成", "rarity": "稀有", "bonus": {"strength": 3}, "use_desc": "戴上护腕热身", "use_effect": "手腕有力，动作标准", "use_bonus": {"strength": 0.3}},
        {"name": "运动水壶", "desc": "及时补充水分", "rarity": "普通", "bonus": {"strength": 1}, "use_desc": "喝一口水", "use_effect": "水分补充，体力恢复", "use_bonus": {"strength": 0.1}},
        {"name": "运动手环", "desc": "记录每一次突破", "rarity": "普通", "bonus": {"agility": 1}, "use_desc": "查看运动数据", "use_effect": "看到进步，更有动力", "use_bonus": {"agility": 0.1}},
        {"name": "筋膜枪", "desc": "快速恢复肌肉疲劳", "rarity": "史诗", "bonus": {"strength": 5}, "use_desc": "按摩放松肌肉", "use_effect": "肌肉放松，疲劳消散", "use_bonus": {"strength": 0.5}},
        {"name": "瑜伽垫", "desc": "舒适防滑", "rarity": "普通", "bonus": {"agility": 2}, "use_desc": "铺开瑜伽垫", "use_effect": "开始拉伸，身体柔软", "use_bonus": {"agility": 0.2}},
        {"name": "蛋白粉", "desc": "肌肉修复加速器", "rarity": "稀有", "bonus": {"strength": 4}, "use_desc": "冲一杯蛋白粉", "use_effect": "肌肉修复，力量增长", "use_bonus": {"strength": 0.4}},
        {"name": "泡沫轴", "desc": "深度放松肌肉", "rarity": "稀有", "bonus": {"strength": 2}, "use_desc": "滚动放松大腿", "use_effect": "肌肉松开，舒适感up", "use_bonus": {"strength": 0.2}},
    ],
    "编程": [
        {"name": "机械键盘(RGB)", "desc": "打字速度+40%，bug率-20%", "rarity": "稀有", "bonus": {"intelligence": 3}, "use_desc": "敲击键盘写代码", "use_effect": "手感极佳，代码流畅", "use_bonus": {"intelligence": 0.3}},
        {"name": "Stack Overflow权杖", "desc": "可召唤全球程序员的帮助", "rarity": "传说", "bonus": {"intelligence": 12}, "use_desc": "搜索解决方案", "use_effect": "答案找到了！", "use_bonus": {"intelligence": 1.0}},
        {"name": "调试放大镜", "desc": "一眼看穿所有bug", "rarity": "史诗", "bonus": {"intelligence": 6}, "use_desc": "用放大镜找bug", "use_effect": "bug无处遁形", "use_bonus": {"intelligence": 0.5}},
        {"name": "代码咖啡杯", "desc": "咖啡因无限续杯", "rarity": "稀有", "bonus": {"willpower": 3}, "use_desc": "喝一口咖啡", "use_effect": "精神焕发，继续coding", "use_bonus": {"willpower": 0.3}},
        {"name": "程序员格子衫", "desc": "传说中的编程圣衣", "rarity": "史诗", "bonus": {"intelligence": 5}, "use_desc": "穿上格子衫", "use_effect": "编程之力涌来", "use_bonus": {"intelligence": 0.5}},
        {"name": "USB小风扇", "desc": "散热神器", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "打开风扇吹吹", "use_effect": "凉爽了，头脑清醒", "use_bonus": {"willpower": 0.1}},
        {"name": "蓝光眼镜", "desc": "保护眼睛", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "戴上蓝光眼镜", "use_effect": "眼睛不累了", "use_bonus": {"willpower": 0.1}},
        {"name": "人体工学椅", "desc": "久坐不累", "rarity": "稀有", "bonus": {"willpower": 4}, "use_desc": "调整坐姿", "use_effect": "腰不酸了，代码更久", "use_bonus": {"willpower": 0.4}},
    ],
    "社交": [
        {"name": "魅力项链", "desc": "社交魅力+50%", "rarity": "稀有", "bonus": {"charisma": 3}, "use_desc": "戴上项链出门", "use_effect": "自信满满", "use_bonus": {"charisma": 0.3}},
        {"name": "破冰笑话集", "desc": "永远不会冷场", "rarity": "普通", "bonus": {"charisma": 1}, "use_desc": "讲个笑话", "use_effect": "气氛活跃了", "use_bonus": {"charisma": 0.1}},
        {"name": "口香糖", "desc": "清新口气", "rarity": "普通", "bonus": {"charisma": 1}, "use_desc": "嚼一片口香糖", "use_effect": "口气清新，更自信", "use_bonus": {"charisma": 0.1}},
        {"name": "社交达人徽章", "desc": "人见人爱的证明", "rarity": "史诗", "bonus": {"charisma": 6}, "use_desc": "佩戴徽章", "use_effect": "社交buff加满", "use_bonus": {"charisma": 0.6}},
        {"name": "香水", "desc": "迷人气息", "rarity": "稀有", "bonus": {"charisma": 2}, "use_desc": "喷一点香水", "use_effect": "香气迷人，魅力up", "use_bonus": {"charisma": 0.2}},
        {"name": "微笑镜子", "desc": "练习微笑", "rarity": "普通", "bonus": {"charisma": 1}, "use_desc": "对着镜子微笑", "use_effect": "笑容更自然", "use_bonus": {"charisma": 0.1}},
    ],
    "工作": [
        {"name": "效率手环", "desc": "工作效率+30%", "rarity": "稀有", "bonus": {"willpower": 3}, "use_desc": "戴上手环开工", "use_effect": "专注模式启动", "use_bonus": {"willpower": 0.3}},
        {"name": "时间管理沙漏", "desc": "每天多出2小时", "rarity": "史诗", "bonus": {"willpower": 6}, "use_desc": "翻转沙漏开始计时", "use_effect": "时间观念增强", "use_bonus": {"willpower": 0.6}},
        {"name": "待办清单", "desc": "任务一目了然", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "列出今日任务", "use_effect": "目标清晰，效率提升", "use_bonus": {"willpower": 0.1}},
        {"name": "提神薄荷糖", "desc": "清凉醒脑", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "吃一颗薄荷糖", "use_effect": "精神一振", "use_bonus": {"willpower": 0.1}},
        {"name": "番茄钟", "desc": "25分钟专注法", "rarity": "稀有", "bonus": {"willpower": 3}, "use_desc": "启动番茄钟", "use_effect": "25分钟全神贯注", "use_bonus": {"willpower": 0.3}},
        {"name": "升职加薪符", "desc": "隐藏的幸运加成", "rarity": "稀有", "bonus": {"charisma": 3}, "use_desc": "默默祈祷", "use_effect": "感觉运气变好了", "use_bonus": {"charisma": 0.3}},
    ],
    "生活": [
        {"name": "保温杯", "desc": "多喝热水", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "喝一口热水", "use_effect": "暖暖的，很贴心", "use_bonus": {"willpower": 0.1}},
        {"name": "眼罩", "desc": "助眠神器", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "戴上眼罩休息", "use_effect": "进入深度睡眠", "use_bonus": {"willpower": 0.1}},
        {"name": "香薰蜡烛", "desc": "营造氛围", "rarity": "稀有", "bonus": {"charisma": 2}, "use_desc": "点燃蜡烛", "use_effect": "放松身心", "use_bonus": {"charisma": 0.2}},
        {"name": "按摩椅", "desc": "全身放松", "rarity": "史诗", "bonus": {"strength": 5}, "use_desc": "坐上按摩椅", "use_effect": "全身放松，疲劳消散", "use_bonus": {"strength": 0.5}},
        {"name": "绿植", "desc": "净化空气", "rarity": "普通", "bonus": {"charisma": 1}, "use_desc": "给植物浇浇水", "use_effect": "心情变好", "use_bonus": {"charisma": 0.1}},
        {"name": "抱枕", "desc": "柔软舒适", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "抱一抱抱枕", "use_effect": "压力释放", "use_bonus": {"willpower": 0.1}},
    ],
    "休息": [
        {"name": "助眠白噪音", "desc": "雨声、海浪声", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "播放白噪音", "use_effect": "进入深度睡眠", "use_bonus": {"willpower": 0.1}},
        {"name": "蒸汽眼罩", "desc": "热敷眼睛", "rarity": "稀有", "bonus": {"willpower": 2}, "use_desc": "戴上蒸汽眼罩", "use_effect": "眼睛疲劳消散", "use_bonus": {"willpower": 0.2}},
        {"name": "冥想APP会员", "desc": "专业引导冥想", "rarity": "稀有", "bonus": {"willpower": 3}, "use_desc": "开始冥想", "use_effect": "内心平静", "use_bonus": {"willpower": 0.3}},
        {"name": "薰衣草精油", "desc": "安神助眠", "rarity": "普通", "bonus": {"willpower": 1}, "use_desc": "滴一滴精油", "use_effect": "香气弥漫，放松入睡", "use_bonus": {"willpower": 0.1}},
    ],
    "其他": [
        {"name": "神秘徽章", "desc": "来历不明但感觉很厉害", "rarity": "普通", "bonus": {"strength": 1}, "use_desc": "佩戴徽章", "use_effect": "感觉神秘力量", "use_bonus": {"strength": 0.1}},
        {"name": "幸运草", "desc": "今天运气不错", "rarity": "普通", "bonus": {"charisma": 1}, "use_desc": "把幸运草放进口袋", "use_effect": "运气提升", "use_bonus": {"charisma": 0.1}},
        {"name": "时光碎片", "desc": "记录这一刻的纪念品", "rarity": "稀有", "bonus": {"intelligence": 2}, "use_desc": "回忆美好时光", "use_effect": "心情愉悦", "use_bonus": {"intelligence": 0.2}},
        {"name": "全能水晶", "desc": "蕴含所有属性的力量", "rarity": "传说", "bonus": {"strength": 3, "intelligence": 3, "agility": 3, "charisma": 3, "willpower": 3}, "use_desc": "握紧水晶", "use_effect": "全属性临时提升", "use_bonus": {"strength": 0.3, "intelligence": 0.3, "agility": 0.3, "charisma": 0.3, "willpower": 0.3}},
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
        "special_effect": None,
        "use_desc": equipment.get("use_desc", "使用物品"),
        "use_effect": equipment.get("use_effect", "感觉不错"),
        "use_bonus": equipment.get("use_bonus", {})
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
        {"name": "午间战士", "desc": "午休时间也不放过", "condition": "12-14点记录活动"},
    ],
    # 活动称号
    "学习": [
        {"name": "学霸附体", "desc": "今天学习状态爆表", "condition": "记录学习活动"},
        {"name": "知识收割机", "desc": "疯狂吸收知识中", "condition": "记录学习活动"},
        {"name": "图书馆常客", "desc": "书山有路勤为径", "condition": "记录10次学习"},
        {"name": "学神", "desc": "知识就是力量", "condition": "记录50次学习"},
        {"name": "终身学习者", "desc": "活到老学到老", "condition": "记录100次学习"},
    ],
    "运动": [
        {"name": "健身狂人", "desc": "汗水就是我的勋章", "condition": "记录运动活动"},
        {"name": "钢铁之躯", "desc": "身体就是最好的武器", "condition": "记录运动活动"},
        {"name": "马拉松选手", "desc": "坚持就是胜利", "condition": "记录10次运动"},
        {"name": "运动达人", "desc": "生命在于运动", "condition": "记录50次运动"},
        {"name": "铁人", "desc": "超越极限", "condition": "记录100次运动"},
    ],
    "编程": [
        {"name": "凌晨两点还在Debug的人", "desc": "代码就是我的生命", "condition": "记录编程活动"},
        {"name": "Bug猎人", "desc": "专门捕猎野生Bug", "condition": "记录编程活动"},
        {"name": "键盘侠", "desc": "用代码改变世界", "condition": "记录10次编程"},
        {"name": "全栈战士", "desc": "前后端通吃", "condition": "记录20次编程"},
        {"name": "代码之神", "desc": "代码如诗", "condition": "记录50次编程"},
        {"name": "架构师", "desc": "系统设计大师", "condition": "记录100次编程"},
    ],
    "社交": [
        {"name": "社交蝴蝶", "desc": "人见人爱花见花开", "condition": "记录社交活动"},
        {"name": "破冰专家", "desc": "没有我暖不了的场", "condition": "记录社交活动"},
        {"name": "人脉王", "desc": "朋友多了路好走", "condition": "记录20次社交"},
    ],
    "工作": [
        {"name": "职场战士", "desc": "打工是不可能打工的...真香", "condition": "记录工作活动"},
        {"name": "加班达人", "desc": "老板看了都感动", "condition": "记录工作活动"},
        {"name": "工作狂人", "desc": "热爱工作", "condition": "记录50次工作"},
    ],
    "创作": [
        {"name": "灵感缪斯", "desc": "创意无限", "condition": "记录创作活动"},
        {"name": "艺术大师", "desc": "用创作表达自我", "condition": "记录20次创作"},
    ],
    "生活": [
        {"name": "生活达人", "desc": "把生活过成诗", "condition": "记录10次生活"},
        {"name": "家务能手", "desc": "家里井井有条", "condition": "记录20次生活"},
    ],
    # 成就称号
    "achievement": [
        {"name": "初出茅庐", "desc": "完成第一次活动记录", "condition": "记录1次活动"},
        {"name": "连续登录", "desc": "坚持就是胜利", "condition": "连续7天记录"},
        {"name": "百次记录", "desc": "时间的朋友", "condition": "累计100次活动"},
        {"name": "全能战士", "desc": "均衡发展", "condition": "五项属性均50+"},
        {"name": "不朽传说", "desc": "登峰造极", "condition": "达到50级"},
        {"name": "签到达人", "desc": "风雨无阻", "condition": "连续签到30天"},
        {"name": "属性大师", "desc": "某项属性达到90", "condition": "任意属性90+"},
        {"name": "万能选手", "desc": "所有活动类型都尝试过", "condition": "8种活动类型各记录1次"},
        {"name": "效率之王", "desc": "一天记录5次活动", "condition": "单日5次活动"},
        {"name": "周末战士", "desc": "周末也不休息", "condition": "周末记录活动"},
    ],
    # 等级称号
    "level": [
        {"name": "新手冒险者", "desc": "刚刚开始旅程", "condition": "达到1级"},
        {"name": "初级勇者", "desc": "小有成就", "condition": "达到5级"},
        {"name": "中级战士", "desc": "实力渐长", "condition": "达到10级"},
        {"name": "高级英雄", "desc": "众人敬仰", "condition": "达到20级"},
        {"name": "传奇大师", "desc": "传说中的存在", "condition": "达到30级"},
        {"name": "不朽传说", "desc": "超越凡人", "condition": "达到50级"},
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

# 每日任务池
DAILY_QUESTS = [
    # 学习类
    {
        "title": "今日学习任务",
        "description": "学习30分钟，阅读一本书的章节",
        "quest_type": "daily",
        "exp_base": 30,
        "gold_base": 10,
        "target_attr": "intelligence"
    },
    {
        "title": "知识探索",
        "description": "学习一个新知识点或技能",
        "quest_type": "daily",
        "exp_base": 35,
        "gold_base": 12,
        "target_attr": "intelligence"
    },
    {
        "title": "复习巩固",
        "description": "复习之前学过的内容，加深记忆",
        "quest_type": "daily",
        "exp_base": 25,
        "gold_base": 8,
        "target_attr": "intelligence"
    },
    {
        "title": "阅读时光",
        "description": "阅读30分钟书籍或文章",
        "quest_type": "daily",
        "exp_base": 28,
        "gold_base": 10,
        "target_attr": "intelligence"
    },
    
    # 运动类
    {
        "title": "运动挑战",
        "description": "完成20分钟的有氧运动",
        "quest_type": "daily",
        "exp_base": 35,
        "gold_base": 12,
        "target_attr": "strength"
    },
    {
        "title": "晨间锻炼",
        "description": "早起做10分钟拉伸运动",
        "quest_type": "daily",
        "exp_base": 25,
        "gold_base": 8,
        "target_attr": "agility"
    },
    {
        "title": "步行挑战",
        "description": "步行至少30分钟或6000步",
        "quest_type": "daily",
        "exp_base": 30,
        "gold_base": 10,
        "target_attr": "strength"
    },
    {
        "title": "核心训练",
        "description": "做3组平板支撑或仰卧起坐",
        "quest_type": "daily",
        "exp_base": 32,
        "gold_base": 11,
        "target_attr": "strength"
    },
    
    # 编程类
    {
        "title": "代码练习",
        "description": "解决一道算法题或写一个小项目",
        "quest_type": "daily",
        "exp_base": 40,
        "gold_base": 15,
        "target_attr": "intelligence"
    },
    {
        "title": "代码重构",
        "description": "优化一段旧代码，提升代码质量",
        "quest_type": "daily",
        "exp_base": 35,
        "gold_base": 12,
        "target_attr": "intelligence"
    },
    {
        "title": "技术学习",
        "description": "学习一个新的框架或工具",
        "quest_type": "daily",
        "exp_base": 38,
        "gold_base": 14,
        "target_attr": "intelligence"
    },
    
    # 社交类
    {
        "title": "社交任务",
        "description": "和一个朋友聊天或帮助一个人",
        "quest_type": "daily",
        "exp_base": 20,
        "gold_base": 8,
        "target_attr": "charisma"
    },
    {
        "title": "感恩表达",
        "description": "向一个人表达感谢或赞美",
        "quest_type": "daily",
        "exp_base": 18,
        "gold_base": 7,
        "target_attr": "charisma"
    },
    {
        "title": "倾听时刻",
        "description": "认真倾听一个人的烦恼或故事",
        "quest_type": "daily",
        "exp_base": 22,
        "gold_base": 9,
        "target_attr": "charisma"
    },
    
    # 生活类
    {
        "title": "生活整理",
        "description": "整理房间或做一顿健康的饭菜",
        "quest_type": "daily",
        "exp_base": 15,
        "gold_base": 5,
        "target_attr": "willpower"
    },
    {
        "title": "健康饮食",
        "description": "吃一顿营养均衡的饭菜",
        "quest_type": "daily",
        "exp_base": 12,
        "gold_base": 4,
        "target_attr": "willpower"
    },
    {
        "title": "早睡早起",
        "description": "今晚11点前睡觉",
        "quest_type": "daily",
        "exp_base": 20,
        "gold_base": 8,
        "target_attr": "willpower"
    },
    {
        "title": "断网时光",
        "description": "放下手机1小时，专注做一件事",
        "quest_type": "daily",
        "exp_base": 25,
        "gold_base": 10,
        "target_attr": "willpower"
    },
    
    # 创意类
    {
        "title": "创意挑战",
        "description": "写一篇文章或画一幅画",
        "quest_type": "daily",
        "exp_base": 30,
        "gold_base": 12,
        "target_attr": "intelligence"
    },
    {
        "title": "摄影练习",
        "description": "拍摄3张有创意的照片",
        "quest_type": "daily",
        "exp_base": 22,
        "gold_base": 8,
        "target_attr": "charisma"
    },
    {
        "title": "音乐时光",
        "description": "练习乐器或学习一首新歌",
        "quest_type": "daily",
        "exp_base": 28,
        "gold_base": 10,
        "target_attr": "agility"
    },
    
    # 冥想放松类
    {
        "title": "冥想练习",
        "description": "冥想10分钟，放松身心",
        "quest_type": "daily",
        "exp_base": 18,
        "gold_base": 6,
        "target_attr": "willpower"
    },
    {
        "title": "深呼吸",
        "description": "做5分钟深呼吸练习",
        "quest_type": "daily",
        "exp_base": 12,
        "gold_base": 4,
        "target_attr": "willpower"
    },
]

# 每周任务池
WEEKLY_QUESTS = [
    {
        "title": "周运动目标",
        "description": "本周运动3次，每次30分钟以上",
        "quest_type": "weekly",
        "exp_base": 150,
        "gold_base": 50,
        "target_attr": "strength"
    },
    {
        "title": "阅读一本书",
        "description": "本周读完一本书",
        "quest_type": "weekly",
        "exp_base": 180,
        "gold_base": 60,
        "target_attr": "intelligence"
    },
    {
        "title": "社交达人",
        "description": "本周参加一次社交活动",
        "quest_type": "weekly",
        "exp_base": 120,
        "gold_base": 40,
        "target_attr": "charisma"
    },
    {
        "title": "技能提升",
        "description": "本周学习一个新技能或完成一个项目",
        "quest_type": "weekly",
        "exp_base": 200,
        "gold_base": 70,
        "target_attr": "intelligence"
    },
    {
        "title": "生活习惯",
        "description": "本周坚持早睡早起5天",
        "quest_type": "weekly",
        "exp_base": 160,
        "gold_base": 55,
        "target_attr": "willpower"
    },
    {
        "title": "创意周",
        "description": "本周完成一个创意作品",
        "quest_type": "weekly",
        "exp_base": 170,
        "gold_base": 58,
        "target_attr": "charisma"
    },
    {
        "title": "健康饮食周",
        "description": "本周自己做饭至少3次",
        "quest_type": "weekly",
        "exp_base": 140,
        "gold_base": 45,
        "target_attr": "willpower"
    },
    {
        "title": "整理大师",
        "description": "本周彻底整理一次房间",
        "quest_type": "weekly",
        "exp_base": 130,
        "gold_base": 42,
        "target_attr": "willpower"
    },
]

# 挑战任务池（难度较高，奖励丰厚）
CHALLENGE_QUESTS = [
    {
        "title": "马拉松挑战",
        "description": "连续跑步5公里",
        "quest_type": "challenge",
        "exp_base": 300,
        "gold_base": 100,
        "target_attr": "strength"
    },
    {
        "title": "编程马拉松",
        "description": "连续编程4小时完成一个项目",
        "quest_type": "challenge",
        "exp_base": 350,
        "gold_base": 120,
        "target_attr": "intelligence"
    },
    {
        "title": "社交达人挑战",
        "description": "一天内和5个不同的人交流",
        "quest_type": "challenge",
        "exp_base": 250,
        "gold_base": 85,
        "target_attr": "charisma"
    },
    {
        "title": "极限专注",
        "description": "连续专注工作/学习2小时不休息",
        "quest_type": "challenge",
        "exp_base": 280,
        "gold_base": 95,
        "target_attr": "willpower"
    },
    {
        "title": "全能挑战",
        "description": "今天完成学习、运动、社交各一项",
        "quest_type": "challenge",
        "exp_base": 320,
        "gold_base": 110,
        "target_attr": "agility"
    },
    {
        "title": "早起挑战",
        "description": "连续3天早上6点前起床",
        "quest_type": "challenge",
        "exp_base": 260,
        "gold_base": 88,
        "target_attr": "willpower"
    },
    {
        "title": "阅读马拉松",
        "description": "连续阅读2小时",
        "quest_type": "challenge",
        "exp_base": 270,
        "gold_base": 90,
        "target_attr": "intelligence"
    },
    {
        "title": "厨艺挑战",
        "description": "做一道从没做过的菜",
        "quest_type": "challenge",
        "exp_base": 240,
        "gold_base": 80,
        "target_attr": "agility"
    },
]

# 成就任务（一次性完成）
ACHIEVEMENT_QUESTS = [
    {
        "title": "初次冒险",
        "description": "完成第一次活动记录",
        "quest_type": "achievement",
        "exp_base": 50,
        "gold_base": 20,
        "target_attr": None
    },
    {
        "title": "连续三天",
        "description": "连续3天记录活动",
        "quest_type": "achievement",
        "exp_base": 100,
        "gold_base": 35,
        "target_attr": "willpower"
    },
    {
        "title": "一周坚持",
        "description": "连续7天记录活动",
        "quest_type": "achievement",
        "exp_base": 250,
        "gold_base": 80,
        "target_attr": "willpower"
    },
    {
        "title": "百次记录",
        "description": "累计记录100次活动",
        "quest_type": "achievement",
        "exp_base": 500,
        "gold_base": 150,
        "target_attr": "willpower"
    },
    {
        "title": "属性大师",
        "description": "任意一项属性达到20",
        "quest_type": "achievement",
        "exp_base": 300,
        "gold_base": 100,
        "target_attr": None
    },
    {
        "title": "全能战士",
        "description": "所有属性都达到15",
        "quest_type": "achievement",
        "exp_base": 400,
        "gold_base": 130,
        "target_attr": None
    },
    {
        "title": "装备收藏家",
        "description": "收集10件装备",
        "quest_type": "achievement",
        "exp_base": 200,
        "gold_base": 65,
        "target_attr": None
    },
    {
        "title": "称号达人",
        "description": "获得5个称号",
        "quest_type": "achievement",
        "exp_base": 180,
        "gold_base": 60,
        "target_attr": None
    },
]


def generate_quests(character_level: int, character_stats: Dict[str, int], quest_type: str = "daily") -> List[Dict]:
    """生成任务"""
    # 找出最弱属性
    weakest_attr = min(character_stats, key=character_stats.get)
    
    # 根据任务类型选择任务池
    if quest_type == "weekly":
        quest_pool = WEEKLY_QUESTS
        quest_count = 2  # 每周任务2个
    elif quest_type == "challenge":
        quest_pool = CHALLENGE_QUESTS
        quest_count = 1  # 挑战任务1个
    else:
        quest_pool = DAILY_QUESTS
        quest_count = 3  # 每日任务3个
    
    # 优先推荐针对最弱属性的任务
    priority_quests = [q for q in quest_pool if q.get("target_attr") == weakest_attr]
    other_quests = [q for q in quest_pool if q.get("target_attr") != weakest_attr]
    
    # 选择任务
    selected = []
    
    # 至少一个针对最弱属性的任务
    if priority_quests:
        selected.append(random.choice(priority_quests))
    
    # 填充剩余位置
    random.shuffle(other_quests)
    while len(selected) < quest_count and other_quests:
        quest = other_quests.pop()
        if quest not in selected:
            selected.append(quest)
    
    # 计算奖励（基于等级）
    result = []
    for quest in selected:
        # 不同类型任务的奖励倍率
        multiplier = {
            "daily": 1,
            "weekly": 1.5,
            "challenge": 2,
            "achievement": 1
        }.get(quest.get("quest_type", "daily"), 1)
        
        result.append({
            "title": quest["title"],
            "description": quest["description"],
            "quest_type": quest.get("quest_type", "daily"),
            "exp_reward": int((quest["exp_base"] + character_level * 5) * multiplier),
            "gold_reward": int((quest["gold_base"] + character_level * 2) * multiplier),
        })
    
    return result


def generate_all_quests(character_level: int, character_stats: Dict[str, int]) -> Dict[str, List[Dict]]:
    """生成所有类型的任务"""
    return {
        "daily": generate_quests(character_level, character_stats, "daily"),
        "weekly": generate_quests(character_level, character_stats, "weekly"),
        "challenge": generate_quests(character_level, character_stats, "challenge"),
    }


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
