'use client'

import { useEffect, useState } from 'react'

// Mock data - in production, fetch from API
const mockOverview = {
  total_agents: 12,
  active_agents: 8,
  total_cost_usd: 156.42,
  total_events: 45230,
  total_tokens: 2340000,
  avg_success_rate: 0.943,
}

const mockAlerts = [
  { id: '1', type: 'cost_spike', severity: 'high', agent: 'agent-coder-002', message: 'Cost spike: $12.50 in last 5 minutes', time: '2 min ago' },
  { id: '2', type: 'dead_loop', severity: 'critical', agent: 'agent-researcher-001', message: 'Detected repetitive behavior pattern (8 iterations)', time: '5 min ago' },
  { id: '3', type: 'timeout_cascade', severity: 'high', agent: 'agent-orchestrator-004', message: '3 consecutive timeouts in delegation chain', time: '8 min ago' },
  { id: '4', type: 'capability_drift', severity: 'medium', agent: 'agent-analyst-003', message: 'Using unexpected tool: file_write', time: '12 min ago' },
]

const mockTopAgents = [
  { id: 'agent-assistant-005', name: 'Quick Assistant', events: 12500, cost: 23.40, success_rate: 0.98, tokens: 450000 },
  { id: 'agent-coder-002', name: 'Code Generator', events: 8900, cost: 67.20, success_rate: 0.95, tokens: 890000 },
  { id: 'agent-researcher-001', name: 'Research Agent', events: 7600, cost: 42.10, success_rate: 0.92, tokens: 560000 },
  { id: 'agent-analyst-003', name: 'Data Analyst', events: 5400, cost: 18.30, success_rate: 0.96, tokens: 340000 },
  { id: 'agent-orchestrator-004', name: 'Orchestrator', events: 3200, cost: 5.42, success_rate: 0.89, tokens: 100000 },
]

const mockRecentEvents = [
  { time: '14:23:05', agent: 'agent-coder-002', type: 'tool_call', tool: 'code_execution', latency: '342ms' },
  { time: '14:23:04', agent: 'agent-researcher-001', type: 'llm_request', tool: '-', latency: '2.1s' },
  { time: '14:23:03', agent: 'agent-assistant-005', type: 'tool_call', tool: 'web_search', latency: '890ms' },
  { time: '14:23:02', agent: 'agent-orchestrator-004', type: 'delegation', tool: '-', latency: '45ms' },
  { time: '14:23:01', agent: 'agent-analyst-003', type: 'llm_response', tool: '-', latency: '1.8s' },
]

function MetricCard({ title, value, subtitle, trend }: { title: string; value: string; subtitle?: string; trend?: 'up' | 'down' | 'neutral' }) {
  return (
    <div className="card">
      <div className="card-header">{title}</div>
      <div className="card-value">{value}</div>
      {subtitle && (
        <div className="text-sm text-gray-500 mt-1">
          {trend === 'up' && <span className="text-green-400">↑ </span>}
          {trend === 'down' && <span className="text-red-400">↓ </span>}
          {subtitle}
        </div>
      )}
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: 'badge-red',
    high: 'badge-red',
    medium: 'badge-yellow',
    low: 'badge-green',
  }
  return <span className={`badge ${colors[severity] || 'badge-blue'}`}>{severity}</span>
}

function AlertTypeBadge({ type }: { type: string }) {
  const labels: Record<string, string> = {
    cost_spike: '💰 Cost',
    dead_loop: '🔄 Loop',
    timeout_cascade: '⏱️ Timeout',
    capability_drift: '📈 Drift',
    prompt_injection: '🛡️ Security',
  }
  return <span className="badge badge-blue">{labels[type] || type}</span>
}

export default function Dashboard() {
  const [overview, setOverview] = useState(mockOverview)
  const [refreshing, setRefreshing] = useState(false)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Agent Monitoring Overview</h1>
          <p className="text-gray-500 text-sm">Real-time AI Agent behavior analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-400">Live</span>
          </div>
          <button
            onClick={() => { setRefreshing(true); setTimeout(() => setRefreshing(false), 1000) }}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors"
          >
            {refreshing ? 'Refreshing...' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Active Agents" value={String(overview.active_agents)} subtitle={`of ${overview.total_agents} total`} />
        <MetricCard title="Total Events" value={overview.total_events.toLocaleString()} subtitle="Last 24 hours" trend="up" />
        <MetricCard title="Total Cost" value={`$${overview.total_cost_usd.toFixed(2)}`} subtitle="Last 24 hours" trend="down" />
        <MetricCard title="Success Rate" value={`${(overview.avg_success_rate * 100).toFixed(1)}%`} subtitle="Across all agents" trend="up" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Alerts */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">🚨 Active Alerts</h2>
            <a href="/alerts" className="text-sm text-blue-400 hover:text-blue-300">View all →</a>
          </div>
          <div className="space-y-3">
            {mockAlerts.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg">
                <div className="flex-shrink-0 mt-0.5">
                  <SeverityBadge severity={alert.severity} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTypeBadge type={alert.type} />
                    <span className="text-sm font-medium text-gray-300">{alert.agent}</span>
                  </div>
                  <p className="text-sm text-gray-400 truncate">{alert.message}</p>
                  <span className="text-xs text-gray-600">{alert.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Agents */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">🤖 Top Agents</h2>
            <a href="/agents" className="text-sm text-blue-400 hover:text-blue-300">View all →</a>
          </div>
          <div className="space-y-2">
            {mockTopAgents.map((agent, i) => (
              <div key={agent.id} className="flex items-center gap-4 p-3 bg-gray-800/50 rounded-lg">
                <div className="text-lg font-bold text-gray-600 w-6">#{i + 1}</div>
                <div className="flex-1">
                  <div className="font-medium text-gray-200">{agent.name}</div>
                  <div className="text-xs text-gray-500">{agent.id}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-300">{(agent.success_rate * 100).toFixed(1)}%</div>
                  <div className="text-xs text-gray-500">${agent.cost.toFixed(2)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Events Stream */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">📡 Recent Events</h2>
          <a href="/traces" className="text-sm text-blue-400 hover:text-blue-300">View traces →</a>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b border-gray-800">
                <th className="text-left py-2 px-3 font-medium">Time</th>
                <th className="text-left py-2 px-3 font-medium">Agent</th>
                <th className="text-left py-2 px-3 font-medium">Event Type</th>
                <th className="text-left py-2 px-3 font-medium">Tool</th>
                <th className="text-right py-2 px-3 font-medium">Latency</th>
              </tr>
            </thead>
            <tbody>
              {mockRecentEvents.map((event, i) => (
                <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="py-2 px-3 font-mono text-gray-500">{event.time}</td>
                  <td className="py-2 px-3 text-gray-300">{event.agent}</td>
                  <td className="py-2 px-3">
                    <span className="badge badge-blue">{event.type}</span>
                  </td>
                  <td className="py-2 px-3 text-gray-400">{event.tool}</td>
                  <td className="py-2 px-3 text-right font-mono text-gray-400">{event.latency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
