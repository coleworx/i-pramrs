import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderOpen, Plus, MapPin, Building2, ArrowRight } from 'lucide-react';
import { PageHeader, EmptyState } from '../components/layout/PageParts';
import { Card, CardContent, CardFooter } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/Badge';
import { Spinner } from '../components/ui/Spinner';
import { apiFetch, cn } from '../lib/utils';


export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');



  useEffect(() => {
    apiFetch('/projects').then(d => setProjects(d.projects)).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;

  const filteredProjects = projects.filter(p => {
    if (filter === 'Active') return p.status === 'Active';
    if (filter === 'Closed') return p.status === 'Closed';
    return true;
  });

  return (
    <div className="space-y-6 animate-fade-in">

      <PageHeader
        title="My Projects"
        description="Manage your SME projects and track associated risks"
      />

      <div className="flex flex-wrap items-center gap-2">
        <Link to="/projects/new">
          <Button size="sm"><Plus className="h-4 w-4" />New Project</Button>
        </Link>
      </div>


      {projects.length > 0 && (
        <div className="flex border-b border-border mb-6">
          {['All', 'Active', 'Closed'].map(tab => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-all cursor-pointer',
                filter === tab
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              {tab} ({projects.filter(p => tab === 'All' || p.status === tab).length})
            </button>
          ))}
        </div>
      )}

      {filteredProjects.length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title={filter === 'All' ? "No projects yet" : `No ${filter.toLowerCase()} projects`}
          description={filter === 'All' 
            ? "Create your first project to start logging and classifying risks with AI." 
            : `You do not have any projects currently marked as ${filter.toLowerCase()}.`
          }
          action={filter === 'All' && <Link to="/projects/new"><Button><Plus className="h-4 w-4" />Create Project</Button></Link>}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredProjects.map((p, i) => (
            <Link key={p.id} to={`/projects/${p.id}`} className="group block animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
              <Card className="h-full transition-all duration-200 hover:shadow-md hover:border-primary/30 hover:-translate-y-0.5">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <h3 className="font-display font-semibold text-foreground leading-tight group-hover:text-primary transition-colors">{p.name}</h3>
                    <StatusBadge status={p.status} />
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs text-muted-foreground mb-3">
                    {p.sector && <span className="flex items-center gap-1"><Building2 className="h-3 w-3" />{p.sector}</span>}
                    {p.location && <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{p.location}</span>}
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
                    {p.description || 'No description provided.'}
                  </p>
                </CardContent>
                <CardFooter className="px-5 py-3 border-t border-border justify-between">
                  <span className="text-xs text-muted-foreground">{p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}</span>
                  <span className="text-xs font-medium text-primary flex items-center gap-1 group-hover:gap-1.5 transition-all">
                    View Risks <ArrowRight className="h-3 w-3" />
                  </span>
                </CardFooter>
              </Card>
            </Link>
          ))}
        </div>
      )}

    </div>
  );
}
