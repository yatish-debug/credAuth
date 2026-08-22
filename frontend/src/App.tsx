import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Home from './routes/Home';
import Verify from './routes/Verify';
import Dashboard from './routes/Dashboard';
import IssueCertificate from './routes/IssueCertificate';
import LoginPortal from './routes/LoginPortal';
import { Search, LayoutDashboard, Key, LogOut } from 'lucide-react';

function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [userRole, setUserRole] = useState<string | null>(localStorage.getItem('user_role'));
  const [userName, setUserName] = useState<string | null>(localStorage.getItem('user_name'));

  useEffect(() => {
    const handleStorage = () => {
      setToken(localStorage.getItem('token'));
      setUserRole(localStorage.getItem('user_role'));
      setUserName(localStorage.getItem('user_name'));
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
    localStorage.removeItem('org_name');
    setToken(null);
    setUserRole(null);
    setUserName(null);
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="border-b border-white/10 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          
          {/* Brand Logo & Tagline */}
          <Link to="/" className="flex-shrink-0 flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-cyan-500 to-emerald-400 p-[1.5px] shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center font-black text-xs tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 via-cyan-200 to-emerald-300">
                CA
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-100 to-cyan-200">
                  CredAuth
                </span>
                <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 rounded-full text-[10px] font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                  v2.5 Trust Layer
                </span>
              </div>
              <p className="text-[10px] text-gray-400 font-medium tracking-wide">Enterprise Credential Trust & Fraud Intelligence</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-2 sm:gap-3">
            <Link 
              to="/verify" 
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all flex items-center gap-1.5 ${
                isActive('/verify') 
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm' 
                  : 'text-gray-300 hover:text-white hover:bg-white/5'
              }`}
            >
              <Search size={14} className="text-cyan-400" />
              <span>Verify & Trust Engine</span>
            </Link>

            <Link 
              to="/dashboard" 
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all flex items-center gap-1.5 ${
                isActive('/dashboard') 
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm' 
                  : 'text-gray-300 hover:text-white hover:bg-white/5'
              }`}
            >
              <LayoutDashboard size={14} className="text-indigo-400" />
              <span>SaaS Dashboard</span>
            </Link>

            {token ? (
              <div className="flex items-center gap-2 pl-2 border-l border-white/10">
                <div className="hidden lg:flex flex-col text-right">
                  <span className="text-xs font-semibold text-white leading-tight">{userName || 'Active User'}</span>
                  <span className="text-[10px] text-indigo-300 font-mono">{userRole || 'TENANT'}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-1.5 sm:px-3 sm:py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/20 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer"
                  title="Logout"
                >
                  <LogOut size={13} />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 pl-2 border-l border-white/10">
                <Link 
                  to="/login" 
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-1.5 sm:px-4 sm:py-1.5 rounded-xl text-xs sm:text-sm font-bold transition-all shadow-lg shadow-indigo-600/25 flex items-center gap-1.5"
                >
                  <Key size={13} />
                  <span>Portal Login</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-indigo-500 selection:text-white flex flex-col">
        <Navigation />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/verify" element={<Verify />} />
            <Route path="/verify/:token" element={<Verify />} />
            <Route path="/login" element={<LoginPortal />} />
            <Route path="/login/admin" element={<LoginPortal />} />
            <Route path="/login/institution" element={<LoginPortal />} />
            <Route path="/login/verifier" element={<LoginPortal />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/certificates/create" element={<IssueCertificate />} />
          </Routes>
        </main>
        
        {/* B2B Platform Global Footer */}
        <footer className="border-t border-white/10 bg-black/60 backdrop-blur-md py-8 text-center text-xs text-gray-400">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="font-bold text-white">CredAuth Platform</span>
              <span className="text-gray-500">•</span>
              <span>B2B Credential Trust & Fraud Intelligence Layer</span>
            </div>
            <div className="flex items-center gap-4 font-mono text-[11px] text-gray-400">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span> API Status: 99.98% Operational
              </span>
              <span>RSA-PSS 2048-bit</span>
              <span>SHA-256 Digest</span>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
