import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { FolderOpen, ShieldAlert, BarChart3, Brain, Plus, TrendingUp } from 'lucide-react';
import { Chart, registerables } from 'chart.js';
import { PageHeader } from '../components/layout/PageParts';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { SeverityBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import { apiFetch, SEV_DOT } from '../lib/utils';

Chart.register(...registerables);

const SEV_COLORS = { Low: '#10b981', Medium: '#f59e0b', High: '#f97316', Critical: '#ef4444' };
const SEV_ORDER = ['Low', 'Medium', 'High', 'Critical'];

function StatCard({ icon: Icon, label, value, className }) {
  return (
    <Card className={className}>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground font-medium">{label}</p>
            <p className="text-3xl font-display font-bold text-foreground mt-1">{value}</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [matrix, setMatrix] = useState(null);
  const matrixRef = useRef(null);
  const sevRef = useRef(null);
  const catRef = useRef(null);
  const matrixChart = useRef(null);
  const sevChart = useRef(null);
  const catChart = useRef(null);

  useEffect(() => {
    apiFetch('/dashboard').then(setData).catch(console.error);
    apiFetch('/dashboard/risk-matrix').then(setMatrix).catch(console.error);
  }, []);

  // Build charts when data arrives
  useEffect(() => {
    if (!data) return;
    const isDark = document.documentElement.classList.contains('dark');
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    const labelColor = isDark ? '#9ca3af' : '#6b7280';

    Chart.defaults.color = labelColor;
    Chart.defaults.borderColor = gridColor;

    if (sevChart.current) sevChart.current.destroy();
    sevChart.current = new Chart(sevRef.current, {
      type: 'doughnut',
      data: {
        labels: SEV_ORDER,
        datasets: [{ data: SEV_ORDER.map(s => data.severity_counts[s] || 0), backgroundColor: SEV_ORDER.map(s => SEV_COLORS[s]), borderColor: isDark ? '#0f172a' : '#fff', borderWidth: 2 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { padding: 12, font: { size: 11 } } } }, cutout: '70%' }
    });

    if (catChart.current) catChart.current.destroy();
    const catLabels = Object.keys(data.category_counts);
    catChart.current = new Chart(catRef.current, {
      type: 'bar',
      data: {
        labels: catLabels,
        datasets: [{ label: 'Risks', data: Object.values(data.category_counts), backgroundColor: 'hsl(243 75% 59% / 0.8)', hoverBackgroundColor: 'hsl(243 75% 59%)', borderRadius: 4, borderSkipped: false }]
      },
      options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { ticks: { stepSize: 1, color: labelColor }, grid: { color: gridColor } }, y: { ticks: { color: labelColor }, grid: { display: false } } } }
    });

    return () => { sevChart.current?.destroy(); catChart.current?.destroy(); };
  }, [data]);

  useEffect(() => {
    if (!matrix) return;
    const isDark = document.documentElement.classList.contains('dark');
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    const labelColor = isDark ? '#9ca3af' : '#6b7280';

    if (matrixChart.current) matrixChart.current.destroy();
    const styled = (matrix.datasets || []).map(ds => ({
      ...ds,
      backgroundColor: SEV_COLORS[ds.label] || '#6366f1',
      borderColor: isDark ? '#0f172a' : '#fff',
      borderWidth: 1.5,
      pointRadius: 6,
      pointHoverRadius: 9,
    }));
    matrixChart.current = new Chart(matrixRef.current, {
      type: 'scatter',
      data: { datasets: styled },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          x: { min: 0, max: 1, title: { display: true, text: 'Probability', color: labelColor }, ticks: { color: labelColor }, grid: { color: gridColor } },
          y: { min: 0, max: 1, title: { display: true, text: 'Impact', color: labelColor }, ticks: { color: labelColor }, grid: { color: gridColor } }
        },
        plugins: { legend: { labels: { color: labelColor, font: { size: 11 } } }, tooltip: { callbacks: { label: ctx => ` ${ctx.raw.title || ''} (P:${ctx.raw.x}, I:${ctx.raw.y})` } } }
      }
    });
    return () => matrixChart.current?.destroy();
  }, [matrix]);

  if (!data) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Dashboard"
        description="System-wide overview across all your projects"
      />

      <div className="flex flex-wrap items-center gap-2">
        <Link to="/projects/new">
          <Button size="sm"><Plus className="h-4 w-4" />New Project</Button>
        </Link>
      </div>


      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FolderOpen}  label="Total Projects"       value={data.total_projects} />
        <StatCard icon={ShieldAlert} label="Risks Logged"         value={data.total_risks} />
        <StatCard icon={TrendingUp}  label="Critical Risks"       value={data.severity_counts?.Critical ?? 0} className="col-span-1" />
        <StatCard icon={Brain}       label="Model Acceptance"     value={data.acceptance_rate != null ? `${data.acceptance_rate}%` : '—'} />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-4">
        <Card className="lg:col-span-4">
          <CardHeader><CardTitle>Risk Matrix</CardTitle></CardHeader>
          <CardContent><div className="h-64"><canvas ref={matrixRef} /></div>
            <p className="mt-3 text-xs text-muted-foreground">Risks plotted by probability × impact. Top-right quadrant = most urgent.</p>
          </CardContent>
        </Card>
        <Card className="lg:col-span-3">
          <CardHeader><CardTitle>Severity Distribution</CardTitle></CardHeader>
          <CardContent><div className="h-64"><canvas ref={sevRef} /></div></CardContent>
        </Card>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-4">
        <Card className="lg:col-span-4">
          <CardHeader><CardTitle>Risks by Category</CardTitle></CardHeader>
          <CardContent><div className="h-56"><canvas ref={catRef} /></div></CardContent>
        </Card>
        <Card className="lg:col-span-3">
          <CardHeader><CardTitle className="flex items-center gap-2"><Brain className="h-4 w-4 text-primary" />Model Performance</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(data.model_comparison || []).map(m => (
              <div key={m.model} className={`flex items-center justify-between text-sm p-2.5 rounded-lg ${m.model === 'random_forest' ? 'bg-primary/5 border border-primary/20' : ''}`}>
                <span className="font-medium capitalize text-foreground flex items-center gap-2">
                  {m.model.replace(/_/g, ' ')}
                  {m.model === 'random_forest' && <span className="text-[10px] font-semibold bg-primary/10 text-primary px-1.5 py-0.5 rounded-full">Primary</span>}
                </span>
                <div className="flex gap-3 text-muted-foreground text-xs">
                  <span>F1 <strong className="text-foreground">{(m.weighted_f1 * 100).toFixed(1)}%</strong></span>
                  <span>Acc <strong className="text-foreground">{(m.accuracy * 100).toFixed(1)}%</strong></span>
                </div>
              </div>
            ))}
            <div className="pt-2 border-t border-border space-y-1.5 text-xs text-muted-foreground">
              <div className="flex justify-between"><span>Classifications</span><strong className="text-foreground">{data.total_classified}</strong></div>
              <div className="flex justify-between"><span>Corrections</span><strong className="text-foreground">{data.total_corrected}</strong></div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
