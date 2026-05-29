import httpx
import json

API_BASE = "http://localhost:8000/api"

# 创建角色
response = httpx.post(f"{API_BASE}/character", json={"name": "冒险者小明"})
print("创建角色:", response.json())

# 记录活动
response = httpx.post(f"{API_BASE}/activity/1", json={"description": "去健身房锻炼了1小时"})
data = response.json()
print("\n活动记录结果:")
print(f"  类型: {data['activity_log']['activity_type']}")
print(f"  经验: +{data['activity_log']['exp_gained']}")
print(f"  金币: +{data['activity_log']['gold_gained']}")
print(f"  AI评价: {data.get('ai_comment', '无')}")
if data.get('equipment_found'):
    print(f"  获得装备: [{data['equipment_found']['rarity']}] {data['equipment_found']['name']}")
if data.get('title_earned'):
    print(f"  获得称号: {data['title_earned']['name']}")
