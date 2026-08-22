import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ShieldCheck, Lock, Award, Briefcase, 
  Cpu, Building2, ArrowRight, CheckCircle2, 
  Sparkles, ChevronDown, Terminal,
  Activity, AlertTriangle, Zap, Server, Search
} from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();
  const [selectedDomain, setSelectedDomain] = useState<'ACADEMIC' | 'RECRUITMENT' | 'TECH' | 'AWARD'>('ACADEMIC');
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [activeCodeTab, setActiveCodeTab] = useState<'curl' | 'python' | 'node'>('curl');
  
  const [stats, setStats] = useState<{
    total_credentials: number;
    average_trust_score: number;
    total_verifications: number;
    total_organizations: number;
  }>({
    total_credentials: 0,
    average_trust_score: 0.0,
    total_verifications: 0,
    total_organizations: 0
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/v1/dashboard/public-stats');
        setStats(res.data);
      } catch (err) {
        console.error("Failed to load public stats:", err);
      }
    };
    fetchStats();
  }, []);

  const domains = [
    {
      id: 'ACADEMIC',
      title: 'Academic & Higher Education',
      icon: <Award size={20} />,
      color: 'from-blue-500 to-indigo-600',
      badgeColor: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      tagline: 'Degrees, Diplomas & Marksheets',
      description: 'Issue and verify university degrees, semester grade cards, and official transcripts with student roll numbers, CGPA, and department validation.',
      metrics: ['Roll No / PRN Tracking', 'CGPA & Percentage Validation', 'Dean Digital Signature', 'University Key Fingerprint']
    },
    {
      id: 'RECRUITMENT',
      title: 'Corporate Recruitment & HR',
      icon: <Briefcase size={20} />,
      color: 'from-emerald-500 to-teal-600',
      badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      tagline: 'Experience Letters & Relieving Deeds',
      description: 'Eliminate moonlighting and forged experience certificates. Verify candidate job designations, employment tenure, department, appraisal ratings, and skills.',
      metrics: ['Employee ID Verification', 'Exact Tenure & Relieving Date', 'Performance Appraisal Grade', 'HR Corporate Key Stamp']
    },
    {
      id: 'TECH',
      title: 'Technical Certifications',
      icon: <Cpu size={20} />,
      color: 'from-cyan-500 to-blue-600',
      badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
      tagline: 'Cloud, Cybersecurity & Dev Badges',
      description: 'Authenticate professional certifications (AWS, Azure, Kubernetes, Security) with unique exam codes, candidate IDs, score percentiles, and verified tech stacks.',
      metrics: ['License & Exam Code Check', 'Tech Stack Verification', 'Score & Percentile Matrix', 'Authorized Testing Body Key']
    },
    {
      id: 'AWARD',
      title: 'Hackathons & Merit Awards',
      icon: <Sparkles size={20} />,
      color: 'from-amber-500 to-orange-600',
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      tagline: 'Competition Honors & Champion Trophies',
      description: 'Issue verifiable proof of achievement for hackathons, coding contests, and research conferences with rank positions, track categories, and jury signatures.',
      metrics: ['1st Place & Gold Medals', 'Project Track & Hackathon Title', 'Jury & Organizer Validation', 'Unforgeable Award Proof']
    }
  ];

  const codeSnippets = {
    curl: `curl -X POST "http://localhost:8000/api/v1/verify" \\
  -H "X-API-Key: ssbt_live_e89104fa2..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "credential_id": "CV-2026-10024",
    "verification_method": "API"
  }'`,
    python: `import requests

url = "http://localhost:8000/api/v1/verify"
headers = {"X-API-Key": "ssbt_live_e89104fa2..."}
payload = {
    "credential_id": "CV-2026-10024",
    "verification_method": "API"
}

response = requests.post(url, json=payload, headers=headers)
evidence = response.json()
print(f"Trust Score: {evidence['trust_score']}/100 | Status: {evidence['final_result']}")`,
    node: `import axios from 'axios';

const { data } = await axios.post('http://localhost:8000/api/v1/verify', {
  credential_id: 'CV-2026-10024',
  verification_method: 'API'
}, {
  headers: { 'X-API-Key': 'ssbt_live_e89104fa2...' }
});

console.log(\`Verified \${data.credential_id} - Trust Score: \${data.trust_score}\`);`
  };

  const faqs = [
    {
      q: "What is the CredAuth Credential Trust & Fraud Intelligence Platform?",
      a: "CredAuth is an enterprise B2B Credential Trust, Verification, and Fraud Intelligence Layer. It provides multi-tenant organizations with cryptographic issuance (RSA-PSS 2048-bit digital signatures, SHA-256 integrity digests), AI document tampering forensics, a modular 0-100 Trust Score engine, programmatic REST APIs, and automated continuous credential monitoring."
    },
    {
      q: "How does the Modular Trust Score (0-100) work?",
      a: "The Trust Score computes a weighted breakdown across 6 core trust vectors: Issuer Authenticity (25%), Cryptographic Signature (20%), Registry Match (20%), QR Token Validation (15%), Document Forensics (10%), and Metadata Consistency (10%). Any tampering or invalid signature is penalized immediately."
    },
    {
      q: "Can enterprises verify credentials programmatically via API?",
      a: "Yes. CredAuth provides a comprehensive REST API (/api/v1/verify, /api/v1/credentials, /api/v1/webhooks) secured by scoped API keys with rate-limiting and HMAC-SHA256 signed webhook event broadcasting."
    },
    {
      q: "How does CredAuth handle batch verification for recruiters?",
      a: "HR and background screening teams can upload CSV candidate lists to run hundreds of verifications simultaneously, producing instant verification flags, risk levels, and downloadable evidence reports."
    }
  ];

  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)] bg-slate-950 text-white overflow-hidden selection:bg-indigo-500 selection:text-white">
      
      {/* ========================================================================= */}
      {/* 1. HERO SECTION                                                           */}
      {/* ========================================================================= */}
      <section className="relative pt-20 pb-24 px-4 sm:px-6 lg:px-8 flex flex-col items-center text-center">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[750px] h-[380px] bg-gradient-to-tr from-indigo-600/25 via-cyan-500/20 to-emerald-500/20 rounded-full blur-[130px] pointer-events-none"></div>

        <div className="relative z-10 max-w-5xl mx-auto flex flex-col items-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 mb-8 shadow-lg shadow-indigo-500/10">
            <ShieldCheck size={16} className="text-cyan-400" />
            <span className="text-xs font-bold uppercase tracking-widest">
              B2B Enterprise Credential Trust & Fraud Intelligence Layer
            </span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[1.1] mb-6">
            <span className="text-white">Trust Every </span>
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-cyan-300 to-emerald-400">
              Credential.
            </span>
            <br />
            <span className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-gray-300 tracking-tight">
              Detect Every Forgery.
            </span>
          </h1>

          <p className="max-w-2xl text-gray-400 text-sm sm:text-base leading-relaxed mb-10">
            Multi-tenant infrastructure enabling universities, corporations, certification bodies, and recruiters to issue, risk-score, monitor, and audit digital credentials with RSA-PSS cryptographic proof and AI document forensics.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => navigate('/verify')}
              className="px-6 py-3.5 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white rounded-2xl font-bold text-sm shadow-xl shadow-indigo-600/25 flex items-center gap-2 transition-all cursor-pointer group"
            >
              <Search size={16} />
              <span>Launch Verification Engine</span>
              <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={() => navigate('/login')}
              className="px-6 py-3.5 bg-white/5 hover:bg-white/10 text-white border border-white/15 rounded-2xl font-bold text-sm transition-all flex items-center gap-2 cursor-pointer"
            >
              <Building2 size={16} className="text-cyan-400" />
              <span>Enter SaaS Workspace</span>
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full max-w-4xl mt-16 p-6 glass rounded-2xl border border-white/10">
            <div>
              <div className="text-2xl sm:text-3xl font-black text-white font-mono">
                {stats.total_credentials}
              </div>
              <div className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold mt-0.5">Signed Credentials</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-emerald-400 font-mono">
                {stats.total_credentials > 0 ? `${stats.average_trust_score}%` : '0.0%'}
              </div>
              <div className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold mt-0.5">Avg Trust Score</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-cyan-400 font-mono">
                {stats.total_verifications > 0 ? `${stats.total_verifications}` : '0'}
              </div>
              <div className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold mt-0.5">Total Verifications</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-black text-indigo-400 font-mono">
                {stats.total_organizations > 0 ? `${stats.total_organizations}` : '0'}
              </div>
              <div className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold mt-0.5">Organizations</div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 2. ARCHITECTURE PILLARS                                                  */}
      {/* ========================================================================= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/10">
        <div className="text-center mb-14">
          <span className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 rounded-full text-xs font-bold uppercase tracking-wider">
            Enterprise Architecture
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mt-3">
            Six Pillars of Credential Authenticity
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              title: "Modular Trust Engine (0-100)",
              desc: "Mathematical scoring evaluating issuer reputation, cryptographic integrity, registry match, and metadata consistency.",
              icon: <Activity size={22} className="text-cyan-400" />
            },
            {
              title: "RSA-PSS Asymmetric Signatures",
              desc: "Each tenant maintains an isolated 2048-bit RSA keypair. Payload hashes are signed to make forgery mathematically impossible.",
              icon: <Lock size={22} className="text-indigo-400" />
            },
            {
              title: "AI Document Forensics",
              desc: "Deep OCR vector analysis comparing physical scans against authoritative database records to detect grade, name, and date alterations.",
              icon: <Zap size={22} className="text-amber-400" />
            },
            {
              title: "Multi-Tenant Isolation",
              desc: "Strict tenant data segregation across universities, corporations, and certification bodies with granular RBAC permissions.",
              icon: <Building2 size={22} className="text-emerald-400" />
            },
            {
              title: "Continuous Monitoring & Alerts",
              desc: "Subscribers receive instant alerts via email or signed webhooks if a candidate credential is revoked, expired, or modified.",
              icon: <AlertTriangle size={22} className="text-rose-400" />
            },
            {
              title: "Developer REST API & Webhooks",
              desc: "Enterprise API keys with custom rate limiting and HMAC-SHA256 signed event streams for frictionless ATS and HRMS integration.",
              icon: <Server size={22} className="text-purple-400" />
            }
          ].map((pillar, idx) => (
            <div key={idx} className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 hover:border-indigo-500/40 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                {pillar.icon}
              </div>
              <h3 className="text-lg font-bold text-white mb-2">{pillar.title}</h3>
              <p className="text-xs text-gray-400 leading-relaxed">{pillar.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. 4-DOMAIN CREDENTIAL REGISTRY                                          */}
      {/* ========================================================================= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/10">
        <div className="text-center mb-12">
          <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 rounded-full text-xs font-bold uppercase tracking-wider">
            Multi-Domain Support
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mt-3">
            Engineered for Every Type of Credential
          </h2>
        </div>

        <div className="flex flex-wrap justify-center gap-3 mb-8">
          {domains.map((dom) => (
            <button
              key={dom.id}
              onClick={() => setSelectedDomain(dom.id as any)}
              className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
                selectedDomain === dom.id
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 border border-indigo-400/50'
                  : 'bg-white/5 hover:bg-white/10 text-gray-400 border border-white/10'
              }`}
            >
              {dom.icon}
              <span>{dom.title}</span>
            </button>
          ))}
        </div>

        {(() => {
          const dom = domains.find(d => d.id === selectedDomain)!;
          return (
            <div className="glass rounded-3xl border border-white/10 p-8 max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <div>
                <span className={`px-3 py-1 rounded-full text-[10px] font-bold border ${dom.badgeColor}`}>
                  {dom.tagline}
                </span>
                <h3 className="text-2xl font-black text-white mt-3 mb-3">{dom.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed mb-6">{dom.description}</p>
                <div className="space-y-2">
                  {dom.metrics.map((m, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-gray-300">
                      <CheckCircle2 size={15} className="text-emerald-400 flex-shrink-0" />
                      <span>{m}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-black/50 rounded-2xl border border-white/10 p-6 font-mono text-xs">
                <div className="text-[11px] text-gray-500 mb-2 border-b border-white/10 pb-2 flex justify-between">
                  <span>Canonical JSON Payload</span>
                  <span className="text-indigo-400">RSA-PSS Digest</span>
                </div>
                <pre className="text-[11px] text-cyan-300 overflow-x-auto leading-relaxed">
{`{
  "credential_id": "CV-2026-10024",
  "category": "${dom.id}",
  "holder_name": "Aarav Sharma",
  "tenant_code": "CREDAUTH_UNIV_01",
  "trust_score": 97.5,
  "status": "ACTIVE"
}`}
                </pre>
              </div>
            </div>
          );
        })()}
      </section>

      {/* ========================================================================= */}
      {/* 4. DEVELOPER API CODE PREVIEW                                            */}
      {/* ========================================================================= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto border-t border-white/10">
        <div className="text-center mb-10">
          <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 rounded-full text-xs font-bold uppercase tracking-wider">
            Developer Hub
          </span>
          <h2 className="text-3xl font-extrabold text-white tracking-tight mt-3">
            Programmatic Verification in Seconds
          </h2>
        </div>

        <div className="glass rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
          <div className="bg-black/60 px-4 py-3 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal size={15} className="text-cyan-400" />
              <span className="text-xs font-mono font-bold text-gray-300">API Integration</span>
            </div>
            <div className="flex items-center gap-2">
              {(['curl', 'python', 'node'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveCodeTab(tab)}
                  className={`px-3 py-1 rounded-lg text-[11px] font-mono font-bold uppercase transition-all cursor-pointer ${
                    activeCodeTab === tab
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6 bg-slate-950 font-mono text-xs text-indigo-300 overflow-x-auto">
            <pre>{codeSnippets[activeCodeTab]}</pre>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. FAQS                                                                  */}
      {/* ========================================================================= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto border-t border-white/10">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-extrabold text-white tracking-tight">
            Frequently Asked Questions
          </h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => (
            <div key={idx} className="glass rounded-2xl border border-white/10 overflow-hidden">
              <button
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                className="w-full p-5 text-left flex justify-between items-center text-sm font-bold text-white hover:text-indigo-300 transition-colors cursor-pointer"
              >
                <span>{faq.q}</span>
                <ChevronDown size={16} className={`text-gray-400 transition-transform ${openFaq === idx ? 'rotate-180 text-indigo-400' : ''}`} />
              </button>
              {openFaq === idx && (
                <div className="px-5 pb-5 text-xs text-gray-400 leading-relaxed border-t border-white/5 pt-3">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

    </div>
  );
}
