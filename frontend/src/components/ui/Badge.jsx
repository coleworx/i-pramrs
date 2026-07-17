import { cn, SEV_CLASSES } from '../../lib/utils';

const variants = {
  default: 'bg-primary/10 text-primary border border-primary/20',
  secondary: 'bg-secondary text-secondary-foreground border border-border',
  destructive: 'bg-destructive/10 text-destructive border border-destructive/20',
  outline: 'border border-border text-foreground bg-transparent',
  success: 'bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 dark:text-emerald-400',
  warning: 'bg-amber-500/10 text-amber-700 border border-amber-500/20 dark:text-amber-400',
};

export function Badge({ className, variant = 'default', ...props }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

export function SeverityBadge({ severity }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide',
        SEV_CLASSES[severity] || variants.secondary
      )}
    >
      {severity}
    </span>
  );
}

export function StatusBadge({ status }) {
  const isActive = status === 'Active' || status === 'Open';
  return (
    <span className={cn(
      'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
      isActive
        ? 'bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 dark:text-emerald-400'
        : 'bg-secondary text-muted-foreground border border-border'
    )}>
      <span className={cn('h-1.5 w-1.5 rounded-full', isActive ? 'bg-emerald-500' : 'bg-muted-foreground')} />
      {status}
    </span>
  );
}
