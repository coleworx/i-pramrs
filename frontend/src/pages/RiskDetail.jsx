import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FileText, Trash2, CheckCircle2, Send, BookOpen, Loader2, Edit } from 'lucide-react';

import { PageHeader } from '../components/layout/PageParts';
import { Button } from '../components/ui/Button';
import { SeverityBadge, StatusBadge } from '../components/ui/Badge';
import { StatusDropdown } from '../components/ui/StatusDropdown';
import { Select } from '../components/ui/FormPrimitives';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { Spinner } from '../components/ui/Spinner';
import { useToast } from '../components/ui/Toast';
import { apiFetch, SEV_DOT } from '../lib/utils';
import { cn } from '../lib/utils';

const SEV_ORDER = ['Low', 'Medium', 'High', 'Critical'];
const SEV_COLORS_BAR = { Low: 'bg-emerald-500', Medium: 'bg-amber-500', High: 'bg-orange-500', Critical: 'bg-red-500' };

export default function RiskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [closeConfirmOpen, setCloseConfirmOpen] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [feedbackLabel, setFeedbackLabel] = useState('');
  const [feedbackReason, setFeedbackReason] = useState('');
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  const load = () => {
    setLoading(true);
    apiFetch(`/risks/${id}`).then(setData).catch(() => navigate('/projects')).finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  const handleToggle = async () => {
    setToggling(true);
    try {
      await apiFetch(`/risks/${id}/toggle-status`, { method: 'POST' });
      const isOpen = data.risk.status === 'Open';
      toast({ message: `Risk ${isOpen ? 'closed' : 'reopened'}.`, type: 'success' });
      load();
    } catch (e) { toast({ message: e.message, type: 'error' }); }
    finally { setToggling(false); }
  };

  const handleStatusSelect = (newStatus) => {
    if (newStatus === data?.risk?.status) return;
    if (newStatus === 'Closed') {
      setCloseConfirmOpen(true);
    } else {
      handleToggle();
    }
  };


  const handleDelete = async () => {
    try {
      const res = await apiFetch(`/risks/${id}/delete`, { method: 'POST' });
      toast({ message: 'Risk deleted.', type: 'success' });
      navigate(`/projects/${res.project_id || data.risk.project_id}`);
    } catch (e) { toast({ message: e.message, type: 'error' }); }
  };

  const handleFeedback = async (e) => {
    e.preventDefault();
    if (!feedbackLabel) { toast({ message: 'Select a severity label.', type: 'error' }); return; }
    setFeedbackLoading(true);
    try {
      await apiFetch(`/risks/${id}/feedback`, {
        method: 'POST',
        body: JSON.stringify({ corrected_label: feedbackLabel, correction_reason: feedbackReason }),
      });
      toast({ message: 'Feedback recorded. Thank you!', type: 'success' });
      load();
    } catch (e) { toast({ message: e.message, type: 'error' }); }
    finally { setFeedbackLoading(false); }
  };

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  if (!data) return null;

  const { risk, classification, mitigations, feedback, all_probs } = data;
  const isOpen = risk.status === 'Open';

  return (
    <div className="space-y-6 animate-fade-in">

      <PageHeader
        title={<span className="flex items-center gap-3 flex-wrap">{risk.title} <StatusBadge status={risk.status} /></span>}
        description={`${risk.risk_category} · ${risk.created_at ? new Date(risk.created_at).toLocaleDateString() : ''}`}
        breadcrumbs={[{ label: 'Projects', href: '/projects' }, { label: risk.project_name, href: `/projects/${risk.project_id}` }, { label: risk.title }]}
      />

      <div className="flex flex-wrap items-center gap-2">
        <Link to={`/risks/${id}/edit`}>
          <Button variant="outline" size="sm"><Edit className="h-4 w-4" />Edit Risk</Button>
        </Link>
        <a href={`/api/risks/${id}/pdf`} target="_blank" rel="noreferrer">
          <Button variant="outline" size="sm"><FileText className="h-4 w-4" />Export PDF</Button>
        </a>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border bg-card text-sm">
          <span className="text-muted-foreground text-xs">Status:</span>
          <StatusDropdown
            status={isOpen ? 'Open' : 'Closed'}
            onSelect={handleStatusSelect}
            disabled={toggling}
          />
        </div>
        <Button variant="outline" size="sm" className="text-destructive border-destructive/30 hover:bg-destructive/10" onClick={() => setDeleteOpen(true)}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>



      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-4">
          {/* Risk description */}
          <div>
            <h2 className="text-sm font-semibold text-foreground mb-2">Description</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">{risk.description}</p>
            <div className="flex gap-4 mt-4">
              {[['Probability', risk.probability], ['Impact', risk.impact], ['Score', (risk.probability * risk.impact).toFixed(3)]].map(([l, v]) => (
                <div key={l} className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">{l}</p>
                  <span className="font-mono text-sm font-semibold bg-secondary border border-border rounded-md px-2 py-0.5">{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ML Classification */}
          {classification && (
            <div>
              <h2 className="text-sm font-semibold text-foreground mb-3">ML Classification</h2>
              <div className="flex items-center gap-3 mb-4">
                <SeverityBadge severity={classification.predicted_label} />
                <div className="flex-1">
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>Model confidence</span>
                    <span className="font-semibold text-foreground tabular-nums">{(classification.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-border rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full transition-all duration-700" style={{ width: `${(classification.confidence * 100).toFixed(0)}%` }} />
                  </div>
                </div>
              </div>

              {all_probs && Object.keys(all_probs).length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Class Distribution</p>
                  {SEV_ORDER.map(label => {
                    const pct = Math.round((all_probs[label] || 0) * 100);
                    return (
                      <div key={label} className="flex items-center gap-2 text-xs">
                        <span className="w-14 text-muted-foreground">{label}</span>
                        <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
                          <div className={cn('h-full rounded-full transition-all duration-700', SEV_COLORS_BAR[label])} style={{ width: `${pct}%` }} />
                        </div>
                        <span className="w-8 text-right tabular-nums text-muted-foreground">{pct}%</span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Feedback panel */}
              <div className="mt-4 pt-4 border-t border-border">
                {!feedback ? (
                  <form onSubmit={handleFeedback} className="space-y-3">
                    <p className="text-xs font-medium text-foreground">Is this classification correct?</p>
                    <p className="text-xs text-muted-foreground">Your correction helps improve the model.</p>
                    <Select value={feedbackLabel} onChange={e => setFeedbackLabel(e.target.value)}>
                      <option value="">— Select correct severity —</option>
                      {SEV_ORDER.map(l => <option key={l} value={l}>{l}</option>)}
                    </Select>
                    <input
                      className="flex h-8 w-full rounded-md border border-input bg-transparent px-3 py-1 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-colors"
                      placeholder="Reason (optional)"
                      value={feedbackReason}
                      onChange={e => setFeedbackReason(e.target.value)}
                    />
                    <Button type="submit" size="sm" disabled={feedbackLoading} className="w-full">
                      {feedbackLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                      Submit Feedback
                    </Button>
                  </form>
                ) : (
                  <div className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span className="text-muted-foreground">
                      Corrected to <strong className="text-foreground">{feedback.corrected_label}</strong>
                      {feedback.correction_reason && <> — "{feedback.correction_reason}"</>}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right column — Mitigations */}
        <div className="lg:col-span-3">
          <div className="flex items-center gap-2 mb-3">
            <h2 className="text-sm font-semibold text-foreground">Mitigation Recommendations</h2>
            <span className="text-xs bg-secondary border border-border rounded-full px-2 py-0.5 text-muted-foreground">Top 3</span>
          </div>
          {classification && (
            <p className="text-xs text-muted-foreground mb-4 leading-relaxed">
              Ranked by TF-IDF cosine similarity to the risk description, filtered by category (<strong className="text-foreground">{risk.risk_category}</strong>) and severity (<strong className="text-foreground">{classification.predicted_label}</strong>).
            </p>
          )}
          {mitigations && mitigations.length > 0 ? (
            <div className="space-y-3">
              {mitigations.map((m, i) => {
                const steps = typeof m.implementation_steps === 'string' ? JSON.parse(m.implementation_steps || '[]') : (m.implementation_steps || []);
                return (
                  <div key={m.id || i} className="group rounded-xl border border-border bg-card hover:border-primary/30 hover:shadow-sm transition-all duration-200 overflow-hidden">
                    <div className="flex items-start gap-3 p-4">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-sm">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground leading-snug">{m.description}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{m.mitigation_id} · Similarity: {Number(m.similarity_score).toFixed(3)}</p>
                      </div>
                    </div>
                    {steps.length > 0 && (
                      <div className="px-4 pb-3 border-t border-border/50 pt-3">
                        <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">Implementation Steps</p>
                        <ol className="space-y-1 list-decimal list-inside">
                          {steps.map((step, j) => (
                            <li key={j} className="text-xs text-muted-foreground leading-relaxed">{step}</li>
                          ))}
                        </ol>
                      </div>
                    )}
                    <div className="px-4 py-2.5 border-t border-border/50 bg-muted/20 flex items-center gap-2">
                      <BookOpen className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      <p className="text-xs text-muted-foreground line-clamp-1">{m.source}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No recommendations available.</p>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDelete}
        title="Delete this risk?"
        description="This will permanently delete the risk along with its classification history, mitigation recommendations, and feedback logs."
        confirmLabel="Delete Risk"
      />

      <ConfirmDialog
        open={closeConfirmOpen}
        onClose={() => setCloseConfirmOpen(false)}
        onConfirm={handleToggle}
        title="Close this risk?"
        description="Are you sure you want to close this risk? Closing this risk indicates that it has been successfully mitigated or resolved."
        confirmLabel="Close Risk"
        confirmVariant="warning"
      />
    </div>
  );
}

