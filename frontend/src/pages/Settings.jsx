import { useState } from 'react'

export default function Settings() {
  const [jiraUrl, setJiraUrl] = useState('https://vaishnavilikhe3578.atlassian.net')
  const [jiraEmail, setJiraEmail] = useState('')
  const [jiraKey, setJiraKey] = useState('QA')
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-[#6b7280] text-sm mt-1">Configure your QA Assistant preferences</p>
      </div>

      <div className="space-y-6">

        {/* Profile */}
        <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-6">
          <h2 className="text-white font-semibold mb-4">Profile</h2>
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 bg-indigo-700 rounded-full flex items-center justify-center text-2xl font-bold">
              {(localStorage.getItem('username') || 'U')[0].toUpperCase()}
            </div>
            <div>
              <p className="text-white font-medium">{localStorage.getItem('username')}</p>
              <p className="text-[#6b7280] text-sm">QA Engineer</p>
              <span className="text-xs bg-indigo-900 text-indigo-300 px-2 py-0.5 rounded-full mt-1 inline-block">
                Pro Plan
              </span>
            </div>
          </div>
        </div>

        {/* Jira Integration */}
        <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-6">
          <h2 className="text-white font-semibold mb-1">Jira Integration</h2>
          <p className="text-[#6b7280] text-xs mb-4">Configure your Atlassian Jira connection</p>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-[#9ca3af] block mb-1.5">Jira URL</label>
              <input
                value={jiraUrl}
                onChange={e => setJiraUrl(e.target.value)}
                className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-[#9ca3af] block mb-1.5">Email</label>
              <input
                value={jiraEmail}
                onChange={e => setJiraEmail(e.target.value)}
                placeholder="your@email.com"
                className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-[#9ca3af] block mb-1.5">Project Key</label>
              <input
                value={jiraKey}
                onChange={e => setJiraKey(e.target.value)}
                className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* AI Model */}
        <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-6">
          <h2 className="text-white font-semibold mb-1">AI Model</h2>
          <p className="text-[#6b7280] text-xs mb-4">Currently using local Ollama</p>
          <div className="flex items-center justify-between bg-[#1e1e30] rounded-xl p-4">
            <div>
              <p className="text-white text-sm font-medium">Llama 3.2 (3B)</p>
              <p className="text-[#6b7280] text-xs">Local CPU • Ollama</p>
            </div>
            <span className="text-xs bg-green-900 text-green-400 px-2 py-1 rounded-full">Active</span>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-xl transition"
        >
          {saved ? '✓ Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}