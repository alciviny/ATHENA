import { TrendingUp, Target, Brain, Clock, AlertTriangle, BarChart3 } from 'lucide-react';
import { useRoiReport, usePerformanceSummary } from '../hooks/useStudyData';
import { Notifications } from './Notifications';

interface DashboardMetrics {
  totalStudyTime: number;
  averageAccuracy: number;
  roiScore: number;
  pendingReviews: number;
  knowledgeNodes: number;
  recentErrors: number;
}

interface DashboardProps {
  onNavigateToRoiReport?: () => void;
}

export function Dashboard({ onNavigateToRoiReport }: Readonly<DashboardProps>) {
  // React Query hooks - cache automático
  const { data: roiReport, isLoading: loadingRoi } = useRoiReport();
  const { data: perfSummary, isLoading: loadingPerf } = usePerformanceSummary();

  const loading = loadingRoi || loadingPerf;

  // Calcula métricas dos dados em cache
  const metrics: DashboardMetrics | null = 
    roiReport && perfSummary
      ? {
          knowledgeNodes: roiReport?.nodes?.length || 0,
          pendingReviews: roiReport?.nodes?.filter(n => n.roi_status === 'HIGH' || n.roi_status === 'ALTO')?.length || 0,
          roiScore: roiReport?.overall_roi || 0,
          totalStudyTime: Math.round((perfSummary?.total_time_seconds || 0) / 60),
          averageAccuracy: perfSummary?.average_accuracy || 0,
          recentErrors: perfSummary?.recent_errors || 0,
        }
      : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!metrics) {
    return <div>Erro ao carregar dados</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard de Aprendizado</h1>

      {/* Notificações */}
      <Notifications highRoiCount={metrics.pendingReviews} recentErrors={metrics.recentErrors} />

      {/* Métricas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Tempo Total de Estudo</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{Math.round(metrics.totalStudyTime / 60)}h</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <Target className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Acurácia Média</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{Math.round(metrics.averageAccuracy * 100)}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-purple-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Score de ROI</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.roiScore}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Revisões Pendentes</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.pendingReviews}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <Brain className="h-8 w-8 text-indigo-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Nós de Conhecimento</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.knowledgeNodes}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-orange-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Erros Recentes</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.recentErrors}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico de Progresso ou Placeholder */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Progresso por Matéria</h2>
        <div className="text-center text-gray-500">
          Gráfico de progresso será implementado aqui
        </div>
      </div>

      {/* Ações */}
      <div className="flex gap-4">
        <button
          onClick={onNavigateToRoiReport}
          className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors"
        >
          <BarChart3 className="w-5 h-5" />
          Ver Relatório de ROI Detalhado
        </button>
      </div>
    </div>
  );
}