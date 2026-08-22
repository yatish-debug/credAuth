import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  FileText, ShieldAlert, PlusCircle, 
  Key, Building2, AlertTriangle, 
  Search, RefreshCw, Copy, Lock, ChevronRight, X, Award,
  QrCode, Activity, AlertOctagon, Terminal, Bell, 
  Webhook as WebhookIcon, Radio, ShieldCheck, CheckCircle2, Send, Cpu, Sparkles,
  Users, UserPlus, Trash2, Database
} from 'lucide-react';

type TabType = 'overview' | 'users' | 'credentials' | 'fraud' | 'organizations' | 'apikeys' | 'webhooks' | 'monitoring' | 'audit' | 'issuers';

export default function Dashboard() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Users State
  const [usersList, setUsersList] = useState<any[]>([]);
  const [userRoleFilter, setUserRoleFilter] = useState<string>('ALL');
  const [userSearchQuery, setUserSearchQuery] = useState<string>('');
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [userForm, setUserForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'ORGANIZATION_ADMIN',
    organization_id: ''
  });

  // Reset Database Modal State
  const [showResetModal, setShowResetModal] = useState(false);
  const [resettingDb, setResettingDb] = useState(false);

  // Credentials State
  const [creds, setCreds] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Fraud Cases State
  const [fraudCases, setFraudCases] = useState<any[]>([]);
  const [fraudStatusFilter, setFraudStatusFilter] = useState<string>('ALL');
  const [selectedFraudCase, setSelectedFraudCase] = useState<any>(null);
  const [caseNoteText, setCaseNoteText] = useState('');
  const [resolveModal, setResolveModal] = useState<any>(null);
  const [resolveResolution, setResolveResolution] = useState('CONFIRMED_FRAUD');
  const [resolveNotes, setResolveNotes] = useState('');

  // Organizations State
  const [orgs, setOrgs] = useState<any[]>([]);
  const [showAddOrgModal, setShowAddOrgModal] = useState(false);
  const [orgForm, setOrgForm] = useState({
    name: '',
    institution_code: '',
    organization_type: 'UNIVERSITY',
    official_domain: '',
    description: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    admin_name: '',
    admin_email: '',
    admin_password: '',
  });

  // API Keys State
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [showAddKeyModal, setShowAddKeyModal] = useState(false);
  const [keyForm, setKeyForm] = useState({
    name: 'Production ATS Integration',
    environment: 'PRODUCTION',
    rate_limit_per_minute: 120,
    permissions: ['credential:read', 'credential:verify', 'verification:create']
  });
  const [createdKeySecret, setCreatedKeySecret] = useState<string | null>(null);

  // Webhooks State
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [showAddWebhookModal, setShowAddWebhookModal] = useState(false);
  const [webhookForm, setWebhookForm] = useState({
    endpoint_url: 'https://api.enterprise.demo/webhooks/credentials',
    events: ['credential.issued', 'credential.verified', 'credential.revoked', 'fraud.detected']
  });

  // Monitoring State
  const [monitoringAlerts, setMonitoringAlerts] = useState<any[]>([]);
  const [monitoringLoading, setMonitoringLoading] = useState(false);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Issuers State
  const [issuers, setIssuers] = useState<any[]>([]);

  // Modals & Action Reason
  const [actionReasonModal, setActionReasonModal] = useState<{ type: 'revoke' | 'suspicious' | 'reinstate', certId: number, certCode: string } | null>(null);
  const [actionReason, setActionReason] = useState('');
  const [showProofModal, setShowProofModal] = useState<any>(null);
  const [proofData, setProofData] = useState<any>(null);
  const [showQrModal, setShowQrModal] = useState<any>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const getHeaders = () => {
    return token ? { headers: { Authorization: `Bearer ${token}` } } : {};
  };

  // Initial Load
  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    loadUserProfile();
    loadDashboardStats();
    loadCredentials();
    loadOrganizations();
  }, [token]);

  // Tab-specific Load
  useEffect(() => {
    if (!token) return;
    if (activeTab === 'users') loadUsers();
    if (activeTab === 'fraud') loadFraudCases();
    if (activeTab === 'organizations') loadOrganizations();
    if (activeTab === 'apikeys') loadApiKeys();
    if (activeTab === 'webhooks') loadWebhooks();
    if (activeTab === 'monitoring') loadMonitoring();
    if (activeTab === 'audit') loadAuditLogs();
    if (activeTab === 'issuers') loadIssuers();
  }, [activeTab]);

  const loadUserProfile = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/auth/me', getHeaders());
      setUser(res.data);
      localStorage.setItem('user_role', res.data.role);
      localStorage.setItem('user_name', res.data.name);
      localStorage.setItem('org_name', res.data.organization || '');
    } catch {
      navigate('/login');
    }
  };

  const loadDashboardStats = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/dashboard/stats', getHeaders());
      setStats(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadUsers = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/users', getHeaders());
      setUsersList(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadCredentials = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/certificates?limit=250', getHeaders());
      setCreds(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadFraudCases = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/fraud/cases', getHeaders());
      setFraudCases(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadOrganizations = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/organizations', getHeaders());
      setOrgs(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadApiKeys = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/api-keys', getHeaders());
      setApiKeys(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadWebhooks = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/webhooks', getHeaders());
      setWebhooks(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadMonitoring = async () => {
    try {
      const alertsRes = await axios.get('http://localhost:8000/api/v1/monitoring/alerts', getHeaders());
      setMonitoringAlerts(alertsRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadAuditLogs = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/audit/logs?limit=150', getHeaders());
      setAuditLogs(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadIssuers = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/issuers', getHeaders());
      setIssuers(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([loadDashboardStats(), loadCredentials(), loadOrganizations()]);
    if (activeTab === 'users') await loadUsers();
    if (activeTab === 'fraud') await loadFraudCases();
    if (activeTab === 'organizations') await loadOrganizations();
    if (activeTab === 'apikeys') await loadApiKeys();
    if (activeTab === 'webhooks') await loadWebhooks();
    if (activeTab === 'monitoring') await loadMonitoring();
    if (activeTab === 'audit') await loadAuditLogs();
    if (activeTab === 'issuers') await loadIssuers();
    setRefreshing(false);
    showToast("Dashboard synchronized with authoritative registry.");
  };

  // User Management Actions
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        name: userForm.name.trim(),
        email: userForm.email.trim(),
        password: userForm.password,
        role: userForm.role,
        organization_id: userForm.organization_id ? parseInt(userForm.organization_id) : null
      };
      await axios.post('http://localhost:8000/api/v1/users', payload, getHeaders());
      setShowAddUserModal(false);
      setUserForm({ name: '', email: '', password: '', role: 'ORGANIZATION_ADMIN', organization_id: '' });
      loadUsers();
      showToast("New user account created successfully!");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to create user.");
    }
  };

  const handleDeleteUser = async (userId: number, userEmail: string) => {
    if (!confirm(`Are you sure you want to permanently delete user: ${userEmail}?`)) return;
    try {
      await axios.delete(`http://localhost:8000/api/v1/users/${userId}`, getHeaders());
      loadUsers();
      showToast(`User ${userEmail} deleted.`);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete user.");
    }
  };

  // Clean Database Reset Action
  const handleResetDatabaseToZero = async () => {
    setResettingDb(true);
    try {
      const res = await axios.post('http://localhost:8000/api/v1/admin/reset-database', {
        confirm_reset: true,
        super_admin_email: "admin@ssbt.demo",
        super_admin_password: "admin123",
        super_admin_name: "CredAuth Root Super Admin"
      }, getHeaders());
      
      setShowResetModal(false);
      await handleRefresh();
      showToast(res.data.message || "Database reset to 0 with 1 Super Admin!");
      alert("✅ DATABASE RESET TO 0 (FRESH SLATE)\n\nAll demo credentials, organizations, and fraud cases have been wiped.\nOnly 1 user remains active:\n\nEmail: admin@ssbt.demo\nPassword: admin123\n\nYou can now onboard your own organizations and create custom users from scratch.");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to reset database.");
    } finally {
      setResettingDb(false);
    }
  };

  // Actions on Credentials
  const handleCredentialAction = async (certId: number, newStatus: string, reason?: string) => {
    try {
      await axios.patch(`http://localhost:8000/api/v1/certificates/${certId}/status`, {
        status: newStatus,
        reason: reason || `Updated to ${newStatus}`
      }, getHeaders());
      showToast(`Credential status updated to ${newStatus}`);
      setActionReasonModal(null);
      setActionReason('');
      loadCredentials();
      loadDashboardStats();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Action failed");
    }
  };

  const handleOpenProofModal = async (cert: any) => {
    setShowProofModal(cert);
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/certificates/${cert.id}/proof`, getHeaders());
      setProofData(res.data);
    } catch {
      setProofData(null);
    }
  };

  // Actions on Fraud Cases
  const handleAddCaseNote = async (caseId: string) => {
    if (!caseNoteText.trim()) return;
    try {
      await axios.post(`http://localhost:8000/api/v1/fraud/cases/${caseId}/note`, {
        note: caseNoteText
      }, getHeaders());
      setCaseNoteText('');
      loadFraudCases();
      showToast("Investigator note recorded.");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to record note");
    }
  };

  const handleResolveCase = async () => {
    if (!resolveModal) return;
    try {
      await axios.post(`http://localhost:8000/api/v1/fraud/cases/${resolveModal.case_id}/resolve`, {
        resolution: resolveResolution,
        notes: resolveNotes || "Case resolved by compliance auditor.",
        auto_revoke_credential: true
      }, getHeaders());
      setResolveModal(null);
      setResolveNotes('');
      loadFraudCases();
      loadDashboardStats();
      showToast(`Case resolved as ${resolveResolution}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to resolve case");
    }
  };

  // API Key creation
  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/api/v1/api-keys', keyForm, getHeaders());
      setCreatedKeySecret(res.data.raw_api_key);
      loadApiKeys();
      showToast("API Key created successfully.");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to create API key");
    }
  };

  const handleRevokeApiKey = async (keyId: string) => {
    if (!confirm("Are you sure you want to revoke this API key? This action is immediate and cannot be undone.")) return;
    try {
      await axios.delete(`http://localhost:8000/api/v1/api-keys/${keyId}`, getHeaders());
      loadApiKeys();
      showToast("API Key revoked.");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to revoke key");
    }
  };

  // Webhook creation & test
  const handleCreateWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8000/api/v1/webhooks', webhookForm, getHeaders());
      setShowAddWebhookModal(false);
      loadWebhooks();
      showToast("Webhook endpoint registered.");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to register webhook");
    }
  };

  const handleTestWebhook = async (webhookId: string) => {
    try {
      await axios.post(`http://localhost:8000/api/v1/webhooks/${webhookId}/test`, {
        event_type: 'credential.verified'
      }, getHeaders());
      showToast("Simulated webhook dispatched successfully!");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Webhook test failed");
    }
  };

  // Trigger Monitoring Integrity Check
  const handleRunMonitoringCheck = async () => {
    setMonitoringLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/api/v1/monitoring/run-check', {}, getHeaders());
      loadMonitoring();
      showToast(res.data.message);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Integrity scan failed");
    } finally {
      setMonitoringLoading(false);
    }
  };

  // Create Organization Handler
  const handleCreateOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8000/api/v1/organizations', orgForm, getHeaders());
      setShowAddOrgModal(false);
      setOrgForm({
        name: '',
        institution_code: '',
        organization_type: 'UNIVERSITY',
        official_domain: '',
        description: '',
        contact_email: '',
        contact_phone: '',
        address: '',
        admin_name: '',
        admin_email: '',
        admin_password: '',
      });
      loadOrganizations();
      showToast("Organization onboarded successfully.");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to onboard organization");
    }
  };

  // Filtered Users
  const filteredUsers = usersList.filter(u => {
    const matchesRole = userRoleFilter === 'ALL' || u.role === userRoleFilter;
    const matchesSearch = !userSearchQuery || 
      u.name.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
      (u.organization_name && u.organization_name.toLowerCase().includes(userSearchQuery.toLowerCase()));
    return matchesRole && matchesSearch;
  });

  // Filtered Credentials
  const filteredCreds = creds.filter(c => {
    const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;
    const matchesCat = categoryFilter === 'ALL' || (c.category || 'ACADEMIC') === categoryFilter;
    const matchesSearch = !searchQuery || 
      c.certificate_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.holder_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.course_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesCat && matchesSearch;
  });

  const getStatusBadge = (st: string) => {
    if (st === 'ACTIVE' || st === 'VERIFIED') return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (st === 'REVOKED' || st === 'HIGH_RISK' || st === 'CRITICAL') return 'bg-red-500/10 text-red-400 border-red-500/30';
    if (st === 'SUSPICIOUS' || st === 'UNDER_REVIEW' || st === 'OPEN') return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    if (st === 'EXPIRED') return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
    return 'bg-gray-500/10 text-gray-400 border-gray-500/30';
  };

  const getRoleBadge = (role: string) => {
    if (role === 'SUPER_ADMIN') return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40';
    if (role === 'ORGANIZATION_ADMIN' || role === 'INSTITUTION_ADMIN') return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
    if (role === 'CREDENTIAL_ISSUER' || role === 'ISSUER') return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
    if (role === 'VERIFICATION_OFFICER' || role === 'VERIFIER') return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    if (role === 'AUDITOR') return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    return 'bg-gray-500/20 text-gray-300 border-gray-500/40';
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-2xl bg-indigo-600 text-white font-bold text-xs shadow-2xl flex items-center gap-2 border border-indigo-400/30 animate-fade-in">
          <CheckCircle2 size={16} className="text-cyan-300" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Workspace Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <span className={`px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 border ${getRoleBadge(user?.role || '')}`}>
              <ShieldCheck size={13} /> {user?.role || 'ORGANIZATION_ADMIN'}
            </span>
            <span className="text-xs text-gray-500">•</span>
            <span className="text-xs text-cyan-300 font-semibold">{user?.organization || 'Platform Super Authority'}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Enterprise Credential Trust Workspace
          </h1>
        </div>

        {/* Action Toolbar */}
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            title="Refresh All Registry Data"
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin text-cyan-400" : ""} />
            <span className="hidden sm:inline">Sync Registry</span>
          </button>

          {user?.role === 'SUPER_ADMIN' && (
            <button
              onClick={() => setShowResetModal(true)}
              className="p-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/30 text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer"
              title="Wipe demo data and reset database to fresh 0 state"
            >
              <Database size={14} className="text-red-400" />
              <span>Reset DB (0 Data)</span>
            </button>
          )}

          {(user?.role === 'SUPER_ADMIN' || user?.role === 'ORGANIZATION_ADMIN') && (
            <button
              onClick={() => {
                setShowAddUserModal(true);
              }}
              className="px-3.5 py-2.5 bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 rounded-xl text-xs font-bold shadow-md flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <UserPlus size={15} />
              <span>Add User</span>
            </button>
          )}

          {(user?.role === 'SUPER_ADMIN' || user?.role === 'ORGANIZATION_ADMIN' || user?.role === 'CREDENTIAL_ISSUER') && (
            <button
              onClick={() => navigate('/certificates/create')}
              className="px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/25 flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <PlusCircle size={15} />
              <span>Issue Credential</span>
            </button>
          )}
        </div>
      </div>

      {/* Navigation Sub-Tabs Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none border-b border-white/5">
        {[
          { id: 'overview', label: 'Intelligence Overview', icon: <Activity size={14} /> },
          { id: 'users', label: `User Management (${usersList.length})`, icon: <Users size={14} /> },
          { id: 'credentials', label: `Credential Registry (${creds.length})`, icon: <Award size={14} /> },
          { id: 'fraud', label: 'Fraud Investigation Center', icon: <ShieldAlert size={14} /> },
          { id: 'organizations', label: `Multi-Tenant Orgs (${orgs.length})`, icon: <Building2 size={14} /> },
          { id: 'apikeys', label: 'Developer & API Keys', icon: <Key size={14} /> },
          { id: 'webhooks', label: 'Webhooks & Events', icon: <WebhookIcon size={14} /> },
          { id: 'monitoring', label: 'Continuous Monitoring', icon: <Bell size={14} /> },
          { id: 'audit', label: 'Immutable Audit Trail', icon: <FileText size={14} /> },
          { id: 'issuers', label: 'Public Issuer Directory', icon: <Radio size={14} /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap cursor-pointer ${
              activeTab === tab.id
                ? 'bg-indigo-600/30 text-white border border-indigo-500/50 shadow-md shadow-indigo-500/10'
                : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
            }`}
          >
            <span className={activeTab === tab.id ? "text-cyan-400" : "text-gray-500"}>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* TAB: USER MANAGEMENT */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="glass rounded-2xl border border-white/10 p-4 flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Search users by name, email, or organization..."
                value={userSearchQuery}
                onChange={(e) => setUserSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-black/40 border border-white/10 focus:border-indigo-500 rounded-xl text-white text-xs outline-none"
              />
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              <select
                value={userRoleFilter}
                onChange={(e) => setUserRoleFilter(e.target.value)}
                className="px-3 py-2 bg-black/40 border border-white/10 text-xs rounded-xl text-gray-300 outline-none"
              >
                <option value="ALL">All Roles</option>
                <option value="SUPER_ADMIN">Super Admin</option>
                <option value="ORGANIZATION_ADMIN">Organization Admin</option>
                <option value="CREDENTIAL_ISSUER">Credential Issuer</option>
                <option value="VERIFICATION_OFFICER">Verification Officer</option>
                <option value="AUDITOR">Compliance Auditor</option>
              </select>

              <button
                onClick={() => setShowAddUserModal(true)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <UserPlus size={14} />
                <span>Create User</span>
              </button>
            </div>
          </div>

          <div className="glass rounded-3xl border border-white/10 overflow-hidden shadow-xl">
            <div className="overflow-x-auto max-h-[600px]">
              <table className="w-full text-left text-xs">
                <thead className="text-[10px] text-gray-400 uppercase tracking-wider bg-black/50 border-b border-white/10 sticky top-0 z-10">
                  <tr>
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Organization Tenant</th>
                    <th className="py-3 px-4">Account Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-white/5 font-mono">
                      <td className="py-3 px-4">
                        <div className="font-bold text-white font-sans">{u.name}</div>
                        <div className="text-[11px] text-cyan-300">{u.email}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getRoleBadge(u.role)}`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-sans text-gray-300">
                        {u.organization_name || (u.role === 'SUPER_ADMIN' ? 'Platform Root (Global)' : 'Independent / Unassigned')}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${u.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-red-500/10 text-red-400 border-red-500/30'}`}>
                          {u.is_active ? 'ACTIVE' : 'DISABLED'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-sans">
                        {user?.role === 'SUPER_ADMIN' && u.id !== user?.id && (
                          <button
                            onClick={() => handleDeleteUser(u.id, u.email)}
                            className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/20 text-xs transition-colors cursor-pointer"
                            title="Delete User"
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/10 relative overflow-hidden">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Total Credentials</div>
              <div className="text-3xl font-black text-white mt-1 font-mono">{stats?.total_credentials ?? creds.length}</div>
              <div className="text-[11px] text-emerald-400 mt-2 flex items-center gap-1 font-mono">
                <CheckCircle2 size={13} /> {stats?.active_credentials ?? creds.filter(c => c.status === 'ACTIVE').length} Active in Registry
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/10 relative overflow-hidden">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Avg Credential Trust</div>
              <div className="text-3xl font-black text-emerald-400 mt-1 font-mono">
                {(creds.length > 0 && stats?.average_trust_score) ? stats.average_trust_score : '0.0'}
              </div>
              <div className="text-[11px] text-gray-400 mt-2 font-mono">0 - 100 Multi-Factor Score</div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/10 relative overflow-hidden">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Total Verifications</div>
              <div className="text-3xl font-black text-cyan-300 mt-1 font-mono">{stats?.total_verifications ?? 0}</div>
              <div className="text-[11px] text-cyan-400 mt-2 font-mono">Instant RSA Cryptographic Audits</div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/10 relative overflow-hidden">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Organizations</div>
              <div className="text-3xl font-black text-indigo-300 mt-1 font-mono">{orgs.length}</div>
              <div className="text-[11px] text-indigo-400 mt-2 flex items-center gap-1 font-mono">
                <Building2 size={13} /> {usersList.length} System Users
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { title: "Academic Degrees", count: stats?.categories?.ACADEMIC || 0, color: "text-blue-400", border: "border-blue-500/20", icon: <Award size={18} /> },
              { title: "Recruitment Experience", count: stats?.categories?.RECRUITMENT || 0, color: "text-emerald-400", border: "border-emerald-500/20", icon: <Building2 size={18} /> },
              { title: "Technical Certifications", count: stats?.categories?.TECHNICAL_COURSE || 0, color: "text-cyan-400", border: "border-cyan-500/20", icon: <Cpu size={18} /> },
              { title: "Hackathon Awards", count: stats?.categories?.ACHIEVEMENT || 0, color: "text-amber-400", border: "border-amber-500/20", icon: <Sparkles size={18} /> },
            ].map((cat, i) => (
              <div key={i} className={`p-4 rounded-2xl bg-black/40 border ${cat.border} flex items-center justify-between`}>
                <div>
                  <div className="text-xs font-bold text-gray-400">{cat.title}</div>
                  <div className="text-2xl font-black text-white mt-0.5">{cat.count}</div>
                </div>
                <div className={`p-2.5 rounded-xl bg-white/5 ${cat.color}`}>{cat.icon}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 glass rounded-3xl border border-white/10 p-6 shadow-xl">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Award size={16} className="text-cyan-400" /> Recent Credentials Issued
                </h3>
                <button onClick={() => setActiveTab('credentials')} className="text-xs text-indigo-400 hover:text-indigo-300 font-bold">
                  View Full Registry →
                </button>
              </div>

              {creds.length === 0 ? (
                <div className="p-8 text-center text-gray-500 text-xs">
                  No credentials in registry. Click <strong>Issue Credential</strong> above to issue your first signed credential!
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="text-[10px] text-gray-400 uppercase tracking-wider bg-black/30 border-b border-white/10">
                      <tr>
                        <th className="py-2.5 px-3">Credential ID</th>
                        <th className="py-2.5 px-3">Candidate</th>
                        <th className="py-2.5 px-3">Program / Title</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 font-mono">
                      {creds.slice(0, 6).map((c) => (
                        <tr key={c.id} className="hover:bg-white/5">
                          <td className="py-2.5 px-3 text-cyan-300 font-bold">{c.certificate_id}</td>
                          <td className="py-2.5 px-3 text-white font-sans">{c.holder_name}</td>
                          <td className="py-2.5 px-3 text-gray-300 font-sans">{c.course_name}</td>
                          <td className="py-2.5 px-3 text-gray-400 text-[10px] uppercase">{c.category || 'ACADEMIC'}</td>
                          <td className="py-2.5 px-3">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(c.status)}`}>
                              {c.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="lg:col-span-4 glass rounded-3xl border border-white/10 p-6 shadow-xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Terminal size={16} className="text-indigo-400" /> Fast Execution
              </h3>
              <div className="space-y-2">
                <button
                  onClick={() => setActiveTab('users')}
                  className="w-full p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-left text-xs font-bold text-white flex items-center justify-between transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <Users size={15} className="text-indigo-400" />
                    <span>Manage User Accounts</span>
                  </div>
                  <ChevronRight size={14} className="text-gray-500" />
                </button>

                <button
                  onClick={() => setActiveTab('organizations')}
                  className="w-full p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-left text-xs font-bold text-white flex items-center justify-between transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <Building2 size={15} className="text-cyan-400" />
                    <span>Onboard Organization</span>
                  </div>
                  <ChevronRight size={14} className="text-gray-500" />
                </button>

                <button
                  onClick={() => navigate('/verify')}
                  className="w-full p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-left text-xs font-bold text-white flex items-center justify-between transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <Search size={15} className="text-emerald-400" />
                    <span>Run Verification Query</span>
                  </div>
                  <ChevronRight size={14} className="text-gray-500" />
                </button>

                <button
                  onClick={() => setActiveTab('fraud')}
                  className="w-full p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-left text-xs font-bold text-white flex items-center justify-between transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <ShieldAlert size={15} className="text-amber-400" />
                    <span>Triage Fraud Cases</span>
                  </div>
                  <ChevronRight size={14} className="text-gray-500" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CREDENTIALS */}
      {activeTab === 'credentials' && (
        <div className="space-y-4">
          <div className="glass rounded-2xl border border-white/10 p-4 flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Search by ID, Candidate Name, Program or Role..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-black/40 border border-white/10 focus:border-indigo-500 rounded-xl text-white text-xs outline-none"
              />
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="px-3 py-2 bg-black/40 border border-white/10 text-xs rounded-xl text-gray-300 outline-none"
              >
                <option value="ALL">All Categories</option>
                <option value="ACADEMIC">Academic Degrees</option>
                <option value="RECRUITMENT">Recruitment & HR</option>
                <option value="TECHNICAL_COURSE">Technical Courses</option>
                <option value="ACHIEVEMENT">Awards & Honors</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 bg-black/40 border border-white/10 text-xs rounded-xl text-gray-300 outline-none"
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">Active Only</option>
                <option value="REVOKED">Revoked</option>
                <option value="SUSPICIOUS">Suspicious</option>
                <option value="EXPIRED">Expired</option>
              </select>
            </div>
          </div>

          <div className="glass rounded-3xl border border-white/10 overflow-hidden shadow-xl">
            <div className="overflow-x-auto max-h-[600px]">
              <table className="w-full text-left text-xs">
                <thead className="text-[10px] text-gray-400 uppercase tracking-wider bg-black/50 border-b border-white/10 sticky top-0 z-10">
                  <tr>
                    <th className="py-3 px-4">Credential ID</th>
                    <th className="py-3 px-4">Candidate / Holder</th>
                    <th className="py-3 px-4">Program / Role</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Grade / CGPA</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredCreds.map((c) => (
                    <tr key={c.id} className="hover:bg-white/5">
                      <td className="py-3 px-4 font-mono text-cyan-300 font-bold">{c.certificate_id}</td>
                      <td className="py-3 px-4 text-white font-bold">{c.holder_name}</td>
                      <td className="py-3 px-4 text-gray-300">{c.course_name}</td>
                      <td className="py-3 px-4 text-gray-400 text-[10px] uppercase font-mono">{c.category || 'ACADEMIC'}</td>
                      <td className="py-3 px-4 text-emerald-400 font-mono">{c.cgpa ? `CGPA: ${c.cgpa}` : (c.grade || 'Passed')}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(c.status)}`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenProofModal(c)}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-cyan-300 border border-white/10 cursor-pointer"
                            title="Inspect Cryptographic Proof"
                          >
                            <Lock size={13} />
                          </button>

                          <button
                            onClick={() => setShowQrModal(c)}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-indigo-300 border border-white/10 cursor-pointer"
                            title="View QR Code"
                          >
                            <QrCode size={13} />
                          </button>

                          {c.status === 'ACTIVE' && (
                            <button
                              onClick={() => setActionReasonModal({ type: 'revoke', certId: c.id, certCode: c.certificate_id })}
                              className="px-2 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/20 text-[10px] font-bold cursor-pointer"
                            >
                              Revoke
                            </button>
                          )}

                          {c.status === 'REVOKED' && (
                            <button
                              onClick={() => setActionReasonModal({ type: 'reinstate', certId: c.id, certCode: c.certificate_id })}
                              className="px-2 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/20 text-[10px] font-bold cursor-pointer"
                            >
                              Reinstate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: FRAUD */}
      {activeTab === 'fraud' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <ShieldAlert size={20} className="text-amber-400" /> Fraud Investigation Center
              </h2>
              <p className="text-xs text-gray-400">Triage detected anomalies, inspect risk scores, and manage resolution workflows.</p>
            </div>
            <select
              value={fraudStatusFilter}
              onChange={(e) => setFraudStatusFilter(e.target.value)}
              className="px-3 py-2 bg-black/40 border border-white/10 text-xs rounded-xl text-gray-300 outline-none"
            >
              <option value="ALL">All Cases</option>
              <option value="OPEN">Open Incidents</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="CONFIRMED_FRAUD">Confirmed Fraud</option>
              <option value="FALSE_POSITIVE">False Positive</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7 space-y-3">
              {fraudCases.length === 0 ? (
                <div className="glass rounded-3xl border border-white/10 p-8 text-center text-gray-500 text-xs">
                  No active fraud cases recorded.
                </div>
              ) : (
                fraudCases.map((fc) => (
                  <div
                    key={fc.id}
                    onClick={() => setSelectedFraudCase(fc)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                      selectedFraudCase?.id === fc.id
                        ? 'bg-indigo-950/40 border-indigo-500 shadow-lg shadow-indigo-500/10'
                        : 'glass border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2 font-mono">
                        <span className="text-xs font-bold text-cyan-300">{fc.case_id}</span>
                        <span className="text-gray-500">•</span>
                        <span className="text-xs text-white">{fc.credential_code}</span>
                      </div>
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(fc.status)}`}>
                        {fc.status}
                      </span>
                    </div>

                    <div className="text-xs text-gray-300 font-bold mb-2">Candidate: {fc.holder_name}</div>

                    <div className="space-y-1">
                      {fc.indicators.slice(0, 2).map((ind: string, idx: number) => (
                        <div key={idx} className="text-[11px] text-amber-300/90 flex items-center gap-1.5 font-mono">
                          <AlertTriangle size={12} className="flex-shrink-0 text-amber-400" />
                          <span className="truncate">{ind}</span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-white/5 flex justify-between items-center text-[10px] text-gray-500 font-mono">
                      <span>Risk Score: <strong className="text-red-400">{fc.risk_score}/100</strong> ({fc.risk_level})</span>
                      <span>{new Date(fc.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="lg:col-span-5">
              {selectedFraudCase ? (
                <div className="glass rounded-3xl border border-white/10 p-6 shadow-2xl space-y-5 sticky top-20">
                  <div className="flex justify-between items-center pb-4 border-b border-white/10">
                    <div>
                      <div className="text-[10px] text-gray-400 font-mono uppercase">Case File</div>
                      <h3 className="text-lg font-black text-white">{selectedFraudCase.case_id}</h3>
                    </div>
                    <button
                      onClick={() => setResolveModal(selectedFraudCase)}
                      className="px-3 py-1.5 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white font-bold text-xs rounded-xl shadow-md transition-all cursor-pointer"
                    >
                      Resolve Case
                    </button>
                  </div>

                  <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-red-300 uppercase">Fraud Risk Level: {selectedFraudCase.risk_level}</span>
                      <span className="text-xl font-black text-red-400 font-mono">{selectedFraudCase.risk_score}/100</span>
                    </div>
                  </div>

                  <div>
                    <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Detected Risk Factors</div>
                    <div className="space-y-1.5">
                      {selectedFraudCase.indicators.map((ind: string, idx: number) => (
                        <div key={idx} className="p-2.5 rounded-xl bg-black/40 border border-white/5 text-xs text-gray-300 font-mono">
                          {ind}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Investigation Notes Timeline</div>
                    <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
                      {(selectedFraudCase.notes_history || []).map((n: any, idx: number) => (
                        <div key={idx} className="p-2.5 rounded-xl bg-white/5 border border-white/5 text-[11px] space-y-1">
                          <div className="flex justify-between text-gray-500 text-[10px]">
                            <span className="font-bold text-cyan-400">{n.author}</span>
                            <span>{new Date(n.timestamp).toLocaleTimeString()}</span>
                          </div>
                          <p className="text-gray-300">{n.text}</p>
                        </div>
                      ))}
                    </div>

                    <div className="mt-3 flex gap-2">
                      <input
                        type="text"
                        placeholder="Add investigator note..."
                        value={caseNoteText}
                        onChange={(e) => setCaseNoteText(e.target.value)}
                        className="flex-1 px-3 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white outline-none"
                      />
                      <button
                        onClick={() => handleAddCaseNote(selectedFraudCase.case_id)}
                        className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
                      >
                        <Send size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="glass rounded-3xl border border-white/10 p-10 text-center flex flex-col items-center justify-center min-h-[300px] text-gray-500">
                  <ShieldAlert size={32} className="mb-2 text-gray-600" />
                  <p className="text-xs">Select a fraud case from the queue to view forensics & audit notes.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: ORGANIZATIONS */}
      {activeTab === 'organizations' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Building2 size={20} className="text-cyan-400" /> Multi-Tenant Organizations
              </h2>
              <p className="text-xs text-gray-400">Manage institutional tenants, RSA 2048-bit keypairs, and issuer trust profiles.</p>
            </div>
            {user?.role === 'SUPER_ADMIN' && (
              <button
                onClick={() => setShowAddOrgModal(true)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md transition-all cursor-pointer flex items-center gap-1.5"
              >
                <PlusCircle size={14} />
                <span>Onboard New Tenant</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {orgs.map((o) => (
              <div key={o.id} className="glass rounded-3xl border border-white/10 p-6 shadow-xl space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] font-mono px-2 py-0.5 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full font-bold">
                      {o.organization_type || 'UNIVERSITY'}
                    </span>
                    <h3 className="text-lg font-black text-white mt-1.5">{o.name}</h3>
                    <div className="text-xs font-mono text-cyan-300">{o.institution_code}</div>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(o.status)}`}>
                    {o.status}
                  </span>
                </div>

                <p className="text-xs text-gray-400 leading-relaxed">{o.description || 'Verified issuing organization authority.'}</p>

                <div className="p-3 bg-black/40 rounded-xl border border-white/5 font-mono text-[11px] space-y-1">
                  <div className="flex justify-between text-gray-400">
                    <span>Issuer Trust Score:</span>
                    <span className="text-emerald-400 font-bold">{o.trust_score || 95.0}/100</span>
                  </div>
                  <div className="flex justify-between text-gray-400">
                    <span>Key Fingerprint:</span>
                    <span className="text-gray-300">{o.key_fingerprint ? o.key_fingerprint.slice(0, 17) + '...' : 'E4:13:93...'}</span>
                  </div>
                  <div className="flex justify-between text-gray-400">
                    <span>Official Domain:</span>
                    <span className="text-cyan-300">{o.official_domain || 'N/A'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: API KEYS */}
      {activeTab === 'apikeys' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Key size={20} className="text-emerald-400" /> Developer Hub & API Keys
              </h2>
              <p className="text-xs text-gray-400">Provision scoped REST API keys for programmatic B2B credential verification.</p>
            </div>
            <button
              onClick={() => {
                setCreatedKeySecret(null);
                setShowAddKeyModal(true);
              }}
              className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold shadow-md transition-all cursor-pointer flex items-center gap-1.5"
            >
              <PlusCircle size={14} />
              <span>Generate API Key</span>
            </button>
          </div>

          <div className="glass rounded-3xl border border-white/10 overflow-hidden shadow-xl">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] text-gray-400 uppercase tracking-wider bg-black/50 border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">Key Name</th>
                  <th className="py-3 px-4">Key Prefix</th>
                  <th className="py-3 px-4">Environment</th>
                  <th className="py-3 px-4">Rate Limit</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono">
                {apiKeys.map((k) => (
                  <tr key={k.id} className="hover:bg-white/5">
                    <td className="py-3 px-4 text-white font-sans font-bold">{k.name}</td>
                    <td className="py-3 px-4 text-cyan-300">{k.prefix || 'ssbt_...'}</td>
                    <td className="py-3 px-4 text-gray-400">{k.environment}</td>
                    <td className="py-3 px-4 text-gray-300">{k.rate_limit_per_minute} req/min</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(k.status)}`}>
                        {k.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {k.status === 'ACTIVE' && (
                        <button
                          onClick={() => handleRevokeApiKey(k.key_id)}
                          className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/20 text-[10px] font-bold transition-colors cursor-pointer"
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 6: WEBHOOKS */}
      {activeTab === 'webhooks' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <WebhookIcon size={20} className="text-purple-400" /> Enterprise Webhooks
              </h2>
              <p className="text-xs text-gray-400">Receive HMAC-SHA256 signed event streams for credential issuance, verifications, and fraud alerts.</p>
            </div>
            <button
              onClick={() => setShowAddWebhookModal(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md transition-all cursor-pointer flex items-center gap-1.5"
            >
              <PlusCircle size={14} />
              <span>Add Webhook Endpoint</span>
            </button>
          </div>

          <div className="space-y-4">
            {webhooks.map((wh) => (
              <div key={wh.id} className="glass rounded-3xl border border-white/10 p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-cyan-300 font-mono">{wh.webhook_id}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(wh.status)}`}>
                      {wh.status}
                    </span>
                  </div>
                  <div className="text-sm font-bold text-white font-mono">{wh.endpoint_url}</div>
                  <div className="flex gap-1.5 flex-wrap pt-1">
                    {wh.events.map((ev: string, idx: number) => (
                      <span key={idx} className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[10px] text-gray-300 font-mono">
                        {ev}
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => handleTestWebhook(wh.webhook_id)}
                  className="px-3.5 py-2 bg-white/5 hover:bg-white/10 text-cyan-300 border border-white/10 rounded-xl text-xs font-bold transition-colors cursor-pointer flex items-center gap-1.5"
                >
                  <Send size={13} />
                  <span>Send Test Event</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 7: MONITORING */}
      {activeTab === 'monitoring' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Bell size={20} className="text-rose-400" /> Continuous Credential Monitoring
              </h2>
              <p className="text-xs text-gray-400">Automated background integrity watches detecting candidate revocations and status modifications.</p>
            </div>
            <button
              onClick={handleRunMonitoringCheck}
              disabled={monitoringLoading}
              className="px-4 py-2 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white rounded-xl text-xs font-bold shadow-md transition-all cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
            >
              <RefreshCw size={14} className={monitoringLoading ? "animate-spin" : ""} />
              <span>Run Automated Integrity Check</span>
            </button>
          </div>

          <div className="glass rounded-3xl border border-white/10 p-6 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Radio size={15} className="text-rose-400 animate-pulse" /> Live Monitoring Alert Stream
            </h3>
            <div className="space-y-2">
              {monitoringAlerts.map((alt) => (
                <div key={alt.id} className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 flex justify-between items-center text-xs">
                  <div>
                    <div className="font-bold text-white flex items-center gap-2">
                      <AlertTriangle size={14} className="text-red-400" />
                      <span>{alt.credential_code} Status Transitioned to {alt.new_status}</span>
                    </div>
                    <p className="text-[11px] text-gray-400 mt-0.5">{alt.message}</p>
                  </div>
                  <span className="text-[10px] text-gray-500 font-mono">{new Date(alt.created_at).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 8: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <FileText size={20} className="text-cyan-400" /> Immutable Centralized Audit Trail
            </h2>
            <p className="text-xs text-gray-400">Tamper-evident logs of all credential issuances, verifications, and administrative actions.</p>
          </div>

          <div className="glass rounded-3xl border border-white/10 overflow-hidden shadow-xl">
            <div className="overflow-x-auto max-h-[550px]">
              <table className="w-full text-left text-xs">
                <thead className="text-[10px] text-gray-400 uppercase tracking-wider bg-black/50 border-b border-white/10 sticky top-0">
                  <tr>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Resource</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono">
                  {auditLogs.map((l) => (
                    <tr key={l.id} className="hover:bg-white/5">
                      <td className="py-2.5 px-4 text-gray-400 text-[11px]">{new Date(l.timestamp).toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-cyan-300 font-bold">{l.action}</td>
                      <td className="py-2.5 px-4 text-white font-sans">{l.resource} ({l.resource_id})</td>
                      <td className="py-2.5 px-4 text-gray-300 font-sans">{l.user_name || 'System'}</td>
                      <td className="py-2.5 px-4">
                        <span className="text-emerald-400 font-bold">{l.result}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 9: ISSUERS */}
      {activeTab === 'issuers' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Radio size={20} className="text-emerald-400" /> Public Issuer Directory & Trust Profiles
            </h2>
            <p className="text-xs text-gray-400">Directory of accredited institutions, public signing keys, and issuer reliability scores.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {issuers.map((iss) => (
              <div key={iss.id} className="glass rounded-3xl border border-white/10 p-6 shadow-xl space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-black text-white">{iss.name}</h3>
                    <div className="text-xs font-mono text-cyan-300">{iss.institution_code}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-400 font-mono">Issuer Trust Score</div>
                    <div className="text-xl font-black text-emerald-400 font-mono">{iss.trust_profile?.issuer_trust_score || 96.0}/100</div>
                  </div>
                </div>

                <div className="p-3 bg-black/40 rounded-xl border border-white/5 font-mono text-[11px] space-y-1">
                  <div className="flex justify-between text-gray-400">
                    <span>Key Fingerprint:</span>
                    <span className="text-gray-300">{iss.key_fingerprint || 'E4:13:93...'}</span>
                  </div>
                  <div className="flex justify-between text-gray-400">
                    <span>Total Issued:</span>
                    <span className="text-white font-bold">{iss.total_credentials} credentials</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: CREATE USER */}
      {showAddUserModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <form onSubmit={handleCreateUser} className="glass rounded-3xl border border-white/15 p-6 sm:p-8 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-white/10">
              <h3 className="text-lg font-black text-white flex items-center gap-2">
                <UserPlus size={18} className="text-indigo-400" /> Create Platform User Account
              </h3>
              <button type="button" onClick={() => setShowAddUserModal(false)} className="text-gray-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1">Full Name</label>
              <input
                type="text"
                required
                value={userForm.name}
                onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                placeholder="e.g. Dr. Rajesh Kumar / Sarah Jenkins"
                className="w-full px-3.5 py-2.5 bg-black/50 border border-white/15 focus:border-indigo-500 rounded-xl text-white text-xs outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1">Email Address (Login Username)</label>
              <input
                type="email"
                required
                value={userForm.email}
                onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                placeholder="user@organization.com"
                className="w-full px-3.5 py-2.5 bg-black/50 border border-white/15 focus:border-indigo-500 rounded-xl text-white text-xs font-mono outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1">Account Password</label>
              <input
                type="password"
                required
                value={userForm.password}
                onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                placeholder="••••••••••••"
                className="w-full px-3.5 py-2.5 bg-black/50 border border-white/15 focus:border-indigo-500 rounded-xl text-white text-xs font-mono outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1">User Role</label>
              <select
                value={userForm.role}
                onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-black/50 border border-white/15 rounded-xl text-xs text-white outline-none"
              >
                {user?.role === 'SUPER_ADMIN' && <option value="SUPER_ADMIN">Super Admin (Platform Root Authority)</option>}
                <option value="ORGANIZATION_ADMIN">Organization Admin (University / Corporate Tenant)</option>
                <option value="CREDENTIAL_ISSUER">Credential Issuer (Authorized Digital Signer)</option>
                <option value="VERIFICATION_OFFICER">Verification Officer / Recruiter</option>
                <option value="AUDITOR">Compliance Auditor (Assurance & Review)</option>
              </select>
            </div>

            {user?.role === 'SUPER_ADMIN' && (
              <div>
                <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-1">Assign to Organization Tenant</label>
                <select
                  value={userForm.organization_id}
                  onChange={(e) => setUserForm({ ...userForm, organization_id: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-black/50 border border-white/15 rounded-xl text-xs text-white outline-none"
                >
                  <option value="">-- Independent / Platform-Wide --</option>
                  {orgs.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name} ({o.institution_code})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-3 border-t border-white/10">
              <button
                type="button"
                onClick={() => setShowAddUserModal(false)}
                className="px-4 py-2 text-xs text-gray-400 hover:text-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 cursor-pointer"
              >
                Create Account
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL: RESET DATABASE TO 0 */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass rounded-3xl border border-red-500/40 p-6 sm:p-8 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-red-400">
              <div className="p-3 rounded-2xl bg-red-500/20 border border-red-500/30">
                <AlertOctagon size={28} />
              </div>
              <div>
                <h3 className="text-lg font-black text-white">Reset Database to 0 (Clean Slate)</h3>
                <p className="text-xs text-red-300">Wipe all demo data and start fresh from scratch.</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-xs text-gray-300 space-y-2 leading-relaxed">
              <p>
                <strong>Warning:</strong> This action will permanently delete:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-[11px] text-gray-400 font-mono">
                <li>All 525+ synthetic credentials and verification dossiers</li>
                <li>All 4 demo organizations and API keys</li>
                <li>All extra demo users and fraud cases</li>
              </ul>
              <p className="text-white font-bold pt-1">
                Only ONE single root account will remain:
              </p>
              <p className="font-mono text-cyan-300 text-[11px] bg-black/40 p-2 rounded-lg border border-white/5">
                Super Admin: admin@ssbt.demo / admin123
              </p>
              <p className="text-gray-400 text-[11px]">
                You can then add your own organizations, create custom users, and issue real credentials.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowResetModal(false)}
                className="px-4 py-2 text-xs text-gray-400 hover:text-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={resettingDb}
                onClick={handleResetDatabaseToZero}
                className="px-5 py-2.5 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-red-600/30 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                {resettingDb ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                ) : (
                  <>
                    <Trash2 size={14} />
                    <span>Confirm & Reset Database to 0</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* OTHER MODALS */}
      {actionReasonModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass rounded-3xl border border-white/10 p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-black text-white">
              {actionReasonModal.type === 'revoke' ? 'Revoke Credential' : 'Reinstate Credential'}
            </h3>
            <p className="text-xs text-gray-400">
              Record mandatory compliance reason for auditing {actionReasonModal.certCode}.
            </p>
            <textarea
              required
              rows={3}
              placeholder="Provide reason for status transition..."
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
              className="w-full p-3 bg-black/40 border border-white/15 rounded-xl text-xs text-white outline-none focus:border-indigo-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setActionReasonModal(null)}
                className="px-4 py-2 rounded-xl text-xs text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => handleCredentialAction(
                  actionReasonModal.certId,
                  actionReasonModal.type === 'revoke' ? 'REVOKED' : 'ACTIVE',
                  actionReason
                )}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold"
              >
                Confirm Status Change
              </button>
            </div>
          </div>
        </div>
      )}

      {showProofModal && proofData && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass rounded-3xl border border-white/10 p-6 max-w-2xl w-full shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-white/10">
              <h3 className="text-base font-black text-white flex items-center gap-2">
                <Lock size={16} className="text-indigo-400" /> Cryptographic Integrity Proof
              </h3>
              <button onClick={() => setShowProofModal(null)} className="text-gray-400 hover:text-white">
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs max-h-[400px] overflow-y-auto pr-1">
              <div>
                <span className="text-gray-500 text-[10px] uppercase">SHA-256 Digest</span>
                <div className="p-2.5 rounded-xl bg-black/50 border border-white/5 text-cyan-300 break-all text-[11px]">
                  {proofData.document_hash}
                </div>
              </div>

              <div>
                <span className="text-gray-500 text-[10px] uppercase">RSA-PSS Digital Signature (Base64)</span>
                <div className="p-2.5 rounded-xl bg-black/50 border border-white/5 text-indigo-300 break-all text-[10px]">
                  {proofData.digital_signature}
                </div>
              </div>

              <div>
                <span className="text-gray-500 text-[10px] uppercase">Signer Public Key Fingerprint</span>
                <div className="p-2.5 rounded-xl bg-black/50 border border-white/5 text-emerald-400 text-[11px]">
                  {proofData.signer_public_key_fingerprint || proofData.key_fingerprint}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {showQrModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass rounded-3xl border border-white/10 p-6 max-w-sm w-full shadow-2xl text-center space-y-4">
            <h3 className="text-base font-black text-white">{showQrModal.certificate_id}</h3>
            <div className="p-4 bg-white rounded-2xl inline-block shadow-lg">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(`http://localhost:5173/verify/${showQrModal.qr_token}`)}`}
                alt="QR Code"
                className="w-44 h-44"
              />
            </div>
            <p className="text-xs text-gray-400 font-mono">Token: {showQrModal.qr_token}</p>
            <button
              onClick={() => setShowQrModal(null)}
              className="w-full py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-bold"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {createdKeySecret && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass rounded-3xl border border-emerald-500/40 p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-black text-white flex items-center gap-2">
              <Key size={18} className="text-emerald-400" /> API Key Generated!
            </h3>
            <p className="text-xs text-gray-300 leading-relaxed">
              Please copy your API key now. You will not be able to view it again.
            </p>
            <div className="p-3 bg-black/60 rounded-xl border border-white/10 flex items-center justify-between font-mono text-xs text-cyan-300">
              <span className="break-all">{createdKeySecret}</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(createdKeySecret);
                  showToast("API Key copied to clipboard!");
                }}
                className="ml-2 p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white"
              >
                <Copy size={14} />
              </button>
            </div>
            <button
              onClick={() => setCreatedKeySecret(null)}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold"
            >
              I Have Saved My Secret Key
            </button>
          </div>
        </div>
      )}

      {resolveModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass rounded-3xl border border-white/10 p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-black text-white">Resolve Case {resolveModal.case_id}</h3>
            <div>
              <label className="block text-xs font-bold text-gray-400 mb-1">Resolution Outcome</label>
              <select
                value={resolveResolution}
                onChange={(e) => setResolveResolution(e.target.value)}
                className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-xl text-xs text-white outline-none"
              >
                <option value="CONFIRMED_FRAUD">Confirmed Fraud (Auto-Revoke Credential)</option>
                <option value="FALSE_POSITIVE">False Positive (Reinstate / Clear)</option>
                <option value="RESOLVED">Resolved (Administrative Note)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-400 mb-1">Compliance Notes</label>
              <textarea
                rows={3}
                value={resolveNotes}
                onChange={(e) => setResolveNotes(e.target.value)}
                placeholder="Document resolution evidence and findings..."
                className="w-full p-3 bg-black/40 border border-white/15 rounded-xl text-xs text-white outline-none"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setResolveModal(null)} className="px-4 py-2 text-xs text-gray-400 hover:text-white">
                Cancel
              </button>
              <button
                onClick={handleResolveCase}
                className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white rounded-xl text-xs font-bold shadow-md"
              >
                Submit Resolution
              </button>
            </div>
          </div>
        </div>
      )}

      {showAddKeyModal && !createdKeySecret && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateApiKey} className="glass rounded-3xl border border-white/10 p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-black text-white">Generate Developer API Key</h3>
            <div>
              <label className="block text-xs font-bold text-gray-400 mb-1">Application Name</label>
              <input
                type="text"
                required
                value={keyForm.name}
                onChange={(e) => setKeyForm({ ...keyForm, name: e.target.value })}
                className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-xl text-xs text-white outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-400 mb-1">Environment</label>
              <select
                value={keyForm.environment}
                onChange={(e) => setKeyForm({ ...keyForm, environment: e.target.value })}
                className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-xl text-xs text-white outline-none"
              >
                <option value="PRODUCTION">Production (ssbt_live_...)</option>
                <option value="TEST">Sandbox Test (ssbt_test_...)</option>
              </select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAddKeyModal(false)} className="px-4 py-2 text-xs text-gray-400 hover:text-white">
                Cancel
              </button>
              <button type="submit" className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold">
                Generate Key
              </button>
            </div>
          </form>
        </div>
      )}

      {showAddWebhookModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateWebhook} className="glass rounded-3xl border border-white/10 p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-black text-white">Register Webhook Endpoint</h3>
            <div>
              <label className="block text-xs font-bold text-gray-400 mb-1">Target HTTPS Endpoint</label>
              <input
                type="url"
                required
                value={webhookForm.endpoint_url}
                onChange={(e) => setWebhookForm({ ...webhookForm, endpoint_url: e.target.value })}
                className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-xl text-xs text-white font-mono outline-none"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAddWebhookModal(false)} className="px-4 py-2 text-xs text-gray-400 hover:text-white">
                Cancel
              </button>
              <button type="submit" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold">
                Save Webhook
              </button>
            </div>
          </form>
        </div>
      )}

      {showAddOrgModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateOrganization} className="glass rounded-3xl border border-white/10 p-6 max-w-md w-full shadow-2xl space-y-3">
            <h3 className="text-lg font-black text-white">Onboard New Organization Tenant</h3>
            <div>
              <label className="block text-[10px] font-bold text-gray-400 uppercase">Organization Name</label>
              <input
                type="text"
                required
                value={orgForm.name}
                onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                className="w-full px-3 py-1.5 bg-black/40 border border-white/15 rounded-xl text-xs text-white outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-gray-400 uppercase">Tenant Code</label>
              <input
                type="text"
                required
                placeholder="e.g. STANFORD_01"
                value={orgForm.institution_code}
                onChange={(e) => setOrgForm({ ...orgForm, institution_code: e.target.value.toUpperCase() })}
                className="w-full px-3 py-1.5 bg-black/40 border border-white/15 rounded-xl text-xs text-white font-mono outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-gray-400 uppercase">Organization Type</label>
              <select
                value={orgForm.organization_type}
                onChange={(e) => setOrgForm({ ...orgForm, organization_type: e.target.value })}
                className="w-full px-3 py-1.5 bg-black/40 border border-white/15 rounded-xl text-xs text-white outline-none"
              >
                <option value="UNIVERSITY">University / Higher Ed</option>
                <option value="TRAINING_INSTITUTE">Training Institute</option>
                <option value="CORPORATION">Corporation / Employer</option>
                <option value="CERTIFICATION_BODY">Certification Body</option>
              </select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAddOrgModal(false)} className="px-4 py-2 text-xs text-gray-400 hover:text-white">
                Cancel
              </button>
              <button type="submit" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold">
                Create Tenant
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}
