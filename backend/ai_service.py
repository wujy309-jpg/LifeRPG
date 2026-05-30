import httpx
import json
import os
from typing import Optional

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> dict:
    """加载AI配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载配置失败: {e}")
    
    # 默认配置
    return {
        "ai_provider": "ollama",
        "providers": {
            "ollama": {
                "name": "Ollama (本地)",
                "base_url": "http://localhost:11434",
                "model": "gemma4:latest",
                "api_key": None
            },
            "openai": {
                "name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-3.5-turbo",
                "api_key": None
            },
            "claude": {
                "name": "Claude",
                "base_url": "https://api.anthropic.com/v1",
                "model": "claude-3-sonnet-20240229",
                "api_key": None
            },
            "deepseek": {
                "name": "DeepSeek",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "api_key": None
            },
            "mimo": {
                "name": "MiMo v2.5 Pro",
                "base_url": "https://api.xiaoai.mi.com/v1",
                "model": "mimo-v2.5-pro",
                "api_key": None
            },
            "custom": {
                "name": "自定义",
                "base_url": "",
                "model": "",
                "api_key": None
            }
        }
    }


def save_config(config: dict):
    """保存AI配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置失败: {e}")


def get_current_provider_config() -> dict:
    """获取当前AI提供商的配置"""
    config = load_config()
    provider = config.get("ai_provider", "ollama")
    providers = config.get("providers", {})
    return providers.get(provider, providers.get("ollama", {}))


SYSTEM_PROMPT = """你是一个创意游戏化系统 LifeRPG 的AI助手。用户会告诉你他们今天做了什么，你需要返回游戏化的反馈。

请严格按照以下JSON格式返回，不要添加任何其他文字：

{
    "activity_type": "学习/运动/编程/社交/工作/创作/生活/休息",
    "exp_gained": 数字,
    "gold_gained": 数字,
    "attribute_changes": {"属性名": 变化值},
    "equipment_found": {
        "name": "装备名称",
        "description": "装备描述",
        "rarity": "普通/稀有/史诗/传说",
        "stat_bonuses": {"属性名": 加成值}
    },
    "title_earned": {
        "name": "称号名称",
        "description": "称号描述"
    },
    "new_quest": {
        "title": "任务标题",
        "description": "任务描述",
        "exp_reward": 数字,
        "gold_reward": 数字
    },
    "comment": "你的趣味评价，要幽默有创意"
}

【重要】属性分析指南 - 必须仔细分析用户行为，智能判断应该提升的属性：

五维属性定义：
- strength(力量)：身体素质、运动能力、体力、耐力、肌肉力量
- intelligence(智力)：学习能力、逻辑思维、知识储备、解决问题、创造力
- agility(敏捷)：反应速度、灵活性、协调性、手速、动作敏捷
- charisma(魅力)：社交能力、领导力、表达能力、说服力、人际交往
- willpower(意志)：毅力、自控力、专注力、决心、抗压能力

智能属性判断示例：
1. "跑步30分钟" → 主要提升strength(力量)，次要agility(敏捷)
2. "看了一本编程书" → 主要提升intelligence(智力)，次要willpower(意志)
3. "和朋友聚餐聊天" → 主要提升charisma(魅力)
4. "冥想15分钟" → 主要提升willpower(意志)
5. "打篮球2小时" → 主要提升strength(力量)和agility(敏捷)
6. "写代码debug" → 主要提升intelligence(智力)和willpower(意志)
7. "做演讲" → 主要提升charisma(魅力)和willpower(意志)
8. "早起跑步" → strength(力量) + willpower(意志)
9. "学习新语言" → intelligence(智力) + charisma(魅力)
10. "做饭" → intelligence(智力) + agility(敏捷) + charisma(魅力)
11. "打扫房间" → willpower(意志) + agility(敏捷)
12. "玩游戏" → agility(敏捷) + intelligence(智力)（如果是策略游戏）
13. "加班到深夜" → willpower(意志)为主
14. "安慰朋友" → charisma(魅力) + willpower(意志)
15. "健身" → strength(力量)为主，willpower(意志)为副

属性变化规则：
- 主属性：+1~2（根据活动强度）
- 相关副属性：+1（50%概率）
- 额外属性：+1（10%概率）
- 要根据具体行为分析，不要固定模式

注意事项：
1. 装备和称号要根据活动内容创意生成，要有趣味性
2. 称号可以参考网络梗、游戏梗、生活梗
3. 评价要幽默，可以吐槽，但要积极向上
4. 根据活动难度和时间调整exp和gold
5. 不是每次都会获得装备和称号，概率大约30%
6. 如果没有获得装备或称号，对应字段设为null
7. **必须仔细分析用户描述，不要简单套用活动类型**

【comment字段要求】这是最重要的部分，必须幽默有趣！
- 风格：像一个毒舌但关心你的朋友，或者一个吐槽up主
- 可以使用：网络热梗、表情包文字、夸张比喻、自嘲式鼓励
- 语气：轻松搞笑，但不要刻薄
- 长度：1-2句话，不要太长
- 示例风格：
  * "好家伙，你这是要成为卷王之王啊！建议下次直接通宵，效率翻倍（bushi）"
  * "你这运动量，连你家狗都自愧不如了"
  * "码农的日常：写代码-删代码-写代码-删代码...恭喜你完成了程序员的冥想"
  * "社交达人就是你！不过你确定不是在群里水群？"
  * "早起的鸟儿有虫吃，早起的你有...困意"

示例称号风格：
- "凌晨两点还在Debug的人"
- "永不DDL战士"
- "咖啡因依赖症患者"
- "早起毁一天选手"
"""


async def chat_with_ai(user_message: str, character_info: dict = None) -> Optional[dict]:
    """与AI对话获取游戏化反馈"""
    provider_config = get_current_provider_config()
    provider_name = provider_config.get("name", "Ollama")
    
    context = ""
    if character_info:
        context = f"\n当前角色信息：等级{character_info.get('level', 1)}, "
        context += f"力量{character_info.get('strength', 10)}, "
        context += f"智力{character_info.get('intelligence', 10)}, "
        context += f"敏捷{character_info.get('agility', 10)}, "
        context += f"魅力{character_info.get('charisma', 10)}, "
        context += f"意志{character_info.get('willpower', 10)}"

    full_prompt = f"{context}\n\n用户活动：{user_message}"

    try:
        # 根据提供商类型选择不同的API调用方式
        if "ollama" in provider_name.lower() or provider_config.get("base_url", "").startswith("http://localhost"):
            return await _chat_with_ollama(provider_config, full_prompt)
        elif "openai" in provider_name.lower() or "api.openai.com" in provider_config.get("base_url", ""):
            return await _chat_with_openai(provider_config, full_prompt)
        elif "claude" in provider_name.lower() or "anthropic" in provider_config.get("base_url", ""):
            return await _chat_with_claude(provider_config, full_prompt)
        else:
            # 通用OpenAI兼容API（适用于DeepSeek、自定义等）
            return await _chat_with_openai_compatible(provider_config, full_prompt)
    except Exception as e:
        print(f"AI服务错误: {e}")
        return None


async def _chat_with_ollama(config: dict, prompt: str) -> Optional[dict]:
    """与Ollama对话"""
    base_url = config.get("base_url", "http://localhost:11434")
    model = config.get("model", "gemma4:latest")
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 512
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                return _parse_json_response(content)
            else:
                print(f"Ollama API error: {response.status_code}")
                return None
    except httpx.ConnectError:
        print("无法连接到Ollama服务，请确保Ollama正在运行")
        return None


async def _chat_with_openai(config: dict, prompt: str) -> Optional[dict]:
    """与OpenAI对话"""
    api_key = config.get("api_key")
    if not api_key:
        print("OpenAI API key未配置")
        return None
    
    base_url = config.get("base_url", "https://api.openai.com/v1")
    model = config.get("model", "gpt-3.5-turbo")
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return _parse_json_response(content)
            else:
                print(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"OpenAI请求失败: {e}")
        return None


async def _chat_with_claude(config: dict, prompt: str) -> Optional[dict]:
    """与Claude对话"""
    api_key = config.get("api_key")
    if not api_key:
        print("Claude API key未配置")
        return None
    
    base_url = config.get("base_url", "https://api.anthropic.com/v1")
    model = config.get("model", "claude-3-sonnet-20240229")
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{base_url}/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [{}])[0].get("text", "")
                return _parse_json_response(content)
            else:
                print(f"Claude API error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"Claude请求失败: {e}")
        return None


async def _chat_with_openai_compatible(config: dict, prompt: str) -> Optional[dict]:
    """与OpenAI兼容API对话（适用于DeepSeek、自定义等）"""
    api_key = config.get("api_key")
    base_url = config.get("base_url", "")
    model = config.get("model", "")
    
    if not base_url or not model:
        print("自定义AI配置不完整")
        return None
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return _parse_json_response(content)
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"API请求失败: {e}")
        return None


def _parse_json_response(content: str) -> Optional[dict]:
    """解析JSON响应"""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试提取JSON部分
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return None


async def generate_daily_summary(logs: list, character_info: dict) -> Optional[str]:
    """生成每日总结"""
    if not logs:
        return None

    provider_config = get_current_provider_config()
    
    activities = "\n".join([
        f"- {log.get('description', '未知活动')} (获得{log.get('exp_gained', 0)}经验值)"
        for log in logs
    ])

    prompt = f"""今日活动记录：
{activities}

角色信息：等级{character_info.get('level', 1)}

请用2-3句话总结今天的表现，要幽默有激励性，像游戏里的NPC一样说话。"""

    try:
        # 使用简化的总结提示
        summary_prompt = f"系统: 你是LifeRPG的NPC，用游戏角色的语气总结玩家的一天。\n\n用户: {prompt}"
        result = await chat_with_ai(summary_prompt)
        if result and isinstance(result, dict):
            return result.get("comment", str(result))
        elif result:
            return str(result)
    except Exception as e:
        print(f"生成总结失败: {e}")

    return None


async def check_ai_status() -> dict:
    """检查AI服务状态"""
    provider_config = get_current_provider_config()
    provider_name = provider_config.get("name", "未知")
    base_url = provider_config.get("base_url", "")
    
    # Ollama特殊处理
    if "ollama" in provider_name.lower() or base_url.startswith("http://localhost"):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {
                        "connected": True,
                        "provider": provider_name,
                        "models": models
                    }
        except:
            pass
        return {
            "connected": False,
            "provider": provider_name,
            "models": []
        }
    
    # 其他API检查（简单测试连接）
    api_key = provider_config.get("api_key")
    if not api_key and "ollama" not in provider_name.lower():
        return {
            "connected": False,
            "provider": provider_name,
            "error": "API key未配置"
        }
    
    return {
        "connected": True,
        "provider": provider_name,
        "models": [provider_config.get("model", "")]
    }


async def list_models() -> list:
    """获取可用模型列表"""
    provider_config = get_current_provider_config()
    base_url = provider_config.get("base_url", "")
    
    # Ollama特殊处理
    if base_url.startswith("http://localhost"):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except:
            pass
    
    return [provider_config.get("model", "")]


def get_ai_providers() -> dict:
    """获取所有可用的AI提供商"""
    config = load_config()
    return config.get("providers", {})


def update_ai_provider(provider_name: str, provider_config: dict = None):
    """更新当前AI提供商"""
    config = load_config()
    
    if provider_config:
        # 更新提供商配置
        if "providers" not in config:
            config["providers"] = {}
        config["providers"][provider_name] = provider_config
    
    config["ai_provider"] = provider_name
    save_config(config)


def update_provider_config(provider_name: str, updates: dict):
    """更新特定提供商的配置"""
    config = load_config()
    
    if "providers" not in config:
        config["providers"] = {}
    
    if provider_name in config["providers"]:
        config["providers"][provider_name].update(updates)
        save_config(config)
        return True
    return False