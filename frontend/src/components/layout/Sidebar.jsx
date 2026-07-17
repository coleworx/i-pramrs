import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FolderOpen, 
  LogOut, 
  Shield, 
  User, 
  Menu, 
  X, 
  PanelLeftClose, 
  PanelLeft 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../ui/Toast';
import { ThemeSwitcher } from './ThemeSwitcher';
import { cn } from '../../lib/utils';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projects', icon: FolderOpen, label: 'Projects' },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // Desktop collapse state
  const [isCollapsed, setIsCollapsed] = useState(false);
  // Mobile menu open state
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch {
      toast({ message: 'Logout failed', type: 'error' });
    }
  };

  const isActive = (to) => pathname === to || (to !== '/dashboard' && pathname.startsWith(to));

  const renderNavLinks = (forceExpanded = false) => {
    const collapsed = isCollapsed && !forceExpanded;
    return (
      <nav className={cn('flex-1 space-y-1 transition-all duration-200 py-4', collapsed ? 'px-2' : 'px-3')}>
        {navItems.map(({ to, icon: Icon, label }) => {
          const active = isActive(to);
          return (
            <Link
              key={to}
              to={to}
              onClick={() => setIsMobileOpen(false)}
              className={cn(
                'group flex items-center rounded-lg text-sm font-medium transition-all duration-150',
                active
                  ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/20'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/80',
                collapsed ? 'justify-center h-10 w-10 mx-auto' : 'gap-3 px-3 py-2.5'
              )}
              title={collapsed ? label : undefined}
            >
              <Icon className="h-4.5 w-4.5 shrink-0" />
              {!collapsed && (
                <span className="transition-opacity duration-200 font-medium">
                  {label}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
    );
  };

  return (
    <>
      {/* ─── MOBILE HEADER ─── */}
      <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-border bg-background/95 backdrop-blur px-4 md:hidden">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsMobileOpen(true)}
            aria-label="Open sidebar"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
          >
            <Menu className="h-5 w-5" />
          </button>
          
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary shadow-sm">
              <Shield className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <span className="font-display font-bold text-sm tracking-wide">
              I-<span className="text-primary">PRAMRS</span>
            </span>
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <ThemeSwitcher />
        </div>
      </header>

      {/* ─── MOBILE DRAWER OVERLAY ─── */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* ─── MOBILE DRAWER SIDEBAR ─── */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-border bg-card text-card-foreground shadow-2xl transition-transform duration-300 md:hidden',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Mobile Sidebar Header */}
        <div className="flex h-14 items-center justify-between border-b border-border px-4">
          <Link to="/dashboard" className="flex items-center gap-2" onClick={() => setIsMobileOpen(false)}>
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <span className="font-display font-bold text-sm tracking-wide">
              I-<span className="text-primary">PRAMRS</span>
            </span>
          </Link>
          <button
            onClick={() => setIsMobileOpen(false)}
            aria-label="Close sidebar"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Mobile Navigation Links (always expanded) */}
        {renderNavLinks(true)}

        {/* Mobile Sidebar Footer */}
        {user && (
          <div className="border-t border-border p-4 bg-muted/20 space-y-3">
            <div className="flex items-center gap-3 px-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-muted-foreground border border-border">
                <User className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{user.username}</p>
                <p className="text-xs text-muted-foreground truncate">{user.email || 'User'}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center h-9 px-3 rounded-lg text-sm font-medium text-destructive border border-destructive/20 bg-destructive/5 hover:bg-destructive/10 transition-colors"
            >
              <LogOut className="h-4 w-4 mr-2" /> Logout
            </button>
          </div>
        )}
      </aside>

      {/* ─── DESKTOP SIDEBAR ─── */}
      <aside
        className={cn(
          'hidden md:flex flex-col border-r border-border bg-card text-card-foreground transition-all duration-300 ease-in-out shrink-0 sticky top-0 h-screen z-20',
          isCollapsed ? 'w-[72px]' : 'w-64'
        )}
      >
        {/* Desktop Sidebar Header */}
        <div className={cn("flex h-14 items-center border-b border-border transition-all duration-200 shrink-0", isCollapsed ? "px-2 justify-center" : "px-4 justify-between")}>
          {!isCollapsed && (
            <Link to="/dashboard" className="flex items-center gap-2 select-none shrink-0 animate-fade-in">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shadow-sm shrink-0">
                <Shield className="h-4.5 w-4.5 text-primary-foreground" />
              </div>
              <span className="font-display font-bold text-sm tracking-wide">
                I-<span className="text-primary">PRAMRS</span>
              </span>
            </Link>
          )}

          {/* Toggle Button for collapsing sidebar */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="h-8 w-8 inline-flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary shrink-0 transition-colors"
          >
            {isCollapsed ? <PanelLeft className="h-4.5 w-4.5" /> : <PanelLeftClose className="h-4.5 w-4.5" />}
          </button>
        </div>

        {/* Navigation Links */}
        {renderNavLinks(false)}

        {/* Desktop Sidebar Footer */}
        {user && (
          <div className={cn("border-t border-border bg-muted/20 transition-all duration-200", isCollapsed ? "p-2" : "p-4 space-y-3")}>
            <div className={cn('flex items-center gap-3 px-1 transition-all duration-200', isCollapsed ? 'justify-center' : '')}>
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-muted-foreground border border-border shrink-0">
                <User className="h-4 w-4" />
              </div>
              {!isCollapsed && (
                <div className="flex-1 min-w-0 transition-opacity duration-200">
                  <p className="text-sm font-medium text-foreground truncate">{user.username}</p>
                  <p className="text-xs text-muted-foreground truncate">{user.email || 'User'}</p>
                </div>
              )}
            </div>

            {isCollapsed ? (
              <button
                onClick={handleLogout}
                aria-label="Logout"
                title="Logout"
                className="h-9 w-9 flex items-center justify-center rounded-lg text-destructive hover:bg-destructive/10 transition-colors mx-auto"
              >
                <LogOut className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center h-9 px-3 rounded-lg text-sm font-medium text-destructive border border-destructive/20 bg-destructive/5 hover:bg-destructive/10 transition-colors"
              >
                <LogOut className="h-4 w-4 mr-2" /> Logout
              </button>
            )}
          </div>
        )}
      </aside>
    </>
  );
}
