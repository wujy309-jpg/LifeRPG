"""
LifeRPG 智能体核心模块
实现自主性、反应性、主动性、社交能力等智能体特征
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from agent_database import (
    get_or_create_user_profile, update_user_profile,
    add_behavior_memory, get_behavior_memories, search_memories,
    add_conversation, get_conversation_history, get_recent_conversations,
    create_long_term_goal, get_long_term_goals, update_goal_progress,
    create_task_plan, get_task_plans, complete_task_plan,
    create_notification, get_pending_notifications, mark_notification_sent,
    get_unread_notifications, mark_notification_read,
    log_emotion, get_recent_emotions, get_emotion_stats,
    log_tool_call, get_tool_calls,
    log_decision, get_decision_logs, update_decision_outcome,
    get_agent_config, update_agent_config
)
from ai_service import chat_with_ai


class LifeRPGAgent:
    """LifeRPG 智能体"""
    
    def __init__(self):
        self.name = "LifeRPG Agent"
        self.version = "2.0"
        self.capabilities = [
            "memory",          # 记忆系统
            "proactive",       # 主动推送
            "planning",        # 规划系统
            "tools",           # 工具调用
            "emotion",         # 情绪感知
            "dialogue",        # 多轮对话
            "decision"         # 自主决策
        ]
    
    # ==================== 记忆系统 ====================
    
    def analyze_behavior_patterns(self, character_id: int) -> Dict:
        """分析用户行为模式"""
        # 获取最近的活动记录
        from database import get_activity_logs
        recent_logs = get_activity_logs(character_id, limit=100)
        
        if not recent_logs:
            return {"patterns": [], "insights": []}
        
        # 分析活动类型分布
        activity_counts = {}
        activity_times = {}
        activity_days = {}
        
        for log in recent_logs:
            activity_type = log.get("activity_type", "其他")
            created_at = log.get("created_at", "")
            
            # 统计活动类型
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
            
            # 分析活动时间
            if created_at:
                try:
                    dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    hour = dt.hour
                    day = dt.strftime("%A")
                    
                    if activity_type not in activity_times:
                        activity_times[activity_type] = []
                    activity_times[activity_type].append(hour)
                    
                    if activity_type not in activity_days:
                        activity_days[activity_type] = []
                    activity_days[activity_type].append(day)
                except:
                    pass
        
        # 识别模式
        patterns = []
        insights = []
        
        # 最常做的活动
        if activity_counts:
            most_common = max(activity_counts.items(), key=lambda x: x[1])
            patterns.append({
                "type": "most_common_activity",
                "activity": most_common[0],
                "count": most_common[1],
                "percentage": round(most_common[1] / len(recent_logs) * 100, 1)
            })
            insights.append(f"你最常做的活动是{most_common[0]}，占总活动的{round(most_common[1] / len(recent_logs) * 100, 1)}%")
        
        # 高效时段分析
        for activity_type, times in activity_times.items():
            if len(times) >= 3:
                avg_hour = sum(times) / len(times)
                if 6 <= avg_hour <= 11:
                    time_label = "上午"
                elif 12 <= avg_hour <= 17:
                    time_label = "下午"
                elif 18 <= avg_hour <= 22:
                    time_label = "晚上"
                else:
                    time_label = "深夜"
                
                patterns.append({
                    "type": "peak_time",
                    "activity": activity_type,
                    "time": time_label,
                    "avg_hour": round(avg_hour, 1)
                })
                insights.append(f"你通常在{time_label}做{activity_type}活动")
        
        # 更新用户画像
        update_user_profile(
            character_id,
            activity_patterns=json.dumps(patterns),
            peak_hours=json.dumps([p for p in patterns if p.get("type") == "peak_time"])
        )
        
        # 存储行为记忆
        add_behavior_memory(
            character_id=character_id,
            memory_type="semantic",
            content=f"用户行为模式分析：{', '.join(insights)}",
            context={"patterns": patterns},
            importance=0.7,
            emotion="neutral",
            related_activity="behavior_analysis"
        )
        
        return {"patterns": patterns, "insights": insights}
    
    def learn_from_activity(self, character_id: int, activity_type: str, 
                           description: str, result: Dict):
        """从活动中学习"""
        # 记录行为记忆
        importance = 0.5
        if result.get("level_up"):
            importance = 0.9
        elif result.get("equipment_found"):
            importance = 0.7
        
        add_behavior_memory(
            character_id=character_id,
            memory_type="episodic",
            content=f"完成了{activity_type}活动：{description}",
            context={
                "exp_gained": result.get("exp_gained", 0),
                "gold_gained": result.get("gold_gained", 0),
                "attribute_changes": result.get("attribute_changes", {})
            },
            importance=importance,
            emotion="positive" if result.get("exp_gained", 0) > 0 else "negative",
            related_activity=activity_type
        )
        
        # 更新用户画像中的习惯
        profile = get_or_create_user_profile(character_id)
        habits = json.loads(profile.get("habits", "{}"))
        
        if activity_type not in habits:
            habits[activity_type] = {"count": 0, "last_time": None}
        
        habits[activity_type]["count"] += 1
        habits[activity_type]["last_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        update_user_profile(character_id, habits=json.dumps(habits))
    
    def get_personalized_suggestion(self, character_id: int) -> str:
        """获取个性化建议"""
        profile = get_or_create_user_profile(character_id)
        memories = get_behavior_memories(character_id, limit=10)
        
        # 分析弱项属性
        from database import get_character
        character = get_character(character_id)
        if not character:
            return "请先创建角色"
        
        attributes = {
            "strength": character.get("strength", 50),
            "intelligence": character.get("intelligence", 50),
            "agility": character.get("agility", 50),
            "charisma": character.get("charisma", 50),
            "willpower": character.get("willpower", 50)
        }
        
        weakest = min(attributes.items(), key=lambda x: x[1])
        
        # 基于弱项提供建议
        suggestions = {
            "strength": "建议多做运动类活动，如跑步、健身、打球等",
            "intelligence": "建议多做学习类活动，如阅读、编程、学习新技能等",
            "agility": "建议多做需要灵活性的活动，如瑜伽、舞蹈、球类运动等",
            "charisma": "建议多做社交类活动，如聚会、聊天、团队活动等",
            "willpower": "建议多做需要毅力的活动，如冥想、早起、坚持习惯等"
        }
        
        return suggestions.get(weakest[0], "继续保持均衡发展")
    
    # ==================== 情绪感知系统 ====================
    
    def detect_emotion_from_text(self, text: str) -> Dict:
        """从文本中检测情绪"""
        # 简单的情绪关键词匹配
        emotion_keywords = {
            "happy": ["开心", "高兴", "快乐", "棒", "好", "赞", "哈哈", "太好了", "不错"],
            "sad": ["难过", "伤心", "失望", "累", "疲惫", "唉", "糟糕"],
            "angry": ["生气", "愤怒", "烦", "讨厌", "气死", "恼火"],
            "anxious": ["焦虑", "紧张", "担心", "害怕", "压力", "不安"],
            "excited": ["兴奋", "激动", "期待", "太棒了", "厉害"],
            "neutral": ["一般", "还好", "普通", "正常"]
        }
        
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if not emotion_scores:
            return {"emotion": "neutral", "intensity": 0.5, "confidence": 0.3}
        
        # 找到最匹配的情绪
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        intensity = min(primary_emotion[1] / 3.0, 1.0)  # 归一化到0-1
        
        return {
            "emotion": primary_emotion[0],
            "intensity": intensity,
            "confidence": 0.6 + intensity * 0.3
        }
    
    def detect_emotion_from_activity(self, character_id: int, activity_type: str,
                                    description: str) -> Dict:
        """从活动中检测情绪"""
        # 正面活动
        positive_activities = ["运动", "学习", "社交", "创作"]
        # 负面活动
        negative_activities = ["沉迷游戏", "刷短视频", "熬夜", "拖延偷懒"]
        
        if activity_type in positive_activities:
            return {"emotion": "happy", "intensity": 0.6, "source": "activity"}
        elif activity_type in negative_activities:
            return {"emotion": "sad", "intensity": 0.5, "source": "activity"}
        
        # 检查描述中的情绪词
        return self.detect_emotion_from_text(description)
    
    def get_emotion_based_response(self, character_id: int, base_response: str) -> str:
        """根据情绪状态调整回复"""
        recent_emotions = get_recent_emotions(character_id, hours=24)
        
        if not recent_emotions:
            return base_response
        
        # 计算主导情绪
        emotion_counts = {}
        for record in recent_emotions:
            emotion = record.get("emotion", "neutral")
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        # 根据情绪调整回复风格
        emotion_adjustments = {
            "happy": "继续保持好心情！",
            "sad": "别难过，每个人都有低谷期，相信明天会更好！",
            "angry": "深呼吸，冷静一下，没什么大不了的。",
            "anxious": "放轻松，一步一步来，你比你想象的更强大。",
            "excited": "你的热情很棒！把这份能量用在正事上吧！",
            "neutral": ""
        }
        
        adjustment = emotion_adjustments.get(dominant_emotion, "")
        if adjustment:
            return f"{base_response}\n\n{adjustment}"
        return base_response
    
    def record_emotion(self, character_id: int, emotion: str, intensity: float = 0.5,
                      trigger: str = None, activity_context: str = None,
                      detected_from: str = "text") -> Dict:
        """记录情绪"""
        return log_emotion(
            character_id=character_id,
            emotion=emotion,
            intensity=intensity,
            trigger=trigger,
            activity_context=activity_context,
            detected_from=detected_from
        )
    
    # ==================== 多轮对话系统 ====================
    
    def start_conversation(self, character_id: int) -> str:
        """开始新对话"""
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        # 记录系统消息
        add_conversation(
            character_id=character_id,
            session_id=session_id,
            role="system",
            content="对话开始",
            context={"session_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        )
        
        return session_id
    
    def process_message(self, character_id: int, session_id: str, 
                       message: str) -> Dict:
        """处理用户消息"""
        # 检测情绪
        emotion_result = self.detect_emotion_from_text(message)
        
        # 记录用户消息
        add_conversation(
            character_id=character_id,
            session_id=session_id,
            role="user",
            content=message,
            emotion=emotion_result.get("emotion"),
            context={"emotion_intensity": emotion_result.get("intensity")}
        )
        
        # 获取对话历史
        history = get_conversation_history(character_id, session_id, limit=10)
        
        # 分析意图
        intent = self.analyze_intent(message)
        
        # 生成回复
        response = self.generate_response(character_id, session_id, message, 
                                         intent, emotion_result, history)
        
        # 记录助手回复
        add_conversation(
            character_id=character_id,
            session_id=session_id,
            role="assistant",
            content=response,
            intent=intent,
            context={"response_to": message[:50]}
        )
        
        # 记录情绪
        self.record_emotion(
            character_id=character_id,
            emotion=emotion_result.get("emotion", "neutral"),
            intensity=emotion_result.get("intensity", 0.5),
            trigger=message[:50],
            activity_context=intent,
            detected_from="text"
        )
        
        return {
            "response": response,
            "intent": intent,
            "emotion": emotion_result,
            "session_id": session_id
        }
    
    def analyze_intent(self, message: str) -> str:
        """分析用户意图"""
        message_lower = message.lower()
        
        # 意图关键词映射
        intent_keywords = {
            "record_activity": ["记录", "做了", "完成", "今天", "刚刚"],
            "check_status": ["状态", "属性", "等级", "经验", "金币"],
            "get_suggestion": ["建议", "推荐", "应该", "做什么"],
            "check_quests": ["任务", "每日", "每周", "挑战"],
            "view_equipment": ["装备", "物品", "背包"],
            "emotional_support": ["难过", "累", "压力", "焦虑", "烦"],
            "general_chat": ["聊天", "聊聊", "无聊"]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return intent
        
        return "general_chat"
    
    def generate_response(self, character_id: int, session_id: str,
                         message: str, intent: str, emotion: Dict,
                         history: List) -> str:
        """生成回复"""
        # 基于意图生成回复
        if intent == "record_activity":
            return self._handle_record_activity(character_id, message)
        elif intent == "check_status":
            return self._handle_check_status(character_id)
        elif intent == "get_suggestion":
            return self._handle_get_suggestion(character_id)
        elif intent == "check_quests":
            return self._handle_check_quests(character_id)
        elif intent == "view_equipment":
            return self._handle_view_equipment(character_id)
        elif intent == "emotional_support":
            return self._handle_emotional_support(character_id, message, emotion)
        else:
            return self._handle_general_chat(character_id, message, history)
    
    def _handle_record_activity(self, character_id: int, message: str) -> str:
        """处理记录活动意图"""
        return "好的，请告诉我你做了什么活动？我会帮你记录并计算奖励。"
    
    def _handle_check_status(self, character_id: int) -> str:
        """处理查看状态意图"""
        from database import get_character
        character = get_character(character_id)
        if not character:
            return "请先创建角色"
        
        return (
            f"当前状态：\n"
            f"等级：{character['level']}\n"
            f"经验：{character['exp']}\n"
            f"金币：{character['gold']}\n"
            f"力量：{character['strength']} | 智力：{character['intelligence']} | "
            f"敏捷：{character['agility']} | 魅力：{character['charisma']} | "
            f"意志：{character['willpower']}"
        )
    
    def _handle_get_suggestion(self, character_id: int) -> str:
        """处理获取建议意图"""
        return self.get_personalized_suggestion(character_id)
    
    def _handle_check_quests(self, character_id: int) -> str:
        """处理查看任务意图"""
        from database import get_quests
        quests = get_quests(character_id, status="active")
        
        if not quests:
            return "当前没有活跃的任务。记录活动会自动生成新任务哦！"
        
        quest_list = "\n".join([f"- {q['title']}: {q['description']}" for q in quests[:5]])
        return f"当前任务：\n{quest_list}"
    
    def _handle_view_equipment(self, character_id: int) -> str:
        """处理查看装备意图"""
        from database import get_equipment
        equipment = get_equipment(character_id)
        
        if not equipment:
            return "背包里还没有装备。记录活动有机会获得装备哦！"
        
        equip_list = "\n".join([f"- {e['name']} ({e['rarity']})" for e in equipment[:5]])
        return f"当前装备：\n{equip_list}"
    
    def _handle_emotional_support(self, character_id: int, message: str, 
                                  emotion: Dict) -> str:
        """处理情感支持意图"""
        responses = {
            "sad": [
                "我理解你的感受。每个人都会有低落的时候，这很正常。",
                "别太苛责自己，休息一下，明天又是新的一天。",
                "记住，你已经做得很好了。给自己一点时间恢复。"
            ],
            "anxious": [
                "深呼吸，试着把注意力放在当下。",
                "焦虑是正常的反应，说明你在乎。但别让它控制你。",
                "把大任务分解成小步骤，一步一步来。"
            ],
            "angry": [
                "我理解你很生气。先冷静一下，深呼吸。",
                "生气是正常的情绪，但别让它影响你的判断。",
                "试着换个角度看问题，也许会有新的发现。"
            ]
        }
        
        emotion_type = emotion.get("emotion", "neutral")
        if emotion_type in responses:
            import random
            return random.choice(responses[emotion_type])
        
        return "我在这里陪着你。有什么想聊的吗？"
    
    def _handle_general_chat(self, character_id: int, message: str, 
                            history: List) -> str:
        """处理一般聊天"""
        # 构建上下文
        context = ""
        if history:
            recent = history[-3:]
            context = "\n".join([f"{h['role']}: {h['content']}" for h in recent])
        
        # 使用AI生成回复
        try:
            prompt = f"""你是一个友好、有创意的游戏化生活助手。用户和你聊天，请给出有趣、有帮助的回复。

对话历史：
{context}

用户消息：{message}

请用1-2句话回复，保持轻松友好的语气。"""
            
            # 这里应该调用AI服务，但为了简化，返回固定回复
            return "我在听呢！有什么想聊的或者需要帮助的吗？"
        except:
            return "我在听呢！有什么想聊的或者需要帮助的吗？"
    
    # ==================== 规划系统 ====================
    
    def create_goal(self, character_id: int, title: str, description: str = "",
                   goal_type: str = "general", target_value: float = None,
                   unit: str = "", deadline: str = None) -> Dict:
        """创建长期目标"""
        goal = create_long_term_goal(
            character_id=character_id,
            title=title,
            description=description,
            goal_type=goal_type,
            target_value=target_value,
            unit=unit,
            deadline=deadline
        )
        
        # 自动生成任务计划
        self._generate_tasks_for_goal(character_id, goal)
        
        # 记录决策
        log_decision(
            character_id=character_id,
            decision_type="goal_creation",
            context={"goal": title, "type": goal_type},
            options=["创建目标", "稍后再说"],
            chosen_option="创建目标",
            reasoning="用户明确表达了想要达成某个目标的意愿",
            confidence=0.9
        )
        
        return goal
    
    def _generate_tasks_for_goal(self, character_id: int, goal: Dict):
        """为目标生成任务计划"""
        goal_type = goal.get("goal_type", "general")
        title = goal.get("title", "")
        
        # 基于目标类型生成任务
        task_templates = {
            "fitness": [
                {"title": "运动30分钟", "task_type": "daily", "priority": 8},
                {"title": "记录体重", "task_type": "weekly", "priority": 5},
                {"title": "准备运动装备", "task_type": "daily", "priority": 3}
            ],
            "learning": [
                {"title": "学习1小时", "task_type": "daily", "priority": 8},
                {"title": "复习笔记", "task_type": "daily", "priority": 6},
                {"title": "完成练习题", "task_type": "weekly", "priority": 7}
            ],
            "habit": [
                {"title": f"执行{title}", "task_type": "daily", "priority": 9},
                {"title": "记录完成情况", "task_type": "daily", "priority": 4},
                {"title": "回顾本周表现", "task_type": "weekly", "priority": 5}
            ],
            "general": [
                {"title": f"推进{title}", "task_type": "daily", "priority": 7},
                {"title": "检查进度", "task_type": "weekly", "priority": 5}
            ]
        }
        
        templates = task_templates.get(goal_type, task_templates["general"])
        
        for template in templates:
            create_task_plan(
                character_id=character_id,
                title=template["title"],
                description=f"目标：{title}",
                goal_id=goal.get("id"),
                task_type=template["task_type"],
                priority=template["priority"],
                scheduled_date=datetime.now().strftime("%Y-%m-%d")
            )
    
    def update_goal(self, character_id: int, goal_id: int, 
                   progress_increment: float = 0.1) -> Dict:
        """更新目标进度"""
        goals = get_long_term_goals(character_id, status="active")
        goal = next((g for g in goals if g["id"] == goal_id), None)
        
        if not goal:
            return {"error": "目标不存在"}
        
        new_progress = min(goal.get("progress", 0) + progress_increment, 1.0)
        new_value = goal.get("current_value", 0) + progress_increment * goal.get("target_value", 100)
        
        updated_goal = update_goal_progress(goal_id, new_value, new_progress)
        
        # 检查是否完成
        if new_progress >= 1.0:
            # 发送完成通知
            create_notification(
                character_id=character_id,
                notification_type="achievement",
                title="目标达成！",
                content=f"恭喜你完成了目标：{goal['title']}",
                priority=10,
                context={"goal_id": goal_id}
            )
        
        return updated_goal
    
    def get_daily_plan(self, character_id: int) -> Dict:
        """获取每日计划"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 获取今日任务
        tasks = get_task_plans(character_id, date=today, completed=False)
        
        # 获取活跃目标
        goals = get_long_term_goals(character_id, status="active")
        
        # 生成建议
        suggestions = []
        if not tasks:
            suggestions.append("今天还没有安排任务，要不要创建一些？")
        
        if goals:
            active_goals = [g for g in goals if g.get("progress", 0) < 1.0]
            if active_goals:
                suggestions.append(f"你有{len(active_goals)}个目标正在推进中")
        
        return {
            "date": today,
            "tasks": tasks,
            "goals": goals,
            "suggestions": suggestions
        }
    
    # ==================== 主动推送系统 ====================
    
    def generate_proactive_notifications(self, character_id: int) -> List[Dict]:
        """生成主动推送通知"""
        notifications = []
        
        # 获取用户信息
        from database import get_character, get_activity_logs
        character = get_character(character_id)
        if not character:
            return notifications
        
        # 获取最近活动
        recent_logs = get_activity_logs(character_id, limit=10)
        today = datetime.now().strftime("%Y-%m-%d")
        today_logs = [l for l in recent_logs if l.get("created_at", "").startswith(today)]
        
        # 1. 早起提醒
        now = datetime.now()
        if now.hour == 7 and now.minute < 30:
            notifications.append(create_notification(
                character_id=character_id,
                notification_type="reminder",
                title="早安！新的一天开始了",
                content="记得完成今天的任务哦！",
                priority=6,
                scheduled_time=now.strftime("%Y-%m-%d %H:%M:%S")
            ))
        
        # 2. 晚间总结
        if now.hour == 21 and now.minute < 30:
            if today_logs:
                exp_sum = sum(l.get("exp_gained", 0) for l in today_logs)
                notifications.append(create_notification(
                    character_id=character_id,
                    notification_type="summary",
                    title="今日总结",
                    content=f"你今天完成了{len(today_logs)}个活动，获得了{exp_sum}经验值！",
                    priority=5,
                    scheduled_time=now.strftime("%Y-%m-%d %H:%M:%S")
                ))
        
        # 3. 连续未活动提醒
        if recent_logs:
            last_activity = recent_logs[0].get("created_at", "")
            if last_activity:
                try:
                    last_dt = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")
                    hours_since = (now - last_dt).total_seconds() / 3600
                    
                    if hours_since > 48:
                        notifications.append(create_notification(
                            character_id=character_id,
                            notification_type="encouragement",
                            title="好久不见！",
                            content="你已经2天没有记录活动了，要不要做点什么？",
                            priority=7,
                            scheduled_time=now.strftime("%Y-%m-%d %H:%M:%S")
                        ))
                except:
                    pass
        
        # 4. 弱项属性提醒
        attributes = {
            "strength": character.get("strength", 50),
            "intelligence": character.get("intelligence", 50),
            "agility": character.get("agility", 50),
            "charisma": character.get("charisma", 50),
            "willpower": character.get("willpower", 50)
        }
        
        weakest = min(attributes.items(), key=lambda x: x[1])
        if weakest[1] < 40:
            attr_names = {
                "strength": "力量",
                "intelligence": "智力",
                "agility": "敏捷",
                "charisma": "魅力",
                "willpower": "意志"
            }
            notifications.append(create_notification(
                character_id=character_id,
                notification_type="suggestion",
                title=f"提升{attr_names[weakest[0]]}",
                content=f"你的{attr_names[weakest[0]]}较低，建议多做相关活动",
                priority=4,
                scheduled_time=now.strftime("%Y-%m-%d %H:%M:%S")
            ))
        
        return notifications
    
    def check_and_send_notifications(self, character_id: int) -> List[Dict]:
        """检查并发送通知"""
        # 获取待发送通知
        pending = get_pending_notifications(character_id)
        
        sent_notifications = []
        for notification in pending:
            # 标记为已发送
            mark_notification_sent(notification["id"])
            sent_notifications.append(notification)
        
        # 生成新的主动通知
        new_notifications = self.generate_proactive_notifications(character_id)
        sent_notifications.extend(new_notifications)
        
        return sent_notifications
    
    def get_notifications(self, character_id: int, unread_only: bool = True) -> List[Dict]:
        """获取通知"""
        if unread_only:
            return get_unread_notifications(character_id)
        
        # 获取所有通知
        from agent_database import get_db
        with get_db() as conn:
            rows = conn.execute(
                """SELECT * FROM push_notifications 
                   WHERE character_id = ? AND sent = 1
                   ORDER BY created_at DESC LIMIT 50""",
                (character_id,)
            ).fetchall()
            return [dict(r) for r in rows]
    
    # ==================== 工具调用系统 ====================
    
    def call_tool(self, character_id: int, tool_name: str, 
                 params: Dict) -> Dict:
        """调用工具"""
        start_time = datetime.now()
        
        try:
            result = self._execute_tool(character_id, tool_name, params)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 记录工具调用
            log_tool_call(
                character_id=character_id,
                tool_name=tool_name,
                input_params=params,
                output_result=json.dumps(result, ensure_ascii=False),
                success=True,
                execution_time=execution_time
            )
            
            return {"success": True, "result": result}
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 记录失败
            log_tool_call(
                character_id=character_id,
                tool_name=tool_name,
                input_params=params,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
            
            return {"success": False, "error": str(e)}
    
    def _execute_tool(self, character_id: int, tool_name: str, 
                     params: Dict) -> Any:
        """执行工具"""
        if tool_name == "weather":
            return self._tool_weather(params)
        elif tool_name == "time":
            return self._tool_time()
        elif tool_name == "motivation":
            return self._tool_motivation(character_id)
        elif tool_name == "activity_suggestion":
            return self._tool_activity_suggestion(character_id, params)
        elif tool_name == "progress_check":
            return self._tool_progress_check(character_id)
        else:
            raise ValueError(f"未知工具: {tool_name}")
    
    def _tool_weather(self, params: Dict) -> Dict:
        """天气工具（模拟）"""
        # 实际应用中应该调用天气API
        return {
            "weather": "晴朗",
            "temperature": "25°C",
            "suggestion": "天气不错，适合户外活动"
        }
    
    def _tool_time(self) -> Dict:
        """时间工具"""
        now = datetime.now()
        return {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "day_of_week": now.strftime("%A"),
            "greeting": self._get_time_greeting(now.hour)
        }
    
    def _get_time_greeting(self, hour: int) -> str:
        """获取时间问候语"""
        if 5 <= hour < 12:
            return "早上好"
        elif 12 <= hour < 14:
            return "中午好"
        elif 14 <= hour < 18:
            return "下午好"
        elif 18 <= hour < 22:
            return "晚上好"
        else:
            return "夜深了，注意休息"
    
    def _tool_motivation(self, character_id: int) -> Dict:
        """激励工具"""
        from database import get_character
        character = get_character(character_id)
        
        if not character:
            return {"motivation": "请先创建角色"}
        
        level = character.get("level", 1)
        
        # 基于等级的激励语
        motivations = {
            (1, 5): "每一步都是进步，继续加油！",
            (6, 10): "你已经超越了大多数人，坚持下去！",
            (11, 20): "你的努力正在开花结果！",
            (21, 30): "你已经成为真正的高手了！",
            (31, 100): "传奇之路，你正在书写！"
        }
        
        for (min_level, max_level), msg in motivations.items():
            if min_level <= level <= max_level:
                return {"motivation": msg, "level": level}
        
        return {"motivation": "继续前进，你是最棒的！", "level": level}
    
    def _tool_activity_suggestion(self, character_id: int, params: Dict) -> Dict:
        """活动建议工具"""
        from database import get_character
        character = get_character(character_id)
        
        if not character:
            return {"suggestions": []}
        
        # 分析弱项
        attributes = {
            "strength": character.get("strength", 50),
            "intelligence": character.get("intelligence", 50),
            "agility": character.get("agility", 50),
            "charisma": character.get("charisma", 50),
            "willpower": character.get("willpower", 50)
        }
        
        weakest = min(attributes.items(), key=lambda x: x[1])
        
        # 基于弱项推荐活动
        activity_suggestions = {
            "strength": ["跑步30分钟", "做俯卧撑", "去健身房"],
            "intelligence": ["阅读30分钟", "学习新技能", "做思维训练"],
            "agility": ["瑜伽30分钟", "打羽毛球", "跳绳"],
            "charisma": ["和朋友聊天", "参加社交活动", "练习演讲"],
            "willpower": ["冥想15分钟", "早起", "坚持一个习惯"]
        }
        
        return {
            "weakest_attribute": weakest[0],
            "suggestions": activity_suggestions.get(weakest[0], ["做点喜欢的事"])
        }
    
    def _tool_progress_check(self, character_id: int) -> Dict:
        """进度检查工具"""
        from database import get_character, get_activity_logs
        character = get_character(character_id)
        
        if not character:
            return {"progress": {}}
        
        # 获取本周活动
        recent_logs = get_activity_logs(character_id, limit=50)
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        week_logs = [
            l for l in recent_logs 
            if l.get("created_at", "") >= week_start.strftime("%Y-%m-%d")
        ]
        
        return {
            "level": character.get("level", 1),
            "exp": character.get("exp", 0),
            "gold": character.get("gold", 0),
            "weekly_activities": len(week_logs),
            "weekly_exp": sum(l.get("exp_gained", 0) for l in week_logs)
        }
    
    # ==================== 自主决策引擎 ====================
    
    def make_decision(self, character_id: int, decision_type: str,
                     context: Dict) -> Dict:
        """做出决策"""
        # 获取相关记忆
        memories = get_behavior_memories(character_id, limit=10)
        
        # 获取用户画像
        profile = get_or_create_user_profile(character_id)
        
        # 获取历史决策
        past_decisions = get_decision_logs(character_id, decision_type=decision_type, limit=5)
        
        # 基于规则的决策
        rule_decision = self._rule_based_decision(
            character_id, decision_type, context, profile, memories
        )
        
        # 基于历史的决策
        history_decision = self._history_based_decision(
            past_decisions, context
        )
        
        # 综合决策
        final_decision = self._combine_decisions(
            rule_decision, history_decision, context
        )
        
        # 记录决策
        log_decision(
            character_id=character_id,
            decision_type=decision_type,
            context=context,
            options=final_decision.get("options", []),
            chosen_option=final_decision.get("chosen"),
            reasoning=final_decision.get("reasoning"),
            confidence=final_decision.get("confidence", 0.5)
        )
        
        return final_decision
    
    def _rule_based_decision(self, character_id: int, decision_type: str,
                            context: Dict, profile: Dict, memories: List) -> Dict:
        """基于规则的决策"""
        if decision_type == "activity_suggestion":
            # 基于弱项属性推荐活动
            from database import get_character
            character = get_character(character_id)
            
            if character:
                attributes = {
                    "strength": character.get("strength", 50),
                    "intelligence": character.get("intelligence", 50),
                    "agility": character.get("agility", 50),
                    "charisma": character.get("charisma", 50),
                    "willpower": character.get("willpower", 50)
                }
                
                weakest = min(attributes.items(), key=lambda x: x[1])
                
                activity_map = {
                    "strength": "运动",
                    "intelligence": "学习",
                    "agility": "运动",
                    "charisma": "社交",
                    "willpower": "冥想"
                }
                
                return {
                    "chosen": activity_map.get(weakest[0], "休息"),
                    "reasoning": f"你的{weakest[0]}属性较低，建议做相关活动",
                    "confidence": 0.8,
                    "options": list(activity_map.values())
                }
        
        elif decision_type == "notification_timing":
            # 基于用户活跃时间决定通知时间
            peak_hours = json.loads(profile.get("peak_hours", "[]"))
            if peak_hours:
                return {
                    "chosen": "peak_time",
                    "reasoning": "用户在高峰时段最活跃",
                    "confidence": 0.7,
                    "options": ["peak_time", "morning", "evening"]
                }
        
        return {
            "chosen": "default",
            "reasoning": "使用默认规则",
            "confidence": 0.5,
            "options": ["default"]
        }
    
    def _history_based_decision(self, past_decisions: List, 
                               context: Dict) -> Dict:
        """基于历史的决策"""
        if not past_decisions:
            return {
                "chosen": None,
                "reasoning": "没有历史决策参考",
                "confidence": 0.3
            }
        
        # 分析历史决策的成功率
        successful_decisions = [
            d for d in past_decisions 
            if d.get("outcome") and "成功" in d.get("outcome", "")
        ]
        
        if successful_decisions:
            # 选择最常成功的决策
            most_common = max(
                successful_decisions,
                key=lambda x: x.get("confidence", 0)
            )
            
            return {
                "chosen": most_common.get("chosen_option"),
                "reasoning": f"历史决策中，'{most_common.get('chosen_option')}'成功率最高",
                "confidence": most_common.get("confidence", 0.5)
            }
        
        return {
            "chosen": past_decisions[0].get("chosen_option"),
            "reasoning": "使用最近的决策",
            "confidence": 0.4
        }
    
    def _combine_decisions(self, rule_decision: Dict, history_decision: Dict,
                          context: Dict) -> Dict:
        """综合决策"""
        # 如果规则决策置信度高，使用规则决策
        if rule_decision.get("confidence", 0) > 0.7:
            return rule_decision
        
        # 如果历史决策置信度高，使用历史决策
        if history_decision.get("confidence", 0) > 0.7:
            return history_decision
        
        # 否则综合两者
        if rule_decision.get("chosen") == history_decision.get("chosen"):
            return {
                "chosen": rule_decision.get("chosen"),
                "reasoning": "规则和历史决策一致",
                "confidence": max(
                    rule_decision.get("confidence", 0),
                    history_decision.get("confidence", 0)
                ),
                "options": rule_decision.get("options", [])
            }
        
        # 选择置信度更高的
        if rule_decision.get("confidence", 0) >= history_decision.get("confidence", 0):
            return rule_decision
        else:
            return history_decision
    
    def learn_from_outcome(self, decision_id: int, outcome: str):
        """从结果中学习"""
        update_decision_outcome(decision_id, outcome)


# 创建全局智能体实例
agent = LifeRPGAgent()


def get_agent() -> LifeRPGAgent:
    """获取智能体实例"""
    return agent