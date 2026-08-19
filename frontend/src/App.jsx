import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Analyze from './pages/Analyze'
import History from './pages/History'
import MyTickets from './pages/MyTickets'
import Settings from './pages/Settings'
import ChatContext from './pages/ChatContext'

function PrivateRoute({ children }) {
  const isLoggedIn = !!localStorage.getItem('user_id')
  return isLoggedIn ? children : <Navigate to="/login" />
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0f0f1a] text-white">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <PrivateRoute>
              <div className="flex min-h-screen">
                <Sidebar />
                <div className="flex-1 ml-64">
                  <Routes>
                    <Route path="/analyze" element={<Analyze />} />
                    <Route path="/history" element={<History />} />
                    <Route path="/tickets" element={<MyTickets />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/chat/:sessionId" element={<ChatContext />} />
                    <Route path="/" element={<Navigate to="/analyze" />} />
                  </Routes>
                </div>
              </div>
            </PrivateRoute>
          } />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App