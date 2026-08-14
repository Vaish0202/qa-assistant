import { useState } from 'react'
import JiraApprovalModal from './JiraApprovalModal'
import axios from 'axios'

export default function ResultCard({ result }) {
  if (!result) return null

  const isBug = result.classification === 'bug'
  const payload = result.payload || {}
  const codeToShow = payload.improved_code || payload.fixed_code || ''
  const changesMade = payload.changes_made || []
  const bestPractices = payload.best_practices || []
  const suggestions = payload.suggestions || []
  const confidence = Math.round((result.classification_confidence || 0.96) * 100)

  const [showJiraModal, setShowJiraModal] = useState(false)
  const [jiraResult, setJiraResult] = useState(
    payload.jira_ticket ? { ticket_key: payload.jira_ticket, ticket_url: payload.jira_url } : null
  )
  const [activeTab, setActiveTab] = useState('overview')
  const [copied, setCopied] = useState(false)

  const handleJiraApprove = async (approvedData) => {
    try {
      const res = await axios.post('/api/jira/create', {
        ...approvedData,
        project_key: 'QA'
      })
      if (res.data.success) {
        setJiraResult({
          ticket_key: res.data.ticket_key,
          ticket_url: res.data.ticket_url
        })
        setShowJiraModal(false)
      }
    } catch (err) {
      console.error('Jira creation failed:', err)
      setShowJiraModal(false)
    }
  }

  const handleCopy = () => {
    const text = `Classification: ${isBug ? 'Bug' : 'Test Issue'}\nRoot Cause: ${payload.root_cause || payload.description}\nSuggested Fix: ${payload.suggested_fix || ''}`
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const severityColor = {
    critical: 'text-red-500',
    high: 'text-orange-400',
    medium: 'text-yellow-400',
    low: 'text-green-400'
  }[payload.severity?.toLowerCase()] || 'text-orange-400'

  return (
    <>
      {showJiraModal && (
        <JiraApprovalModal
          bugData={payload}
          onApprove={handleJiraApprove}
          onCancel={() => setShowJiraModal(false)}
        />
      )}

      <div className="mt-8 space-y-4">

        {/* Top header card */}
        <div className={`rounded-2xl border p-5 ${
          isBug ? 'bg-red-950/30 border-red-800' : 'bg-yellow-950/30 border-yellow-800'
        }`}>
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                isBug ? 'bg-red-600 text-white' : 'bg-yellow-600 text-white'
              }`}>
                {isBug ? '🐛 BUG DETECTED' : '⚠️ TEST ISSUE'}
              </span>
              <span className="text-[#6b7280] text-xs">
                Analysis ID: AN-{Date.now().toString().slice(-8)}
              </span>
            </div>
            <span className="text-[#6b7280] text-xs">
              Analyzed on {new Date().toLocaleString()}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#0f0f1a] rounded-xl p-3 text-center">
              <p className="text-xs text-[#6b7280] mb-1">Classification</p>
              <p className={`text-sm font-bold ${isBug ? 'text-red-400' : 'text-yellow-400'}`}>
                {isBug ? 'PRODUCT BUG' : 'TEST ISSUE'}
              </p>
            </div>
            <div className="bg-[#0f0f1a] rounded-xl p-3 text-center">
              <p className="text-xs text-[#6b7280] mb-1">Confidence</p>
              <p className="text-sm font-bold text-green-400">{confidence}%</p>
            </div>
            <div className="bg-[#0f0f1a] rounded-xl p-3 text-center">
              <p className="text-xs text-[#6b7280] mb-1">Severity</p>
              <p className={`text-sm font-bold ${severityColor}`}>
                {(payload.severity || 'HIGH').toUpperCase()}
              </p>
            </div>
          </div>
        </div>

        {/* Main content + Quick Actions side by side */}
        <div className="grid grid-cols-3 gap-4">

          {/* Left — main analysis */}
          <div className="col-span-2 space-y-4">

            {/* Root Cause */}
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <span>🔍</span> Root Cause
              </h3>
              <p className="text-[#9ca3af] text-sm leading-relaxed">
                {payload.root_cause || payload.description || 'Analysis complete'}
              </p>
            </div>

            {/* Bug specific */}
            {isBug && (
              <>
                {/* Evidence */}
                <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
                  <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <span>🔬</span> Evidence
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-green-400">✓</span>
                        <span className="text-[#6b7280]">Expected:</span>
                        <span className="text-white">{payload.expected_result || '—'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-red-400">✗</span>
                        <span className="text-[#6b7280]">Actual:</span>
                        <span className="text-white">{payload.actual_result || '—'}</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[#6b7280] text-xs">Steps to reproduce:</p>
                      {(payload.steps_to_reproduce || []).map((s, i) => (
                        <p key={i} className="text-[#9ca3af] text-xs">• {s}</p>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Impact */}
                <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
                  <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <span>⚡</span> Impact
                  </h3>
                  <p className="text-[#9ca3af] text-sm">{payload.suggested_fix || 'Review the application logic.'}</p>
                </div>

                {/* Detailed analysis tabs */}
                <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
                  <h3 className="text-white font-semibold mb-4">Detailed Analysis</h3>
                  <div className="flex gap-2 mb-4 flex-wrap">
                    {['overview', 'logs', 'response'].map(tab => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                          activeTab === tab
                            ? 'bg-indigo-600 text-white'
                            : 'bg-[#1e1e30] text-[#9ca3af] hover:text-white'
                        }`}
                      >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                      </button>
                    ))}
                  </div>
                  <div className="text-[#9ca3af] text-sm">
                    {activeTab === 'overview' && (
                      <p>{payload.description || 'The test failure indicates an application-level bug that needs developer attention.'}</p>
                    )}
                    {activeTab === 'logs' && (
                      <pre className="bg-[#0f0f1a] rounded-xl p-3 text-xs text-green-400 overflow-x-auto">
                        {result.testcase_logs || 'No logs available'}
                      </pre>
                    )}
                    {activeTab === 'response' && (
                      <p className="text-[#9ca3af] text-sm">
                        Bug type: {payload.bug_type} | Framework: {result.framework}
                      </p>
                    )}
                  </div>

                  {/* Suggested next steps */}
                  {jiraResult && (
                    <div className="mt-4 pt-4 border-t border-[#2a2a3d]">
                      <p className="text-xs text-[#6b7280] mb-2">Suggested Next Steps</p>
                      <div className="flex gap-2 flex-wrap">
                        {['Check service logs', 'Validate logic', 'Re-run test after fix'].map(s => (
                          <button key={s} className="text-xs bg-[#1e1e30] border border-[#2a2a3d] text-[#9ca3af] px-3 py-1.5 rounded-lg hover:text-white transition">
                            {s}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Failed TC specific */}
            {!isBug && (
              <>
                {suggestions.length > 0 && (
                  <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
                    <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                      <span>💡</span> Suggestions
                    </h3>
                    {suggestions.map((s, i) => (
                      <div key={i} className="bg-[#1e1e30] rounded-xl p-3 mb-2">
                        <p className="text-red-400 text-xs mb-1">Issue: {s.issue}</p>
                        <p className="text-green-400 text-xs">Fix: {s.fix}</p>
                      </div>
                    ))}
                  </div>
                )}

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

                {changesMade.length > 0 && (
                  <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
                    <h3 className="text-white font-semibold mb-3">📝 Changes Made</h3>
                    <ul className="space-y-1">
                      {changesMade.map((c, i) => (
                        <li key={i} className="text-[#9ca3af] text-sm flex items-start gap-2">
                          <span className="text-indigo-400">•</span> {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {bestPractices.length > 0 && (
                  <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
                    <h3 className="text-white font-semibold mb-3">⭐ Best Practices</h3>
                    <ul className="space-y-1">
                      {bestPractices.map((p, i) => (
                        <li key={i} className="text-[#9ca3af] text-sm flex items-start gap-2">
                          <span className="text-yellow-400">•</span> {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Right — Quick Actions + Test Summary */}
          <div className="space-y-4">

            {/* Quick Actions */}
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-4">Quick Actions</h3>
              <div className="space-y-2">

                {/* Jira button — shows modal if no ticket yet */}
                {isBug && !jiraResult && (
                  <button
                    onClick={() => setShowJiraModal(true)}
                    className="w-full flex items-center gap-3 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-3 rounded-xl text-sm font-medium transition"
                  >
                    <span>🎫</span> Create Jira Ticket
                  </button>
                )}

                {/* Already created */}
                {isBug && jiraResult && (
                  <a
                    href={jiraResult.ticket_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full flex items-center gap-3 bg-green-900/40 border border-green-700 text-green-300 px-4 py-3 rounded-xl text-sm font-medium transition hover:bg-green-900/60 block"
                  >
                    <span>✓</span> {jiraResult.ticket_key} — View in Jira
                  </a>
                )}

                <button
                  onClick={handleCopy}
                  className="w-full flex items-center gap-3 bg-[#1e1e30] hover:bg-[#2a2a3d] text-[#9ca3af] hover:text-white px-4 py-3 rounded-xl text-sm font-medium transition"
                >
                  <span>{copied ? '✓' : '📋'}</span>
                  {copied ? 'Copied!' : 'Copy Summary'}
                </button>

                <button
                  onClick={() => window.print()}
                  className="w-full flex items-center gap-3 bg-[#1e1e30] hover:bg-[#2a2a3d] text-[#9ca3af] hover:text-white px-4 py-3 rounded-xl text-sm font-medium transition"
                >
                  <span>⬇️</span> Download Report
                </button>
              </div>
            </div>

            {/* Test Summary */}
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-4">Test Summary</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-[#6b7280] text-xs">Test Case</p>
                  <p className="text-white">Test Analysis</p>
                </div>
                <div>
                  <p className="text-[#6b7280] text-xs">Status</p>
                  <p className="text-red-400 flex items-center gap-1">
                    <span>⊗</span> FAILED
                  </p>
                </div>
                <div>
                  <p className="text-[#6b7280] text-xs">Execution Time</p>
                  <p className="text-white">{result.processing_time_seconds}s</p>
                </div>
                <div>
                  <p className="text-[#6b7280] text-xs">Framework</p>
                  <p className="text-white capitalize">{result.framework || 'selenium'}</p>
                </div>
              </div>
            </div>

            {/* Recommended Action */}
            <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-3">Recommended Action</h3>
              <p className="text-[#9ca3af] text-xs leading-relaxed">
                {isBug
                  ? `This appears to be a genuine product bug. ${payload.suggested_fix || 'Review the application logic on the server.'}`
                  : `This test has issues that need fixing. ${payload.root_cause || 'Review the test code.'}`
                }
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}