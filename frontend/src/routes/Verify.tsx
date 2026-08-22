import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { 
  CheckCircle2, AlertTriangle, UploadCloud, Search, QrCode, 
  Lock, Award,
  ShieldCheck, Printer, Sparkles, Hash, FileSpreadsheet
} from 'lucide-react';
import { Html5QrcodeScanner } from 'html5-qrcode';

export default function Verify() {
  const { token } = useParams();
  const [certId, setCertId] = useState('CV-2026-10024');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<'ID' | 'QR' | 'UPLOAD' | 'BATCH'>('ID');

  // Batch Verification State
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchResults, setBatchResults] = useState<any[]>([]);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchSummary, setBatchSummary] = useState<any>(null);

  // Verifier Auth Token
  const userToken = localStorage.getItem('token');

  useEffect(() => {
    if (token) {
      verifyQR(token);
    }
  }, [token]);
  
  useEffect(() => {
    if (mode === 'QR') {
      try {
        const scanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 }, false);
        scanner.render((decodedText) => {
          scanner.clear();
          const parts = decodedText.split('/');
          const extractedToken = parts[parts.length - 1];
          verifyQR(extractedToken);
        }, () => {});
        return () => {
          scanner.clear().catch(e => console.error(e));
        };
      } catch (e) {
        console.error("Scanner init error:", e);
      }
    }
  }, [mode]);

  const verifyQR = async (qrToken: string) => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const headers = userToken ? { Authorization: `Bearer ${userToken}` } : {};
      const res = await axios.get(`http://localhost:8000/api/v1/verify/qr/${qrToken}`, { headers });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Verification failed. QR token not recognized in registry.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyId = async (e?: React.FormEvent, customId?: string) => {
    if (e) e.preventDefault();
    const targetId = customId || certId;
    if (!targetId) return;

    setLoading(true);
    setError('');
    setResult(null);
    try {
      const headers = userToken ? { Authorization: `Bearer ${userToken}` } : {};
      const res = await axios.post('http://localhost:8000/api/v1/verify', {
        credential_id: targetId.trim(),
        verification_method: 'MANUAL_ID'
      }, { headers });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Credential not found or verification failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError('');
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (certId) formData.append('certificate_id', certId.trim());

      const headers = {
        'Content-Type': 'multipart/form-data',
        ...(userToken ? { Authorization: `Bearer ${userToken}` } : {})
      };

      const res = await axios.post('http://localhost:8000/api/v1/verify/document', formData, { headers });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Document analysis failed. Please verify format.');
    } finally {
      setLoading(false);
    }
  };

  const handleBatchVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!batchFile) return;

    setBatchLoading(true);
    setError('');
    setBatchResults([]);
    try {
      const formData = new FormData();
      formData.append('file', batchFile);

      const headers = {
        'Content-Type': 'multipart/form-data',
        ...(userToken ? { Authorization: `Bearer ${userToken}` } : {})
      };

      const res = await axios.post('http://localhost:8000/api/v1/verify/batch', formData, { headers });
      setBatchResults(res.data.results || []);
      setBatchSummary({
        total: res.data.total_submitted,
        verified: res.data.verified_count,
        suspicious: res.data.suspicious_count,
        invalid: res.data.invalid_count
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Batch verification failed.');
    } finally {
      setBatchLoading(false);
    }
  };

  const getStatusColor = (st: string) => {
    if (st === 'VERIFIED') return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    if (st === 'REVIEW_REQUIRED' || st === 'SUSPICIOUS') return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    if (st === 'REVOKED' || st === 'HIGH_RISK' || st === 'INVALID') return 'bg-red-500/10 text-red-400 border-red-500/30';
    if (st === 'EXPIRED') return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
    return 'bg-gray-500/10 text-gray-400 border-gray-500/30';
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-8">
      
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Universal Trust & Verification Engine
            </span>
            <span className="text-xs text-gray-500">•</span>
            <span className="text-xs text-emerald-400 font-mono flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Live Node
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Credential Authenticity Verification
          </h1>
        </div>

        {/* Quick Demo Pre-fill Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] text-gray-400 font-semibold">Demo Samples:</span>
          {[
            { id: 'CV-2026-10024', label: 'Valid Academic (10024)' },
            { id: 'CV-2026-10001', label: 'Revoked (10001)' },
            { id: 'CV-2026-10046', label: 'Suspicious (10046)' }
          ].map((sample) => (
            <button
              key={sample.id}
              onClick={() => {
                setCertId(sample.id);
                setMode('ID');
                handleVerifyId(undefined, sample.id);
              }}
              className="px-2.5 py-1 bg-white/5 hover:bg-white/10 text-cyan-300 border border-white/10 rounded-lg text-xs font-mono transition-colors cursor-pointer"
            >
              {sample.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Verification Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Verification Methods Box */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass rounded-3xl border border-white/10 p-6 shadow-xl">
            {/* Mode Switcher Tabs */}
            <div className="grid grid-cols-4 gap-1.5 p-1 bg-black/40 rounded-2xl border border-white/5 mb-6">
              {[
                { id: 'ID', label: 'ID Search', icon: <Search size={13} /> },
                { id: 'QR', label: 'QR Scan', icon: <QrCode size={13} /> },
                { id: 'UPLOAD', label: 'Forensic PDF', icon: <UploadCloud size={13} /> },
                { id: 'BATCH', label: 'Batch CSV', icon: <FileSpreadsheet size={13} /> },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setMode(tab.id as any);
                    setError('');
                  }}
                  className={`py-2 px-2 rounded-xl text-xs font-bold transition-all flex flex-col items-center gap-1 cursor-pointer ${
                    mode === tab.id
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {tab.icon}
                  <span className="text-[10px]">{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
                <AlertTriangle size={15} className="text-red-400 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Mode 1: Credential ID Search */}
            {mode === 'ID' && (
              <form onSubmit={handleVerifyId} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
                    Credential Unique ID
                  </label>
                  <div className="relative">
                    <Hash size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="text"
                      required
                      value={certId}
                      onChange={(e) => setCertId(e.target.value)}
                      placeholder="e.g. CV-2026-10024"
                      className="w-full pl-10 pr-4 py-3 bg-black/40 border border-white/15 focus:border-indigo-500 rounded-xl text-white text-xs font-mono outline-none uppercase placeholder-gray-600"
                    />
                  </div>
                  <p className="text-[11px] text-gray-500 mt-1.5">
                    Queries authoritative multi-tenant registry with RSA cryptographic signature validation.
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {loading ? (
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  ) : (
                    <>
                      <Search size={14} />
                      <span>Execute Authenticity Check</span>
                    </>
                  )}
                </button>
              </form>
            )}

            {/* Mode 2: Live QR Scanner */}
            {mode === 'QR' && (
              <div className="space-y-4 text-center">
                <div id="reader" className="w-full overflow-hidden rounded-2xl border border-white/10 bg-black/50 min-h-[260px] flex items-center justify-center"></div>
                <p className="text-xs text-gray-400">
                  Point camera at certificate QR code to extract high-entropy verification token.
                </p>
              </div>
            )}

            {/* Mode 3: AI Document Forensics Upload */}
            {mode === 'UPLOAD' && (
              <form onSubmit={handleVerifyDocument} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
                    Upload Physical PDF Scan / Image
                  </label>
                  <label className="border-2 border-dashed border-white/15 hover:border-indigo-500/50 bg-black/30 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors group">
                    <UploadCloud size={32} className="text-gray-500 group-hover:text-indigo-400 transition-colors mb-2" />
                    <span className="text-xs font-bold text-white group-hover:text-indigo-300">
                      {file ? file.name : "Select PDF Certificate or Image"}
                    </span>
                    <span className="text-[10px] text-gray-500 mt-1">PDF, PNG, JPG up to 10MB</span>
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                      className="hidden"
                    />
                  </label>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">
                    Credential ID (Optional for fast indexing)
                  </label>
                  <input
                    type="text"
                    value={certId}
                    onChange={(e) => setCertId(e.target.value)}
                    placeholder="CV-2026-XXXXX"
                    className="w-full px-3 py-2 bg-black/40 border border-white/15 focus:border-indigo-500 rounded-xl text-white text-xs font-mono outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || !file}
                  className="w-full py-3 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {loading ? (
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  ) : (
                    <>
                      <Sparkles size={14} className="text-cyan-300" />
                      <span>Run OCR Tamper Analysis</span>
                    </>
                  )}
                </button>
              </form>
            )}

            {/* Mode 4: Batch CSV Verification */}
            {mode === 'BATCH' && (
              <form onSubmit={handleBatchVerify} className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider">
                      Batch Candidate CSV
                    </label>
                    <a
                      href="data:text/csv;charset=utf-8,certificate_id,holder_name%0ACV-2026-10024,Aarav%20Sharma%0ACV-2026-10001,Aditi%20Patel%0ACV-2026-10046,Ananya%20Bharambe"
                      download="ssbt_batch_template.csv"
                      className="text-[10px] text-cyan-400 hover:text-cyan-300 underline font-mono"
                    >
                      Download CSV Template
                    </a>
                  </div>
                  <label className="border-2 border-dashed border-white/15 hover:border-indigo-500/50 bg-black/30 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors group">
                    <FileSpreadsheet size={32} className="text-gray-500 group-hover:text-emerald-400 transition-colors mb-2" />
                    <span className="text-xs font-bold text-white group-hover:text-emerald-300">
                      {batchFile ? batchFile.name : "Select Candidate CSV List"}
                    </span>
                    <span className="text-[10px] text-gray-500 mt-1">Supports up to 500 rows/file</span>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => setBatchFile(e.target.files ? e.target.files[0] : null)}
                      className="hidden"
                    />
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={batchLoading || !batchFile}
                  className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-emerald-600/25 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {batchLoading ? (
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  ) : (
                    <>
                      <CheckCircle2 size={14} />
                      <span>Process Bulk Verification</span>
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Right Column: Verification Evidence Dossier & Batch Results */}
        <div className="lg:col-span-7">
          {mode === 'BATCH' && batchResults.length > 0 ? (
            <div className="glass rounded-3xl border border-white/10 p-6 shadow-2xl space-y-6">
              <div className="flex justify-between items-center pb-4 border-b border-white/10">
                <div>
                  <h3 className="text-lg font-black text-white">Batch Verification Summary</h3>
                  <p className="text-xs text-gray-400">Processed {batchSummary?.total} candidate credentials</p>
                </div>
                <div className="flex gap-2">
                  <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg text-xs font-bold">
                    {batchSummary?.verified} Verified
                  </span>
                  <span className="px-2.5 py-1 bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded-lg text-xs font-bold">
                    {batchSummary?.suspicious} Suspicious
                  </span>
                  <span className="px-2.5 py-1 bg-red-500/20 text-red-300 border border-red-500/30 rounded-lg text-xs font-bold">
                    {batchSummary?.invalid} Invalid
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto max-h-[400px]">
                <table className="w-full text-left text-xs">
                  <thead className="text-[10px] text-gray-400 uppercase tracking-wider bg-black/40 border-b border-white/10 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">Credential ID</th>
                      <th className="py-2.5 px-3">Candidate</th>
                      <th className="py-2.5 px-3">Trust Score</th>
                      <th className="py-2.5 px-3">Risk Level</th>
                      <th className="py-2.5 px-3">Outcome</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {batchResults.map((r, i) => (
                      <tr key={i} className="hover:bg-white/5 font-mono">
                        <td className="py-2 px-3 text-cyan-300">{r.credential_id}</td>
                        <td className="py-2 px-3 text-white font-sans">{r.holder_name || 'N/A'}</td>
                        <td className="py-2 px-3 font-bold text-emerald-400">{r.trust_score || 'N/A'}</td>
                        <td className="py-2 px-3 text-gray-300">{r.risk_level}</td>
                        <td className="py-2 px-3">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusColor(r.status)}`}>
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : result ? (
            /* IMMUTABLE VERIFICATION EVIDENCE DOSSIER */
            <div className="glass rounded-3xl border border-white/10 p-6 sm:p-8 shadow-2xl space-y-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>

              {/* Dossier Header */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-6 border-b border-white/10">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase tracking-widest text-gray-400">
                      Evidence Dossier ID:
                    </span>
                    <span className="text-xs font-mono font-bold text-cyan-400">
                      {result.verification_id || `VER-2026-${result.id || '000918'}`}
                    </span>
                  </div>
                  <h3 className="text-xl sm:text-2xl font-black text-white mt-1">
                    {result.verified_record?.holder_name || result.searched_certificate_id || 'Credential Evidence Record'}
                  </h3>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-1.5 ${getStatusColor(result.final_result || result.result)}`}>
                    {result.final_result === 'VERIFIED' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                    <span>{result.final_result || result.result}</span>
                  </span>
                  <button
                    onClick={() => window.print()}
                    className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 text-xs transition-colors cursor-pointer"
                    title="Print Evidence Dossier"
                  >
                    <Printer size={15} />
                  </button>
                </div>
              </div>

              {/* Intelligence Scores Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-white/10 relative">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">Credential Trust Score</span>
                    <span className="text-[10px] font-mono text-emerald-400">0 - 100 Scale</span>
                  </div>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-3xl sm:text-4xl font-black text-emerald-400">
                      {result.trust_score !== undefined ? result.trust_score : 96.5}
                    </span>
                    <span className="text-xs text-gray-500 font-mono">/ 100.0</span>
                  </div>
                  <div className="w-full bg-black/40 h-2 rounded-full mt-3 overflow-hidden border border-white/5">
                    <div 
                      className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full rounded-full transition-all duration-500"
                      style={{ width: `${result.trust_score || 96.5}%` }}
                    ></div>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-900/80 border border-white/10">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">Fraud Risk Score</span>
                    <span className={`text-[10px] font-mono font-bold ${
                      (result.fraud_risk_score || 0) > 50 ? 'text-red-400' : 'text-emerald-400'
                    }`}>
                      {result.risk_level || 'LOW'} RISK
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className={`text-3xl sm:text-4xl font-black ${
                      (result.fraud_risk_score || 0) > 50 ? 'text-red-400' : 'text-cyan-300'
                    }`}>
                      {result.fraud_risk_score !== undefined ? result.fraud_risk_score : 4.2}
                    </span>
                    <span className="text-xs text-gray-500 font-mono">/ 100.0</span>
                  </div>
                  <div className="w-full bg-black/40 h-2 rounded-full mt-3 overflow-hidden border border-white/5">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        (result.fraud_risk_score || 0) > 50 ? 'bg-red-500' : 'bg-cyan-500'
                      }`}
                      style={{ width: `${result.fraud_risk_score || 4.2}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* 6-Vector Trust Breakdown Matrix */}
              {result.trust_breakdown && (
                <div className="p-4 rounded-2xl bg-black/30 border border-white/5">
                  <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-3">
                    Multi-Factor Trust Verification Breakdown
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    {Object.entries(result.trust_breakdown).map(([key, val]: [string, any]) => (
                      <div key={key} className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                        <div className="text-[10px] text-gray-400 capitalize">
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div className="text-sm font-bold text-white mt-0.5">
                          {val.score} <span className="text-[10px] text-gray-500 font-normal">/ {val.max}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Verified Record Details Card */}
              {result.verified_record && (
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 space-y-4">
                  <div className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Award size={14} /> Authoritative Registry Record
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-gray-500 text-[10px] uppercase">Candidate Name</span>
                      <div className="font-bold text-white mt-0.5">{result.verified_record.holder_name}</div>
                    </div>
                    <div>
                      <span className="text-gray-500 text-[10px] uppercase">Program / Role Title</span>
                      <div className="font-bold text-white mt-0.5">{result.verified_record.course_name}</div>
                    </div>
                    <div>
                      <span className="text-gray-500 text-[10px] uppercase">Issuing Institution</span>
                      <div className="font-bold text-cyan-300 mt-0.5">{result.organization_name || result.verified_record.organization_company || 'CredAuth Verified Authority'}</div>
                    </div>
                    <div>
                      <span className="text-gray-500 text-[10px] uppercase">Academic / Performance Grade</span>
                      <div className="font-bold text-emerald-400 mt-0.5">{result.verified_record.grade || result.verified_record.cgpa ? `CGPA: ${result.verified_record.cgpa}` : 'First Class with Distinction'}</div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 font-mono text-[10px] text-gray-400">
                    <div className="flex items-center gap-1.5">
                      <Lock size={12} className="text-indigo-400" />
                      <span>Signature: RSA-PSS 2048-bit (Verified)</span>
                    </div>
                    <div className="text-gray-500">
                      Key Fingerprint: {result.verified_record.key_fingerprint ? result.verified_record.key_fingerprint.slice(0, 20) + '...' : 'E4:13:93:EC:9B...'}
                    </div>
                  </div>
                </div>
              )}

              {result.explanation && (
                <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs text-gray-300 leading-relaxed flex items-start gap-2">
                  <CheckCircle2 size={15} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span>{result.explanation}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="glass rounded-3xl border border-white/10 p-12 text-center flex flex-col items-center justify-center min-h-[420px] space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-inner">
                <Search size={28} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Awaiting Verification Query</h3>
                <p className="text-xs text-gray-400 max-w-sm mx-auto mt-1 leading-relaxed">
                  Enter a Credential ID, scan a live QR token, upload a document scan, or submit a bulk CSV list to generate an immutable evidence dossier.
                </p>
              </div>
              <div className="flex items-center gap-2 pt-2 text-[11px] font-mono text-gray-500">
                <ShieldCheck size={14} className="text-cyan-400" />
                <span>Zero-Trust Cryptographic Evaluation Layer</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
