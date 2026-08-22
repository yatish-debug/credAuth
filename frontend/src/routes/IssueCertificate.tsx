import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, Save, Lock, Award, BookOpen, User, Briefcase, 
  Cpu, Trophy, CheckCircle, Building2
} from 'lucide-react';

export default function IssueCertificate() {
  const [category, setCategory] = useState<'ACADEMIC' | 'RECRUITMENT' | 'TECHNICAL_COURSE' | 'ACHIEVEMENT'>('ACADEMIC');
  const [orgs, setOrgs] = useState<any[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  
  const [formData, setFormData] = useState({
    certificate_type: 'Bachelor Degree',
    category: 'ACADEMIC',
    holder_name: '',
    student_id: '',
    course_name: '',
    department: 'Computer Science & Engineering',
    academic_year: '2022-2026',
    marks_obtained: '',
    total_marks: '1000',
    percentage: '',
    cgpa: '',
    grade: 'First Class with Distinction',
    remarks: '',
    
    // Recruitment & Technical Domain fields
    role_designation: '',
    organization_company: '',
    skills_acquired: '',
    employment_type: 'Full-Time',
    license_number: '',
    score_or_rank: '',
    
    issue_date: new Date().toISOString().split('T')[0],
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get('http://localhost:8000/api/v1/organizations', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        setOrgs(res.data);
        if (res.data.length > 0) {
          setSelectedOrgId(String(res.data[0].id));
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchOrgs();
  }, []);

  // Change category handler
  const handleCategorySelect = (cat: 'ACADEMIC' | 'RECRUITMENT' | 'TECHNICAL_COURSE' | 'ACHIEVEMENT') => {
    setCategory(cat);
    let defaultType = 'Bachelor Degree';
    let defaultCourse = formData.course_name;
    let defaultRole = formData.role_designation;
    
    if (cat === 'RECRUITMENT') {
      defaultType = 'Experience Certificate';
      defaultCourse = 'Software Engineering';
      defaultRole = 'Senior Security Engineer';
    } else if (cat === 'TECHNICAL_COURSE') {
      defaultType = 'Professional Certification';
      defaultCourse = 'Cloud & Cybersecurity Architect';
    } else if (cat === 'ACHIEVEMENT') {
      defaultType = 'Hackathon Winner Award';
      defaultCourse = 'National AI & Cybersecurity Hackathon';
    } else {
      defaultType = 'Bachelor Degree';
      defaultCourse = 'B.Tech in Computer Engineering';
    }

    setFormData(prev => ({
      ...prev,
      category: cat,
      certificate_type: defaultType,
      course_name: defaultCourse,
      role_designation: defaultRole
    }));
  };

  const handleMarksChange = (obtained: string, total: string) => {
    const ob = parseFloat(obtained);
    const tot = parseFloat(total);
    let pct = '';
    let autoCgpa = '';
    if (!isNaN(ob) && !isNaN(tot) && tot > 0) {
      const calculatedPct = (ob / tot) * 100;
      pct = calculatedPct.toFixed(2);
      autoCgpa = (calculatedPct / 9.5).toFixed(2);
    }
    setFormData(prev => ({
      ...prev,
      marks_obtained: obtained,
      total_marks: total,
      percentage: pct,
      cgpa: prev.cgpa || autoCgpa
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      const payload: any = {
        ...formData,
        category: category,
        organization_id: selectedOrgId ? parseInt(selectedOrgId) : null,
        marks_obtained: formData.marks_obtained ? parseFloat(formData.marks_obtained) : null,
        total_marks: formData.total_marks ? parseFloat(formData.total_marks) : null,
        percentage: formData.percentage ? parseFloat(formData.percentage) : null,
        cgpa: formData.cgpa ? parseFloat(formData.cgpa) : null,
        issue_date: new Date(formData.issue_date).toISOString()
      };
      
      await axios.post('http://localhost:8000/api/v1/certificates', payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to issue certificate.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-10 px-4 sm:px-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/dashboard')} className="p-2 hover:bg-white/10 rounded-xl transition-colors cursor-pointer">
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-2">
            Issue Multi-Domain Cryptographic Credential
          </h1>
          <p className="text-gray-400 text-sm">
            Issue tamper-proof certificates across Academic Degrees, Corporate Recruitment & Employment, Technical Courses, and Hackathons.
          </p>
        </div>
      </div>

      {/* ISSUING ORGANIZATION SELECTION (For Super Admin or Multi-Tenant Users) */}
      {orgs.length > 0 && (
        <div className="mb-6 glass rounded-2xl border border-white/10 p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="flex items-center gap-2">
            <Building2 size={18} className="text-cyan-400" />
            <div>
              <div className="text-xs font-bold text-white">Issuing Organization Authority</div>
              <div className="text-[11px] text-gray-400">Cryptographic RSA-PSS signature will be generated using this tenant keypair</div>
            </div>
          </div>
          <select
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            className="w-full sm:w-auto px-4 py-2 bg-black/50 border border-white/15 focus:border-indigo-500 rounded-xl text-xs font-bold text-white outline-none"
          >
            {orgs.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name} ({o.institution_code})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* DOMAIN CATEGORY SELECTOR TABS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        <button
          type="button"
          onClick={() => handleCategorySelect('ACADEMIC')}
          className={`p-4 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
            category === 'ACADEMIC'
              ? 'bg-indigo-950/60 border-indigo-500 shadow-lg shadow-indigo-500/20 scale-[1.02]'
              : 'glass border-white/10 hover:border-white/20 hover:bg-white/5 opacity-70'
          }`}
        >
          <div className="flex justify-between items-center mb-2">
            <BookOpen className="text-indigo-400" size={24} />
            {category === 'ACADEMIC' && <CheckCircle size={16} className="text-indigo-400" />}
          </div>
          <div>
            <div className="text-sm font-bold text-white">Academic & Degrees</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Degrees, Diplomas, CGPA, Grades</div>
          </div>
        </button>

        <button
          type="button"
          onClick={() => handleCategorySelect('RECRUITMENT')}
          className={`p-4 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
            category === 'RECRUITMENT'
              ? 'bg-blue-950/60 border-blue-500 shadow-lg shadow-blue-500/20 scale-[1.02]'
              : 'glass border-white/10 hover:border-white/20 hover:bg-white/5 opacity-70'
          }`}
        >
          <div className="flex justify-between items-center mb-2">
            <Briefcase className="text-blue-400" size={24} />
            {category === 'RECRUITMENT' && <CheckCircle size={16} className="text-blue-400" />}
          </div>
          <div>
            <div className="text-sm font-bold text-white">Recruitment & Jobs</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Experience, Internships, Offers</div>
          </div>
        </button>

        <button
          type="button"
          onClick={() => handleCategorySelect('TECHNICAL_COURSE')}
          className={`p-4 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
            category === 'TECHNICAL_COURSE'
              ? 'bg-cyan-950/60 border-cyan-500 shadow-lg shadow-cyan-500/20 scale-[1.02]'
              : 'glass border-white/10 hover:border-white/20 hover:bg-white/5 opacity-70'
          }`}
        >
          <div className="flex justify-between items-center mb-2">
            <Cpu className="text-cyan-400" size={24} />
            {category === 'TECHNICAL_COURSE' && <CheckCircle size={16} className="text-cyan-400" />}
          </div>
          <div>
            <div className="text-sm font-bold text-white">Technical Courses</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Cloud, AI, DevOps, Badges</div>
          </div>
        </button>

        <button
          type="button"
          onClick={() => handleCategorySelect('ACHIEVEMENT')}
          className={`p-4 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
            category === 'ACHIEVEMENT'
              ? 'bg-purple-950/60 border-purple-500 shadow-lg shadow-purple-500/20 scale-[1.02]'
              : 'glass border-white/10 hover:border-white/20 hover:bg-white/5 opacity-70'
          }`}
        >
          <div className="flex justify-between items-center mb-2">
            <Trophy className="text-amber-400" size={24} />
            {category === 'ACHIEVEMENT' && <CheckCircle size={16} className="text-amber-400" />}
          </div>
          <div>
            <div className="text-sm font-bold text-white">Awards & Hackathons</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Competitions, Trophies, Merit</div>
          </div>
        </button>
      </div>

      <div className="glass p-6 sm:p-8 rounded-2xl border border-white/10 shadow-2xl">
        {error && <div className="p-4 bg-red-500/10 text-red-400 border border-red-500/20 rounded-xl mb-6 text-sm">{error}</div>}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* SECTION 1: Recipient / Candidate Profile */}
          <div className="p-4 bg-black/40 rounded-xl border border-white/10 space-y-4">
            <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
              <User size={15} /> 1. Recipient / Candidate Profile
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-gray-300">
                  {category === 'RECRUITMENT' ? 'Candidate / Employee Full Name *' : 'Recipient Full Name *'}
                </label>
                <input 
                  type="text" 
                  required
                  value={formData.holder_name}
                  onChange={e => setFormData({...formData, holder_name: e.target.value})}
                  placeholder="e.g. Yatish Hemant Bharambe"
                  className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-300">
                  {category === 'RECRUITMENT' ? 'Employee / Candidate ID *' : 
                   category === 'TECHNICAL_COURSE' ? 'Candidate ID / Exam ID *' : 
                   category === 'ACHIEVEMENT' ? 'Participant / Team ID *' : 'Student PRN / Roll Number *'}
                </label>
                <input 
                  type="text" 
                  required
                  value={formData.student_id}
                  onChange={e => setFormData({...formData, student_id: e.target.value.toUpperCase()})}
                  placeholder={category === 'RECRUITMENT' ? 'e.g. EMP-98214' : category === 'TECHNICAL_COURSE' ? 'e.g. CERT-AWS-7412' : 'e.g. PRN-202201540001'}
                  className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono outline-none focus:ring-2 focus:ring-indigo-500 text-sm uppercase"
                />
              </div>
            </div>
          </div>

          {/* SECTION 2: Domain Specific Program / Employment Details */}
          <div className="p-4 bg-black/40 rounded-xl border border-white/10 space-y-4">
            <h3 className="text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
              {category === 'RECRUITMENT' ? <Briefcase size={15} /> : category === 'TECHNICAL_COURSE' ? <Cpu size={15} /> : category === 'ACHIEVEMENT' ? <Trophy size={15} /> : <BookOpen size={15} />}
              2. {category === 'RECRUITMENT' ? 'Employment & Role Particulars' : category === 'TECHNICAL_COURSE' ? 'Technical Certification Specification' : category === 'ACHIEVEMENT' ? 'Event & Competition Details' : 'Academic Program Details'}
            </h3>

            {/* Fields for Recruitment & Employment */}
            {category === 'RECRUITMENT' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300">Document Type *</label>
                    <select 
                      value={formData.certificate_type}
                      onChange={e => setFormData({...formData, certificate_type: e.target.value})}
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    >
                      <option value="Experience Certificate">Experience Certificate</option>
                      <option value="Employment Verification Letter">Employment Verification Letter</option>
                      <option value="Internship Completion Letter">Internship Completion Letter</option>
                      <option value="Official Job Offer Letter">Official Job Offer Letter</option>
                      <option value="Relieving & Experience Letter">Relieving & Experience Letter</option>
                      <option value="Performance Merit Letter">Performance Merit Letter</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Job Title / Designation *</label>
                    <input 
                      type="text" 
                      required
                      value={formData.role_designation}
                      onChange={e => setFormData({...formData, role_designation: e.target.value, course_name: e.target.value})}
                      placeholder="e.g. Senior Security Engineer"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Company / Organization Name</label>
                    <input 
                      type="text" 
                      value={formData.organization_company}
                      onChange={e => setFormData({...formData, organization_company: e.target.value})}
                      placeholder="e.g. CredVerify Technologies Inc."
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300">Department / Team</label>
                    <input 
                      type="text" 
                      value={formData.department}
                      onChange={e => setFormData({...formData, department: e.target.value})}
                      placeholder="e.g. Cloud Security & Infrastructure"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Employment Type *</label>
                    <select 
                      value={formData.employment_type}
                      onChange={e => setFormData({...formData, employment_type: e.target.value})}
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    >
                      <option value="Full-Time Permanent">Full-Time Permanent</option>
                      <option value="Full-Time Contract">Full-Time Contract</option>
                      <option value="Software Internship">Software Internship</option>
                      <option value="Part-Time / Consultant">Part-Time / Consultant</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Tenure / Duration (Session)</label>
                    <input 
                      type="text" 
                      value={formData.academic_year}
                      onChange={e => setFormData({...formData, academic_year: e.target.value})}
                      placeholder="e.g. June 2023 - July 2026"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-300">Core Technical Competencies & Technologies</label>
                  <input 
                    type="text" 
                    value={formData.skills_acquired}
                    onChange={e => setFormData({...formData, skills_acquired: e.target.value})}
                    placeholder="e.g. Python, Kubernetes, Threat Hunting, AWS Security, SOC, FastAPI"
                    className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  />
                </div>
              </div>
            )}

            {/* Fields for Technical Certifications & Courses */}
            {category === 'TECHNICAL_COURSE' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300">Credential Type *</label>
                    <select 
                      value={formData.certificate_type}
                      onChange={e => setFormData({...formData, certificate_type: e.target.value})}
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    >
                      <option value="Professional Certification">Professional Certification</option>
                      <option value="Certified Solutions Architect">Certified Solutions Architect</option>
                      <option value="Security Specialist Credential">Security Specialist Credential</option>
                      <option value="Technical Bootcamp Graduate">Technical Bootcamp Graduate</option>
                      <option value="Skill Badge Verification">Skill Badge Verification</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Certification Name / Course *</label>
                    <input 
                      type="text" 
                      required
                      value={formData.course_name}
                      onChange={e => setFormData({...formData, course_name: e.target.value})}
                      placeholder="e.g. Certified Cloud Security Architect (CCSA)"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Exam / License Code</label>
                    <input 
                      type="text" 
                      value={formData.license_number}
                      onChange={e => setFormData({...formData, license_number: e.target.value})}
                      placeholder="e.g. AWS-SAA-C03 / CISSP-98214"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300">Core Technologies & Stack Covered</label>
                    <input 
                      type="text" 
                      value={formData.skills_acquired}
                      onChange={e => setFormData({...formData, skills_acquired: e.target.value})}
                      placeholder="e.g. Docker, Kubernetes, Terraform, Cryptography, CI/CD"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Exam Score / Percentile</label>
                    <input 
                      type="text" 
                      value={formData.score_or_rank}
                      onChange={e => setFormData({...formData, score_or_rank: e.target.value})}
                      placeholder="e.g. Score: 940/1000 (Top 2%)"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Fields for Hackathons & Awards */}
            {category === 'ACHIEVEMENT' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300">Award Type *</label>
                    <select 
                      value={formData.certificate_type}
                      onChange={e => setFormData({...formData, certificate_type: e.target.value})}
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    >
                      <option value="1st Place Winner Trophy">1st Place Winner Trophy</option>
                      <option value="Hackathon Runner-Up">Hackathon Runner-Up</option>
                      <option value="Best Innovation Award">Best Innovation Award</option>
                      <option value="Merit & Excellence Certificate">Merit & Excellence Certificate</option>
                      <option value="Speaker / Contributor Honor">Speaker / Contributor Honor</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Competition / Hackathon Name *</label>
                    <input 
                      type="text" 
                      required
                      value={formData.course_name}
                      onChange={e => setFormData({...formData, course_name: e.target.value})}
                      placeholder="e.g. National Cybersecurity & AI Hackathon 2026"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Rank / Placement Position</label>
                    <input 
                      type="text" 
                      value={formData.score_or_rank}
                      onChange={e => setFormData({...formData, score_or_rank: e.target.value})}
                      placeholder="e.g. 1st Place Gold Champion (Out of 450 Teams)"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300">Project / Track Title</label>
                    <input 
                      type="text" 
                      value={formData.department}
                      onChange={e => setFormData({...formData, department: e.target.value})}
                      placeholder="e.g. Zero-Knowledge Cryptographic Credential Registry"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Technologies Showcased</label>
                    <input 
                      type="text" 
                      value={formData.skills_acquired}
                      onChange={e => setFormData({...formData, skills_acquired: e.target.value})}
                      placeholder="e.g. Python, RSA-2048, OpenCV, FastAPI, React"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Default Academic Fields */}
            {category === 'ACADEMIC' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300">Certificate Type *</label>
                    <select 
                      value={formData.certificate_type}
                      onChange={e => setFormData({...formData, certificate_type: e.target.value})}
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    >
                      <option value="Bachelor Degree">Bachelor Degree</option>
                      <option value="Master Degree">Master Degree</option>
                      <option value="Doctorate Degree">Doctorate Degree</option>
                      <option value="Diploma">Diploma</option>
                      <option value="Professional Certification">Professional Certification</option>
                      <option value="Transcript of Marks">Transcript of Marks</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Course / Degree Major *</label>
                    <input 
                      type="text" 
                      required
                      value={formData.course_name}
                      onChange={e => setFormData({...formData, course_name: e.target.value})}
                      placeholder="e.g. B.Tech in Computer Engineering"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Department / Specialization</label>
                    <input 
                      type="text" 
                      value={formData.department}
                      onChange={e => setFormData({...formData, department: e.target.value})}
                      placeholder="e.g. Cybersecurity & AI"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-300">Academic Session / Years</label>
                    <input 
                      type="text" 
                      value={formData.academic_year}
                      onChange={e => setFormData({...formData, academic_year: e.target.value})}
                      placeholder="e.g. 2022-2026"
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-300">Issue Date *</label>
                    <input 
                      type="date" 
                      required
                      value={formData.issue_date}
                      onChange={e => setFormData({...formData, issue_date: e.target.value})}
                      className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* SECTION 3: Performance, Grades & Ratings */}
          <div className="p-4 bg-black/40 rounded-xl border border-white/10 space-y-4">
            <h3 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-2">
              <Award size={15} /> 3. Performance, Grades & Ratings
            </h3>

            {category === 'ACADEMIC' && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <label className="text-xs font-semibold text-gray-300">Marks Obtained</label>
                  <input 
                    type="number" 
                    step="0.1"
                    value={formData.marks_obtained}
                    onChange={e => handleMarksChange(e.target.value, formData.total_marks)}
                    placeholder="e.g. 892"
                    className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-white font-mono outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-300">Total Marks</label>
                  <input 
                    type="number" 
                    value={formData.total_marks}
                    onChange={e => handleMarksChange(formData.marks_obtained, e.target.value)}
                    placeholder="e.g. 1000"
                    className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-white font-mono outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-300">Percentage (%)</label>
                  <input 
                    type="number" 
                    step="0.01"
                    value={formData.percentage}
                    onChange={e => setFormData({...formData, percentage: e.target.value})}
                    placeholder="e.g. 89.20"
                    className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-cyan-300 font-mono font-bold outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-300">CGPA (out of 10)</label>
                  <input 
                    type="number" 
                    step="0.01"
                    max="10"
                    value={formData.cgpa}
                    onChange={e => setFormData({...formData, cgpa: e.target.value})}
                    placeholder="e.g. 8.92"
                    className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-amber-300 font-mono font-bold outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  />
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-gray-300">
                  {category === 'RECRUITMENT' ? 'Performance Rating / Appraisal *' :
                   category === 'TECHNICAL_COURSE' ? 'Certification Proficiency Grade *' :
                   category === 'ACHIEVEMENT' ? 'Merit Classification *' : 'Awarded Grade / Division *'}
                </label>
                <select 
                  value={formData.grade}
                  onChange={e => setFormData({...formData, grade: e.target.value})}
                  className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm font-semibold"
                >
                  <option value="First Class with Distinction">First Class with Distinction (O / A+)</option>
                  <option value="First Class / Outstanding">First Class / Outstanding (A)</option>
                  <option value="Exceeds Expectations">Exceeds Expectations (High Honors)</option>
                  <option value="Certified Professional">Certified Professional (Pass)</option>
                  <option value="Higher Second Class">Higher Second Class (B+)</option>
                  <option value="Second Class">Second Class (B)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-300">Honors / Official Recommendation Note</label>
                <input 
                  type="text" 
                  value={formData.remarks}
                  onChange={e => setFormData({...formData, remarks: e.target.value})}
                  placeholder="e.g. Highly Recommended / Dean's List / Gold Medalist"
                  className="w-full mt-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                />
              </div>
            </div>
          </div>
          
          {/* Security Notice */}
          <div className="p-4 bg-indigo-950/40 border border-indigo-500/20 rounded-xl flex items-start gap-3">
            <Lock className="text-indigo-400 shrink-0 mt-0.5" size={18} />
            <div className="text-xs text-indigo-200">
              <span className="font-bold">Cryptographic Asymmetric Binding:</span>
              <p className="text-gray-400 mt-1">
                This {category.toLowerCase()} credential will be signed using the issuing organization's RSA-2048 private key. All role, technical skill, and performance attributes will be cryptographically locked against forgery.
              </p>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 disabled:opacity-50 text-white rounded-xl font-bold transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 text-sm cursor-pointer"
          >
            <Save size={18} />
            {loading ? 'Cryptographically Signing & Generating PDF...' : `Issue & Sign ${category} Credential`}
          </button>
        </form>
      </div>
    </div>
  );
}
