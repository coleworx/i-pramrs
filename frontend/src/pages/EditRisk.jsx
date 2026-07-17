import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, Info } from 'lucide-react';
import { PageHeader } from '../components/layout/PageParts';
import { Button } from '../components/ui/Button';
import { Input, Label, Textarea, Select } from '../components/ui/FormPrimitives';
import { useToast } from '../components/ui/Toast';

import { apiFetch } from '../lib/utils';
import { Spinner } from '../components/ui/Spinner';

const CATEGORIES = ['Technical', 'Schedule', 'Cost/Financial', 'Resource/Staffing', 'Scope/Requirements', 'External/Stakeholder'];

export default function EditRisk() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [projectId, setProjectId] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [form, setForm] = useState({ title: '', description: '', risk_category: '', probability: 0.5, impact: 0.5 });

  useEffect(() => {
    apiFetch(`/risks/${id}`)
      .then(d => {
        setProjectId(d.risk.project_id);
        setProjectName(d.risk.project_name);
        setForm({
          title: d.risk.title || '',
          description: d.risk.description || '',
          risk_category: d.risk.risk_category || '',
          probability: d.risk.probability ?? 0.5,
          impact: d.risk.impact ?? 0.5,
        });
      })
      .catch(() => {
        toast({ message: 'Risk not found', type: 'error' });
        navigate('/projects');
      })
      .finally(() => setLoading(false));
  }, [id, navigate, toast]);

  const set = k => v => setForm(p => ({ ...p, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.risk_category) { toast({ message: 'Please select a risk category.', type: 'error' }); return; }
    setSaving(true);
    try {
      await apiFetch(`/risks/${id}`, {
        method: 'PUT',
        body: JSON.stringify(form),
      });
      toast({ message: 'Risk updated and re-classified successfully!', type: 'success' });
      navigate(`/risks/${id}`);
    } catch (err) {
      toast({ message: err.message || 'Failed to update risk', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;

  return (
    <div className="animate-fade-in max-w-2xl">
      <PageHeader
        title="Edit Risk"
        description={`Update and re-classify risk details`}
        breadcrumbs={[
          { label: 'Projects', href: '/projects' },
          { label: projectName, href: `/projects/${projectId}` },
          { label: form.title, href: `/risks/${id}` },
          { label: 'Edit Risk' },
        ]}
      />

      {/* Info callout */}
      <div className="flex gap-3 p-4 rounded-lg border border-primary/20 bg-primary/5 text-sm text-foreground mb-6">
        <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
        <p className="text-muted-foreground leading-relaxed">
          <strong className="text-foreground">Note:</strong> Editing the risk's description, category, probability, or impact will automatically trigger an AI re-classification of the risk's severity and update the recommended mitigation strategies.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <Label htmlFor="title">Risk Title <span className="text-destructive">*</span></Label>
          <Input id="title" placeholder="e.g. ZESCO load shedding affecting server uptime" value={form.title} onChange={e => set('title')(e.target.value)} required />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="desc">
            Risk Description <span className="text-destructive">*</span>
            <span className="text-muted-foreground font-normal ml-1 text-xs">(primary ML input)</span>
          </Label>
          <Textarea id="desc" rows={4} placeholder="Describe what could go wrong…" value={form.description} onChange={e => set('description')(e.target.value)} required className="min-h-[100px]" />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="cat">Risk Category <span className="text-destructive">*</span></Label>
          <Select id="cat" value={form.risk_category} onChange={e => set('risk_category')(e.target.value)} required>
            <option value="">— Select category —</option>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </Select>
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
          <Button type="submit" disabled={saving} className="sm:min-w-[160px]">
            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
            {saving ? 'Saving…' : 'Save Changes'}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
