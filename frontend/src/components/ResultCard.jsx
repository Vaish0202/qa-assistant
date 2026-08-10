export default function ResultCard({ result }) {
  if (!result) return null

  const isBug = result.classification === 'bug'
  const payload = result.payload || {}

  // Handle both improved_code and fixed_code
  const codeToShow = payload.improved_code || payload.fixed_code || ''
  const changesMade = payload.changes_made || []
  const bestPractices = payload.best_practices || []
  const suggestions = payload.suggestions || []

  return (
    <div className="mt-6 space-y-4">

      <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold ${
        isBug ? 'bg-red-900 text-red-300' : 'bg-yellow-900 text-yellow-300'
      }`}>
        {isBug ? '🐛 BUG DETECTED' : '⚠️ FAILED TESTCASE'}
        <span className="text-xs opacity-70">{result.action_type}</span>
      </div>

      <p className="text-xs text-gray-500">Processing time: {result.processing_time_seconds}s</p>

      {/* BUG PATH */}
      {isBug && payload.jira_ticket && (
        <div className="bg-blue-900 border border-blue-700 rounded-lg p-4 space-y-2">
          <h3 className="text-blue-300 font-semibold">🎫 Jira Ticket Created</h3>
          <p className="text-white font-mono text-xl">{payload.jira_ticket}</p>
          <a href={payload.jira_url} target="_blank" rel="noopener noreferrer"
            className="text-blue-400 underline text-sm">Open in Jira</a>
          <div className="mt-3 space-y-1 text-sm text-gray-300">
            <p>Summary: {payload.summary}</p>
            <p>Severity: {payload.severity}</p>
            <p>Bug type: {payload.bug_type}</p>
            <p>Fix hint: {payload.suggested_fix}</p>
          </div>
        </div>
      )}

      {isBug && !payload.jira_ticket && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <h3 className="text-red-300 font-semibold">🐛 Bug Analysis</h3>
          <p className="text-gray-300 text-sm mt-1">{payload.summary}</p>
          <p className="text-gray-400 text-xs mt-1">Severity: {payload.severity}</p>
          <p className="text-yellow-400 text-xs mt-1">Jira ticket creation failed — check Jira config</p>
        </div>
      )}

      {/* FAILED TESTCASE PATH */}
      {!isBug && (
        <div className="space-y-4">

          {/* Root Cause */}
          <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
            <h3 className="text-green-300 font-semibold mb-1">✅ Root Cause</h3>
            <p className="text-gray-300 text-sm">{payload.root_cause}</p>
            <p className="text-xs mt-1 text-gray-400">
              Type: {payload.analysis_type} | Severity: {payload.severity}
            </p>
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-3">💡 Suggestions</h3>
              {suggestions.map((s, i) => (
                <div key={i} className="text-sm mb-2">
                  <p className="text-red-400">Issue: {s.issue}</p>
                  <p className="text-green-400">Fix: {s.fix}</p>
                </div>
              ))}
            </div>
          )}

          {/* Improved Code */}
          {codeToShow && (
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-3">🔧 Improved Code</h3>
              <pre className="text-green-300 text-sm overflow-x-auto whitespace-pre-wrap">
                {codeToShow}
              </pre>
            </div>
          )}

          {/* Changes Made */}
          {changesMade.length > 0 && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-2">📝 Changes Made</h3>
              <ul className="list-disc list-inside space-y-1">
                {changesMade.map((c, i) => (
                  <li key={i} className="text-gray-300 text-sm">{c}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Best Practices */}
          {bestPractices.length > 0 && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-2">⭐ Best Practices</h3>
              <ul className="list-disc list-inside space-y-1">
                {bestPractices.map((p, i) => (
                  <li key={i} className="text-gray-300 text-sm">{p}</li>
                ))}
              </ul>
            </div>
          )}

        </div>
      )}
    </div>
  )
}