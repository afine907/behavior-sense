"""
BehaviorSense SDK基本使用示例
"""
import asyncio
from behavior_sdk import BehaviorSenseClient, AgentEvent, TokenUsage


async def main():
    # 创建客户端
    async with BehaviorSenseClient(base_url="http://localhost:8001") as client:

        # 1. 发送Agent事件
        print("📊 发送Agent事件...")
        event = AgentEvent(
            agent_id="example-agent-001",
            agent_type="llm_agent",
            event_type="tool_call",
            model_name="gpt-4",
            tool_call={
                "tool_name": "web_search",
                "tool_type": "search",
                "latency_ms": 250,
                "success": True,
            },
        )
        result = await client.track_event(event)
        print(f"✅ 事件发送成功: {result}")

        # 2. 创建Agent画像
        print("\n🤖 创建Agent画像...")
        from behavior_sdk import AgentProfile
        profile = AgentProfile(
            agent_id="example-agent-001",
            agent_name="Example Agent",
            agent_type="llm_agent",
            model_name="gpt-4",
            capabilities=["search", "analysis", "code_generation"],
        )
        await client.create_agent(profile)
        print("✅ Agent创建成功")

        # 3. 设置标签
        print("\n🏷️ 设置Agent标签...")
        await client.set_agent_tag("example-agent-001", "environment", "production")
        await client.set_agent_tag("example-agent-001", "team", "engineering")
        print("✅ 标签设置成功")

        # 4. 获取Agent信息
        print("\n📋 获取Agent信息...")
        agent = await client.get_agent("example-agent-001")
        print(f"Agent: {agent.agent_name}")
        print(f"Type: {agent.agent_type}")
        print(f"Model: {agent.model_name}")

        # 5. 获取统计信息
        print("\n📊 获取统计信息...")
        stats = await client.get_agent_stats("example-agent-001")
        print(f"Events: {stats.get('total_events', 0)}")
        print(f"Cost: ${stats.get('total_cost_usd', 0):.2f}")

        # 6. 获取全局概览
        print("\n🌍 获取全局概览...")
        overview = await client.get_overview()
        print(f"Total Agents: {overview.get('total_agents', 0)}")
        print(f"Total Cost: ${overview.get('total_cost_usd', 0):.2f}")


if __name__ == "__main__":
    asyncio.run(main())
