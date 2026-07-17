import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { Loader2, Info } from 'lucide-react';
import { PageHeader } from '../components/layout/PageParts';
import { Button } from '../components/ui/Button';
import { Input, Label, Textarea, Select } from '../components/ui/FormPrimitives';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { useToast } from '../components/ui/Toast';
import { apiFetch } from '../lib/utils';
import { Spinner } from '../components/ui/Spinner';

const CATEGORIES = ['Technical', 'Schedule', 'Cost/Financial', 'Resource/Staffing', 'Scope/Requirements', 'External/Stakeholder'];

export default function LogRisk() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', risk_category: '', probability: 0.5, impact: 0.5 });

  useEffect(() => {
    apiFetch(`/projects/${projectId}`).then(d => setProject(d.project)).catch(() => navigate('/projects'));
  }, [projectId]);

  const set = k => v => setForm(p => ({ ...p, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.risk_category) { toast({ message: 'Please select a risk category.', type: 'error' }); return; }
    setLoading(true);
    try {
      const data = await apiFetch(`/risks/new/${projectId}`, {
        method: 'POST',
        body: JSON.stringify(form),
      });
      toast({ message: 'Risk classified successfully!', type: 'success' });
      navigate(`/risks/${data.risk_id}`);
    } catch (err) {
      toast({ message: err.message || 'Failed to log risk', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  if (!project) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;

  return (
    <div className="animate-fade-in max-w-2xl">
      <PageHeader
        title="Log New Risk"
        description={`Project: ${project.name}`}
        breadcrumbs={[{ label: 'Projects', href: '/projects' }, { label: project.name, href: `/projects/${projectId}` }, { label: 'Log Risk' }]}
      />

      {/* Info callout — outside any card */}
      <div className="flex gap-3 p-4 rounded-lg border border-primary/20 bg-primary/5 text-sm text-foreground mb-6">
        <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
        <p className="text-muted-foreground leading-relaxed">
          <strong className="text-foreground">How this works:</strong> Enter your risk details below. The system will automatically classify severity using a trained Random Forest model and recommend the top 3 mitigation strategies.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <Label htmlFor="title">Risk Title <span className="text-destructive">*</span></Label>
          <Input id="title" autoFocus placeholder="e.g. ZESCO load shedding affecting server uptime" value={form.title} onChange={e => set('title')(e.target.value)} required />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="desc">
            Risk Description <span className="text-destructive">*</span>
            <span className="text-muted-foreground font-normal ml-1 text-xs">(primary ML input — be specific)</span>
          </Label>
          <Textarea id="desc" rows={4} placeholder="Describe what could go wrong, potential causes, and early warning signs…" value={form.description} onChange={e => set('description')(e.target.value)} required className="min-h-[100px]" />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="cat">Risk Category <span className="text-destructive">*</span></Label>
          <Select id="cat" value={form.risk_category} onChange={e => set('risk_category')(e.target.value)} required>
            <option value="">— Select category —</option>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </Select>
          <p className="text-xs text-muted-foreground">Based on PMI Risk Breakdown Structure (PMI, 2021)</p>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {[{ key: 'probability', label: 'Probability of Occurrence', hint: 'Low ← → High' }, { key: 'impact', label: 'Impact if it Occurs', hint: 'Minor ← → Catastrophic' }].map(({ key, label, hint }) => (
            <div key={key} className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>{label} <span className="text-xs text-muted-foreground font-normal">(0–1)</span></Label>
                <span className="font-mono text-sm font-semibold text-primary tabular-nums">{Number(form[key]).toFixed(2)}</span>
              </div>
              <input
                type="range" min="0.05" max="0.95" step="0.05"
                value={form[key]}
                onChange={e => set(key)(parseFloat(e.target.value))}
                className="w-full h-1.5 rounded-full bg-border appearance-none cursor-pointer accent-primary"
              />
              <p className="text-xs text-muted-foreground text-center">{hint}</p>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 pt-2">
          <Button type="submit" disabled={loading} className="flex-1 sm:flex-none sm:min-w-[200px]">
            {loading ? <><Loader2 className="h-4 w-4 animate-spin" />Classifying…</> : 'Classify & Get Recommendations'}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
