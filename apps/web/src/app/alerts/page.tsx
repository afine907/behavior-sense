'use client'

import { useState } from 'react'

const mockAlerts = [
  { id: 'alert-1', type: 'dead_loop', severity: 'critical', agent_id: 'agent-researcher-001', message: 'Agent stuck in repetitive search pattern (8 iterations)', time: '2 min ago', resolved: false, auto_action: 'paused' },
  { id: 'alert-2', type: 'cost_spike', severity: 'high', agent_id: 'agent-coder-002', message: 'Cost spike: $12.50 in last 5 minutes (5x normal)', time: '5 min ago', resolved: false, auto_action: 'throttled' },
  { id: 'alert-3', type: 'timeout_cascade', severity: 'high', agent_id: 'agent-orchestrator-004', message: '3 consecutive timeouts in delegation chain', time: '8 min ago', resolved: false, auto_action: 'none' },
  { id: 'alert-4', type: 'capability_drift', severity: 'medium', agent_id: 'agent-analyst-003', message: 'Using unexpected tool: file_write (not in baseline)', time: '12 min ago', resolved: false, auto_action: 'none' },
  { id: 'alert-5', type: 'prompt_injection', severity: 'critical', agent_id: 'agent-assistant-005', message: 'Potential prompt injection detected in user input', time: '15 min ago', resolved: true, auto_action: 'blocked' },
  { id: 'alert-6', type: 'token_explosion', severity: 'medium', agent_id: 'agent-expensive-001', message: 'Single request consumed 85K tokens', time: '20 min ago', resolved: true, auto_action: 'logged' },
  { id: 'alert-7', type: 'resource_contention', severity: 'low', agent_id: 'agent-coder-002', message: '3 agents competing for database access', time: '25 min ago', resolved: true, auto_action: 'none' },
]

const alertTypeIcons: Record<string, string> = {
  dead_loop: '🔄',
  cost_spike: '💰',
  timeout_cascade: '⏱️',
  capability_drift: '📈',
  prompt_injection: '🛡️',
  token_explosion: '💥',
  resource_contention: '⚡',
  error_rate_spike: '❌',
  tool_abuse: '🔧',
}

const severityColors: Record<string, string> = {
  critical: 'border-l-red-500 bg-red-950/20',
  high: 'border-l-orange-500 bg-orange-950/20',
  medium: 'border-l-yellow-500 bg-yellow-950/20',
  low: 'border-l-blue-500 bg-blue-950/20',
}

export default function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState('all')
  const [showResolved, setShowResolved] = useState(false)

  const filtered = mockAlerts.filter(alert => {
    if (severityFilter !== 'all' && alert.severity !== severityFilter) return false
    if (!showResolved && alert.resolved) return false
    return true
  })

  const unresolvedCount = mockAlerts.filter(a => !a.resolved).length
  const criticalCount = mockAlerts.filter(a => a.severity === 'critical' && !a.resolved).length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Alert Center</h1>
          <p className="text-gray-500 text-sm">Monitor and respond to agent anomalies</p>
        </div>
        <div className="flex gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-red-400">{criticalCount}</div>
            <div className="text-xs text-gray-500">Critical</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{unresolvedCount}</div>
            <div className="text-xs text-gray-500">Unresolved</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <input type="checkbox" checked={showResolved} onChange={(e) => setShowResolved(e.target.checked)} className="rounded" />
          Show resolved
        </label>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filtered.map((alert) => (
          <div key={alert.id} className={`card border-l-4 ${severityColors[alert.severity]} ${alert.resolved ? 'opacity-60' : ''}`}>
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <span className="text-2xl">{alertTypeIcons[alert.type] || '⚠️'}</span>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold">{alert.type.replace(/_/g, ' ')}</span>
                    <span className={`badge ${alert.severity === 'critical' ? 'badge-red' : alert.severity === 'high' ? 'badge-red' : alert.severity === 'medium' ? 'badge-yellow' : 'badge-blue'}`}>
                      {alert.severity}
                    </span>
                    {alert.resolved && <span className="badge badge-green">resolved</span>}
                  </div>
                  <p className="text-gray-300 text-sm mb-2">{alert.message}</p>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>Agent: <span className="font-mono">{alert.agent_id}</span></span>
                    <span>{alert.time}</span>
                    {alert.auto_action !== 'none' && (
                      <span className="badge badge-blue">Auto: {alert.auto_action}</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {!alert.resolved && (
                  <>
                    <button className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-sm">Acknowledge</button>
                    <button className="px-3 py-1 bg-green-900/50 hover:bg-green-900/80 text-green-400 rounded text-sm">Resolve</button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
