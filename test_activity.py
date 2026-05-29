import httpx
import time

start = time.time()
r = httpx.post('http://localhost:8000/api/activity/4', 
               json={'description': '写代码1小时'}, 
               timeout=60)
elapsed = time.time() - start

print(f'状态码: {r.status_code}')
print(f'耗时: {elapsed:.1f}秒')
data = r.json()
print(f'经验值: +{data["activity_log"]["exp_gained"]}')
print(f'金币: +{data["activity_log"]["gold_gained"]}')
print(f'AI评价: {data.get("ai_comment", "无（AI超时或未响应）")}')
