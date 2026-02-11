import { useMemo } from 'react';
import { AlertTriangle, TrendingUp, CheckCircle } from 'lucide-react';

interface NotificationItem {
  id: string;
  type: 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: Date;
}

interface NotificationsProps {
  readonly highRoiCount: number;
  readonly recentErrors: number;
}

export function Notifications({ highRoiCount, recentErrors }: NotificationsProps) {
  const notifications = useMemo(() => {
    const newNotifications: NotificationItem[] = [];

    if (highRoiCount > 0) {
      newNotifications.push({
        id: 'high-roi',
        type: 'warning',
        title: 'Revisões Prioritárias',
        message: `${highRoiCount} tópicos precisam de atenção imediata. Alto ROI detectado.`,
        timestamp: new Date()
      });
    }

    if (recentErrors > 0) {
      newNotifications.push({
        id: 'recent-errors',
        type: 'info',
        title: 'Erros Recentes',
        message: `${recentErrors} erros foram registrados recentemente. Revise os conceitos.`,
        timestamp: new Date()
      });
    }

    // Notificação de sucesso quando não há problemas
    if (highRoiCount === 0 && recentErrors === 0) {
      newNotifications.push({
        id: 'good-progress',
        type: 'success',
        title: 'Bom Progresso!',
        message: 'Seus estudos estão indo bem. Continue assim!',
        timestamp: new Date()
      });
    }

    return newNotifications;
  }, [highRoiCount, recentErrors]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'warning': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case 'success': return <CheckCircle className="w-5 h-5 text-green-500" />;
      default: return <TrendingUp className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBgColor = (type: string) => {
    switch (type) {
      case 'warning': return 'bg-amber-500/10 border-amber-500/20';
      case 'success': return 'bg-green-500/10 border-green-500/20';
      default: return 'bg-blue-500/10 border-blue-500/20';
    }
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-20 right-6 z-50 space-y-3 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`p-4 rounded-lg border backdrop-blur-md shadow-lg animate-in slide-in-from-right-2 ${getBgColor(notification.type)}`}
        >
          <div className="flex items-start gap-3">
            {getIcon(notification.type)}
            <div className="flex-1">
              <h4 className="font-semibold text-slate-200 text-sm">{notification.title}</h4>
              <p className="text-slate-300 text-sm mt-1">{notification.message}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}