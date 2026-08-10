import { useState, useEffect } from 'react'
import { getHistory } from '../api'

export default function History() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const userId = localStorage.getItem('user_id') || 'default_user'

  useEffect(() => {
    getHistory(userId)
      .then(res => setHistory(res.data.analyses || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [])

  const getBadgeColor = (classification) => {
    if (classification === 'bug') return 'bg-red-900 text-red-300'
    if (classification === 'failed_testcase') return 'bg-yellow-900 text-yellow-300'
    return 'bg-gray-700 text-gray-300'
  }

  const toggleExpand = (id) => {
    setExpanded(expanded === id ? null : id)
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">Analysis History</h1>
        <span className="text-gray-400 text-sm">{history.length} analyses</span>
      </div>

      {loading && <p className="text-gray-400">Loading history...</p>}

      {!loading && history.length === 0 && (
        <div className="text-center py-16">
          <div className="text-5xl mb-4">📭</div>
          <p className="text-gray-400">No analyses yet. Go analyze a test failure!</p>
        </div>
      )}

      <div className="space-y-3">
        {history.map((item) => (
          <div
            key={item.id}
            className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden"
          >
            {/* Header — always visible, clickable */}
            <div
              onClick={() => toggleExpand(item.id)}
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-800 transition"
            >
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${getBadgeColor(item.classification)}`}>
                  {item.classification === 'bug' ? '🐛 BUG' : '⚠️ FAILED TC'}
                </span>
                <span className="text-gray-300 text-sm font-medium">{item.analysis_type}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-500 text-xs">
                  {new Date(item.created_at).toLocaleString()}
                </span>
                <span className="text-gray-400 text-xs">
                  {expanded === item.id ? '▲' : '▼'}
                </span>
              </div>
            </div>

            {/* Expanded content */}
            {expanded === item.id && (
              <div className="border-t border-gray-800 p-4 space-y-2">
                {item.alert && (
                  <div className="bg-blue-900/30 border border-blue-800 rounded p-3">
                    <p className="text-blue-300 text-sm">{item.alert}</p>
                  </div>
                )}
                <div className="text-xs text-gray-500 space-y-1">
                  <p>ID: {item.id}</p>
                  <p>Classification: {item.classification}</p>
                  <p>Analysis type: {item.analysis_type}</p>
                  <p>Created: {item.created_at}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}