import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getAnalysis } from '../api'
import ResultCard from '../components/ResultCard'

export default function AnalysisView() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getAnalysis(sessionId)
      .then(res => setResult(res.data))
      .catch(err => setError(err.response?.data?.detail || 'Could not load this analysis'))
  }, [sessionId])

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <button
        onClick={() => navigate(`/chat/${sessionId}`)}
        className="text-sm text-[#9ca3af] hover:text-white mb-4"
      >
        ← Back to conversation
      </button>
      <h1 className="text-2xl font-bold text-white">Saved Analysis</h1>
      {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
      {!result && !error && <p className="text-[#6b7280] text-sm mt-4">Loading…</p>}
      {result && <ResultCard result={result} />}
    </div>
  )
}