import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { PageHeader } from '../components/layout/PageParts';
import { Button } from '../components/ui/Button';
import { Input, Label, Textarea, Select } from '../components/ui/FormPrimitives';
import { useToast } from '../components/ui/Toast';
import { apiFetch } from '../lib/utils';
import { Spinner } from '../components/ui/Spinner';

const SECTORS   = ['Agribusiness','Retail','Construction','Manufacturing','ICT/Software Services','Logistics','Hospitality','Mining Supply Chain'];
const LOCATIONS = ['Lusaka','Ndola','Kitwe','Livingstone','Chipata','Solwezi','Kabwe','Choma'];

export default function EditProject() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [form, setForm] = useState({ name: '', description: '', sector: '', location: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiFetch(`/projects/${id}`)
      .then(d => {
        setForm({
          name: d.project.name || '',
          description: d.project.description || '',
          sector: d.project.sector || '',
          location: d.project.location || '',
        });
      })
      .catch(() => {
        toast({ message: 'Project not found', type: 'error' });
        navigate('/projects');
      })
      .finally(() => setLoading(false));
  }, [id, navigate, toast]);

  const set = k => e => setForm(p => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast({ message: 'Project name is required.', type: 'error' }); return; }
    setSaving(true);
    try {
      await apiFetch(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(form) });
      toast({ message: `Project "${form.name}" updated successfully.`, type: 'success' });
      navigate(`/projects/${id}`);
    } catch (err) {
      toast({ message: err.message || 'Failed to update project', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;

  return (
    <div className="animate-fade-in max-w-xl">
      <PageHeader
        title="Edit Project"
        description={`Update details for ${form.name}`}
        breadcrumbs={[{ label: 'Projects', href: '/projects' }, { label: form.name, href: `/projects/${id}` }, { label: 'Edit Project' }]}
      />

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <Label htmlFor="proj-name">Project Name <span className="text-destructive">*</span></Label>
          <Input
            id="proj-name"
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
