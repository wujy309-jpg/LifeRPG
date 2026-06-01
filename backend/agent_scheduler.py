"""
LifeRPG 智能体调度器
负责定时任务、主动推送、事件触发
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class AgentScheduler:
    """智能体调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}
        self.callbacks = {}
    
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("智能体调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("智能体调度器已停止")
    
    def add_daily_reminder(self, character_id: int, hour: int = 7, minute: int = 0):
        """添加每日提醒"""
        job_id = f"daily_reminder_{character_id}"
        
        async def daily_reminder():
            from agent import get_agent
            from agent_database import create_notification
            
            agent = get_agent()
            now = datetime.now()
            
            # 生成早安通知
            create_notification(
                character_id=character_id,
                notification_type="reminder",
                title="早安！新的一天开始了",
                content="记得完成今天的任务哦！",
                priority=6,
                scheduled_time=now.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            print(f"[{now}] 已发送每日提醒给角色 {character_id}")
        
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            daily_reminder,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name=f"每日提醒-{character_id}"
        )
        self.jobs[job_id] = {
            "type": "daily_reminder",
            "character_id": character_id,
            "hour": hour,
            "minute": minute
        }
        
        print(f"已添加每日提醒: {hour}:{minute}")
    
    def add_evening_summary(self, character_id: int, hour: int = 21, minute: int = 0):
        """添加晚间总结"""
        job_id = f"evening_summary_{character_id}"
        
        async def evening_summary():
            from agent import get_agent
            from agent_database import create_notification
            from database import get_activity_logs
            
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            
            # 获取今日活动
            logs = get_activity_logs(character_id, limit=50)
            today_logs = [l for l in logs if l.get("created_at", "").startswith(today)]
            
            if today_logs:
                exp_sum = sum(l.get("exp_gained", 0) for l in today_logs)
                gold_sum = sum(l.get("gold_gained", 0) for l in today_logs)
                
                content = f"你今天完成了{len(today_logs)}个活动，获得了{exp_sum}经验值和{gold_sum}金币！"
            else:
                content = "你今天还没有记录活动，要不要做点什么？"
            
            create_notification(
                character_id=character_id,
                notification_type="summary",
                title="今日总结",
                content=content,
                priority=5,
                scheduled_time=now.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            print(f"[{now}] 已发送晚间总结给角色 {character_id}")
        
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            evening_summary,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name=f"晚间总结-{character_id}"
        )
        self.jobs[job_id] = {
            "type": "evening_summary",
            "character_id": character_id,
            "hour": hour,
            "minute": minute
        }
        
        print(f"已添加晚间总结: {hour}:{minute}")
    
    def add_weekly_review(self, character_id: int, day_of_week: int = 6, 
                         hour: int = 10, minute: int = 0):
        """添加每周回顾"""
        job_id = f"weekly_review_{character_id}"
        
        async def weekly_review():
            from agent import get_agent
            from agent_database import create_notification
            from database import get_activity_logs
            
            now = datetime.now()
            week_start = now - timedelta(days=now.weekday())
            
            # 获取本周活动
            logs = get_activity_logs(character_id, limit=100)
            week_logs = [
                l for l in logs 
                if l.get("created_at", "") >= week_start.strftime("%Y-%m-%d")
            ]
            
            if week_logs:
                exp_sum = sum(l.get("exp_gained", 0) for l in week_logs)
                
                # 分析活动类型
                activity_types = {}
                for log in week_logs:
                    at = log.get("activity_type", "其他")
                    activity_types[at] = activity_types.get(at, 0) + 1
                
                most_common = max(activity_types.items(), key=lambda x: x[1])
                
                content = (
                    f"本周完成了{len(week_logs)}个活动，获得{exp_sum}经验值。"
                    f"最常做的活动是{most_common[0]}（{most_common[1]}次）。"
                )
            else:
                content = "本周还没有记录活动，下周加油！"
            
            create_notification(
                character_id=character_id,
                notification_type="review",
                title="每周回顾",
                content=content,
                priority=7,
                scheduled_time=now.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            print(f"[{now}] 已发送每周回顾给角色 {character_id}")
        
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            weekly_review,
            CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
            id=job_id,
            name=f"每周回顾-{character_id}"
        )
        self.jobs[job_id] = {
            "type": "weekly_review",
            "character_id": character_id,
            "day_of_week": day_of_week,
            "hour": hour,
            "minute": minute
        }
        
        print(f"已添加每周回顾: 周{day_of_week} {hour}:{minute}")
    
    def add_inactivity_check(self, character_id: int, hours: int = 48):
        """添加不活跃检查"""
        job_id = f"inactivity_check_{character_id}"
        
        async def inactivity_check():
            from agent import get_agent
            from agent_database import create_notification
            from database import get_activity_logs
            
            now = datetime.now()
            
            # 获取最近活动
            logs = get_activity_logs(character_id, limit=1)
            
            if logs:
                last_activity = logs[0].get("created_at", "")
                if last_activity:
                    try:
                        last_dt = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")
                        hours_since = (now - last_dt).total_seconds() / 3600
                        
                        if hours_since >= hours:
                            create_notification(
                                character_id=character_id,
                                notification_type="encouragement",
                                title="好久不见！",
                                content=f"你已经{int(hours_since)}小时没有记录活动了，要不要做点什么？",
                                priority=7,
                                scheduled_time=now.strftime("%Y-%m-%d %H:%M:%S")
                            )
                            
                            print(f"[{now}] 已发送不活跃提醒给角色 {character_id}")
                    except:
                        pass
        
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
        
        # 每6小时检查一次
        self.scheduler.add_job(
            inactivity_check,
            IntervalTrigger(hours=6),
            id=job_id,
            name=f"不活跃检查-{character_id}"
        )
        self.jobs[job_id] = {
            "type": "inactivity_check",
            "character_id": character_id,
            "hours": hours
        }
        
        print(f"已添加不活跃检查: 每6小时检查一次")
    
    def add_goal_reminder(self, character_id: int, goal_id: int, 
                         deadline: str):
        """添加目标截止提醒"""
        job_id = f"goal_reminder_{goal_id}"
        
        async def goal_reminder():
            from agent_database import create_notification, get_long_term_goals
            
            goals = get_long_term_goals(character_id, status="active")
            goal = next((g for g in goals if g["id"] == goal_id), None)
            
            if goal:
                progress = goal.get("progress", 0)
                title = goal.get("title", "")
                
                if progress < 1.0:
                    # 提前3天提醒
                    deadline_dt = datetime.strptime(deadline, "%Y-%m-%d")
                    days_left = (deadline_dt - datetime.now()).days
                    
                    if days_left <= 3:
                        create_notification(
                            character_id=character_id,
                            notification_type="warning",
                            title=f"目标即将截止：{title}",
                            content=f"还有{days_left}天截止，当前进度：{progress*100:.0f}%",
                            priority=9,
                            scheduled_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
        
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
        
        # 提前3天开始提醒
        deadline_dt = datetime.strptime(deadline, "%Y-%m-%d")
        reminder_date = deadline_dt - timedelta(days=3)
        
        if reminder_date > datetime.now():
            self.scheduler.add_job(
                goal_reminder,
                CronTrigger(
                    year=reminder_date.year,
                    month=reminder_date.month,
                    day=reminder_date.day,
                    hour=9,
                    minute=0
                ),
                id=job_id,
                name=f"目标提醒-{goal_id}"
            )
            self.jobs[job_id] = {
                "type": "goal_reminder",
                "character_id": character_id,
                "goal_id": goal_id,
                "deadline": deadline
            }
            
            print(f"已添加目标提醒: {title} ({deadline})")
    
    def add_custom_job(self, job_id: str, func: Callable, trigger, **kwargs):
        """添加自定义任务"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            func,
            trigger,
            id=job_id,
            **kwargs
        )
        self.jobs[job_id] = {
            "type": "custom",
            "trigger": str(trigger)
        }
        
        print(f"已添加自定义任务: {job_id}")
    
    def remove_job(self, job_id: str):
        """移除任务"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            print(f"已移除任务: {job_id}")
    
    def get_jobs(self) -> List[Dict]:
        """获取所有任务"""
        jobs = []
        for job_id, info in self.jobs.items():
            job = self.scheduler.get_job(job_id)
            if job:
                jobs.append({
                    "id": job_id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    **info
                })
        return jobs
    
    def setup_character_schedule(self, character_id: int, config: Dict = None):
        """为角色设置默认调度"""
        config = config or {}
        
        # 每日提醒
        self.add_daily_reminder(
            character_id,
            hour=config.get("reminder_hour", 7),
            minute=config.get("reminder_minute", 0)
        )
        
        # 晚间总结
        self.add_evening_summary(
            character_id,
            hour=config.get("summary_hour", 21),
            minute=config.get("summary_minute", 0)
        )
        
        # 每周回顾
        self.add_weekly_review(
            character_id,
            day_of_week=config.get("review_day", 6),
            hour=config.get("review_hour", 10),
            minute=config.get("review_minute", 0)
        )
        
        # 不活跃检查
        self.add_inactivity_check(
            character_id,
            hours=config.get("inactivity_hours", 48)
        )
        
        print(f"已为角色 {character_id} 设置默认调度")


# 创建全局调度器实例
scheduler = AgentScheduler()


def get_scheduler() -> AgentScheduler:
    """获取调度器实例"""
    return scheduler


def start_scheduler():
    """启动调度器"""
    scheduler.start()


def stop_scheduler():
    """停止调度器"""
    scheduler.stop()


def setup_all_characters_schedule():
    """为所有角色设置调度"""
    from database import get_all_characters
    
    characters = get_all_characters()
    for character in characters:
        character_id = character["id"]
        
        # 获取角色的智能体配置
        from agent_database import get_agent_config
        config = get_agent_config(character_id)
        
        # 如果启用了主动推送，设置调度
        if config.get("proactive_enabled", True):
            scheduler.setup_character_schedule(character_id)


if __name__ == "__main__":
    # 测试调度器
    import asyncio
    
    async def test():
        start_scheduler()
        
        # 为测试角色设置调度
        scheduler.setup_character_schedule(1)
        
        # 运行一段时间
        await asyncio.sleep(60)
        
        stop_scheduler()
    
    asyncio.run(test())