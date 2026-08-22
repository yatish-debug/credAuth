import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import axios from 'axios';
import { 
  Lock, Mail, AlertCircle, Shield, Building2,
  ArrowRight, KeyRound, ShieldCheck, FileCheck, Eye, Search
} from 'lucide-react';

type RolePortal = 'SUPER_ADMIN' | 'ORGANIZATION_ADMIN' | 'CREDENTIAL_ISSUER' | 'VERIFICATION_OFFICER' | 'AUDITOR';

export default function LoginPortal() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  const getInitialPortal = (): RolePortal => {
    const roleParam = searchParams.get('role')?.toUpperCase();
    if (roleParam === 'SUPER_ADMIN' || roleParam === 'ADMIN') return 'SUPER_ADMIN';
    if (roleParam === 'ORGANIZATION_ADMIN' || roleParam === 'INSTITUTION' || roleParam === 'INSTITUTION_ADMIN') return 'ORGANIZATION_ADMIN';
    if (roleParam === 'ISSUER' || roleParam === 'CREDENTIAL_ISSUER') return 'CREDENTIAL_ISSUER';
    if (roleParam === 'VERIFIER' || roleParam === 'VERIFICATION_OFFICER' || roleParam === 'RECRUITER') return 'VERIFICATION_OFFICER';
    if (roleParam === 'AUDITOR' || roleParam === 'COMPLIANCE') return 'AUDITOR';
    return 'SUPER_ADMIN';
  };

  const [activePortal, setActivePortal] = useState<RolePortal>(getInitialPortal());
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initial = getInitialPortal();
    setActivePortal(initial);
    applyDefaultDemo(initial);
  }, [searchParams, location.pathname]);

  const applyDefaultDemo = (portal: RolePortal) => {
    if (portal === 'SUPER_ADMIN') {
      setEmail('admin@ssbt.demo');
      setPassword('admin123');
    } else if (portal === 'ORGANIZATION_ADMIN') {
      setEmail('univadmin@demo-university.edu');
      setPassword('univadmin123');
    } else if (portal === 'CREDENTIAL_ISSUER') {
      setEmail('chen.issuer@ssbt-university.edu');
      setPassword('issuer123');
    } else if (portal === 'VERIFICATION_OFFICER') {
      setEmail('tcs.verifier@tcs.demo');
      setPassword('verifier123');
    } else if (portal === 'AUDITOR') {
      setEmail('auditor@kpmg.demo');
      setPassword('auditor123');
    }
  };

  const handlePortalSwitch = (portal: RolePortal) => {
    setActivePortal(portal);
    setError('');
    applyDefaultDemo(portal);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('username', email.trim());
      params.append('password', password);
      
      const res = await axios.post('http://localhost:8000/api/v1/auth/login', params);
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user_role', res.data.role);
      localStorage.setItem('user_name', res.data.name);
      localStorage.setItem('org_name', res.data.organization_name || '');
      localStorage.setItem('org_id', res.data.organization_id ? String(res.data.organization_id) : '');
      if (res.data.permissions) {
        localStorage.setItem('user_permissions', JSON.stringify(res.data.permissions));
      }
      
      window.dispatchEvent(new Event('storage'));
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const portalMeta = {
    SUPER_ADMIN: {
      title: 'Platform Super Admin',
      badge: 'Root Governance Authority',
      badgeColor: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
      desc: 'Global multi-tenant governance: onboard organizations, manage tenant RSA keypairs, configure trust parameters, monitor system uptime.',
      demoCreds: 'admin@ssbt.demo / admin123',
    },
    ORGANIZATION_ADMIN: {
      title: 'Organization / University Admin',
      badge: 'Tenant Issuing Authority',
      badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
      desc: 'Enterprise tenant workspace: manage institution staff, configure cryptographic signing certificates, manage fraud incidents, oversee registry.',
      demoCreds: 'univadmin@demo-university.edu / univadmin123',
    },
    CREDENTIAL_ISSUER: {
      title: 'Credential Issuer Studio',
      badge: 'Authorized Digital Signer',
      badgeColor: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      desc: 'Issuance studio: generate cryptographically signed academic degrees, experience letters, skill badges with instant RSA-PSS signatures & QR codes.',
      demoCreds: 'chen.issuer@ssbt-university.edu / issuer123',
    },
    VERIFICATION_OFFICER: {
      title: 'Verification Officer / HR Recruiter',
      badge: 'Corporate Background Verifier',
      badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      desc: 'Candidate verification console: execute single, QR, and batch CSV checks, compute Trust Scores, and generate immutable Evidence Dossiers.',
      demoCreds: 'tcs.verifier@tcs.demo / verifier123',
    },
    AUDITOR: {
      title: 'Compliance & Fraud Auditor',
      badge: 'Regulatory Audit & Assurance',
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      desc: 'Independent compliance audit console: inspect immutable system audit logs, evaluate fraud detection accuracy, and review resolved cases.',
      demoCreds: 'auditor@kpmg.demo / auditor123',
    }
  }[activePortal];

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 sm:p-6 lg:p-8 bg-gradient-to-b from-slate-950 via-slate-900 to-black relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-600/15 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-5xl glass rounded-3xl border border-white/10 shadow-2xl overflow-hidden relative z-10 grid grid-cols-1 lg:grid-cols-12">
        
        {/* Left Column: Role Gateway Selector */}
        <div className="lg:col-span-5 p-6 sm:p-8 bg-black/40 border-b lg:border-b-0 lg:border-r border-white/10 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 rounded-full text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck size={13} /> CredAuth RBAC Gateway
              </span>
            </div>

            <h2 className="text-2xl font-extrabold text-white tracking-tight mb-2">
              Select Your Access Role
            </h2>
            <p className="text-gray-400 text-xs leading-relaxed mb-5">
              Choose a role below to auto-fill verified credentials from the synthetic demo environment.
            </p>

            <div className="space-y-2.5">
              {[
                { id: 'SUPER_ADMIN', label: 'Super Admin', sub: 'Platform Root Authority', icon: <Shield size={16} /> },
                { id: 'ORGANIZATION_ADMIN', label: 'Organization Admin', sub: 'University / Corporate Tenant', icon: <Building2 size={16} /> },
                { id: 'CREDENTIAL_ISSUER', label: 'Credential Issuer', sub: 'Authorized Signer & Registrar', icon: <FileCheck size={16} /> },
                { id: 'VERIFICATION_OFFICER', label: 'Verification Officer / HR', sub: 'Recruiter & Background Verifier', icon: <Search size={16} /> },
                { id: 'AUDITOR', label: 'Compliance Auditor', sub: 'Third-Party Assurance & Audit', icon: <Eye size={16} /> },
              ].map((roleItem) => (
                <button
                  key={roleItem.id}
                  type="button"
                  onClick={() => handlePortalSwitch(roleItem.id as RolePortal)}
                  className={`w-full p-3 rounded-xl border text-left transition-all flex items-center justify-between cursor-pointer ${
                    activePortal === roleItem.id 
                      ? 'bg-indigo-600/20 border-indigo-500/60 shadow-md shadow-indigo-500/10 text-white' 
                      : 'bg-white/5 border-white/5 hover:border-white/20 hover:bg-white/10 text-gray-400'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={activePortal === roleItem.id ? 'text-indigo-400' : 'text-gray-500'}>
                      {roleItem.icon}
                    </span>
                    <div>
                      <div className="font-bold text-xs leading-tight">{roleItem.label}</div>
                      <div className="text-[10px] text-gray-500">{roleItem.sub}</div>
                    </div>
                  </div>
                  {activePortal === roleItem.id && (
                    <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-white/10 text-[11px] text-gray-500 flex items-center justify-between font-mono">
            <span>Synthetic Dataset: Active</span>
            <span className="text-emerald-400">All 5 Roles Online</span>
          </div>
        </div>

        {/* Right Column: Active Portal Login Form */}
        <div className="lg:col-span-7 p-6 sm:p-10 flex flex-col justify-center bg-slate-950/60">
          <div className="max-w-md w-full mx-auto">
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${portalMeta.badgeColor}`}>
                  {portalMeta.badge}
                </span>
              </div>
              <h3 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                {portalMeta.title}
              </h3>
              <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                {portalMeta.desc}
              </p>
            </div>

            {error && (
              <div className="mb-5 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center gap-2 animate-shake">
                <AlertCircle size={16} className="text-red-400 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-black/40 border border-white/15 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-white text-xs placeholder-gray-600 transition-all outline-none font-mono"
                    placeholder="name@organization.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-black/40 border border-white/15 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-white text-xs placeholder-gray-600 transition-all outline-none font-mono"
                    placeholder="••••••••••••"
                  />
                </div>
              </div>

              <div className="p-3 bg-white/5 border border-white/10 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <KeyRound size={13} className="text-cyan-400" />
                  <span className="text-[11px] text-gray-400 font-mono">Demo: {portalMeta.demoCreds}</span>
                </div>
                <button
                  type="button"
                  onClick={() => applyDefaultDemo(activePortal)}
                  className="text-[10px] font-bold text-cyan-400 hover:text-cyan-300 underline cursor-pointer"
                >
                  Auto-Fill
                </button>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                ) : (
                  <>
                    <span>Authenticate & Access Workspace</span>
                    <ArrowRight size={14} />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
