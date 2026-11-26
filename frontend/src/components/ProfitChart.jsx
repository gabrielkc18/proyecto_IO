import { BarChart2, TrendingUp } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

export default function ProfitChart({ chartType, history }) {
  const completedHistory = [...history]
    .filter((item) => item.status === 'Completado')
    .reverse();

  if (chartType === 'bar') {
    return (
      <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4 flex flex-col justify-between">
        <h3 className="font-bold text-[#172554] text-base flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-[#3B82F6]" /> Utilidad por ejecución
        </h3>
        {completedHistory.length > 0 ? (
          <div className="h-56 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={completedHistory}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="executionId" tickFormatter={(id) => `#${id}`} tick={{ fontSize: 12, fill: '#64748B' }} />
                <YAxis tickFormatter={(value) => `$${value / 1000}k`} tick={{ fontSize: 12, fill: '#64748B' }} />
                <Tooltip formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Utilidad']} />
                <Bar dataKey="profit" name="Utilidad" fill="#3B82F6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-sm text-gray-500">No hay resultados óptimos para comparar.</p>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
      <h3 className="font-bold text-[#172554] text-sm flex items-center gap-2">
        <TrendingUp className="w-4 h-4 text-[#3B82F6]" /> Comparativa de utilidades en el tiempo
      </h3>
      {completedHistory.length > 0 ? (
        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={completedHistory}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} />
              <YAxis tickFormatter={(value) => `$${value / 1000}k`} tick={{ fontSize: 10, fill: '#64748B' }} />
              <Tooltip formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Utilidad Óptima']} />
              <Line type="monotone" dataKey="profit" stroke="#3B82F6" strokeWidth={3} dot={{ r: 6, fill: '#1E40AF' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="text-sm text-gray-500">No hay resultados óptimos para comparar.</p>
      )}
    </div>
  );
}
