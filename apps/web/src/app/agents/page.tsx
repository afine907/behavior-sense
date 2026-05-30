'use client'

import { useState } from 'react'

const mockAgents = [
  { id: 'agent-researcher-001', name: 'Research Agent', type: 'llm_agent', model: 'claude-3-opus', status: 'active', events: 7600, cost: 42.10, success_rate: 0.92, tokens: 560000, safety: 'standard', risk: 0.15 },
  { id: 'agent-coder-002', name: 'Code Generator', type: 'llm_agent', model: 'gpt-4', status: 'active', events: 8900, cost: 67.20, success_rate: 0.95, tokens: 890000, safety: 'standard', risk: 0.22 },
  { id: 'agent-analyst-003', name: 'Data Analyst', type: 'workflow_agent', model: 'claude-3-sonnet', status: 'active', events: 5400, cost: 18.30, success_rate: 0.96, tokens: 340000, safety: 'trusted', risk: 0.08 },
  { id: 'agent-orchestrator-004', name: 'Orchestrator', type: 'multi_agent', model: 'gpt-4-turbo', status: 'active', events: 3200, cost: 5.42, success_rate: 0.89, tokens: 100000, safety: 'standard', risk: 0.31 },
  { id: 'agent-assistant-005', name: 'Quick Assistant', type: 'llm_agent', model: 'claude-3-haiku', status: 'active', events: 12500, cost: 23.40, success_rate: 0.98, tokens: 450000, safety: 'trusted', risk: 0.05 },
  { id: 'agent-stuck-001', name: 'Stuck Agent', type: 'llm_agent', model: 'gpt-4', status: 'error', events: 450, cost: 8.90, success_rate: 0.45, tokens: 120000, safety: 'restricted', risk: 0.72 },
  { id: 'agent-expensive-001', name: 'Expensive Agent', type: 'llm_agent', model: 'gpt-4', status: 'paused', events: 2300, cost: 89.50, success_rate: 0.88, tokens: 1200000, safety: 'standard', risk: 0.55 },
]

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: 'badge-green',
    idle: 'badge-blue',
    paused: 'badge-yellow',
    error: 'badge-red',
    terminated: 'badge-red',
  }
  return <span className={`badge ${colors[status] || 'badge-blue'}`}>{status}</span>
}

function SafetyBadge({ rating }: { rating: string }) {
  const colors: Record<string, string> = {
    trusted: 'badge-green',
    standard: 'badge-blue',
    restricted: 'badge-yellow',
    quarantined: 'badge-red',
    blocked: 'badge-red',
  }
  return <span className={`badge ${colors[rating] || 'badge-blue'}`}>{rating}</span>
}

function RiskBar({ score }: { score: number }) {
  const color = score > 0.7 ? 'bg-red-500' : score > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${score * 100}%` }} />
      </div>
      <span className="text-xs text-gray-400">{(score * 100).toFixed(0)}%</span>
    </div>
  )
}

export default function AgentsPage() {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  const filtered = mockAgents.filter(agent => {
    if (search && !agent.name.toLowerCase().includes(search.toLowerCase()) && !agent.id.includes(search)) return false
    if (typeFilter !== 'all' && agent.type !== typeFilter) return false
    if (statusFilter !== 'all' && agent.status !== statusFilter) return false
    return true
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Agents</h1>
        <p className="text-gray-500 text-sm">Monitor and manage your AI agents</p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <input
          type="text"
          placeholder="Search agents..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500 w-64"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
        >
          <option value="all">All Types</option>
          <option value="llm_agent">LLM Agent</option>
          <option value="workflow_agent">Workflow</option>
          <option value="multi_agent">Multi-Agent</option>
          <option value="tool_agent">Tool Agent</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="idle">Idle</option>
          <option value="paused">Paused</option>
          <option value="error">Error</option>
        </select>
        <div className="ml-auto text-sm text-gray-500">
          {filtered.length} agent{filtered.length !== 1 ? 's' : ''} found
        </div>
      </div>

      {/* Agent Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800 bg-gray-900/50">
              <th className="text-left py-3 px-4 font-medium">Agent</th>
              <th className="text-left py-3 px-4 font-medium">Type</th>
              <th className="text-left py-3 px-4 font-medium">Model</th>
              <th className="text-left py-3 px-4 font-medium">Status</th>
              <th className="text-left py-3 px-4 font-medium">Safety</th>
              <th className="text-right py-3 px-4 font-medium">Events</th>
              <th className="text-right py-3 px-4 font-medium">Cost</th>
              <th className="text-right py-3 px-4 font-medium">Success</th>
              <th className="text-left py-3 px-4 font-medium">Risk</th>
              <th className="text-center py-3 px-4 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((agent) => (
              <tr key={agent.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                <td className="py-3 px-4">
                  <div>
                    <div className="font-medium text-gray-200">{agent.name}</div>
                    <div className="text-xs text-gray-500 font-mono">{agent.id}</div>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className="badge badge-blue">{agent.type.replace('_', ' ')}</span>
                </td>
                <td className="py-3 px-4 text-gray-400 font-mono text-xs">{agent.model}</td>
                <td className="py-3 px-4"><StatusBadge status={agent.status} /></td>
                <td className="py-3 px-4"><SafetyBadge rating={agent.safety} /></td>
                <td className="py-3 px-4 text-right font-mono">{agent.events.toLocaleString()}</td>
                <td className="py-3 px-4 text-right font-mono">${agent.cost.toFixed(2)}</td>
                <td className="py-3 px-4 text-right">
                  <span className={agent.success_rate >= 0.9 ? 'text-green-400' : agent.success_rate >= 0.7 ? 'text-yellow-400' : 'text-red-400'}>
                    {(agent.success_rate * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="py-3 px-4"><RiskBar score={agent.risk} /></td>
                <td className="py-3 px-4 text-center">
                  <a href={`/agents/${agent.id}`} className="text-blue-400 hover:text-blue-300 text-sm">Details →</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
