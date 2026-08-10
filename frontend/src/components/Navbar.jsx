import { Link, useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()
  const username = localStorage.getItem('username')

  const logout = () => {
    localStorage.clear()
    navigate('/login')
  }

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
      <div className="flex items-center gap-2">
        <span className="text-2xl">🤖</span>
        <span className="text-xl font-bold text-white">QA Assistant</span>
        <span className="text-xs text-gray-400 ml-2">Agentic AI</span>
      </div>

      <div className="flex items-center gap-6">
        {username && (
          <>
            <Link to="/analyze" className="text-gray-300 hover:text-white transition">
              Analyze
            </Link>
            <Link to="/history" className="text-gray-300 hover:text-white transition">
              History
            </Link>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400">👤 {username}</span>
              <button
                onClick={logout}
                className="text-sm bg-red-600 hover:bg-red-700 px-3 py-1 rounded transition"
              >
                Logout
              </button>
            </div>
          </>
        )}
      </div>
    </nav>
  )
}