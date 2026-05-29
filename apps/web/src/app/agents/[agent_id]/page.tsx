'use client'

import { useState } from 'react'

// Mock data for a single agent
const agentData = {
  id: 'agent-coder-002',
  name: 'Code Generator',
  type: 'llm_agent',
  model: 'gpt-4',
  framework: 'langchain',
  owner: 'engineering-team',
  status: 'active',
  safety_rating: 'standard',
  cost_tier: 'standard',
  description: 'AI agent specialized in code generation, debugging, and refactoring',
  capabilities: ['code_generation', 'debugging', 'refactoring', 'testing', 'documentation'],
  supported_tools: ['code_execution', 'file_read', 'file_write', 'terminal', 'git'],
  risk_score: 0.22,
  create_time: '2024-01-15T10:00:00Z',
  last_active: '2024-01-20T14:23:05Z',
}

const statsData = {
  total_events: 8900,
  total_sessions: 342,
  total_tasks: 156,
  total_tool_calls: 5200,
  total_llm_calls: 3700,
  total_tokens: 890000,
  total_cost_usd: 67.20,
  avg_latency_ms: 1250,
  success_rate: 0.95,
  error_rate: 0.05,
  events_1d: 450,
  events_7d: 2800,
  tokens_1d: 45000,
  tokens_7d: 280000,
  cost_1d: 3.40,
  cost_7d: 21.50,
}

const recentTraces = [
  { trace_id: 'trace-abc123', task: 'Refactor auth module', duration: '2m 34s', spans: 12, status: 'ok', cost: '$0.45' },
  { trace_id: 'trace-def456', task: 'Fix unit tests', duration: '1m 12s', spans: 8, status: 'ok', cost: '$0.22' },
  { trace_id: 'trace-ghi789', task: 'Add API endpoint', duration: '3m 45s', spans: 18, status: 'error', cost: '$0.67' },
  { trace_id: 'trace-jkl012', task: 'Write documentation', duration: '45s', spans: 5, status: 'ok', cost: '$0.15' },
]

type Tab = 'overview' | 'timeline' | 'costs' | 'tools' | 'traces'

export default function AgentDetailPage({ params }: { params: { agent_id: string } }) {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const agent = agentData
  const stats = statsData

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: 'overview', label: 'Overview', icon: '📊' },
    { key: 'timeline', label: 'Timeline', icon: '⏱️' },
    { key: 'costs', label: 'Costs', icon: '💰' },
    { key: 'tools', label: 'Tools', icon: '🔧' },
    { key: 'traces', label: 'Traces', icon: '🔗' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold">{agent.name}</h1>
            <span className="badge badge-green">{agent.status}</span>
            <span className="badge badge-blue">{agent.type.replace('_', ' ')}</span>
          </div>
          <p className="text-gray-400 text-sm">{agent.description}</p>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>ID: <span className="font-mono">{agent.id}</span></span>
            <span>Model: <span className="font-mono">{agent.model}</span></span>
            <span>Framework: {agent.framework}</span>
            <span>Owner: {agent.owner}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm">Pause</button>
          <button className="px-4 py-2 bg-red-900/50 hover:bg-red-900/80 text-red-400 rounded-lg text-sm">Terminate</button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[
          { label: 'Events', value: stats.total_events.toLocaleString() },
          { label: 'Tasks', value: String(stats.total_tasks) },
          { label: 'Tool Calls', value: stats.total_tool_calls.toLocaleString() },
          { label: 'Tokens', value: `${(stats.total_tokens / 1000).toFixed(0)}K` },
          { label: 'Cost', value: `$${stats.total_cost_usd.toFixed(2)}` },
          { label: 'Success', value: `${(stats.success_rate * 100).toFixed(1)}%` },
        ].map((stat) => (
          <div key={stat.label} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-xs text-gray-500 mb-1">{stat.label}</div>
            <div className="text-xl font-bold">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-800">
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Capabilities</h3>
            <div className="flex flex-wrap gap-2">
              {agent.capabilities.map((cap) => (
                <span key={cap} className="badge badge-blue">{cap.replace('_', ' ')}</span>
              ))}
            </div>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Supported Tools</h3>
            <div className="flex flex-wrap gap-2">
              {agent.supported_tools.map((tool) => (
                <span key={tool} className="badge badge-green">{tool.replace('_', ' ')}</span>
              ))}
            </div>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Risk Assessment</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Risk Score</span>
                <span className={`font-bold ${agent.risk_score > 0.5 ? 'text-red-400' : agent.risk_score > 0.3 ? 'text-yellow-400' : 'text-green-400'}`}>
                  {(agent.risk_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${agent.risk_score > 0.5 ? 'bg-red-500' : agent.risk_score > 0.3 ? 'bg-yellow-500' : 'bg-green-500'}`}
                  style={{ width: `${agent.risk_score * 100}%` }}
                />
              </div>
              <div className="text-sm text-gray-500">Safety Rating: <span className="text-gray-300">{agent.safety_rating}</span></div>
            </div>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Activity</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-400">Created</span><span>{new Date(agent.create_time).toLocaleDateString()}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Last Active</span><span>{new Date(agent.last_active).toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Events Today</span><span>{stats.events_1d}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Events (7d)</span><span>{stats.events_7d}</span></div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'traces' && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b border-gray-800 bg-gray-900/50">
                <th className="text-left py-3 px-4 font-medium">Trace ID</th>
                <th className="text-left py-3 px-4 font-medium">Task</th>
                <th className="text-right py-3 px-4 font-medium">Duration</th>
                <th className="text-right py-3 px-4 font-medium">Spans</th>
                <th className="text-left py-3 px-4 font-medium">Status</th>
                <th className="text-right py-3 px-4 font-medium">Cost</th>
                <th className="text-center py-3 px-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {recentTraces.map((trace) => (
                <tr key={trace.trace_id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="py-3 px-4 font-mono text-xs">{trace.trace_id}</td>
                  <td className="py-3 px-4">{trace.task}</td>
                  <td className="py-3 px-4 text-right font-mono">{trace.duration}</td>
                  <td className="py-3 px-4 text-right">{trace.spans}</td>
                  <td className="py-3 px-4">
                    <span className={`badge ${trace.status === 'ok' ? 'badge-green' : 'badge-red'}`}>{trace.status}</span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono">{trace.cost}</td>
                  <td className="py-3 px-4 text-center">
                    <a href={`/traces/${trace.trace_id}`} className="text-blue-400 hover:text-blue-300">View →</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'costs' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Cost Breakdown</h3>
            <div className="space-y-3">
              {[
                { period: 'Today', cost: stats.cost_1d },
                { period: 'Last 7 days', cost: stats.cost_7d },
                { period: 'All time', cost: stats.total_cost_usd },
              ].map((item) => (
                <div key={item.period} className="flex items-center justify-between">
                  <span className="text-gray-400">{item.period}</span>
                  <span className="font-mono text-lg">${item.cost.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Token Usage</h3>
            <div className="space-y-3">
              {[
                { period: 'Today', tokens: stats.tokens_1d },
                { period: 'Last 7 days', tokens: stats.tokens_7d },
                { period: 'All time', tokens: stats.total_tokens },
              ].map((item) => (
                <div key={item.period} className="flex items-center justify-between">
                  <span className="text-gray-400">{item.period}</span>
                  <span className="font-mono text-lg">{(item.tokens / 1000).toFixed(0)}K</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'timeline' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Recent Activity Timeline</h3>
          <div className="space-y-4">
            {[
              { time: '14:23:05', event: 'Tool call: code_execution', status: 'ok' },
              { time: '14:22:58', event: 'LLM request to gpt-4', status: 'ok' },
              { time: '14:22:45', event: 'Tool call: file_read', status: 'ok' },
              { time: '14:22:30', event: 'Task started: Refactor auth module', status: 'ok' },
              { time: '14:20:15', event: 'Tool call: terminal (npm test)', status: 'error' },
              { time: '14:20:00', event: 'LLM request to gpt-4', status: 'ok' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="flex flex-col items-center">
                  <div className={`w-3 h-3 rounded-full ${item.status === 'ok' ? 'bg-green-500' : 'bg-red-500'}`} />
                  {i < 5 && <div className="w-0.5 h-8 bg-gray-800 mt-1" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-gray-500">{item.time}</span>
                    <span className="text-sm">{item.event}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'tools' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Tool Usage Analysis</h3>
          <div className="space-y-4">
            {[
              { name: 'code_execution', calls: 2100, success: 0.97, avg_latency: 342, cost: 12.30 },
              { name: 'file_read', calls: 1500, success: 0.99, avg_latency: 45, cost: 0.50 },
              { name: 'file_write', calls: 800, success: 0.98, avg_latency: 52, cost: 0.30 },
              { name: 'terminal', calls: 500, success: 0.92, avg_latency: 1250, cost: 8.20 },
              { name: 'git', calls: 300, success: 0.99, avg_latency: 180, cost: 1.10 },
            ].map((tool) => (
              <div key={tool.name} className="flex items-center gap-4 p-3 bg-gray-800/50 rounded-lg">
                <div className="w-32 font-medium">{tool.name}</div>
                <div className="flex-1">
                  <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${tool.success * 100}%` }} />
                  </div>
                </div>
                <div className="text-right text-sm">
                  <div>{tool.calls.toLocaleString()} calls</div>
                  <div className="text-gray-500">{(tool.success * 100).toFixed(1)}% · {tool.avg_latency}ms</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
