export default function ResultCard({ result }) {
  if (!result) return null

  const isBug = result.classification === 'bug'
  const payload = result.payload || {}
  const codeToShow = payload.improved_code || payload.fixed_code || ''
  const changesMade = payload.changes_made || []
  const bestPractices = payload.best_practices || []
  const suggestions = payload.suggestions || []
  const confidence = result.payload?.confidence ||
    (result.classification_confidence * 100) || 96

  return (
    <div className="mt-8 space-y-4">

      {/* Classification header */}
      <div className={`rounded-2xl p-5 border ${
        isBug
          ? 'bg-red-900/20 border-red-700'
          : 'bg-yellow-900/20 border-yellow-700'
      }`}>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
              isBug ? 'bg-red-600 text-white' : 'bg-yellow-600 text-white'
            }`}>
              {isBug ? '🐛 BUG DETECTED' : '⚠️ TEST ISSUE'}
            </span>
            <span className="text-[#9ca3af] text-xs">
              Analysis ID: AN-{Date.now().toString().slice(-8)}
            </span>
          </div>
          <span className="text-[#6b7280] text-xs">
            ⏱ {result.processing_time_seconds}s
          </span>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="bg-[#13131f] rounded-xl p-3 text-center">
            <p className="text-xs text-[#6b7280] mb-1">Classification</p>
            <p className={`text-sm font-bold ${isBug ? 'text-red-400' : 'text-yellow-400'}`}>
              {isBug ? 'PRODUCT BUG' : 'TEST ISSUE'}
            </p>
          </div>
          <div className="bg-[#13131f] rounded-xl p-3 text-center">
            <p className="text-xs text-[#6b7280] mb-1">Confidence</p>
            <p className="text-sm font-bold text-green-400">
              {Math.round(confidence)}%
            </p>
          </div>
          <div className="bg-[#13131f] rounded-xl p-3 text-center">
            <p className="text-xs text-[#6b7280] mb-1">Severity</p>
            <p className={`text-sm font-bold ${
              payload.severity === 'critical' ? 'text-red-500' :
              payload.severity === 'high' ? 'text-orange-400' :
              payload.severity === 'medium' ? 'text-yellow-400' : 'text-green-400'
            }`}>
              {(payload.severity || 'medium').toUpperCase()}
            </p>
          </div>
        </div>
      </div>

      {/* BUG PATH */}
      {isBug && (
        <div className="space-y-4">
          {/* Root cause */}
          <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span>🔍</span> Root Cause
            </h3>
            <p className="text-[#9ca3af] text-sm">{payload.description || payload.root_cause}</p>
          </div>

          {/* Jira ticket */}
          {payload.jira_ticket && (
            <div className="bg-blue-900/20 border border-blue-700 rounded-2xl p-5">
              <h3 className="text-blue-300 font-semibold mb-3 flex items-center gap-2">
                <span>🎫</span> Jira Ticket Created
              </h3>
              <p className="text-white font-mono text-2xl font-bold mb-2">
                {payload.jira_ticket}
              </p>
              <a
                href={payload.jira_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm underline"
              >
                Open in Jira →
              </a>
              <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
                <div>
                  <p className="text-[#6b7280] text-xs">Summary</p>
                  <p className="text-[#e5e7eb]">{payload.summary}</p>
                </div>
                <div>
                  <p className="text-[#6b7280] text-xs">Fix hint</p>
                  <p className="text-[#e5e7eb]">{payload.suggested_fix}</p>
                </div>
              </div>
            </div>
          )}

          {/* No Jira ticket yet */}
          {!payload.jira_ticket && (
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-2">Bug Details</h3>
              <p className="text-[#9ca3af] text-sm mb-2">{payload.summary}</p>
              <p className="text-xs text-yellow-400">
                ⚠️ Jira ticket not created — check Jira configuration
              </p>
            </div>
          )}
        </div>
      )}

      {/* FAILED TC PATH */}
      {!isBug && (
        <div className="space-y-4">

          {/* Root cause */}
          <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span>🔍</span> Root Cause
            </h3>
            <p className="text-[#9ca3af] text-sm">{payload.root_cause}</p>
            <div className="flex gap-3 mt-3">
              <span className="text-xs bg-[#1e1e30] border border-[#2a2a3d] px-2 py-1 rounded text-[#9ca3af]">
                {payload.analysis_type}
              </span>
              <span className={`text-xs px-2 py-1 rounded border ${
                payload.severity === 'high'
                  ? 'bg-red-900/30 border-red-700 text-red-400'
                  : 'bg-yellow-900/30 border-yellow-700 text-yellow-400'
              }`}>
                {payload.severity}
              </span>
            </div>
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <span>💡</span> Suggestions
              </h3>
              <div className="space-y-3">
                {suggestions.map((s, i) => (
                  <div key={i} className="bg-[#1e1e30] rounded-xl p-3">
                    <p className="text-red-400 text-xs mb-1">Issue: {s.issue}</p>
                    <p className="text-green-400 text-xs">Fix: {s.fix}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Improved code */}
          {codeToShow && (
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <span>🔧</span> Improved Code
                </h3>
                <button
                  onClick={() => navigator.clipboard.writeText(codeToShow)}
                  className="text-xs text-[#6b7280] hover:text-white border border-[#2a2a3d] px-2 py-1 rounded"
                >
                  Copy
                </button>
              </div>
              <div className="bg-[#0f0f1a] rounded-xl p-4 border border-[#2a2a3d]">
                <p className="text-xs text-[#6b7280] mb-2">Python</p>
                <pre className="text-green-400 text-xs overflow-x-auto whitespace-pre-wrap">
                  {codeToShow}
                </pre>
              </div>
            </div>
          )}

          {/* Changes made */}
          {changesMade.length > 0 && (
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <span>📝</span> Changes Made
              </h3>
              <ul className="space-y-1">
                {changesMade.map((c, i) => (
                  <li key={i} className="text-[#9ca3af] text-sm flex items-start gap-2">
                    <span className="text-indigo-400 mt-0.5">•</span> {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Best practices */}
          {bestPractices.length > 0 && (
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <span>⭐</span> Best Practices
              </h3>
              <ul className="space-y-1">
                {bestPractices.map((p, i) => (
                  <li key={i} className="text-[#9ca3af] text-sm flex items-start gap-2">
                    <span className="text-yellow-400 mt-0.5">•</span> {p}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}