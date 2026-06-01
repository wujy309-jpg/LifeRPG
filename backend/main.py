from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
import json
import random
from datetime import datetime, date

from database import (
    init_db, create_character, get_character, update_character,
    add_activity_log, get_activity_logs, add_equipment, get_equipment,
    add_title, get_titles, add_quest, get_quests, complete_quest, get_db,
    get_all_characters, get_character_count, delete_character,
    get_activity_stats, get_activity_history, get_attribute_history,
    get_weekly_activity_type_stats,
    init_reality_tables, get_reality_rewards, add_custom_reward, redeem_reward,
    get_habit_challenges, create_habit_challenge, check_in_challenge,
    get_immunity_cards, buy_immunity_card, check_penalty, get_penalty_history,
    get_challenge_templates,
    check_in, get_check_in_status,
    get_activity_templates, add_activity_template, delete_activity_template, use_activity_template
)
from game_engine import (
    classify_activity, calculate_exp_gain, calculate_gold_gain,
    calculate_attribute_changes, check_level_up, generate_equipment,
    generate_title, generate_quests, generate_all_quests, get_level_title, exp_for_level,
    get_rarity_color, get_attribute_level, get_attribute_progress,
    classify_negative_activity, apply_attribute_penalty, ATTRIBUTE_MIN
)
from ai_service import (
    chat_with_ai, check_ai_status, list_models, generate_daily_summary,
    get_ai_providers, update_ai_provider, update_provider_config, load_config
)
from models import (
    CharacterCreate, CharacterResponse, ActivityInput,
    GameFeedback, ActivityLogResponse, EquipmentResponse,
    TitleResponse, QuestResponse, DailySummary
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_reality_tables()
    print("数据库初始化完成")
    yield


app = FastAPI(
    title="LifeRPG API",
    description="把你的生活游戏化！",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件
import os
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")


# ============ 角色 API ============

@app.get("/api/characters")
async def api_get_all_characters():
    """获取所有角色列表"""
    characters = get_all_characters()
    return {
        "characters": characters,
        "count": len(characters),
        "max_count": 3
    }


@app.post("/api/character", response_model=CharacterResponse)
async def api_create_character(data: CharacterCreate):
    """创建新角色"""
    # 检查角色数量限制
    count = get_character_count()
    if count >= 3:
        raise HTTPException(status_code=400, detail="最多只能创建3个角色，请先删除一个角色")
    
    character = create_character(
        name=data.name,
        gender=data.gender or "",
        age=data.age or 0,
        height=data.height or 0,
        weight=data.weight or 0,
        education=data.education or "",
        occupation=data.occupation or ""
    )
    return character


@app.get("/api/character/{character_id}", response_model=CharacterResponse)
async def api_get_character(character_id: int):
    """获取角色信息"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    return character


@app.delete("/api/character/{character_id}")
async def api_delete_character(character_id: int):
    """删除角色"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    success = delete_character(character_id)
    if success:
        return {"message": f"角色 {character['name']} 已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")


@app.get("/api/character/{character_id}/full")
async def api_get_character_full(character_id: int):
    """获取角色完整信息（含装备、称号、任务）"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    equipment = get_equipment(character_id)
    titles = get_titles(character_id)
    quests = get_quests(character_id, status="active")
    recent_logs = get_activity_logs(character_id, limit=5)

    # 计算下一级所需经验
    next_level_exp = exp_for_level(character["level"])
    level_title = get_level_title(character["level"])

    return {
        "character": character,
        "equipment": equipment,
        "titles": titles,
        "active_quests": quests,
        "recent_activities": recent_logs,
        "next_level_exp": next_level_exp,
        "level_title": level_title
    }


# ============ 活动 API ============

def _generate_negative_comment(activity_type: str, severity: str) -> str:
    """生成负面活动的吐槽评论"""
    comments = {
        "沉迷游戏": {
            "high": [
                "好家伙，一上午就献给游戏了？你的意志力正在疯狂掉血啊！建议下次设个闹钟，2小时就停",
                "游戏打了一上午？你的意志力已经被BOSS击败了！需要回城补给了",
                "一上午游戏，你的意志力已经破产了！建议去意志力商店充值（起来活动活动）"
            ],
            "medium": [
                "打了这么久游戏？你的意志力正在掉血，建议适可而止",
                "游戏时间到！你的意志力提醒你该休息了"
            ],
            "low": [
                "稍微放松一下可以，但别沉迷哦~"
            ]
        },
        "刷短视频": {
            "high": [
                "刷了一下午抖音？短视频的魔力太大了，你的意志力已经被吞噬",
                "短视频停不下来？你的意志力正在被算法控制！快醒醒"
            ],
            "medium": [
                "刷了这么久视频？你的意志力在默默流泪...",
                "短视频的黑洞效应太强了，注意时间！"
            ],
            "low": [
                "稍微刷一下放松可以，别停不下来哦~"
            ]
        },
        "熬夜": {
            "high": [
                "熬夜冠军就是你！不过你的力量和意志都在默默流泪...",
                "通宵一时爽，第二天火葬场！你的身体在抗议了",
                "熬夜一时爽，一直熬夜一直...掉属性！快去睡觉"
            ],
            "medium": [
                "又熬夜了？你的意志力和力量都在掉血啊",
                "晚睡对身体不好哦，早点休息明天才能满血复活"
            ],
            "low": [
                "稍微晚一点没事，但别太晚哦~"
            ]
        },
        "拖延偷懒": {
            "high": [
                "拖延症晚期患者！你的意志力已经降到谷底了",
                "一整天啥也没干？你的意志力正在疯狂掉血！快行动起来",
                "拖延一时爽，一直拖延...你的意志力已经破产了"
            ],
            "medium": [
                "又拖延了？你的意志力在默默流泪...",
                "拖延是意志力的天敌！快行动起来"
            ],
            "low": [
                "稍微休息一下可以，别一直拖延哦~"
            ]
        },
        "不健康饮食": {
            "high": [
                "暴饮暴食？你的力量在默默流泪...",
                "垃圾食品吃太多？身体在抗议了！"
            ],
            "medium": [
                "又吃垃圾食品了？注意健康饮食哦",
                "偶尔放纵一下可以，别太频繁"
            ],
            "low": [
                "偶尔吃点零食没事，注意均衡饮食~"
            ]
        },
        "过度社交": {
            "high": [
                "水群一上午？你的意志力正在被群消息淹没",
                "无意义社交太多了，你的意志力在掉血"
            ],
            "medium": [
                "水群这么久？注意时间管理哦",
                "社交可以，但别太浪费时间"
            ],
            "low": [
                "稍微聊聊天放松可以，别太沉迷哦~"
            ]
        }
    }
    
    activity_comments = comments.get(activity_type, {})
    severity_comments = activity_comments.get(severity, activity_comments.get("medium", ["注意控制时间哦~"]))
    return random.choice(severity_comments)


@app.post("/api/activity/{character_id}", response_model=GameFeedback)
async def api_log_activity(character_id: int, data: ActivityInput):
    """记录活动并获取游戏化反馈"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    old_level = character["level"]

    # 尝试AI分析，失败则用本地逻辑
    ai_result = None
    ai_comment = None
    is_negative = False
    negative_activity = None
    
    # 先检查是否是负面活动（本地关键词匹配）
    negative_activity = classify_negative_activity(data.description)
    
    try:
        # 设置30秒超时，AI响应慢时快速降级到本地逻辑
        ai_result = await asyncio.wait_for(chat_with_ai(data.description, character), timeout=30.0)
        if ai_result:
            ai_comment = ai_result.get("comment")
            # 检查AI是否识别为负面活动（属性变化中有负值）
            ai_attr_changes = ai_result.get("attribute_changes", {})
            has_negative_attr = any(v < 0 for v in ai_attr_changes.values())
            if has_negative_attr:
                is_negative = True
    except asyncio.TimeoutError:
        print("AI响应超时，使用本地逻辑")
        ai_result = None
    except Exception as e:
        print(f"AI分析失败，使用本地逻辑: {e}")
        ai_result = None

    # 确定活动类型
    if negative_activity:
        # 负面活动使用特殊类型
        activity_type = negative_activity["activity_type"]
        is_negative = True
    elif data.activity_type:
        activity_type = data.activity_type
    elif ai_result and ai_result.get("activity_type"):
        activity_type = ai_result["activity_type"]
    else:
        activity_type = classify_activity(data.description)

    # 计算收益
    if is_negative and negative_activity:
        # 负面活动：使用本地负面活动配置
        exp_gained = negative_activity["exp"]
        gold_gained = negative_activity["gold"]
        attribute_changes = negative_activity["penalty"]
        if not ai_comment:
            # 生成负面活动的吐槽评论
            ai_comment = _generate_negative_comment(negative_activity["activity_type"], negative_activity["severity"])
    elif ai_result and ai_result.get("exp_gained"):
        exp_gained = ai_result["exp_gained"]
        gold_gained = ai_result.get("gold_gained", 10)
        attribute_changes = ai_result.get("attribute_changes", {})
    else:
        current_stats = {
            "strength": character["strength"],
            "intelligence": character["intelligence"],
            "agility": character["agility"],
            "charisma": character["charisma"],
            "willpower": character["willpower"]
        }
        exp_gained = calculate_exp_gain(activity_type, data.description, character["level"])
        gold_gained = calculate_gold_gain(activity_type, character["level"])
        attribute_changes = calculate_attribute_changes(activity_type, current_stats)

    # 更新角色
    new_exp = character["exp"] + exp_gained
    new_gold = character["gold"] + gold_gained
    new_level, remaining_exp = check_level_up(new_exp, character["level"])
    level_up = new_level > old_level

    # 应用属性变化（确保属性不低于最低值）
    updates = {
        "exp": remaining_exp,
        "gold": new_gold,
        "level": new_level,
    }
    for attr, change in attribute_changes.items():
        if attr in character and isinstance(character[attr], (int, float)):
            new_value = character[attr] + change
            # 属性不能低于最低值
            updates[attr] = max(new_value, ATTRIBUTE_MIN)

    character = update_character(character_id, **updates)

    # 记录活动日志
    activity_log = add_activity_log(
        character_id=character_id,
        activity_type=activity_type,
        description=data.description,
        exp_gained=exp_gained,
        gold_gained=gold_gained,
        attribute_changes=attribute_changes,
        ai_feedback=ai_comment
    )

    # 生成装备
    equipment = None
    equip_chance = ai_result.get("equipment_found") if ai_result else None
    if equip_chance and equip_chance.get("name"):
        # AI 生成的装备
        equip_data = equip_chance
        equipment = add_equipment(
            character_id=character_id,
            name=equip_data["name"],
            description=equip_data.get("description", ""),
            rarity=equip_data.get("rarity", "普通"),
            stat_bonuses=equip_data.get("stat_bonuses", {}),
            special_effect=equip_data.get("special_effect")
        )
    else:
        # 本地生成装备
        equip_data = generate_equipment(activity_type, character["level"])
        if equip_data:
            equipment = add_equipment(
                character_id=character_id,
                name=equip_data["name"],
                description=equip_data.get("description", ""),
                rarity=equip_data.get("rarity", "普通"),
                stat_bonuses=equip_data.get("stat_bonuses", {}),
                special_effect=equip_data.get("special_effect")
            )

    # 生成称号
    title = None
    title_chance = ai_result.get("title_earned") if ai_result else None
    if title_chance and title_chance.get("name"):
        # AI 生成的称号
        title_data = title_chance
        title = add_title(
            character_id=character_id,
            name=title_data["name"],
            description=title_data.get("description", ""),
            unlock_condition=f"完成{activity_type}活动时解锁"
        )
    else:
        # 本地生成称号
        stats = {
            "strength": character["strength"],
            "intelligence": character["intelligence"],
            "agility": character["agility"],
            "charisma": character["charisma"],
            "willpower": character["willpower"]
        }
        title_data = generate_title(activity_type, data.description, stats)
        if title_data:
            title = add_title(
                character_id=character_id,
                name=title_data["name"],
                description=title_data.get("description", ""),
                unlock_condition=title_data.get("condition", f"完成{activity_type}活动时解锁")
            )

    # 生成任务 (每日最多3个)
    quest = None
    active_quests = get_quests(character_id, status="active")
    if len(active_quests) < 3:
        quest_data = None
        if ai_result and ai_result.get("new_quest"):
            quest_data = ai_result["new_quest"]
        else:
            stats = {
                "strength": character["strength"],
                "intelligence": character["intelligence"],
                "agility": character["agility"],
                "charisma": character["charisma"],
                "willpower": character["willpower"]
            }
            quests = generate_quests(character["level"], stats)
            if quests:
                quest_data = quests[0]

        if quest_data:
            quest = add_quest(
                character_id=character_id,
                title=quest_data.get("title", "新任务"),
                description=quest_data.get("description", ""),
                quest_type="daily",
                exp_reward=quest_data.get("exp_reward", 20),
                gold_reward=quest_data.get("gold_reward", 10)
            )

    return GameFeedback(
        activity_log=activity_log,
        character=character,
        level_up=level_up,
        new_level=new_level if level_up else None,
        equipment_found=equipment,
        title_earned=title,
        quest_generated=quest,
        ai_comment=ai_comment
    )


@app.get("/api/activities/{character_id}", response_model=list[ActivityLogResponse])
async def api_get_activities(character_id: int, limit: int = 20):
    """获取活动记录"""
    return get_activity_logs(character_id, limit)


# ============ 装备 API ============

@app.get("/api/equipment/{character_id}", response_model=list[EquipmentResponse])
async def api_get_equipment(character_id: int):
    """获取装备列表"""
    return get_equipment(character_id)


@app.post("/api/equipment/{equipment_id}/use")
async def api_use_equipment(equipment_id: int):
    """使用装备"""
    with get_db() as conn:
        # 获取装备信息
        row = conn.execute(
            "SELECT * FROM equipment WHERE id = ?",
            (equipment_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="装备不存在")
        
        equipment = dict(row)
        character_id = equipment["character_id"]
        
        # 获取角色信息
        character = get_character(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 解析使用效果
        use_bonus = json.loads(equipment.get("use_bonus", "{}"))
        use_effect = equipment.get("use_effect", "感觉不错")
        use_desc = equipment.get("use_desc", "使用物品")
        
        # 应用使用效果（临时属性加成）
        updates = {}
        for attr, bonus in use_bonus.items():
            if attr in character and isinstance(character[attr], (int, float)):
                # 使用效果是小数，需要累积到下一次活动
                # 这里我们直接给一个小的属性提升
                current = character[attr]
                # 将小数转换为整数提升（每使用10次提升1点）
                new_value = current + bonus
                updates[attr] = new_value
        
        if updates:
            update_character(character_id, **updates)
        
        # 删除装备（使用后消耗）
        conn.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
        
        return {
            "message": f"{use_desc} - {use_effect}",
            "equipment_name": equipment["name"],
            "effects": use_bonus
        }


# ============ 称号 API ============

@app.get("/api/titles/{character_id}", response_model=list[TitleResponse])
async def api_get_titles(character_id: int):
    """获取称号列表"""
    return get_titles(character_id)


# ============ 任务 API ============

@app.get("/api/quests/{character_id}", response_model=list[QuestResponse])
async def api_get_quests(character_id: int, status: str = None):
    """获取任务列表"""
    return get_quests(character_id, status)


@app.get("/api/quests/{character_id}/all")
async def api_get_all_quests(character_id: int):
    """获取所有类型的任务"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    stats = {
        "strength": character["strength"],
        "intelligence": character["intelligence"],
        "agility": character["agility"],
        "charisma": character["charisma"],
        "willpower": character["willpower"]
    }
    
    all_quests = generate_all_quests(character["level"], stats)
    
    # 获取当前活跃任务
    active_quests = get_quests(character_id, status="active")
    completed_quests = get_quests(character_id, status="completed")
    
    return {
        "available_quests": all_quests,
        "active_quests": active_quests,
        "completed_today": len([q for q in completed_quests if q.get("created_at", "").startswith(date.today().isoformat())]),
        "active_count": len(active_quests)
    }


@app.post("/api/quests/{quest_id}/complete")
async def api_complete_quest(quest_id: int):
    """完成任务"""
    quest = complete_quest(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 给角色加奖励
    character = get_character(quest["character_id"])
    if character:
        new_exp = character["exp"] + quest["exp_reward"]
        new_gold = character["gold"] + quest["gold_reward"]
        new_level, remaining_exp = check_level_up(new_exp, character["level"])
        update_character(
            quest["character_id"],
            exp=remaining_exp,
            gold=new_gold,
            level=new_level
        )

    return {"message": "任务完成！", "quest": quest}


# ============ 每日总结 API ============

@app.get("/api/daily-summary/{character_id}", response_model=DailySummary)
async def api_daily_summary(character_id: int):
    """获取今日总结"""
    logs = get_activity_logs(character_id, limit=50)
    today = date.today().isoformat()

    # 过滤今天的活动
    today_logs = [l for l in logs if l.get("created_at", "").startswith(today)]

    total_exp = sum(l.get("exp_gained", 0) for l in today_logs)
    total_gold = sum(l.get("gold_gained", 0) for l in today_logs)

    character = get_character(character_id)
    summary = None
    if character:
        summary = await generate_daily_summary(today_logs, character)

    return DailySummary(
        date=today,
        total_exp=total_exp,
        total_gold=total_gold,
        activities_count=len(today_logs),
        activities=today_logs,
        summary=summary
    )


# ============ 签到 API ============

@app.post("/api/checkin/{character_id}")
async def api_check_in(character_id: int):
    """每日签到"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    result = check_in(character_id)
    return result


@app.get("/api/checkin/status/{character_id}")
async def api_check_in_status(character_id: int):
    """获取签到状态"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return get_check_in_status(character_id)


# ============ 活动模板 API ============

@app.get("/api/templates/{character_id}")
async def api_get_templates(character_id: int):
    """获取活动模板列表"""
    return get_activity_templates(character_id)


@app.post("/api/templates/{character_id}")
async def api_add_template(character_id: int, data: dict):
    """添加活动模板"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    name = data.get("name", "")
    description = data.get("description", "")
    activity_type = data.get("activity_type")
    
    if not name or not description:
        raise HTTPException(status_code=400, detail="名称和描述不能为空")
    
    return add_activity_template(character_id, name, description, activity_type)


@app.delete("/api/templates/{template_id}")
async def api_delete_template(template_id: int):
    """删除活动模板"""
    delete_activity_template(template_id)
    return {"message": "删除成功"}


@app.post("/api/templates/use/{template_id}")
async def api_use_template(template_id: int):
    """使用活动模板"""
    template = use_activity_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


# ============ 系统 API ============

@app.get("/api/status")
async def api_status():
    """系统状态检查"""
    ai_status = await check_ai_status()
    models = await list_models() if ai_status.get("connected") else []

    return {
        "status": "running",
        "ai_status": ai_status,
        "available_models": models
    }


# ============ 统计 API ============

@app.get("/api/stats/{character_id}")
def api_get_stats(character_id: int):
    """获取角色统计数据"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    stats = get_activity_stats(character_id)
    return stats


@app.get("/api/stats/{character_id}/history")
def api_get_activity_history(character_id: int, days: int = 30):
    """获取活动历史"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    history = get_activity_history(character_id, days)
    return {"history": history, "days": days}


# ============ 数据导出 API ============

@app.get("/api/export/{character_id}")
def api_export_data(character_id: int, format: str = "json"):
    """导出角色数据
    
    format: json 或 csv
    """
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 获取所有相关数据
    activity_logs = get_activity_logs(character_id, limit=10000)
    equipment = get_equipment(character_id)
    titles = get_titles(character_id)
    quests = get_quests(character_id)
    
    export_data = {
        "character": dict(character),
        "activity_logs": activity_logs,
        "equipment": equipment,
        "titles": titles,
        "quests": quests,
        "exported_at": datetime.now().isoformat()
    }
    
    if format == "csv":
        # CSV格式只导出活动记录
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "类型", "描述", "经验", "金币", "属性变化", "AI反馈"])
        for log in activity_logs:
            writer.writerow([
                log.get("created_at", ""),
                log.get("activity_type", ""),
                log.get("description", ""),
                log.get("exp_gained", 0),
                log.get("gold_gained", 0),
                log.get("attribute_changes", "{}"),
                log.get("ai_feedback", "")
            ])
        return {"format": "csv", "data": output.getvalue()}
    
    return export_data


@app.get("/api/stats/{character_id}/attributes")
def api_get_attribute_history(character_id: int, days: int = 30):
    """获取属性变化历史"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    history = get_attribute_history(character_id, days)
    return {"history": history, "days": days}


@app.get("/api/stats/{character_id}/weekly-types")
def api_get_weekly_types(character_id: int):
    """获取本周活动类型统计"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    types = get_weekly_activity_type_stats(character_id)
    return {"types": types}


# ============ AI配置 API ============

@app.get("/api/ai/providers")
async def api_get_ai_providers():
    """获取所有AI提供商配置"""
    config = load_config()
    providers = config.get("providers", {})
    current_provider = config.get("ai_provider", "ollama")
    
    # 隐藏API key的完整值，只显示前8位和后4位
    masked_providers = {}
    for name, provider in providers.items():
        masked_provider = provider.copy()
        api_key = masked_provider.get("api_key")
        if api_key and len(api_key) > 12:
            masked_provider["api_key_masked"] = f"{api_key[:8]}...{api_key[-4:]}"
            masked_provider["api_key_set"] = True
        else:
            masked_provider["api_key_masked"] = None
            masked_provider["api_key_set"] = False
        masked_providers[name] = masked_provider
    
    return {
        "current_provider": current_provider,
        "providers": masked_providers
    }


@app.post("/api/ai/switch/{provider_name}")
async def api_switch_ai_provider(provider_name: str):
    """切换AI提供商"""
    config = load_config()
    providers = config.get("providers", {})
    
    if provider_name not in providers:
        raise HTTPException(status_code=404, detail=f"提供商 '{provider_name}' 不存在")
    
    update_ai_provider(provider_name)
    return {"message": f"已切换到 {providers[provider_name].get('name', provider_name)}"}


@app.post("/api/ai/config/{provider_name}")
async def api_update_ai_config(provider_name: str, data: dict):
    """更新AI提供商配置"""
    config = load_config()
    providers = config.get("providers", {})
    
    if provider_name not in providers:
        raise HTTPException(status_code=404, detail=f"提供商 '{provider_name}' 不存在")
    
    # 允许更新的字段
    allowed_fields = ["api_key", "base_url", "model", "name"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not updates:
        raise HTTPException(status_code=400, detail="没有有效的更新字段")
    
    update_provider_config(provider_name, updates)
    return {"message": f"{provider_name} 配置已更新"}


@app.post("/api/ai/test/{provider_name}")
async def api_test_ai_connection(provider_name: str):
    """测试AI提供商连接"""
    config = load_config()
    providers = config.get("providers", {})
    
    if provider_name not in providers:
        raise HTTPException(status_code=404, detail=f"提供商 '{provider_name}' 不存在")
    
    # 临时切换到指定提供商进行测试
    original_provider = config.get("ai_provider")
    update_ai_provider(provider_name)
    
    try:
        status = await check_ai_status()
        return {
            "provider": provider_name,
            "connected": status.get("connected", False),
            "error": status.get("error")
        }
    finally:
        # 恢复原提供商
        if original_provider:
            update_ai_provider(original_provider)


@app.get("/api/level-info")
async def api_level_info():
    """获取等级信息"""
    from game_engine import ACTIVITY_CONFIG
    return {
        "activity_types": list(ACTIVITY_CONFIG.keys()),
        "level_titles": {
            1: "新手冒险者",
            5: "初级勇者",
            10: "中级战士",
            20: "高级英雄",
            30: "传奇大师",
            50: "不朽传说"
        }
    }


@app.get("/api/character/{character_id}/attributes")
async def api_get_character_attributes(character_id: int):
    """获取角色属性详情（包含进度信息）"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    from game_engine import ATTRIBUTES, get_attribute_progress
    
    attributes = {}
    for attr_key, attr_info in ATTRIBUTES.items():
        value = character.get(attr_key, 10)
        attributes[attr_key] = {
            "name": attr_info["name"],
            "icon": attr_info["icon"],
            "desc": attr_info["desc"],
            "value": value,
            **get_attribute_progress(value)
        }
    
    return {
        "character_id": character_id,
        "attributes": attributes,
        "total_stats": round(sum(character.get(attr, 10) for attr in ATTRIBUTES.keys()) / 5)
    }


@app.get("/api/rules")
async def api_get_rules():
    """获取游戏规则"""
    from game_engine import ACTIVITY_CONFIG, RARITY_CONFIG, ATTRIBUTES
    
    return {
        "attributes": ATTRIBUTES,
        "activity_types": {
            k: {
                "name": k,
                "base_exp": v["base_exp"],
                "base_gold": v["base_gold"],
                "primary_attr": v["primary_attr"],
                "secondary_attr": v["secondary_attr"]
            }
            for k, v in ACTIVITY_CONFIG.items()
        },
        "rarity": {
            k: {
                "name": k,
                "color": v["color"],
                "stat_range": v["stat_range"]
            }
            for k, v in RARITY_CONFIG.items()
        },
        "level_formula": "EXP(n) = 100 × 1.5^(n-1)",
        "attribute_soft_cap": 50,
        "attribute_hard_cap": 100,
        "initial_attributes": 10
    }


# 前端路由
@app.get("/favicon.svg")
async def serve_favicon():
    favicon_path = os.path.join(frontend_path, "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/svg+xml")
    return {"detail": "Not Found"}


@app.get("/")
async def serve_frontend():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "LifeRPG API 运行中！请构建前端或访问 /docs 查看API文档"}


# ==================== 现实连接 API ====================

@app.get("/api/reality/rewards/{character_id}")
async def api_get_reality_rewards(character_id: int):
    """获取现实奖励列表"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    rewards = get_reality_rewards(character_id)
    return {"rewards": rewards, "gold": character["gold"]}


@app.post("/api/reality/rewards/{character_id}/add")
async def api_add_custom_reward(character_id: int, data: dict):
    """添加自定义奖励"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    name = data.get("name")
    description = data.get("description", "")
    cost = data.get("cost", 50)
    if not name:
        raise HTTPException(status_code=400, detail="奖励名称不能为空")
    result = add_custom_reward(character_id, name, description, cost)
    return result


@app.post("/api/reality/rewards/{character_id}/redeem/{reward_id}")
async def api_redeem_reward(character_id: int, reward_id: int):
    """兑换奖励"""
    result = redeem_reward(character_id, reward_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "兑换失败"))
    return result


@app.get("/api/reality/challenges/templates")
async def api_get_challenge_templates():
    """获取挑战模板"""
    templates = get_challenge_templates()
    return {"templates": templates}


@app.get("/api/reality/challenges/{character_id}")
async def api_get_habit_challenges(character_id: int):
    """获取习惯挑战"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    challenges = get_habit_challenges(character_id)
    return {"challenges": challenges, "gold": character["gold"]}


@app.post("/api/reality/challenges/{character_id}/create")
async def api_create_habit_challenge(character_id: int, data: dict):
    """创建习惯挑战"""
    name = data.get("name")
    description = data.get("description", "")
    duration_days = data.get("duration_days", 21)
    cost = data.get("cost", 50)
    if not name:
        raise HTTPException(status_code=400, detail="挑战名称不能为空")
    result = create_habit_challenge(character_id, name, description, duration_days, cost)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "创建失败"))
    return result


@app.post("/api/reality/challenges/{challenge_id}/checkin/{character_id}")
async def api_check_in_challenge(character_id: int, challenge_id: int):
    """习惯挑战打卡"""
    result = check_in_challenge(character_id, challenge_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "打卡失败"))
    return result


@app.get("/api/reality/cards/{character_id}")
async def api_get_immunity_cards(character_id: int):
    """获取免罪金牌"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    cards = get_immunity_cards(character_id)
    return {"cards": cards, "gold": character["gold"]}


@app.post("/api/reality/cards/{character_id}/buy")
async def api_buy_immunity_card(character_id: int, data: dict):
    """购买免罪金牌"""
    card_type = data.get("card_type")
    if not card_type:
        raise HTTPException(status_code=400, detail="卡牌类型不能为空")
    result = buy_immunity_card(character_id, card_type)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "购买失败"))
    return result


@app.get("/api/reality/penalty/{character_id}")
async def api_check_penalty(character_id: int):
    """检查惩罚"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    result = check_penalty(character_id)
    return result


@app.get("/api/reality/penalty/{character_id}/history")
async def api_get_penalty_history(character_id: int):
    """获取惩罚历史"""
    history = get_penalty_history(character_id)
    return {"history": history}


# ==================== 智能体 API ====================

from agent import get_agent
from agent_database import init_agent_tables


@app.on_event("startup")
async def startup_event():
    """启动时初始化智能体表"""
    init_agent_tables()
    
    # 启动智能体调度器
    from agent_scheduler import start_scheduler, setup_all_characters_schedule
    start_scheduler()
    setup_all_characters_schedule()
    
    print("智能体系统初始化完成")


@app.post("/api/agent/chat/{character_id}")
async def api_agent_chat(character_id: int, data: dict):
    """智能体对话"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    message = data.get("message", "")
    session_id = data.get("session_id")
    
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    agent = get_agent()
    
    # 如果没有session_id，开始新对话
    if not session_id:
        session_id = agent.start_conversation(character_id)
    
    # 处理消息
    result = agent.process_message(character_id, session_id, message)
    
    return result


@app.get("/api/agent/sessions/{character_id}")
async def api_get_agent_sessions(character_id: int):
    """获取对话会话列表"""
    from agent_database import get_conversation_history
    history = get_conversation_history(character_id, limit=100)
    
    # 按session_id分组
    sessions = {}
    for record in history:
        session_id = record.get("session_id")
        if session_id not in sessions:
            sessions[session_id] = {
                "session_id": session_id,
                "messages": [],
                "last_activity": record.get("created_at")
            }
        sessions[session_id]["messages"].append(record)
    
    return {"sessions": list(sessions.values())}


@app.get("/api/agent/memory/{character_id}")
async def api_get_agent_memory(character_id: int, memory_type: str = None):
    """获取智能体记忆"""
    agent = get_agent()
    
    # 获取行为记忆
    from agent_database import get_behavior_memories
    memories = get_behavior_memories(character_id, memory_type=memory_type)
    
    # 获取行为模式分析
    patterns = agent.analyze_behavior_patterns(character_id)
    
    return {
        "memories": memories,
        "patterns": patterns.get("patterns", []),
        "insights": patterns.get("insights", [])
    }


@app.get("/api/agent/emotion/{character_id}")
async def api_get_emotion_status(character_id: int):
    """获取情绪状态"""
    from agent_database import get_recent_emotions, get_emotion_stats
    
    recent = get_recent_emotions(character_id, hours=24)
    stats = get_emotion_stats(character_id, days=7)
    
    return {
        "recent_emotions": recent,
        "emotion_stats": stats
    }


@app.get("/api/agent/notifications/{character_id}")
async def api_get_notifications(character_id: int, unread_only: bool = True):
    """获取通知"""
    agent = get_agent()
    
    # 检查并发送新通知
    agent.check_and_send_notifications(character_id)
    
    # 获取通知
    notifications = agent.get_notifications(character_id, unread_only=unread_only)
    
    return {"notifications": notifications}


@app.post("/api/agent/notifications/{notification_id}/read")
async def api_mark_notification_read(notification_id: int):
    """标记通知已读"""
    from agent_database import mark_notification_read
    mark_notification_read(notification_id)
    return {"message": "已标记为已读"}


@app.get("/api/agent/goals/{character_id}")
async def api_get_goals(character_id: int, status: str = "active"):
    """获取长期目标"""
    from agent_database import get_long_term_goals
    goals = get_long_term_goals(character_id, status=status)
    return {"goals": goals}


@app.post("/api/agent/goals/{character_id}")
async def api_create_goal(character_id: int, data: dict):
    """创建长期目标"""
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    agent = get_agent()
    goal = agent.create_goal(
        character_id=character_id,
        title=data.get("title", ""),
        description=data.get("description", ""),
        goal_type=data.get("goal_type", "general"),
        target_value=data.get("target_value"),
        unit=data.get("unit", ""),
        deadline=data.get("deadline")
    )
    
    return goal


@app.put("/api/agent/goals/{goal_id}/progress")
async def api_update_goal_progress(goal_id: int, data: dict):
    """更新目标进度"""
    agent = get_agent()
    character_id = data.get("character_id")
    
    if not character_id:
        raise HTTPException(status_code=400, detail="需要character_id")
    
    result = agent.update_goal(
        character_id=character_id,
        goal_id=goal_id,
        progress_increment=data.get("progress", 0.1)
    )
    
    return result


@app.get("/api/agent/tasks/{character_id}")
async def api_get_tasks(character_id: int, date: str = None):
    """获取任务计划"""
    from agent_database import get_task_plans
    tasks = get_task_plans(character_id, date=date)
    return {"tasks": tasks}


@app.post("/api/agent/tasks/{character_id}")
async def api_create_task(character_id: int, data: dict):
    """创建任务计划"""
    from agent_database import create_task_plan
    task = create_task_plan(
        character_id=character_id,
        title=data.get("title", ""),
        description=data.get("description", ""),
        goal_id=data.get("goal_id"),
        task_type=data.get("task_type", "daily"),
        priority=data.get("priority", 5),
        scheduled_date=data.get("scheduled_date"),
        scheduled_time=data.get("scheduled_time"),
        recurrence=data.get("recurrence")
    )
    return task


@app.post("/api/agent/tasks/{task_id}/complete")
async def api_complete_task(task_id: int):
    """完成任务"""
    from agent_database import complete_task_plan
    task = complete_task_plan(task_id)
    return task


@app.get("/api/agent/daily-plan/{character_id}")
async def api_get_daily_plan(character_id: int):
    """获取每日计划"""
    agent = get_agent()
    plan = agent.get_daily_plan(character_id)
    return plan


@app.post("/api/agent/tool/{character_id}")
async def api_call_tool(character_id: int, data: dict):
    """调用智能体工具"""
    agent = get_agent()
    result = agent.call_tool(
        character_id=character_id,
        tool_name=data.get("tool_name", ""),
        params=data.get("params", {})
    )
    return result


@app.get("/api/agent/decision/{character_id}")
async def api_get_decisions(character_id: int, decision_type: str = None):
    """获取决策历史"""
    from agent_database import get_decision_logs
    decisions = get_decision_logs(character_id, decision_type=decision_type)
    return {"decisions": decisions}


@app.post("/api/agent/decision/{character_id}")
async def api_make_decision(character_id: int, data: dict):
    """让智能体做决策"""
    agent = get_agent()
    decision = agent.make_decision(
        character_id=character_id,
        decision_type=data.get("decision_type", "general"),
        context=data.get("context", {})
    )
    return decision


@app.get("/api/agent/profile/{character_id}")
async def api_get_agent_profile(character_id: int):
    """获取用户画像"""
    from agent_database import get_or_create_user_profile
    profile = get_or_create_user_profile(character_id)
    return profile


@app.put("/api/agent/profile/{character_id}")
async def api_update_agent_profile(character_id: int, data: dict):
    """更新用户画像"""
    from agent_database import update_user_profile
    profile = update_user_profile(character_id, **data)
    return profile


@app.get("/api/agent/config/{character_id}")
async def api_get_agent_config(character_id: int):
    """获取智能体配置"""
    from agent_database import get_agent_config
    config = get_agent_config(character_id)
    return config


@app.put("/api/agent/config/{character_id}")
async def api_update_agent_config(character_id: int, data: dict):
    """更新智能体配置"""
    from agent_database import update_agent_config
    config = update_agent_config(character_id, **data)
    return config


@app.get("/api/agent/suggestion/{character_id}")
async def api_get_suggestion(character_id: int):
    """获取个性化建议"""
    agent = get_agent()
    suggestion = agent.get_personalized_suggestion(character_id)
    return {"suggestion": suggestion}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
