import { CheckCircle2, X } from 'lucide-react';

export function NavItem({ icon, label, active, onClick }) {
  return <button onClick={onClick} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold transition-all ${active ? 'bg-[#3B82F6] text-white shadow-lg shadow-blue-500/30' : 'text-blue-200 hover:bg-blue-900/40 hover:text-white'}`}>
    {icon}<span>{label}</span>
  </button>;
}

export function KPICard({ title, value, badge, icon, bgColor, textColor = 'text-[#172554]', titleColor = 'text-gray-500' }) {
  return <div className={`${bgColor} p-6 rounded-2xl border border-blue-100 shadow-sm flex items-center justify-between`}>
    <div><span className={`text-xs font-semibold uppercase tracking-wider ${titleColor}`}>{title}</span><div className="flex items-baseline gap-2 mt-1"><h3 className={`text-2xl font-extrabold ${textColor}`}>{value}</h3>{badge && <span className="text-xs font-bold text-emerald-300 bg-blue-900/40 px-2 py-0.5 rounded-full">{badge}</span>}</div></div>
    <div className="p-3 bg-[#EFF6FF] rounded-xl">{icon}</div>
  </div>;
}

export function ActivityItem({ title, subtitle, time }) {
  return <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-blue-50/50 transition-colors"><CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /><div className="flex-1 min-w-0"><p className="text-xs font-bold text-[#172554] truncate">{title}</p><p className="text-[11px] text-gray-500 truncate">{subtitle}</p></div><span className="text-[10px] text-gray-400 shrink-0">{time}</span></div>;
}

export function StepBadge({ number, label, active, completed }) {
  return <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold ${active ? 'bg-[#3B82F6] text-white' : completed ? 'bg-emerald-100 text-emerald-700' : 'text-gray-400'}`}><span className="w-4 h-4 rounded-full bg-white/20 flex items-center justify-center text-[10px]">{number}</span><span>{label}</span></div>;
}

export function ThemeOption({ label, icon, active, onClick }) {
  return <button onClick={onClick} className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-2 text-xs font-semibold transition-all ${active ? 'border-[#3B82F6] bg-blue-50 text-[#1E40AF]' : 'border-gray-200 hover:bg-gray-50 text-gray-600'}`}>{icon}<span>{label}</span></button>;
}

export function ModalWrapper({ title, children, onClose }) {
  return <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4"><div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-blue-100 overflow-hidden animate-fade-in"><div className="px-6 py-4 bg-[#172554] text-white flex justify-between items-center"><h3 className="font-bold text-sm">{title}</h3><button onClick={onClose} className="text-blue-200 hover:text-white"><X className="w-5 h-5" /></button></div><div className="p-6">{children}</div></div></div>;
}
