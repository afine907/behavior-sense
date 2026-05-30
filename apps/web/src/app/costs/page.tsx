'use client'

const mockCostData = {
  total_cost: 156.42,
  cost_today: 12.30,
  cost_7d: 89.50,
  cost_30d: 456.80,
  budget_remaining: 843.20,
  budget_total: 1000.00,
  by_agent: [
    { agent: 'agent-coder-002', name: 'Code Generator', cost: 67.20, tokens: 890000, calls: 3700 },
    { agent: 'agent-researcher-001', name: 'Research Agent', cost: 42.10, tokens: 560000, calls: 2800 },
    { agent: 'agent-assistant-005', name: 'Quick Assistant', cost: 23.40, tokens: 450000, calls: 5200 },
    { agent: 'agent-analyst-003', name: 'Data Analyst', cost: 18.30, tokens: 340000, calls: 2100 },
    { agent: 'agent-orchestrator-004', name: 'Orchestrator', cost: 5.42, tokens: 100000, calls: 800 },
  ],
  by_model: [
    { model: 'gpt-4', cost: 89.50, tokens: 1200000, percentage: 57.2 },
    { model: 'claude-3-opus', cost: 42.10, tokens: 560000, percentage: 26.9 },
    { model: 'claude-3-sonnet', cost: 18.30, tokens: 340000, percentage: 11.7 },
    { model: 'claude-3-haiku', cost: 6.52, tokens: 240000, percentage: 4.2 },
  ],
  daily_trend: [
    { date: '01/14', cost: 8.20 },
    { date: '01/15', cost: 12.50 },
    { date: '01/16', cost: 9.80 },
    { date: '01/17', cost: 15.30 },
    { date: '01/18', cost: 11.40 },
    { date: '01/19', cost: 18.90 },
    { date: '01/20', cost: 12.30 },
  ],
}

function BarChart({ data, max }: { data: { label: string; value: number }[]; max: number }) {
  return (
    <div className="space-y-2">
      {data.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <div className="w-32 text-sm text-gray-400 truncate">{item.label}</div>
          <div className="flex-1 h-6 bg-gray-800 rounded overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded"
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
          <div className="w-20 text-sm font-mono text-right">${item.value.toFixed(2)}</div>
        </div>
      ))}
    </div>
  )
}

export default function CostsPage() {
  const data = mockCostData
  const budgetPercent = ((data.budget_total - data.budget_remaining) / data.budget_total) * 100

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Cost Analysis</h1>
        <p className="text-gray-500 text-sm">Monitor and optimize AI agent costs</p>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="card-header">Total Cost</div>
          <div className="card-value">${data.total_cost.toFixed(2)}</div>
          <div className="text-sm text-gray-500 mt-1">All time</div>
        </div>
        <div className="card">
          <div className="card-header">Today</div>
          <div className="card-value">${data.cost_today.toFixed(2)}</div>
          <div className="text-sm text-green-400 mt-1">↓ 12% vs yesterday</div>
        </div>
        <div className="card">
          <div className="card-header">Last 7 Days</div>
          <div className="card-value">${data.cost_7d.toFixed(2)}</div>
          <div className="text-sm text-red-400 mt-1">↑ 8% vs previous week</div>
        </div>
        <div className="card">
          <div className="card-header">Budget Remaining</div>
          <div className="card-value">${data.budget_remaining.toFixed(2)}</div>
          <div className="mt-2">
            <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${budgetPercent > 80 ? 'bg-red-500' : budgetPercent > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                style={{ width: `${budgetPercent}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">{budgetPercent.toFixed(0)}% used</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost by Agent */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Cost by Agent</h3>
          <BarChart
            data={data.by_agent.map(a => ({ label: a.name, value: a.cost }))}
            max={Math.max(...data.by_agent.map(a => a.cost))}
          />
        </div>

        {/* Cost by Model */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Cost by Model</h3>
          <div className="space-y-3">
            {data.by_model.map((model) => (
              <div key={model.model} className="flex items-center gap-4">
                <div className="w-28 font-mono text-sm">{model.model}</div>
                <div className="flex-1">
                  <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-600 rounded-full"
                      style={{ width: `${model.percentage}%` }}
                    />
                  </div>
                </div>
                <div className="w-24 text-right text-sm">
                  <div className="font-mono">${model.cost.toFixed(2)}</div>
                  <div className="text-xs text-gray-500">{model.percentage}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Daily Trend */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Daily Cost Trend</h3>
        <div className="flex items-end gap-2 h-40">
          {data.daily_trend.map((day) => {
            const maxCost = Math.max(...data.daily_trend.map(d => d.cost))
            const height = (day.cost / maxCost) * 100
            return (
              <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
                <div className="text-xs font-mono text-gray-400">${day.cost.toFixed(1)}</div>
                <div className="w-full bg-blue-600 rounded-t" style={{ height: `${height}%` }} />
                <div className="text-xs text-gray-500">{day.date}</div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Agent Detail Table */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-gray-800">
          <h3 className="text-lg font-semibold">Agent Cost Details</h3>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800 bg-gray-900/50">
              <th className="text-left py-3 px-4 font-medium">Agent</th>
              <th className="text-right py-3 px-4 font-medium">Total Cost</th>
              <th className="text-right py-3 px-4 font-medium">Tokens</th>
              <th className="text-right py-3 px-4 font-medium">LLM Calls</th>
              <th className="text-right py-3 px-4 font-medium">Cost/Call</th>
              <th className="text-right py-3 px-4 font-medium">Cost/1K Tokens</th>
            </tr>
          </thead>
          <tbody>
            {data.by_agent.map((agent) => (
              <tr key={agent.agent} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                <td className="py-3 px-4">
                  <div className="font-medium">{agent.name}</div>
                  <div className="text-xs text-gray-500 font-mono">{agent.agent}</div>
                </td>
                <td className="py-3 px-4 text-right font-mono">${agent.cost.toFixed(2)}</td>
                <td className="py-3 px-4 text-right font-mono">{(agent.tokens / 1000).toFixed(0)}K</td>
                <td className="py-3 px-4 text-right">{agent.calls.toLocaleString()}</td>
                <td className="py-3 px-4 text-right font-mono">${(agent.cost / agent.calls).toFixed(4)}</td>
                <td className="py-3 px-4 text-right font-mono">${((agent.cost / agent.tokens) * 1000).toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
