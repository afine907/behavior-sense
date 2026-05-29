'use client'

import { useState } from 'react'

const mockAuditOrders = [
  { id: 'audit-1', agent_id: 'agent-researcher-001', rule: 'Dead Loop Detection', level: 'high', status: 'pending', assignee: null, created: '10 min ago', trigger: 'Agent stuck in repetitive search pattern (8 iterations)' },
  { id: 'audit-2', agent_id: 'agent-coder-002', rule: 'Cost Budget Exceeded', level: 'medium', status: 'in_review', assignee: 'alice', created: '25 min ago', trigger: 'Hourly cost $12.50 exceeded budget $5.00' },
  { id: 'audit-3', agent_id: 'agent-assistant-005', rule: 'Prompt Injection Guard', level: 'critical', status: 'approved', assignee: 'bob', created: '1 hour ago', trigger: 'Potential prompt injection in user input - blocked' },
  { id: 'audit-4', agent_id: 'agent-orchestrator-004', rule: 'Timeout Cascade', level: 'high', status: 'rejected', assignee: 'alice', created: '2 hours ago', trigger: '3 consecutive timeouts in delegation chain' },
  { id: 'audit-5', agent_id: 'agent-analyst-003', rule: 'Capability Drift', level: 'low', status: 'pending', assignee: null, created: '3 hours ago', trigger: 'Using unexpected tool: file_write' },
  { id: 'audit-6', agent_id: 'agent-expensive-001', rule: 'Token Explosion', level: 'medium', status: 'in_review', assignee: 'charlie', created: '4 hours ago', trigger: 'Single request consumed 85K tokens' },
]

const statusColors: Record<string, string> = {
  pending: 'badge-yellow',
  in_review: 'badge-blue',
  approved: 'badge-green',
  rejected: 'badge-red',
  closed: 'badge-green',
}

const levelColors: Record<string, string> = {
  critical: 'text-red-400',
  high: 'text-orange-400',
  medium: 'text-yellow-400',
  low: 'text-blue-400',
}

export default function AuditPage() {
  const [statusFilter, setStatusFilter] = useState('all')
  const [levelFilter, setLevelFilter] = useState('all')
  const [selectedOrder, setSelectedOrder] = useState<string | null>(null)

  const filtered = mockAuditOrders.filter(order => {
    if (statusFilter !== 'all' && order.status !== statusFilter) return false
    if (levelFilter !== 'all' && order.level !== levelFilter) return false
    return true
  })

  const pendingCount = mockAuditOrders.filter(o => o.status === 'pending').length
  const inReviewCount = mockAuditOrders.filter(o => o.status === 'in_review').length
  const selected = mockAuditOrders.find(o => o.id === selectedOrder)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Audit Workbench</h1>
          <p className="text-gray-500 text-sm">Review and manage agent behavior audit orders</p>
        </div>
        <div className="flex gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{pendingCount}</div>
            <div className="text-xs text-gray-500">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{inReviewCount}</div>
            <div className="text-xs text-gray-500">In Review</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="in_review">In Review</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
        >
          <option value="all">All Levels</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Audit Orders List */}
        <div className="lg:col-span-2 space-y-3">
          {filtered.map((order) => (
            <div
              key={order.id}
              className={`card cursor-pointer transition-all ${selectedOrder === order.id ? 'ring-2 ring-blue-500' : 'hover:bg-gray-800/50'}`}
              onClick={() => setSelectedOrder(order.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`badge ${statusColors[order.status]}`}>{order.status.replace('_', ' ')}</span>
                    <span className={`text-sm font-medium ${levelColors[order.level]}`}>{order.level}</span>
                    <span className="text-xs text-gray-600">{order.id}</span>
                  </div>
                  <div className="font-medium mb-1">{order.rule}</div>
                  <div className="text-sm text-gray-400 mb-2">{order.trigger}</div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>Agent: <span className="font-mono">{order.agent_id}</span></span>
                    <span>Created: {order.created}</span>
                    {order.assignee && <span>Assignee: {order.assignee}</span>}
                  </div>
                </div>
                {order.status === 'pending' && (
                  <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm">
                    Assign
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Detail Panel */}
        <div className="card">
          {selected ? (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Audit Detail</h3>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Order ID</span>
                  <span className="font-mono">{selected.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Agent</span>
                  <span className="font-mono">{selected.agent_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Rule</span>
                  <span>{selected.rule}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Level</span>
                  <span className={levelColors[selected.level]}>{selected.level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Status</span>
                  <span className={`badge ${statusColors[selected.status]}`}>{selected.status}</span>
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-400 mb-1">Trigger Data</div>
                <div className="p-3 bg-gray-800 rounded text-sm">{selected.trigger}</div>
              </div>

              <div>
                <div className="text-sm text-gray-400 mb-1">Reviewer Notes</div>
                <textarea
                  className="w-full p-3 bg-gray-800 border border-gray-700 rounded text-sm focus:outline-none focus:border-blue-500"
                  rows={3}
                  placeholder="Add review notes..."
                />
              </div>

              <div className="flex gap-2">
                <button className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm font-medium">
                  Approve
                </button>
                <button className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm font-medium">
                  Reject
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-12">
              <div className="text-4xl mb-4">🔍</div>
              <p>Select an audit order to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
