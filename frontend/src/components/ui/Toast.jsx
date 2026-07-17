import { createContext, useContext, useState, useCallback } from 'react';
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import { cn } from '../../lib/utils';

const ToastContext = createContext(null);

const config = {
  success: { icon: CheckCircle2, cls: 'border-emerald-500/30 bg-emerald-500/5 dark:bg-emerald-500/10', iconCls: 'text-emerald-500' },
  error:   { icon: AlertCircle,  cls: 'border-red-500/30 bg-red-500/5 dark:bg-red-500/10',           iconCls: 'text-red-500' },
  info:    { icon: Info,         cls: 'border-primary/30 bg-primary/5',                              iconCls: 'text-primary' },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const toast = useCallback(({ message, type = 'info', duration = 4000 }) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
  }, []);

  const dismiss = id => setToasts(prev => prev.filter(t => t.id !== id));

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-16 right-4 z-50 flex flex-col gap-2 w-full max-w-sm pointer-events-none">
        {toasts.map(t => {
          const { icon: Icon, cls, iconCls } = config[t.type] || config.info;
          return (
            <div key={t.id} className={cn('pointer-events-auto flex items-start gap-3 rounded-lg border p-4 shadow-lg bg-card animate-slide-in-right', cls)}>
              <Icon className={cn('h-4 w-4 shrink-0 mt-0.5', iconCls)} />
              <p className="flex-1 text-sm font-medium text-foreground">{t.message}</p>
              <button onClick={() => dismiss(t.id)} className="text-muted-foreground hover:text-foreground transition-colors shrink-0">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
