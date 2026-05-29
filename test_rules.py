import httpx
import json

# 测试规则API
r = httpx.get('http://localhost:8000/api/rules')
print("规则API状态码:", r.status_code)
rules = r.json()
print("属性类型:", list(rules['attributes'].keys()))
print("活动类型:", list(rules['activity_types'].keys()))
print("稀有度:", list(rules['rarity'].keys()))
print()

# 测试属性API
r = httpx.get('http://localhost:8000/api/character/4/attributes')
print("属性API状态码:", r.status_code)
attrs = r.json()
print("总属性:", attrs['total_stats'])
for attr_key, attr_data in attrs['attributes'].items():
    print(f"  {attr_data['icon']} {attr_data['name']}: {attr_data['value']} ({attr_data['level']})")
