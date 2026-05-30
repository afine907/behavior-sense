"""
Agent监控示例
"""
import asyncio
from behavior_sdk import BehaviorSenseClient


async def monitor_agents():
    """监控所有Agent"""
    async with BehaviorSenseClient(base_url="http://localhost:8001") as client:

        print("🔍 开始Agent监控...")

        # 获取所有Agent
        agents = await client.list_agents()
        print(f"发现 {agents.get('total', 0)} 个Agent")

        for agent in agents.get('agents', []):
            agent_id = agent['agent_id']

            # 获取统计
            stats = await client.get_agent_stats(agent_id)

            # 获取风险评估
            risk = await client.get_agent_risk(agent_id)

            # 打印摘要
            print(f"\n{'='*50}")
            print(f"Agent: {agent.get('agent_name', agent_id)}")
            print(f"  Status: {agent.get('status', 'unknown')}")
            print(f"  Events: {stats.get('total_events', 0)}")
            print(f"  Cost: ${stats.get('total_cost_usd', 0):.2f}")
            print(f"  Success Rate: {stats.get('success_rate', 0):.1%}")
            print(f"  Risk Score: {risk.get('risk_score', 0):.2f}")
            print(f"  Risk Level: {risk.get('risk_level', 'unknown')}")


async def check_anomalies():
    """检查异常"""
    async with BehaviorSenseClient(base_url="http://localhost:8001") as client:

        print("\n🚨 检查异常...")

        scores = await client.get_anomaly_scores()

        for agent in scores.get('agents', []):
            if agent.get('score', 0) > 0.5:
                print(f"⚠️ {agent['agent_id']}: score={agent['score']:.2f}, level={agent.get('level', 'unknown')}")


async def main():
    await monitor_agents()
    await check_anomalies()


if __name__ == "__main__":
    asyncio.run(main())
