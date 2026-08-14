import { useState, useEffect } from 'react'

export default function MyTickets() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch from Jira via our backend
    fetch('/api/tickets')
      .then(r => r.json())
      .then(data => setTickets(data.tickets || []))
      .catch(() => setTickets([]))
      .finally(() => setLoading(false))
  }, [])

  const mockTickets = [
    { key: 'QA-52', summary: 'Cart Total Mismatch', priority: 'High', status: 'To Do', created: '14 Aug 2026' },
    { key: 'QA-51', summary: 'Invalid redirect after login', priority: 'High', status: 'In Progress', created: '13 Aug 2026' },
    { key: 'QA-50', summary: 'PDF export generates empty file', priority: 'Medium', status: 'To Do', created: '13 Aug 2026' },
    { key: 'QA-49', summary: 'Stock deducted without order', priority: 'Critical', status: 'Done', created: '12 Aug 2026' },
  ]

  const displayTickets = tickets.length > 0 ? tickets : mockTickets

  const priorityColor = (p) => ({
    Critical: 'text-red-500',
    High: 'text-orange-400',
    Medium: 'text-yellow-400',
    Low: 'text-green-400'
  }[p] || 'text-gray-400')

  const statusBadge = (s) => ({
    'To Do': 'bg-gray-700 text-gray-300',
    'In Progress': 'bg-blue-900 text-blue-300',
    'Done': 'bg-green-900 text-green-300'
  }[s] || 'bg-gray-700 text-gray-300')

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">My Tickets</h1>
        <p className="text-[#6b7280] text-sm mt-1">Jira tickets created by QA Assistant</p>
      </div>

      <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2a2a3d] flex justify-between items-center">
          <p className="text-sm text-[#9ca3af]">{displayTickets.length} tickets</p>
          
            href="https://vaishnavilikhe3578.atlassian.net/jira/software/projects/QA/list"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-700 px-3 py-1.5 rounded-lg"
          >
            Open in Jira →
          </a>
        </div>

        {loading ? (
          <div className="text-center py-16 text-[#6b7280]">Loading tickets...</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2a2a3d]">
                {['Key', 'Summary', 'Priority', 'Status', 'Created'].map(h => (
                  <th key={h} className="text-left text-xs font-medium text-[#6b7280] px-6 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayTickets.map((ticket, i) => (
                <tr key={i} className="border-b border-[#2a2a3d] hover:bg-[#1e1e30] transition">
                  <td className="px-6 py-4">
                    <span className="text-indigo-400 font-mono text-sm font-medium">
                      {ticket.key}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-white">{ticket.summary}</td>
                  <td className="px-6 py-4">
                    <span className={`text-xs font-medium ${priorityColor(ticket.priority)}`}>
                      {ticket.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-xs px-2 py-1 rounded-full ${statusBadge(ticket.status)}`}>
                      {ticket.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-[#6b7280]">{ticket.created}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}