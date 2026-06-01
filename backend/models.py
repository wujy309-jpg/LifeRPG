from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class CharacterCreate(BaseModel):
    name: str
    gender: Optional[str] = ""
    age: Optional[int] = 0
    height: Optional[float] = 0
    weight: Optional[float] = 0
    education: Optional[str] = ""
    occupation: Optional[str] = ""


class CharacterResponse(BaseModel):
    id: int
    name: str
    level: int
    exp: int
    gold: int
    strength: int
    intelligence: int
    agility: int
    charisma: int
    willpower: int
    gender: Optional[str] = ""
    age: Optional[int] = 0
    height: Optional[float] = 0
    weight: Optional[float] = 0
    education: Optional[str] = ""
    occupation: Optional[str] = ""
    created_at: Optional[str] = None


class ActivityInput(BaseModel):
    description: str
    activity_type: Optional[str] = None  # 如果不提供，AI自动判断


class EquipmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    rarity: str
    stat_bonuses: Optional[str]
    special_effect: Optional[str]
    use_desc: Optional[str] = "使用物品"
    use_effect: Optional[str] = "感觉不错"
    use_bonus: Optional[str] = "{}"
    equipped: bool
    created_at: Optional[str]


class TitleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    unlock_condition: Optional[str]
    equipped: bool
    created_at: Optional[str]


class QuestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    quest_type: str
    exp_reward: int
    gold_reward: int
    status: str
    due_date: Optional[str]
    completed_at: Optional[str] = None
    created_at: Optional[str]


class ActivityLogResponse(BaseModel):
    id: int
    character_id: int
    activity_type: str
    description: Optional[str]
    exp_gained: int
    gold_gained: int
    attribute_changes: Optional[str]
    ai_feedback: Optional[str]
    created_at: Optional[str]


class GameFeedback(BaseModel):
    activity_log: ActivityLogResponse
    character: CharacterResponse
    level_up: bool
    new_level: Optional[int]
    equipment_found: Optional[EquipmentResponse]
    title_earned: Optional[TitleResponse]
    quest_generated: Optional[QuestResponse]
    ai_comment: Optional[str]


class DailySummary(BaseModel):
    date: str
    total_exp: int
    total_gold: int
    activities_count: int
    activities: List[ActivityLogResponse]
    summary: Optional[str]
