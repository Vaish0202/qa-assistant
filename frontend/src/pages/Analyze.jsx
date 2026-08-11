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
    setLoading(true)
    setError('')
    setResult(null)
    setSessionId(null)
    setChatMessages([])

    try {
      const res = await analyzeTestcase({
        user_id: userId,
        testcase_logs: logs,
        testcase_description: description,
        testcase_code: code
      })
      setResult(res.data)
      setSessionId(res.data.session_id)

      // Add initial AI message to chat
      const payload = res.data.payload
      const summary = payload?.root_cause || payload?.summary || 'Analysis complete'
      setChatMessages([{
        role: 'assistant',
        content: `I've analyzed your test failure. ${summary} Feel free to ask any followup questions!`
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
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.response
      }])

      if (res.data.is_resolved) {
        setChatMessages(prev => [...prev, {
          role: 'system',
          content: '✅ Issue marked as resolved!'
        }])
      }
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: 'system',
        content: 'Failed to get response. Please try again.'
      }])
    } finally {
      setChatLoading(false)
    }
  }

  const handleClear = () => {
    setLogs('')
    setDescription('')
    setCode('')
    setResult(null)
    setError('')
    setSessionId(null)
    setChatMessages([])
  }

  const loadExample = () => {
    setLogs('AssertionError: assert 150.00 == 120.00\nCart total mismatch')
    setDescription('Test verifies cart total is correct sum of items added')
    setCode("def test_checkout_total(driver):\n    total = driver.find_element(By.ID, 'cart-total').text\n    assert float(total) == 120.00")
    setResult(null)
    setSessionId(null)
    setChatMessages([])
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Analyze Test Failure</h1>
          <p className="text-gray-400 mt-1">
            Paste your failing test. AI will classify and diagnose automatically.
          </p>
        </div>
        <button
          onClick={handleClear}
          className="text-sm bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition"
        >
          Clear / New Analysis
        </button>
      </div>

      <button
        onClick={loadExample}
        className="mb-4 text-sm text-blue-400 hover:text-blue-300 underline"
      >
        Load example test failure
      </button>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Test Logs / Error Output *
          </label>
          <textarea
            rows={4}
            value={logs}
            onChange={e => setLogs(e.target.value)}
            placeholder="Paste your test error logs here..."
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-mono text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Test Case Description *
          </label>
          <textarea
            rows={2}
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="What is this test supposed to verify?"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Test Case Code *
          </label>
          <textarea
            rows={6}
            value={code}
            onChange={e => setCode(e.target.value)}
            placeholder="Paste your test code here..."
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-mono text-sm"
          />
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 text-white font-semibold py-4 rounded-lg transition text-lg"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              Analyzing... (may take 30-60s)
            </span>
          ) : 'Analyze Test Failure'}
        </button>
      </div>

      {/* Analysis Result */}
      <ResultCard result={result} />

      {/* Chat Box — appears after analysis */}
      {sessionId && (
        <div className="mt-8 border border-gray-700 rounded-xl overflow-hidden">
          <div className="bg-gray-800 px-4 py-3 flex justify-between items-center">
            <div>
              <h3 className="text-white font-semibold">Ask Followup Questions</h3>
              <p className="text-gray-400 text-xs mt-0.5">
                AI remembers your test failure context
              </p>
            </div>
            <span className="text-xs text-gray-500">
              Session: {sessionId.slice(0, 8)}...
            </span>
          </div>

          {/* Messages */}
          <div className="bg-gray-900 p-4 space-y-3 max-h-96 overflow-y-auto">
            {chatMessages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl px-4 py-2 rounded-lg text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : msg.role === 'system'
                    ? 'bg-green-900 text-green-300 w-full text-center'
                    : 'bg-gray-800 text-gray-200'
                }`}>
                  {msg.role === 'assistant' && (
                    <span className="text-xs text-gray-400 block mb-1">🤖 QA Assistant</span>
                  )}
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 px-4 py-2 rounded-lg">
                  <span className="text-gray-400 text-sm">🤖 Thinking...</span>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="bg-gray-800 p-3 flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleChatSend()}
              placeholder="Ask a followup question... (e.g. 'I applied the fix, now getting StaleElement')"
              className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
            />
            <button
              onClick={handleChatSend}
              disabled={chatLoading || !chatInput.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  )
}