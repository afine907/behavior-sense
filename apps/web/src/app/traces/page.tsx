'use client'

import { useState } from 'react'

const mockTraces = [
  { trace_id: 'trace-abc123', agent_id: 'agent-coder-002', task: 'Refactor auth module', start_time: '14:20:30', duration_ms: 154000, spans: 12, errors: 0, tokens: 15000, cost: 0.45, status: 'ok' },
  { trace_id: 'trace-def456', agent_id: 'agent-researcher-001', task: 'Research best practices', start_time: '14:18:00', duration_ms: 245000, spans: 18, errors: 1, tokens: 32000, cost: 0.89, status: 'error' },
  { trace_id: 'trace-ghi789', agent_id: 'agent-coder-002', task: 'Fix unit tests', start_time: '14:15:22', duration_ms: 72000, spans: 8, errors: 0, tokens: 8000, cost: 0.22, status: 'ok' },
  { trace_id: 'trace-jkl012', agent_id: 'agent-analyst-003', task: 'Generate report', start_time: '14:12:00', duration_ms: 180000, spans: 15, errors: 2, tokens: 25000, cost: 0.67, status: 'error' },
  { trace_id: 'trace-mno345', agent_id: 'agent-assistant-005', task: 'Answer user query', start_time: '14:10:00', duration_ms: 15000, spans: 5, errors: 0, tokens: 3000, cost: 0.08, status: 'ok' },
  { trace_id: 'trace-pqr678', agent_id: 'agent-orchestrator-004', task: 'Coordinate workflow', start_time: '14:08:00', duration_ms: 320000, spans: 24, errors: 3, tokens: 45000, cost: 1.20, status: 'error' },
]

const mockWaterfall = {
  trace_id: 'trace-abc123',
  total_duration_ms: 154000,
  spans: [
    { span_id: 'span-1', name: 'Refactor auth module', kind: 'agent', depth: 0, offset_ms: 0, duration_ms: 154000, status: 'ok' },
    { span_id: 'span-2', name: 'LLM: Plan refactoring', kind: 'llm', depth: 1, offset_ms: 100, duration_ms: 25000, status: 'ok' },
    { span_id: 'span-3', name: 'Read current code', kind: 'tool', depth: 1, offset_ms: 25200, duration_ms: 450, status: 'ok' },
    { span_id: 'span-4', name: 'LLM: Generate new code', kind: 'llm', depth: 1, offset_ms: 25700, duration_ms: 35000, status: 'ok' },
    { span_id: 'span-5', name: 'Write new file', kind: 'tool', depth: 1, offset_ms: 60800, duration_ms: 520, status: 'ok' },
    { span_id: 'span-6', name: 'Run tests', kind: 'tool', depth: 1, offset_ms: 61400, duration_ms: 45000, status: 'ok' },
    { span_id: 'span-7', name: 'LLM: Analyze results', kind: 'llm', depth: 1, offset_ms: 106500, duration_ms: 18000, status: 'ok' },
    { span_id: 'span-8', name: 'Commit changes', kind: 'tool', depth: 1, offset_ms: 124600, duration_ms: 1200, status: 'ok' },
  ],
}

function formatDuration(ms: number): string {
  if (ms >= 60000) return `${(ms / 60000).toFixed(1)}m`
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
}

function TraceWaterfall({ waterfall }: { waterfall: typeof mockWaterfall }) {
  const maxDuration = waterfall.total_duration_ms
  const kindColors: Record<string, string> = {
    agent: 'bg-blue-600',
    llm: 'bg-purple-600',
    tool: 'bg-green-600',
    chain: 'bg-yellow-600',
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">Trace Waterfall: {waterfall.trace_id}</h3>
      <div className="space-y-1">
        {waterfall.spans.map((span) => (
          <div key={span.span_id} className="flex items-center gap-3">
            <div className="w-48 text-right text-xs text-gray-400 truncate" style={{ paddingLeft: `${span.depth * 20}px` }}>
              {span.name}
            </div>
            <div className="flex-1 relative h-6 bg-gray-800 rounded">
              <div
                className={`absolute h-full rounded ${kindColors[span.kind] || 'bg-gray-600'} ${span.status === 'error' ? 'opacity-50' : ''}`}
                style={{
                  left: `${(span.offset_ms / maxDuration) * 100}%`,
                  width: `${Math.max((span.duration_ms / maxDuration) * 100, 0.5)}%`,
                }}
              />
            </div>
            <div className="w-20 text-xs text-gray-400 font-mono text-right">
              {formatDuration(span.duration_ms)}
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-4 mt-4 text-xs text-gray-500">
        {Object.entries(kindColors).map(([kind, color]) => (
          <div key={kind} className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded ${color}`} />
            <span>{kind}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function TracesPage() {
  const [selectedTrace, setSelectedTrace] = useState<string | null>(null)
  const [agentFilter, setAgentFilter] = useState('all')

  const filtered = agentFilter === 'all' ? mockTraces : mockTraces.filter(t => t.agent_id === agentFilter)
  const uniqueAgents = [...new Set(mockTraces.map(t => t.agent_id))]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Traces</h1>
        <p className="text-gray-500 text-sm">Explore agent execution traces and performance</p>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={agentFilter}
          onChange={(e) => setAgentFilter(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
        >
          <option value="all">All Agents</option>
          {uniqueAgents.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      {/* Waterfall (if trace selected) */}
      {selectedTrace && (
        <TraceWaterfall waterfall={mockWaterfall} />
      )}

      {/* Traces Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800 bg-gray-900/50">
              <th className="text-left py-3 px-4 font-medium">Trace ID</th>
              <th className="text-left py-3 px-4 font-medium">Agent</th>
              <th className="text-left py-3 px-4 font-medium">Task</th>
              <th className="text-left py-3 px-4 font-medium">Time</th>
              <th className="text-right py-3 px-4 font-medium">Duration</th>
              <th className="text-right py-3 px-4 font-medium">Spans</th>
              <th className="text-right py-3 px-4 font-medium">Errors</th>
              <th className="text-right py-3 px-4 font-medium">Tokens</th>
              <th className="text-right py-3 px-4 font-medium">Cost</th>
              <th className="text-left py-3 px-4 font-medium">Status</th>
              <th className="text-center py-3 px-4 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((trace) => (
              <tr
                key={trace.trace_id}
                className={`border-b border-gray-800/50 hover:bg-gray-800/30 cursor-pointer ${selectedTrace === trace.trace_id ? 'bg-gray-800/50' : ''}`}
                onClick={() => setSelectedTrace(trace.trace_id)}
              >
                <td className="py-3 px-4 font-mono text-xs">{trace.trace_id}</td>
                <td className="py-3 px-4 text-xs font-mono">{trace.agent_id}</td>
                <td className="py-3 px-4">{trace.task}</td>
                <td className="py-3 px-4 font-mono text-xs">{trace.start_time}</td>
                <td className="py-3 px-4 text-right font-mono">{formatDuration(trace.duration_ms)}</td>
                <td className="py-3 px-4 text-right">{trace.spans}</td>
                <td className="py-3 px-4 text-right">
                  {trace.errors > 0 ? <span className="text-red-400">{trace.errors}</span> : <span className="text-gray-600">0</span>}
                </td>
                <td className="py-3 px-4 text-right font-mono">{(trace.tokens / 1000).toFixed(1)}K</td>
                <td className="py-3 px-4 text-right font-mono">${trace.cost.toFixed(2)}</td>
                <td className="py-3 px-4">
                  <span className={`badge ${trace.status === 'ok' ? 'badge-green' : 'badge-red'}`}>{trace.status}</span>
                </td>
                <td className="py-3 px-4 text-center">
                  <button className="text-blue-400 hover:text-blue-300 text-sm">Expand</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
