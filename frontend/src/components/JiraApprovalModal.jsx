import { useState } from 'react'

export default function JiraApprovalModal({ bugData, onApprove, onCancel }) {
  const [priority, setPriority] = useState('High')
  const [severity, setSeverity] = useState(bugData?.severity || 'high')
  const [dueDate, setDueDate] = useState('')
  const [assignee, setAssignee] = useState('')
  const [summary, setSummary] = useState(bugData?.summary || '')
  const [loading, setLoading] = useState(false)

  const handleApprove = async () => {
    setLoading(true)
    await onApprove({
      ...bugData,
      priority,
      severity,
      due_date: dueDate,
      assignee,
      summary
    })
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
      <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl w-full max-w-lg">

        {/* Header */}
        <div className="px-6 py-5 border-b border-[#2a2a3d]">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎫</span>
            <div>
              <h2 className="text-white font-semibold text-lg">Create Jira Ticket</h2>
              <p className="text-[#6b7280] text-xs mt-0.5">
                Review and confirm ticket details before creating
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">

          {/* Summary */}
          <div>
            <label className="text-xs font-medium text-[#9ca3af] block mb-1.5">
              Summary *
            </label>
            <input
              value={summary}
              onChange={e => setSummary(e.target.value)}
              className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Priority + Severity row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-[#9ca3af] block mb-1.5">
                Priority *
              </label>
              <select
                value={priority}
                onChange={e => setPriority(e.target.value)}
                className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
              >
                <option>Highest</option>
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
                <option>Lowest</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-[#9ca3af] block mb-1.5">
                Severity *
              </label>
              <select
                value={severity}
                onChange={e => setSeverity(e.target.value)}
                className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          {/* Assignee + Due date */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-[#9ca3af] block mb-1.5">
                Assignee
              </label>
              <input
                value={assignee}
                onChange={e => setAssignee(e.target.value)}
                placeholder="Leave blank for unassigned"
                className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 placeholder-[#4b5563]"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-[#9ca3af] block mb-1.5">
                Due Date
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={e => setDueDate(e.target.value)}
                className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Bug details preview */}
          <div className="bg-[#1e1e30] rounded-xl p-4 space-y-2">
            <p className="text-xs font-medium text-[#9ca3af] mb-2">Bug Details (from AI analysis)</p>
            <div className="text-xs text-[#6b7280] space-y-1">
              <p><span className="text-[#9ca3af]">Type:</span> {bugData?.bug_type}</p>
              <p><span className="text-[#9ca3af]">Root cause:</span> {bugData?.description?.slice(0, 100)}...</p>
              <p><span className="text-[#9ca3af]">Fix hint:</span> {bugData?.suggested_fix}</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#2a2a3d] flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 bg-[#1e1e30] hover:bg-[#2a2a3d] text-[#9ca3af] font-medium py-2.5 rounded-xl transition text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleApprove}
            disabled={loading || !summary}
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-900 text-white font-medium py-2.5 rounded-xl transition text-sm flex items-center justify-center gap-2"
          >
            {loading ? (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
            ) : '🎫'}
            {loading ? 'Creating...' : 'Create Ticket'}
          </button>
        </div>
      </div>
    </div>
  )
}