import { useState } from 'react';
import { TrendingUp, TrendingDown, Minus, Download, Filter } from 'lucide-react';
import { useRoiReport } from '../hooks/useStudyData';
import type { RoiReport } from '../types/athena';

export function RoiReport() {
  // React Query hook - cache automático
  const { data: report, isLoading: loading } = useRoiReport();
  const [sortBy, setSortBy] = useState<'roi' | 'stability' | 'weight'>('roi');
  const [filterBy, setFilterBy] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const getRoiIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'alto':
      case 'high':
        return <TrendingUp className="w-4 h-4 text-red-500" />;
      case 'estratégico':
      case 'strategic':
        return <TrendingUp className="w-4 h-4 text-amber-500" />;
      case 'baixo':
      case 'low':
        return <TrendingDown className="w-4 h-4 text-green-500" />;
      default:
        return <Minus className="w-4 h-4 text-slate-500" />;
    }
  };

  const getRoiColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'alto':
      case 'high':
        return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'estratégico':
      case 'strategic':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      default:
        return 'text-green-400 bg-green-500/10 border-green-500/20';
    }
  };

  const filteredAndSortedNodes = report?.nodes
    ?.filter(node => {
      if (filterBy === 'all') return true;
      const roi = node.roi_score;
      switch (filterBy) {
        case 'high': return roi > 0.7;
        case 'medium': return roi >= 0.3 && roi <= 0.7;
        case 'low': return roi < 0.3;
        default: return true;
      }
    })
    ?.sort((a, b) => {
      switch (sortBy) {
        case 'roi': return b.roi_score - a.roi_score;
        case 'stability': return b.stability - a.stability;
        case 'weight': return (b.weight || 0) - (a.weight || 0);
        default: return 0;
      }
    }) || [];

  const exportReport = () => {
    if (!report) return;

    const csvContent = [
      ['Tópico', 'Matéria', 'ROI Score', 'Estabilidade', 'Peso', 'Status ROI'],
      ...filteredAndSortedNodes.map(node => [
        node.topic,
        node.subject || 'N/A',
        node.roi_score.toFixed(3),
        node.stability.toFixed(3),
        (node.weight || 0).toString(),
        node.roi_status || 'N/A'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = globalThis.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `roi-report-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    globalThis.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!report) {
    return <div>Erro ao carregar relatório</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Relatório de ROI Detalhado</h1>
        <button
          onClick={exportReport}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
        >
          <Download className="w-4 h-4" />
          Exportar CSV
        </button>
      </div>

      {/* Filtros e Ordenação */}
      <div className="flex items-center gap-4 bg-slate-900 p-4 rounded-lg">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-slate-400">Filtrar por ROI:</span>
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value as 'all' | 'high' | 'medium' | 'low')}
            title="Filtrar resultados por ROI"
            className="bg-slate-800 text-slate-200 px-3 py-1 rounded border border-slate-700 text-sm"
          >
            <option value="all">Todos</option>
            <option value="high">Alto (&gt;0.7)</option>
            <option value="medium">Médio (0.3-0.7)</option>
            <option value="low">Baixo (&lt;0.3)</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">Ordenar por:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'roi' | 'stability' | 'weight')}
            title="Ordenar resultados"
            className="bg-slate-800 text-slate-200 px-3 py-1 rounded border border-slate-700 text-sm"
          >
            <option value="roi">ROI Score</option>
            <option value="stability">Estabilidade</option>
            <option value="weight">Peso</option>
          </select>
        </div>

        <div className="text-sm text-slate-400">
          {filteredAndSortedNodes.length} tópicos encontrados
        </div>
      </div>

      {/* Tabela de Resultados */}
      <div className="bg-slate-900 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Tópico</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Matéria</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">ROI Score</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Estabilidade</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Peso</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {filteredAndSortedNodes.map((node) => (
                <tr key={node.topic} className="hover:bg-slate-800/50">
                  <td className="px-4 py-3 text-sm text-slate-200">{node.topic}</td>
                  <td className="px-4 py-3 text-sm text-slate-400">{node.subject || 'N/A'}</td>
                  <td className="px-4 py-3 text-sm text-slate-200">{node.roi_score.toFixed(3)}</td>
                  <td className="px-4 py-3 text-sm text-slate-200">{node.stability.toFixed(3)}</td>
                  <td className="px-4 py-3 text-sm text-slate-200">{node.weight || 0}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${getRoiColor(node.roi_status || '')}`}>
                      {getRoiIcon(node.roi_status || '')}
                      {node.roi_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-slate-200 mb-2">ROI Geral</h3>
          <p className="text-2xl font-bold text-blue-400">{report.overall_roi?.toFixed(3) || 'N/A'}</p>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-slate-200 mb-2">Tópicos Prioritários</h3>
          <p className="text-2xl font-bold text-red-400">
            {report.nodes?.filter(n => n.roi_score > 0.7).length || 0}
          </p>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-slate-200 mb-2">Tópicos Consolidados</h3>
          <p className="text-2xl font-bold text-green-400">
            {report.nodes?.filter(n => n.roi_score < 0.3).length || 0}
          </p>
        </div>
      </div>
    </div>
  );
}