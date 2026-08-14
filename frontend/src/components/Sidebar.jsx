import { Link, useLocation, useNavigate } from 'react-router-dom'

const navItems = [
  {
    path: '/analyze',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
    label: 'Analyze'
  },
  {
    path: '/history',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    label: 'History'
  }
]

export default function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const username = localStorage.getItem('username') || 'User'

  const logout = () => {
    localStorage.clear()
    navigate('/login')
  }

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-[#13131f] border-r border-[#2a2a3d] flex flex-col z-50">

      {/* Logo */}
      <div className="p-6 border-b border-[#2a2a3d]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center text-lg">
            🤖
          </div>
          <div>
            <p className="font-bold text-white text-sm">QA Assistant</p>
            <p className="text-[#6b7280] text-xs">Agentic AI</p>
          </div>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(item => {
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-[#9ca3af] hover:bg-[#1e1e30] hover:text-white'
              }`}
            >
              {item.icon}
              {item.label}
            </Link>
          )
        })}
      </nav>

      {/* Pro Plan badge */}
      <div className="p-4 border-t border-[#2a2a3d]">
        <div className="bg-[#1e1e30] rounded-lg p-3 mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-[#9ca3af]">Pro Plan</span>
            <span className="text-xs text-indigo-400">Active</span>
          </div>
          <div className="w-full bg-[#2a2a3d] rounded-full h-1.5">
            <div className="bg-indigo-500 h-1.5 rounded-full w-3/4"></div>
          </div>
          <p className="text-xs text-[#6b7280] mt-1">78% of limit used</p>
        </div>

        {/* User */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-700 rounded-full flex items-center justify-center text-xs font-bold">
              {username[0].toUpperCase()}
            </div>
            <div>
              <p className="text-xs font-medium text-white">{username}</p>
              <p className="text-xs text-[#6b7280]">QA Engineer</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="text-[#6b7280] hover:text-red-400 transition"
            title="Logout"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}