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
    get_weekly_activity_type_stats
)
from game_engine import (
    classify_activity, calculate_exp_gain, calculate_gold_gain,
    calculate_attribute_changes, check_level_up, generate_equipment,
    generate_title, generate_quests, generate_all_quests, get_level_title, exp_for_level,
    get_rarity_color, get_attribute_level, get_attribute_progress
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
    try:
        # 设置30秒超时，AI响应慢时快速降级到本地逻辑
        ai_result = await asyncio.wait_for(chat_with_ai(data.description, character), timeout=30.0)
        if ai_result:
            ai_comment = ai_result.get("comment")
    except asyncio.TimeoutError:
        print("AI响应超时，使用本地逻辑")
        ai_result = None
    except Exception as e:
        print(f"AI分析失败，使用本地逻辑: {e}")
        ai_result = None

    # 确定活动类型
    if data.activity_type:
        activity_type = data.activity_type
    elif ai_result and ai_result.get("activity_type"):
        activity_type = ai_result["activity_type"]
    else:
        activity_type = classify_activity(data.description)

    # 计算收益
    if ai_result and ai_result.get("exp_gained"):
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

    # 应用属性变化
    updates = {
        "exp": remaining_exp,
        "gold": new_gold,
        "level": new_level,
    }
    for attr, change in attribute_changes.items():
        if attr in character and isinstance(character[attr], (int, float)):
            updates[attr] = character[attr] + change

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
        "total_stats": sum(character.get(attr, 10) for attr in ATTRIBUTES.keys())
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
