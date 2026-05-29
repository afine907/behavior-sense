'use client'

import { useState } from 'react'

export default function SettingsPage() {
  const [notifications, setNotifications] = useState({
    email: true,
    slack: false,
    webhook: true,
    criticalOnly: false,
  })

  const [budget, setBudget] = useState({
    daily: 50,
    weekly: 300,
    monthly: 1000,
    alertThreshold: 80,
  })

  const [rules, setRules] = useState({
    autoEnable: true,
    defaultPriority: 50,
    hotReload: true,
    evaluationInterval: 5,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-500 text-sm">Configure agent monitoring preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Notification Settings */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Notifications</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Email Notifications</div>
                <div className="text-sm text-gray-500">Receive alerts via email</div>
              </div>
              <button
                onClick={() => setNotifications((n) => ({ ...n, email: !n.email }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications.email ? 'bg-blue-600' : 'bg-gray-700'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    notifications.email ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Slack Notifications</div>
                <div className="text-sm text-gray-500">Post alerts to Slack channel</div>
              </div>
              <button
                onClick={() => setNotifications((n) => ({ ...n, slack: !n.slack }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications.slack ? 'bg-blue-600' : 'bg-gray-700'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    notifications.slack ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Webhook</div>
                <div className="text-sm text-gray-500">Send alerts to custom webhook URL</div>
              </div>
              <button
                onClick={() => setNotifications((n) => ({ ...n, webhook: !n.webhook }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications.webhook ? 'bg-blue-600' : 'bg-gray-700'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    notifications.webhook ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Critical Alerts Only</div>
                <div className="text-sm text-gray-500">Only notify for critical severity</div>
              </div>
              <button
                onClick={() => setNotifications((n) => ({ ...n, criticalOnly: !n.criticalOnly }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications.criticalOnly ? 'bg-blue-600' : 'bg-gray-700'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    notifications.criticalOnly ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Webhook URL</label>
              <input
                type="text"
                placeholder="https://hooks.slack.com/..."
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Budget Settings */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Budget</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Daily Budget ($)</label>
              <input
                type="number"
                value={budget.daily}
                onChange={(e) => setBudget((b) => ({ ...b, daily: Number(e.target.value) }))}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Weekly Budget ($)</label>
              <input
                type="number"
                value={budget.weekly}
                onChange={(e) => setBudget((b) => ({ ...b, weekly: Number(e.target.value) }))}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Monthly Budget ($)</label>
              <input
                type="number"
                value={budget.monthly}
                onChange={(e) => setBudget((b) => ({ ...b, monthly: Number(e.target.value) }))}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Alert Threshold (%)</label>
              <input
                type="range"
                min="50"
                max="100"
                value={budget.alertThreshold}
                onChange={(e) =>
                  setBudget((b) => ({ ...b, alertThreshold: Number(e.target.value) }))
                }
                className="w-full"
              />
              <div className="text-sm text-gray-500 text-right">{budget.alertThreshold}%</div>
            </div>
          </div>
        </div>

        {/* Rule Engine Settings */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Rule Engine</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Auto-enable New Rules</div>
                <div className="text-sm text-gray-500">
                  Automatically enable newly created rules
                </div>
              </div>
              <button
                onClick={() => setRules((r) => ({ ...r, autoEnable: !r.autoEnable }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  rules.autoEnable ? 'bg-blue-600' : 'bg-gray-700'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    rules.autoEnable ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Hot Reload</div>
                <div className="text-sm text-gray-500">Auto-reload rules from YAML files</div>
              </div>
              <button
                onClick={() => setRules((r) => ({ ...r, hotReload: !r.hotReload }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  rules.hotReload ? 'bg-blue-600' : 'bg-gray-700'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    rules.hotReload ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Default Priority</label>
              <input
                type="number"
                value={rules.defaultPriority}
                onChange={(e) =>
                  setRules((r) => ({ ...r, defaultPriority: Number(e.target.value) }))
                }
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">
                Evaluation Interval (seconds)
              </label>
              <input
                type="number"
                value={rules.evaluationInterval}
                onChange={(e) =>
                  setRules((r) => ({ ...r, evaluationInterval: Number(e.target.value) }))
                }
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* API Keys */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">API Keys</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">API Key</label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value="bsk-xxxxxxxxxxxxxxxxxxxx"
                  readOnly
                  className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm font-mono"
                />
                <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm">
                  Copy
                </button>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">
                  Regenerate
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Webhook Secret</label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value="whsec-xxxxxxxxxxxxxxxxxxxx"
                  readOnly
                  className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm font-mono"
                />
                <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm">
                  Copy
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium">
          Save Settings
        </button>
      </div>
    </div>
  )
}
