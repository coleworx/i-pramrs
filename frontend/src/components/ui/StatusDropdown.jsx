import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown } from 'lucide-react';
import { StatusBadge } from './Badge';
import { cn } from '../../lib/utils';

const STATUS_OPTIONS = ['Open', 'Closed'];

/**
 * Clickable status badge that opens a small dropdown to switch status.
 * onSelect(newStatus) is called only when a *different* status is chosen.
 */
export function StatusDropdown({ status, onSelect, disabled = false }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const handleSelect = (value) => {
    setOpen(false);
    if (value !== status) onSelect(value);
  };

  return (
    <div ref={ref} className="relative inline-block">
      <button
        disabled={disabled}
        onClick={() => setOpen(v => !v)}
        className={cn(
          'inline-flex items-center gap-1 rounded-full transition-all',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <StatusBadge status={status} />
        <ChevronDown
          className={cn(
            'h-3 w-3 text-muted-foreground transition-transform duration-150',
            open && 'rotate-180'
          )}
        />
      </button>

      {open && (
        <div
          role="listbox"
          className={cn(
            'absolute left-0 top-full mt-1.5 z-30',
            'w-36 rounded-lg border border-border bg-card shadow-lg',
            'py-1 animate-dropdown-in'
          )}
        >

          {STATUS_OPTIONS.map(opt => (
            <button
              key={opt}
              role="option"
              aria-selected={opt === status}
              onClick={() => handleSelect(opt)}
              className={cn(
                'w-full flex items-center justify-between px-3 py-2 text-sm transition-colors',
                opt === status
                  ? 'text-foreground bg-accent cursor-default'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground cursor-pointer'
              )}
            >
              <StatusBadge status={opt} />
              {opt === status && <Check className="h-3.5 w-3.5 text-primary" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
