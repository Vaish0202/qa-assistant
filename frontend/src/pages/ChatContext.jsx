import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function ChatContext() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [messages, setMessages] = useState([])

  useEffect(() => {
    axios.get(`/api/chat/session/${sessionId}`)
      .then(res => {
        setSession(res.data)
        setMessages(res.data.messages || [])
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [sessionId])

  const handleSend = async () => {
    if (!chatInput.trim()) return
    const userMsg = chatInput.trim()
    setChatInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setChatLoading(true)

    try {
      const res = await axios.post('/api/chat/followup', {
        session_id: sessionId,
        message: userMsg
      })
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }])
    } catch {
      setMessages(prev => [...prev, { role: 'system', content: 'Failed to get response.' }])
    } finally {
      setChatLoading(false)
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-screen text-[#6b7280]">
      Loading session...
    </div>
  )

  return (
    <div className="flex h-screen">

      {/* Left context panel */}
      <div className="w-64 bg-[#13131f] border-r border-[#2a2a3d] p-6 flex flex-col gap-6">
        <div>
          <button
            onClick={() => navigate('/history')}
            className="text-[#6b7280] hover:text-white text-sm flex items-center gap-2 mb-6"
          >
            ← Back to History
          </button>
          <h2 className="text-white font-semibold mb-4">Analysis Context</h2>
        </div>

        <div className="space-y-4 text-sm">
          <div>
            <p className="text-[#6b7280] text-xs mb-1">ID</p>
            <p className="text-white font-mono text-xs">AN-{sessionId?.slice(-8).toUpperCase()}</p>
          </div>

          <div>
            <span className={`px-2 py-1 rounded-full text-xs font-bold ${
              session?.classification === 'bug'
                ? 'bg-red-600 text-white'
                : 'bg-yellow-600 text-white'
            }`}>
              {session?.classification === 'bug' ? '🐛 PRODUCT BUG' : '⚠️ TEST ISSUE'}
            </span>
          </div>

          <div>
            <p className="text-[#6b7280] text-xs mb-1">Framework</p>
            <p className="text-white capitalize">{session?.framework || 'unknown'}</p>
          </div>

          <div>
            <p className="text-[#6b7280] text-xs mb-1">Status</p>
            <p className={session?.is_resolved ? 'text-green-400' : 'text-red-400'}>
              {session?.is_resolved ? '✓ Resolved' : '⊗ FAILED'}
            </p>
          </div>

          <div>
            <p className="text-[#6b7280] text-xs mb-1">Analyzed On</p>
            <p className="text-white text-xs">
              {session?.created_at ? new Date(session.created_at).toLocaleString() : '—'}
            </p>
          </div>

          <button
            onClick={() => navigate('/analyze')}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium py-2 rounded-lg transition mt-4"
          >
            View Full Analysis
          </button>
        </div>
      </div>

      {/* Right chat panel */}
      <div className="flex-1 flex flex-col">

        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2a3d] flex justify-between items-center">
          <div>
            <h2 className="text-white font-semibold">Ask Follow-up Questions</h2>
            <p className="text-[#6b7280] text-xs mt-0.5">AI remembers your test failure context</p>
          </div>
          <button
            onClick={() => setMessages([])}
            className="flex items-center gap-1 text-xs text-[#6b7280] hover:text-white border border-[#2a2a3d] px-3 py-1.5 rounded-lg transition"
          >
            🔄 Clear Chat
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 p-6 space-y-4 overflow-y-auto">
          {messages.map((msg, i) => (
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
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-xs text-indigo-400 font-medium">QA Assistant</p>
                    <p className="text-xs text-[#4b5563]">
                      {new Date().toLocaleTimeString()}
                    </p>
                  </div>
                )}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.role === 'user' && (
                  <span className="text-indigo-300 text-xs ml-2">✓</span>
                )}
              </div>
            </div>
          ))}

          {chatLoading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-sm mr-3">🤖</div>
              <div className="bg-[#1e1e30] rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:'0.1s'}}></div>
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:'0.2s'}}></div>
                </div>
              </div>
            </div>
          )}

          {messages.length === 0 && (
            <div className="text-center py-16">
              <div className="text-4xl mb-3">💬</div>
              <p className="text-[#6b7280] text-sm">No messages yet. Ask a question about this analysis.</p>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-[#2a2a3d] flex gap-3">
          <input
            type="text"
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask a follow-up question... (e.g. Why is this a bug?)"
            className="flex-1 bg-[#1e1e30] border border-[#2a2a3d] rounded-xl px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 text-sm"
          />
          <button
            onClick={handleSend}
            disabled={chatLoading || !chatInput.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-900 text-white px-5 py-3 rounded-xl text-sm font-medium transition flex items-center gap-2"
          >
            Send
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}