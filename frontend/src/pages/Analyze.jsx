import { useState } from 'react'
import { analyzeTestcase } from '../api'
import ResultCard from '../components/ResultCard'
import axios from 'axios'

export default function Analyze() {
  const [logs, setLogs] = useState('')
  const [description, setDescription] = useState('')
  const [code, setCode] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  const userId = localStorage.getItem('user_id') || 'default_user'

  const handleAnalyze = async () => {
    if (!logs || !description || !code) {
      setError('Please fill in all three fields')
      return
    }
    setLoading(true); setError(''); setResult(null)
    setSessionId(null); setChatMessages([])

    try {
      const res = await analyzeTestcase({
        user_id: userId,
        testcase_logs: logs,
        testcase_description: description,
        testcase_code: code
      })
      setResult(res.data)
      setSessionId(res.data.session_id)
      const payload = res.data.payload
      const summary = payload?.root_cause || payload?.summary || 'Analysis complete'
      setChatMessages([{
        role: 'assistant',
        content: `I've analyzed your test failure. ${summary} Feel free to ask any follow-up questions!`
      }])
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Is the API running?')
    } finally {
      setLoading(false)
    }
  }

  const handleChatSend = async () => {
    if (!chatInput.trim() || !sessionId) return
    const userMsg = chatInput.trim()
    setChatInput('')
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setChatLoading(true)
    try {
      const res = await axios.post('/api/chat/followup', {
        session_id: sessionId,
        message: userMsg
      })
      setChatMessages(prev => [...prev, { role: 'assistant', content: res.data.response }])
    } catch {
      setChatMessages(prev => [...prev, { role: 'system', content: 'Failed to get response.' }])
    } finally {
      setChatLoading(false)
    }
  }

  const handleClear = () => {
    setLogs(''); setDescription(''); setCode('')
    setResult(null); setError('')
    setSessionId(null); setChatMessages([])
  }

  const loadExample = () => {
    setLogs('AssertionError: assert 150.00 == 120.00\nCart total mismatch: expected 120.00 got 150.00')
    setDescription('Test verifies cart total is correct sum of items added')
    setCode("def test_checkout_total(driver):\n    total = driver.find_element(By.ID, 'cart-total').text\n    assert float(total) == 120.00")
    setResult(null); setSessionId(null); setChatMessages([])
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Analyze Test Failure</h1>
          <p className="text-[#6b7280] text-sm mt-1">
            Paste your failing test details. AI will classify and diagnose automatically.
          </p>
        </div>
        <button
          onClick={handleClear}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
        >
          <span>+</span> New Analysis
        </button>
      </div>

      <button onClick={loadExample} className="text-indigo-400 hover:text-indigo-300 text-sm mb-6 underline">
        Load example test failure
      </button>

      {/* Form */}
      <div className="space-y-5">
        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-sm font-medium text-[#9ca3af]">
              Test Logs / Error Output *
            </label>
            <span className="text-xs text-[#4b5563]">{logs.length} / 50000</span>
          </div>
          <textarea
            rows={4}
            value={logs}
            onChange={e => setLogs(e.target.value)}
            placeholder="Paste your test error logs here..."
            className="w-full bg-[#13131f] border border-[#2a2a3d] rounded-xl px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 font-mono text-sm resize-none"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-sm font-medium text-[#9ca3af]">
              Test Case Description *
            </label>
            <span className="text-xs text-[#4b5563]">{description.length} / 2000</span>
          </div>
          <textarea
            rows={2}
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="What is this test supposed to verify?"
            className="w-full bg-[#13131f] border border-[#2a2a3d] rounded-xl px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 text-sm resize-none"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-sm font-medium text-[#9ca3af]">
              Test Case Code *
            </label>
            <span className="text-xs text-[#4b5563]">{code.length} / 50000</span>
          </div>
          <textarea
            rows={6}
            value={code}
            onChange={e => setCode(e.target.value)}
            placeholder="Paste your test code here..."
            className="w-full bg-[#13131f] border border-[#2a2a3d] rounded-xl px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 font-mono text-sm resize-none"
          />
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-400 px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-900 text-white font-semibold py-4 rounded-xl transition flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              <span>Analyzing... (may take 30-60s)</span>
            </>
          ) : (
            <>
              <span>🤖</span>
              <span>Analyze Test Failure</span>
            </>
          )}
        </button>
      </div>

      {/* Result */}
      <ResultCard result={result} />

      {/* Chat */}
      {sessionId && (
        <div className="mt-8 bg-[#13131f] border border-[#2a2a3d] rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-[#2a2a3d] flex justify-between items-center">
            <div>
              <h3 className="text-white font-semibold">Ask Follow-up Questions</h3>
              <p className="text-[#6b7280] text-xs mt-0.5">
                AI remembers your test failure context
              </p>
            </div>
            <button
              onClick={() => setChatMessages([])}
              className="flex items-center gap-1 text-xs text-[#6b7280] hover:text-white border border-[#2a2a3d] px-3 py-1.5 rounded-lg transition"
            >
              🔄 Clear Chat
            </button>
          </div>

          {/* Messages */}
          <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
            {chatMessages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0">
                    🤖
                  </div>
                )}
                <div className={`max-w-2xl rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-[#1e1e30] text-[#e5e7eb]'
                }`}>
                  {msg.role === 'assistant' && (
                    <p className="text-xs text-indigo-400 font-medium mb-1">QA Assistant</p>
                  )}
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-sm mr-3">🤖</div>
                <div className="bg-[#1e1e30] rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-100"></div>
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-200"></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-[#2a2a3d] flex gap-3">
            <input
              type="text"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleChatSend()}
              placeholder="Ask a follow-up question... (e.g. Why is this a bug?)"
              className="flex-1 bg-[#1e1e30] border border-[#2a2a3d] rounded-xl px-4 py-2.5 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 text-sm"
            />
            <button
              onClick={handleChatSend}
              disabled={chatLoading || !chatInput.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-900 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition flex items-center gap-2"
            >
              <span>Send</span>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}