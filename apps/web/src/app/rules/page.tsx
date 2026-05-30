'use client'

import { useState } from 'react'

const mockRules = [
  { id: 'rule-1', name: 'Hourly Cost Budget', category: 'cost', condition: 'cost_usd_hourly > 5.0', priority: 100, enabled: true, triggered: 12, last_triggered: '5 min ago' },
  { id: 'rule-2', name: 'Dead Loop Detection', category: 'anomaly', condition: 'same_action_count_1min >= 5', priority: 95, enabled: true, triggered: 3, last_triggered: '2 min ago' },
  { id: 'rule-3', name: 'Prompt Injection Guard', category: 'security', condition: 'has_prompt_injection_markers == True', priority: 100, enabled: true, triggered: 1, last_triggered: '15 min ago' },
  { id: 'rule-4', name: 'Token Explosion Limit', category: 'cost', condition: 'total_tokens > 100000', priority: 90, enabled: true, triggered: 5, last_triggered: '20 min ago' },
  { id: 'rule-5', name: 'Timeout Cascade Alert', category: 'performance', condition: 'timeout_count_5min >= 3', priority: 90, enabled: true, triggered: 2, last_triggered: '8 min ago' },
  { id: 'rule-6', name: 'Unauthorized Tool Access', category: 'security', condition: 'tool_name not in allowed_tools', priority: 85, enabled: true, triggered: 0, last_triggered: 'Never' },
  { id: 'rule-7', name: 'Delegation Chain Limit', category: 'multi-agent', condition: 'delegation_depth > 5', priority: 75, enabled: false, triggered: 0, last_triggered: 'Never' },
  { id: 'rule-8', name: 'Agent Idle Detection', category: 'efficiency', condition: 'idle_duration_minutes > 60', priority: 40, enabled: true, triggered: 7, last_triggered: '1 hour ago' },
]

const categoryColors: Record<string, string> = {
  cost: 'badge-green',
  security: 'badge-red',
  anomaly: 'badge-yellow',
  performance: 'badge-blue',
  'multi-agent': 'badge-blue',
  efficiency: 'badge-green',
}

export default function RulesPage() {
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [showDisabled, setShowDisabled] = useState(true)

  const filtered = mockRules.filter(rule => {
    if (categoryFilter !== 'all' && rule.category !== categoryFilter) return false
    if (!showDisabled && !rule.enabled) return false
    return true
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Rules</h1>
          <p className="text-gray-500 text-sm">Manage agent behavior monitoring rules</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium">
          + New Rule
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-xs text-gray-500 mb-1">Total Rules</div>
          <div className="text-2xl font-bold">{mockRules.length}</div>
        </div>
        <div className="card">
          <div className="text-xs text-gray-500 mb-1">Enabled</div>
          <div className="text-2xl font-bold text-green-400">{mockRules.filter(r => r.enabled).length}</div>
        </div>
        <div className="card">
          <div className="text-xs text-gray-500 mb-1">Triggered Today</div>
          <div className="text-2xl font-bold text-yellow-400">{mockRules.reduce((s, r) => s + r.triggered, 0)}</div>
        </div>
        <div className="card">
          <div className="text-xs text-gray-500 mb-1">Categories</div>
          <div className="text-2xl font-bold">{new Set(mockRules.map(r => r.category)).size}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
        >
          <option value="all">All Categories</option>
          <option value="cost">Cost</option>
          <option value="security">Security</option>
          <option value="anomaly">Anomaly</option>
          <option value="performance">Performance</option>
          <option value="multi-agent">Multi-Agent</option>
          <option value="efficiency">Efficiency</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <input type="checkbox" checked={showDisabled} onChange={(e) => setShowDisabled(e.target.checked)} className="rounded" />
          Show disabled
        </label>
      </div>

      {/* Rules Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800 bg-gray-900/50">
              <th className="text-left py-3 px-4 font-medium">Rule</th>
              <th className="text-left py-3 px-4 font-medium">Category</th>
              <th className="text-left py-3 px-4 font-medium">Condition</th>
              <th className="text-right py-3 px-4 font-medium">Priority</th>
              <th className="text-left py-3 px-4 font-medium">Status</th>
              <th className="text-right py-3 px-4 font-medium">Triggered</th>
              <th className="text-left py-3 px-4 font-medium">Last</th>
              <th className="text-center py-3 px-4 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((rule) => (
              <tr key={rule.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                <td className="py-3 px-4 font-medium">{rule.name}</td>
                <td className="py-3 px-4">
                  <span className={`badge ${categoryColors[rule.category] || 'badge-blue'}`}>{rule.category}</span>
                </td>
                <td className="py-3 px-4 font-mono text-xs text-gray-400 max-w-xs truncate">{rule.condition}</td>
                <td className="py-3 px-4 text-right font-mono">{rule.priority}</td>
                <td className="py-3 px-4">
                  <span className={`badge ${rule.enabled ? 'badge-green' : 'badge-yellow'}`}>
                    {rule.enabled ? 'enabled' : 'disabled'}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">{rule.triggered}</td>
                <td className="py-3 px-4 text-gray-500 text-xs">{rule.last_triggered}</td>
                <td className="py-3 px-4 text-center">
                  <div className="flex gap-2 justify-center">
                    <button className="text-blue-400 hover:text-blue-300 text-xs">Edit</button>
                    <button className={`${rule.enabled ? 'text-yellow-400 hover:text-yellow-300' : 'text-green-400 hover:text-green-300'} text-xs`}>
                      {rule.enabled ? 'Disable' : 'Enable'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
