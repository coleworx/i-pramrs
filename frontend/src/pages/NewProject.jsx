import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { PageHeader } from '../components/layout/PageParts';
import { Button } from '../components/ui/Button';
import { Input, Label, Textarea, Select } from '../components/ui/FormPrimitives';
import { useToast } from '../components/ui/Toast';
import { apiFetch } from '../lib/utils';

const SECTORS   = ['Agribusiness','Retail','Construction','Manufacturing','ICT/Software Services','Logistics','Hospitality','Mining Supply Chain'];
const LOCATIONS = ['Lusaka','Ndola','Kitwe','Livingstone','Chipata','Solwezi','Kabwe','Choma'];

export default function NewProject() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [form, setForm] = useState({ name: '', description: '', sector: '', location: '' });
  const [loading, setLoading] = useState(false);

  const set = k => e => setForm(p => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast({ message: 'Project name is required.', type: 'error' }); return; }
    setLoading(true);
    try {
      await apiFetch('/projects', { method: 'POST', body: JSON.stringify(form) });
      toast({ message: `Project "${form.name}" created.`, type: 'success' });
      navigate('/projects');
    } catch (err) {
      toast({ message: err.message || 'Failed to create project', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in max-w-xl">
      <PageHeader
        title="New Project"
        description="Register a new SME project for risk monitoring"
        breadcrumbs={[{ label: 'Projects', href: '/projects' }, { label: 'New Project' }]}
      />

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <Label htmlFor="proj-name">Project Name <span className="text-destructive">*</span></Label>
          <Input
            id="proj-name"
            autoFocus
            placeholder="e.g. Mobile POS Rollout – Lusaka Branch"
            value={form.name}
            onChange={set('name')}
            required
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="proj-desc">Description</Label>
          <Textarea
            id="proj-desc"
            placeholder="Brief overview of the project scope and objectives"
            value={form.description}
            onChange={set('description')}
            className="min-h-[90px]"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="proj-sector">Sector</Label>
            <Select id="proj-sector" value={form.sector} onChange={set('sector')}>
              <option value="">— Select sector —</option>
              {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="proj-location">Location</Label>
            <Select id="proj-location" value={form.location} onChange={set('location')}>
              <option value="">— Select location —</option>
              {LOCATIONS.map(l => <option key={l} value={l}>{l}</option>)}
            </Select>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <Button type="submit" disabled={loading} className="sm:min-w-[160px]">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? 'Creating…' : 'Create Project'}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
