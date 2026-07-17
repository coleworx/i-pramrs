import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Plus, FileText, Trash2, FolderMinus, FolderCheck, Eye, ShieldAlert, Edit } from 'lucide-react';

import { PageHeader, EmptyState } from '../components/layout/PageParts';
import { Button } from '../components/ui/Button';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { StatusDropdown } from '../components/ui/StatusDropdown';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { Spinner } from '../components/ui/Spinner';
import { useToast } from '../components/ui/Toast';
import { apiFetch, cn } from '../lib/utils';


export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [project, setProject] = useState(null);
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [closeConfirmOpen, setCloseConfirmOpen] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [filter, setFilter] = useState('All');

  // Risk action states
  const [riskToToggle, setRiskToToggle] = useState(null);
  const [closeRiskConfirmOpen, setCloseRiskConfirmOpen] = useState(false);
  const [riskToDelete, setRiskToDelete] = useState(null);
  const [riskDeleteOpen, setRiskDeleteOpen] = useState(false);

  const load = () => {
    setLoading(true);
    apiFetch(`/projects/${id}`)
      .then(d => { setProject(d.project); setRisks(d.risks); })
      .catch(() => navigate('/projects'))
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  const handleToggle = async () => {
    setToggling(true);
    try {
      await apiFetch(`/projects/${id}/toggle-status`, { method: 'POST' });
      toast({ message: `Project ${project.status === 'Active' ? 'closed' : 'reopened'}.`, type: 'success' });
      load();
    } catch (e) { toast({ message: e.message, type: 'error' }); }
    finally { setToggling(false); }
  };

  const handleToggleClick = () => {
    if (isActive) {
      setCloseConfirmOpen(true);
    } else {
      handleToggle();
    }
  };

  const handleDelete = async () => {
    try {
      await apiFetch(`/projects/${id}/delete`, { method: 'POST' });
      toast({ message: 'Project deleted.', type: 'success' });
      navigate('/projects');
    } catch (e) { toast({ message: e.message, type: 'error' }); }
  };

  // Risk action handlers
  // Called by StatusDropdown with the newly-selected status value
  const handleRiskStatusSelect = (risk, newStatus) => {
    if (newStatus === risk.status) return;          // no-op: same status selected
    if (newStatus === 'Closed') {
      // Confirm before closing
      setRiskToToggle(risk);
      setCloseRiskConfirmOpen(true);
    } else {
      // Reopening — no confirmation needed
      toggleRiskStatus(risk.id);
    }
  };

  const toggleRiskStatus = async (riskId) => {
    try {
      await apiFetch(`/risks/${riskId}/toggle-status`, { method: 'POST' });
      toast({ message: 'Risk status updated successfully.', type: 'success' });
      load();
    } catch (e) {
      toast({ message: e.message, type: 'error' });
    } finally {
      setRiskToToggle(null);
    }
  };

  const handleRiskDelete = async () => {
    if (!riskToDelete) return;
    try {
      await apiFetch(`/risks/${riskToDelete.id}/delete`, { method: 'POST' });
      toast({ message: 'Risk deleted successfully.', type: 'success' });
      load();
    } catch (e) {
      toast({ message: e.message, type: 'error' });
    } finally {
      setRiskToDelete(null);
    }
  };



  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  if (!project) return null;

  const isActive = project.status === 'Active';

  const filteredRisks = risks.filter(r => {
    if (filter === 'Open') return r.status === 'Open';
    if (filter === 'Closed') return r.status === 'Closed';
    return true;
  });

  return (
    <div className="space-y-6 animate-fade-in">

      <PageHeader
        title={<span className="flex items-center gap-3">{project.name} <StatusBadge status={project.status} /></span>}
        description={[project.sector, project.location].filter(Boolean).join(' · ')}
        breadcrumbs={[{ label: 'Projects', href: '/projects' }, { label: project.name }]}
      />

      <div className="flex flex-wrap items-center gap-2">
        <Link to={`/risks/new/${id}`}>
          <Button size="sm"><Plus className="h-4 w-4" />Log Risk</Button>
        </Link>
        <Link to={`/projects/${id}/edit`}>
          <Button variant="outline" size="sm"><Edit className="h-4 w-4" />Edit Project</Button>
        </Link>
        {risks.length > 0 && (
          <a href={`/api/projects/${id}/pdf`} target="_blank" rel="noreferrer">
            <Button variant="outline" size="sm"><FileText className="h-4 w-4" />Export PDF</Button>
          </a>
        )}
        <Button variant={isActive ? 'warning' : 'success'} size="sm" onClick={handleToggleClick} disabled={toggling}>
          {isActive ? <><FolderMinus className="h-4 w-4" />Close Project</> : <><FolderCheck className="h-4 w-4" />Reopen</>}
        </Button>
        <Button variant="outline" size="sm" className="text-destructive border-destructive/30 hover:bg-destructive/10" onClick={() => setDeleteOpen(true)}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>


      {/* Risk Register */}
      {risks.length === 0 ? (
        <EmptyState
          icon={ShieldAlert}
          title="No risks logged yet"
          description="Log your first risk to receive an AI-powered severity classification and mitigation recommendations."
          action={<Link to={`/risks/new/${id}`}><Button><Plus className="h-4 w-4" />Log First Risk</Button></Link>}
        />
      ) : (
        <div className="rounded-xl border border-border bg-card shadow-sm overflow-visible">
          {/* Card Header with tabs */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between px-5 py-4 border-b border-border gap-3">
            <div className="flex items-center gap-2">
              <h2 className="font-display font-semibold text-sm text-foreground">Risk Register</h2>
              <span className="text-xs text-muted-foreground bg-secondary px-2 py-0.5 rounded-full">
                {filteredRisks.length} of {risks.length}
              </span>
            </div>
            
            {/* Filter Tabs */}
            <div className="flex items-center gap-1 border border-border rounded-lg p-0.5 bg-muted/30 w-fit">
              {['All', 'Open', 'Closed'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setFilter(tab)}
                  className={cn(
                    'px-3 py-1 text-xs font-medium rounded-md transition-all cursor-pointer',
                    filter === tab
                      ? 'bg-background text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {/* Mobile Card List */}
          <div className="md:hidden divide-y divide-border overflow-visible">
            {filteredRisks.map((r) => (
              <div key={r.id} className="p-4 space-y-3 overflow-visible">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-0.5">
                    <h3 className="font-display font-semibold text-foreground text-sm leading-snug">{r.title}</h3>
                    <span className="inline-block text-xs text-muted-foreground">{r.risk_category}</span>
                  </div>
                  <div className="shrink-0">
                    <StatusDropdown
                      status={r.status}
                      onSelect={(newStatus) => handleRiskStatusSelect(r, newStatus)}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 py-2 border-y border-border/40 text-xs">
                  <div>
                    <span className="text-muted-foreground block mb-0.5">P × I</span>
                    <span className="font-mono font-medium text-foreground">P:{r.probability.toFixed(2)} · I:{r.impact.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block mb-0.5">Severity</span>
                    {r.predicted_label ? <SeverityBadge severity={r.predicted_label} /> : <span className="text-muted-foreground">—</span>}
                  </div>
                  <div>
                    <span className="text-muted-foreground block mb-1">Confidence</span>
                    {r.confidence ? (
                      <span className="font-medium text-foreground">{(r.confidence * 100).toFixed(0)}%</span>
                    ) : '—'}
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-1">
                  <Link to={`/risks/${r.id}`}>
                    <Button variant="outline" size="sm" className="h-8 px-3">
                      <Eye className="h-3.5 w-3.5 mr-1 text-muted-foreground" /> View
                    </Button>
                  </Link>
                  <Link to={`/risks/${r.id}/edit`}>
                    <Button variant="outline" size="sm" className="h-8 px-3">
                      <Edit className="h-3.5 w-3.5 mr-1 text-muted-foreground" /> Edit
                    </Button>
                  </Link>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="h-8 px-3 text-destructive border-destructive/20 hover:bg-destructive/10 hover:text-destructive" 
                    onClick={() => { setRiskToDelete(r); setRiskDeleteOpen(true); }}
                  >
                    <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Desktop Table View */}
          <div className="hidden md:block overflow-visible">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  {['#', 'Risk Details', 'P × I', 'Severity', 'Confidence', 'Status', ''].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredRisks.map((r, i) => (
                  <tr key={r.id} className="hover:bg-muted/10 transition-colors">
                    <td className="px-4 py-3.5 align-middle text-muted-foreground text-xs">{i + 1}</td>
                    <td className="px-4 py-3.5 align-middle">
                      <div className="flex flex-col">
                        <span className="font-medium text-foreground text-sm leading-snug">{r.title}</span>
                        <span className="text-xs text-muted-foreground mt-0.5">{r.risk_category}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 align-middle">
                      <div className="flex items-center gap-1.5 text-xs font-mono">
                        <span className="text-muted-foreground">P:</span> {r.probability.toFixed(2)}
                        <span className="text-muted-foreground ml-0.5">I:</span> {r.impact.toFixed(2)}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 align-middle">
                      {r.predicted_label ? <SeverityBadge severity={r.predicted_label} /> : <span className="text-muted-foreground">—</span>}
                    </td>
                    <td className="px-4 py-3.5 align-middle">
                      {r.confidence ? (
                        <div className="flex items-center gap-2 min-w-[80px]">
                          <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden">
                            <div className="h-full bg-primary rounded-full" style={{ width: `${(r.confidence * 100).toFixed(0)}%` }} />
                          </div>
                          <span className="text-xs text-muted-foreground tabular-nums">{(r.confidence * 100).toFixed(0)}%</span>
                        </div>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3.5 align-middle">
                      <StatusDropdown
                        status={r.status}
                        onSelect={(newStatus) => handleRiskStatusSelect(r, newStatus)}
                      />
                    </td>
                    <td className="px-4 py-3.5 align-middle text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Link to={`/risks/${r.id}`} title="View Details">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          </Button>
                        </Link>
                        <Link to={`/risks/${r.id}/edit`} title="Edit Risk">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Edit className="h-4 w-4 text-muted-foreground" />
                          </Button>
                        </Link>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive" 
                          onClick={() => { setRiskToDelete(r); setRiskDeleteOpen(true); }}
                          title="Delete Risk"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Delete Project Confirmation */}
      <ConfirmDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDelete}
        title="Delete project?"
        description="This will permanently delete the project along with all associated risks, classifications, recommendations, and feedback. This cannot be undone."
        confirmLabel="Delete Project"
      />

      {/* Close Project Confirmation */}
      <ConfirmDialog
        open={closeConfirmOpen}
        onClose={() => setCloseConfirmOpen(false)}
        onConfirm={handleToggle}
        title="Close project?"
        description="Closing this project will automatically set all of its associated risks to Closed. You can reopen this project later if needed."
        confirmLabel="Close Project"
        confirmVariant="warning"
      />

      {/* Close Risk Confirmation */}
      <ConfirmDialog
        open={closeRiskConfirmOpen}
        onClose={() => { setCloseRiskConfirmOpen(false); setRiskToToggle(null); }}
        onConfirm={() => { if (riskToToggle) { toggleRiskStatus(riskToToggle.id); } }}
        title="Close Risk?"
        description={`Are you sure you want to close the risk "${riskToToggle?.title}"? This indicates the risk is resolved or mitigated.`}
        confirmLabel="Close Risk"
        confirmVariant="warning"
      />

      {/* Delete Risk Confirmation */}
      <ConfirmDialog
        open={riskDeleteOpen}
        onClose={() => { setRiskDeleteOpen(false); setRiskToDelete(null); }}
        onConfirm={handleRiskDelete}
        title="Delete Risk?"
        description={`Are you sure you want to permanently delete the risk "${riskToDelete?.title}"? This cannot be undone.`}
        confirmLabel="Delete Risk"
      />
    </div>
  );
}
