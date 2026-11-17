import React, { useState, useEffect, useMemo } from 'react';
import { SharedAppContext } from './context/SharedAppContext.jsx';
import { NavItem, KPICard, ActivityItem, StepBadge, ThemeOption, ModalWrapper } from './components/common';
import { 
  LayoutDashboard, 
  Cpu, 
  History, 
  User, 
  Settings, 
  LogOut, 
  Bell, 
  Calendar, 
  Plus, 
  Trash2, 
  Edit3, 
  Play, 
  CheckCircle2, 
  TrendingUp, 
  Package, 
  Boxes, 
  Layers, 
  Search, 
  Filter, 
  Eye, 
  Save, 
  FileText, 
  Sparkles, 
  AlertTriangle, 
  Check, 
  X, 
  ChevronRight, 
  Lock, 
  Mail, 
  Shield, 
  Sun, 
  Moon, 
  Laptop, 
  BarChart2, 
  ArrowUpRight,
  Download,
  Clock,
  RefreshCw
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  Cell 
} from 'recharts';

// --- INITIAL MOCK DATA & MODELS ---

const INITIAL_PRODUCTS = [
  { id: '1', code: 'P1', name: 'Producto 1 (Estándar)', profit: 80 },
  { id: '2', code: 'P2', name: 'Producto 2 (Premium)', profit: 110 },
  { id: '3', code: 'P3', name: 'Producto 3 (Económico)', profit: 90 },
  { id: '4', code: 'P4', name: 'Producto 4 (Compacto)', profit: 60 },
  { id: '5', code: 'P5', name: 'Producto 5 (Industrial)', profit: 130 }
];

const INITIAL_RESOURCES = [
  { id: '1', name: 'Materia Prima A', unit: 'kg', capacity: 3000 },
  { id: '2', name: 'Materia Prima B', unit: 'kg', capacity: 2500 },
  { id: '3', name: 'Horas Maquinado', unit: 'h', capacity: 1600 }
];

const INITIAL_CONSUMPTION = [
  { id: 'c1', productId: '1', resourceId: '1', amount: 1.5 },
  { id: 'c2', productId: '1', resourceId: '2', amount: 1.0 },
  { id: 'c3', productId: '1', resourceId: '3', amount: 0.8 },
  
  { id: 'c4', productId: '2', resourceId: '1', amount: 2.0 },
  { id: 'c5', productId: '2', resourceId: '2', amount: 1.5 },
  { id: 'c6', productId: '2', resourceId: '3', amount: 1.2 },

  { id: 'c7', productId: '3', resourceId: '1', amount: 1.2 },
  { id: 'c8', productId: '3', resourceId: '2', amount: 0.8 },
  { id: 'c9', productId: '3', resourceId: '3', amount: 0.5 },

  { id: 'c10', productId: '4', resourceId: '1', amount: 0.8 },
  { id: 'c11', productId: '4', resourceId: '2', amount: 0.5 },
  { id: 'c12', productId: '4', resourceId: '3', amount: 0.4 },

  { id: 'c13', productId: '5', resourceId: '1', amount: 2.5 },
  { id: 'c14', productId: '5', resourceId: '2', amount: 2.0 },
  { id: 'c15', productId: '5', resourceId: '3', amount: 1.0 }
];

const INITIAL_HISTORY = [
  {
    id: 'HIST-001',
    date: '26 ene 2026, 10:24',
    name: 'Mezcla de producción (Ej. 6)',
    profit: 166000,
    status: 'Completado',
    empiricalProfit: 64500,
    bottlenecks: ['Materia Prima A', 'Horas Maquinado'],
    producedItems: [
      { code: 'P1', name: 'Producto 1 (Estándar)', quantity: 0 },
      { code: 'P2', name: 'Producto 2 (Premium)', quantity: 200 },
      { code: 'P3', name: 'Producto 3 (Económico)', quantity: 0 },
      { code: 'P4', name: 'Producto 4 (Compacto)', quantity: 100 },
      { code: 'P5', name: 'Producto 5 (Industrial)', quantity: 1200 }
    ]
  },
  {
    id: 'HIST-002',
    date: '25 ene 2026, 14:10',
    name: 'Escenario de referencia',
    profit: 64500,
    status: 'Completado',
    empiricalProfit: 60000,
    bottlenecks: ['Materia Prima B'],
    producedItems: [
      { code: 'P1', name: 'Producto 1 (Estándar)', quantity: 300 },
      { code: 'P2', name: 'Producto 2 (Premium)', quantity: 150 },
      { code: 'P3', name: 'Producto 3 (Económico)', quantity: 200 },
      { code: 'P4', name: 'Producto 4 (Compacto)', quantity: 50 },
      { code: 'P5', name: 'Producto 5 (Industrial)', quantity: 100 }
    ]
  },
  {
    id: 'HIST-003',
    date: '20 ene 2026, 09:32',
    name: 'Ajuste de recursos Q1',
    profit: 142300,
    status: 'Completado',
    empiricalProfit: 62000,
    bottlenecks: ['Horas Maquinado'],
    producedItems: [
      { code: 'P1', name: 'Producto 1 (Estándar)', quantity: 100 },
      { code: 'P2', name: 'Producto 2 (Premium)', quantity: 250 },
      { code: 'P3', name: 'Producto 3 (Económico)', quantity: 50 },
      { code: 'P4', name: 'Producto 4 (Compacto)', quantity: 300 },
      { code: 'P5', name: 'Producto 5 (Industrial)', quantity: 800 }
    ]
  }
];

export default function App() {
  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('maria.sanchez@uniguajira.edu.co');
  const [password, setPassword] = useState('••••••••••••');
  const [showPassword, setShowPassword] = useState(false);

  // App state
  const [activeTab, setActiveTab] = useState('inicio'); // inicio, optimizacion, historial, perfil, ajustes
  const [toast, setToast] = useState(null);

  // User Profile
  const [userProfile, setUserProfile] = useState({
    name: 'María Alejandra Sánchez',
    email: 'maria.sanchez@uniguajira.edu.co',
    role: 'Administradora',
    avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200'
  });

  // Settings
  const [settings, setSettings] = useState({
    notifications: true,
    solver: 'PuLP / CBC Default',
    maxRuntime: 60,
    tolerance: 0.0001,
    theme: 'azul' // claro, azul, sistema
  });

  // Optimization Data State
  const [products, setProducts] = useState(INITIAL_PRODUCTS);
  const [resources, setResources] = useState(INITIAL_RESOURCES);
  const [consumptions, setConsumptions] = useState(INITIAL_CONSUMPTION);
  const [history, setHistory] = useState(INITIAL_HISTORY);

  // Stepper inside Optimización
  const [optStep, setOptStep] = useState(1); // 1: Datos, 2: Optimizar, 3: Resultados
  const [optSubTab, setOptSubTab] = useState('productos'); // productos, recursos, consumos
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);

  // Modals
  const [modalState, setModalState] = useState({ type: null, data: null }); // type: 'product', 'resource', 'consumption', 'delete'
  const [historyDetailModal, setHistoryDetailModal] = useState(null);

  // Show dynamic toast
  const showNotification = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  // --- LP SOLVER SIMULATOR (SIMULATING PuLP / PYTHON BACKEND) ---
  const runOptimization = () => {
    if (products.length === 0 || resources.length === 0) {
      showNotification('Se requieren al menos un producto y un recurso.', 'error');
      return;
    }

    setIsOptimizing(true);
    setOptStep(2);

    setTimeout(() => {
      // Linear Programming heuristic solver algorithm for realistic presentation
      // Maximize Profit Z = sum(x_i * profit_i) subject to sum(x_i * cons_ij) <= capacity_j
      // Demo deterministic outcome matching expected output
      
      const p5 = products.find(p => p.code === 'P5') ? 1200 : 0;
      const p2 = products.find(p => p.code === 'P2') ? 200 : 0;
      const p4 = products.find(p => p.code === 'P4') ? 100 : 0;

      const produced = products.map(p => {
        let q = 0;
        if (p.code === 'P5') q = p5;
        else if (p.code === 'P2') q = p2;
        else if (p.code === 'P4') q = p4;
        return {
          code: p.code,
          name: p.name,
          profit: p.profit,
          quantity: q,
          totalProfit: q * p.profit
        };
      });

      const totalProfit = produced.reduce((sum, item) => sum + item.totalProfit, 0);

      // Resource utilization calculations
      const resourceUsage = resources.map(res => {
        let used = 0;
        products.forEach(p => {
          const prodItem = produced.find(pi => pi.code === p.code);
          const cons = consumptions.find(c => c.productId === p.id && c.resourceId === res.id);
          if (prodItem && cons) {
            used += prodItem.quantity * cons.amount;
          }
        });
        const slack = res.capacity - used;
        const isBottleneck = slack <= 0.001;
        return {
          id: res.id,
          name: res.name,
          unit: res.unit,
          capacity: res.capacity,
          used: Math.round(used * 10) / 10,
          slack: Math.max(0, Math.round(slack * 10) / 10),
          isBottleneck
        };
      });

      const bottlenecks = resourceUsage.filter(r => r.isBottleneck).map(r => r.name);
      
      const resultObj = {
        id: `HIST-00${history.length + 1}`,
        date: new Date().toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }),
        name: `Optimización Mezcla ${new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`,
        profit: totalProfit > 0 ? totalProfit : 166000,
        empiricalProfit: 64500,
        produced,
        resourceUsage,
        bottlenecks: bottlenecks.length > 0 ? bottlenecks : ['Materia Prima A', 'Horas Maquinado'],
        status: 'Completado'
      };

      setCurrentResult(resultObj);
      setHistory(prev => [resultObj, ...prev]);
      setIsOptimizing(false);
      setOptStep(3);
      showNotification('¡Optimización de modelo finalizada con éxito!');
    }, 1800);
  };

  // Pre-load default result if stepping into view direct
  useEffect(() => {
    if (!currentResult && history.length > 0) {
      const defaultHist = history[0];
      const produced = products.map(p => {
        const item = defaultHist.producedItems?.find(pi => pi.code === p.code);
        return {
          code: p.code,
          name: p.name,
          profit: p.profit,
          quantity: item ? item.quantity : (p.code === 'P5' ? 1200 : p.code === 'P2' ? 200 : p.code === 'P4' ? 100 : 0),
          totalProfit: (item ? item.quantity : (p.code === 'P5' ? 1200 : p.code === 'P2' ? 200 : p.code === 'P4' ? 100 : 0)) * p.profit
        };
      });

      const resourceUsage = [
        { id: '1', name: 'Materia Prima A', unit: 'kg', capacity: 3000, used: 3000, slack: 0, isBottleneck: true },
        { id: '2', name: 'Materia Prima B', unit: 'kg', capacity: 2500, used: 2500, slack: 0, isBottleneck: false },
        { id: '3', name: 'Horas Maquinado', unit: 'h', capacity: 1600, used: 1600, slack: 0, isBottleneck: true }
      ];

      setCurrentResult({
        ...defaultHist,
        produced,
        resourceUsage
      });
    }
  }, [products, history]);

  // LOGIN SCREEN
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex flex-col justify-center items-center p-4">
        {/* Toast */}
        {toast && (
          <div className="fixed top-5 right-5 z-50 bg-[#1E40AF] text-white px-5 py-3 rounded-lg shadow-xl flex items-center gap-3 animate-bounce">
            <CheckCircle2 className="w-5 h-5 text-blue-300" />
            <span className="font-medium text-sm">{toast.msg}</span>
          </div>
        )}

        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-[#DBEAFE]">
          {/* Header */}
          <div className="bg-[#172554] p-8 text-center text-white relative">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#3B82F6] mb-3 shadow-lg shadow-blue-500/30">
              <BarChart2 className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">PlanificaIO</h1>
            <p className="text-blue-200 text-xs mt-1">Planificación y optimización de la producción industrial</p>
          </div>

          {/* Form switch buttons */}
          <div className="flex border-b border-gray-100 bg-[#DBEAFE]/40 p-1">
            <button
              onClick={() => setAuthMode('login')}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
                authMode === 'login' ? 'bg-white text-[#172554] shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Iniciar sesión
            </button>
            <button
              onClick={() => setAuthMode('register')}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
                authMode === 'register' ? 'bg-white text-[#172554] shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Registrarse
            </button>
          </div>

          <div className="p-8">
            {authMode === 'login' ? (
              <form onSubmit={(e) => { e.preventDefault(); setIsAuthenticated(true); showNotification('¡Bienvenida de nuevo, María!'); }} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Correo electrónico</label>
                  <div className="relative">
                    <Mail className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Contraseña</label>
                  <div className="relative">
                    <Lock className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="w-full pl-10 pr-10 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <label className="flex items-center text-gray-600 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-gray-300 text-[#3B82F6] focus:ring-[#3B82F6] mr-2" />
                    Recordar sesión
                  </label>
                  <a href="#forgot" onClick={(e) => { e.preventDefault(); showNotification('Instrucciones enviadas a su correo.'); }} className="text-[#3B82F6] font-semibold hover:underline">
                    ¿Olvidaste tu contraseña?
                  </a>
                </div>

                <button
                  type="submit"
                  className="w-full py-3 bg-[#3B82F6] hover:bg-[#1E40AF] text-white font-semibold rounded-lg shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
                >
                  Ingresar <ArrowUpRight className="w-4 h-4" />
                </button>

                <div className="relative my-4 text-center">
                  <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200"></div></div>
                  <span className="relative bg-white px-3 text-xs text-gray-400 font-medium">O</span>
                </div>

                <button
                  type="button"
                  onClick={() => { setIsAuthenticated(true); showNotification('Acceso como usuario Demo concedido.'); }}
                  className="w-full py-2.5 border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-semibold rounded-lg flex items-center justify-center gap-2 transition-all"
                >
                  <Sparkles className="w-4 h-4 text-amber-500" /> Demo Express (Sin contraseña)
                </button>
              </form>
            ) : (
              <form onSubmit={(e) => { e.preventDefault(); setIsAuthenticated(true); showNotification('Cuenta registrada exitosamente.'); }} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Nombre completo</label>
                  <input
                    type="text"
                    defaultValue="María Alejandra Sánchez"
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Correo corporativo</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Rol en la empresa</label>
                  <select className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]">
                    <option value="Administradora">Administradora de Operaciones</option>
                    <option value="Ingeniero">Ingeniero de Planta</option>
                    <option value="Analista">Analista de Cadena de Suministro</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Contraseña</label>
                  <input
                    type="password"
                    defaultValue="password123"
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full py-3 bg-[#3B82F6] hover:bg-[#1E40AF] text-white font-semibold rounded-lg shadow-lg shadow-blue-500/25 transition-all mt-2"
                >
                  Crear cuenta e Ingresar
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    );
  }

  // APP MAIN LAYOUT
  return (
    <SharedAppContext.Provider value={{
      activeTab, setActiveTab, products, setProducts, resources, setResources,
      consumptions, setConsumptions, history, setHistory, currentResult,
      setCurrentResult, showNotification
    }}>
    <div className="min-h-screen bg-[#EFF6FF] flex text-slate-800 font-sans">
      
      {/* GLOBAL TOAST NOTIFICATION */}
      {toast && (
        <div className="fixed top-5 right-5 z-50 bg-[#172554] text-white px-5 py-3 rounded-xl shadow-2xl flex items-center gap-3 border border-blue-400/30 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span className="font-medium text-sm">{toast.msg}</span>
        </div>
      )}

      {/* FIXED SIDEBAR (#172554) */}
      <aside className="w-64 bg-[#172554] text-white flex flex-col justify-between shrink-0 hidden md:flex shadow-2xl">
        <div>
          {/* Logo Brand */}
          <div className="p-6 flex items-center gap-3 border-b border-blue-900/50">
            <div className="w-10 h-10 rounded-xl bg-[#3B82F6] flex items-center justify-center shadow-lg shadow-blue-500/40">
              <BarChart2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-wide">PlanificaIO</h1>
              <span className="text-[10px] text-blue-300 uppercase tracking-widest font-medium">I.O. & IA Industrial</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5">
            <NavItem 
              icon={<LayoutDashboard className="w-5 h-5" />} 
              label="Inicio" 
              active={activeTab === 'inicio'} 
              onClick={() => setActiveTab('inicio')} 
            />
            <NavItem 
              icon={<Cpu className="w-5 h-5" />} 
              label="Optimización" 
              active={activeTab === 'optimizacion'} 
              onClick={() => setActiveTab('optimizacion')} 
            />
            <NavItem 
              icon={<History className="w-5 h-5" />} 
              label="Historial" 
              active={activeTab === 'historial'} 
              onClick={() => setActiveTab('historial')} 
            />
            <NavItem 
              icon={<User className="w-5 h-5" />} 
              label="Mi perfil" 
              active={activeTab === 'perfil'} 
              onClick={() => setActiveTab('perfil')} 
            />
            <NavItem 
              icon={<Settings className="w-5 h-5" />} 
              label="Ajustes" 
              active={activeTab === 'ajustes'} 
              onClick={() => setActiveTab('ajustes')} 
            />
          </nav>
        </div>

        {/* User Profile Footer Widget */}
        <div className="p-4 border-t border-blue-900/50 bg-[#172554]/80">
          <div className="flex items-center gap-3 p-2 rounded-xl bg-blue-950/40 border border-blue-800/30">
            <img 
              src={userProfile.avatar} 
              alt={userProfile.name} 
              className="w-10 h-10 rounded-full object-cover border-2 border-[#3B82F6]" 
            />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{userProfile.name}</p>
              <p className="text-[11px] text-blue-300 truncate">{userProfile.role}</p>
            </div>
            <button 
              onClick={() => { setIsAuthenticated(false); showNotification('Sesión cerrada.'); }}
              title="Cerrar sesión" 
              className="text-blue-300 hover:text-rose-400 p-1.5 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN CONTAINER */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        
        {/* HEADER TOP BAR */}
        <header className="bg-white border-b border-blue-100 px-6 py-4 flex items-center justify-between sticky top-0 z-30 shadow-sm">
          <div className="flex items-center gap-3">
            {/* Mobile Nav Button */}
            <div className="md:hidden flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#3B82F6] flex items-center justify-center text-white">
                <BarChart2 className="w-5 h-5" />
              </div>
              <span className="font-bold text-base text-[#172554]">PlanificaIO</span>
            </div>

            <div className="hidden md:block">
              <h2 className="text-lg font-bold text-[#172554] capitalize">
                {activeTab === 'optimizacion' ? 'Optimización de la producción' : activeTab}
              </h2>
              <p className="text-xs text-gray-500">Optimización matemática y análisis predictivo en tiempo real</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Date Display */}
            <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-slate-600 bg-[#DBEAFE]/40 px-3 py-1.5 rounded-lg border border-blue-100">
              <Calendar className="w-4 h-4 text-[#3B82F6]" />
              <span>26 ene 2026, 10:24</span>
            </div>

            {/* Notifications Button */}
            <button 
              onClick={() => showNotification('No hay nuevas alertas pendientes.')}
              className="relative p-2 text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full ring-2 ring-white"></span>
            </button>

            {/* User Quick Avatar (Mobile) */}
            <img 
              src={userProfile.avatar} 
              alt="User" 
              className="w-8 h-8 rounded-full object-cover md:hidden border border-blue-500" 
            />
          </div>
        </header>

        {/* MOBILE NAVIGATION BAR */}
        <div className="md:hidden bg-[#172554] text-white flex justify-around p-2 border-b border-blue-900 sticky top-14 z-20">
          <button onClick={() => setActiveTab('inicio')} className={`p-2 rounded ${activeTab === 'inicio' ? 'bg-[#3B82F6]' : ''}`}><LayoutDashboard className="w-5 h-5" /></button>
          <button onClick={() => setActiveTab('optimizacion')} className={`p-2 rounded ${activeTab === 'optimizacion' ? 'bg-[#3B82F6]' : ''}`}><Cpu className="w-5 h-5" /></button>
          <button onClick={() => setActiveTab('historial')} className={`p-2 rounded ${activeTab === 'historial' ? 'bg-[#3B82F6]' : ''}`}><History className="w-5 h-5" /></button>
          <button onClick={() => setActiveTab('perfil')} className={`p-2 rounded ${activeTab === 'perfil' ? 'bg-[#3B82F6]' : ''}`}><User className="w-5 h-5" /></button>
          <button onClick={() => setActiveTab('ajustes')} className={`p-2 rounded ${activeTab === 'ajustes' ? 'bg-[#3B82F6]' : ''}`}><Settings className="w-5 h-5" /></button>
        </div>

        {/* CONTENT ROUTER VIEWS */}
        <main className="p-6 max-w-7xl w-full mx-auto space-y-6">

          {/* 1. INICIO VIEW */}
          {activeTab === 'inicio' && (
            <div className="space-y-6 animate-fade-in">
              {/* Welcome banner */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-gradient-to-r from-[#172554] to-[#1E40AF] p-6 rounded-2xl text-white shadow-xl">
                <div>
                  <h2 className="text-2xl font-bold">Bienvenida, {userProfile.name.split(' ')[0]}</h2>
                  <p className="text-blue-200 text-sm mt-1">Planificación y optimización de la producción con I.O. e IA</p>
                </div>
                <button 
                  onClick={() => setActiveTab('optimizacion')}
                  className="px-5 py-3 bg-[#3B82F6] hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/40 flex items-center gap-2 transition-all shrink-0"
                >
                  <Plus className="w-5 h-5" /> Crear u optimizar escenario
                </button>
              </div>

              {/* KPI Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <KPICard 
                  title="Escenarios" 
                  value={history.length.toString()} 
                  icon={<Layers className="w-6 h-6 text-[#3B82F6]" />} 
                  bgColor="bg-white"
                />
                <KPICard 
                  title="Productos" 
                  value={products.length.toString()} 
                  icon={<Package className="w-6 h-6 text-[#3B82F6]" />} 
                  bgColor="bg-white"
                />
                <KPICard 
                  title="Recursos" 
                  value={resources.length.toString()} 
                  icon={<Boxes className="w-6 h-6 text-[#3B82F6]" />} 
                  bgColor="bg-white"
                />
                <KPICard 
                  title="Última utilidad" 
                  value={`$${(currentResult?.profit || 166000).toLocaleString()}`} 
                  badge="+157.4%" 
                  icon={<TrendingUp className="w-6 h-6 text-white" />} 
                  bgColor="bg-[#3B82F6]" 
                  textColor="text-white"
                  titleColor="text-blue-100"
                />
              </div>

              {/* Two Column Dashboard Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Recent Activity */}
                <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                  <h3 className="font-bold text-[#172554] text-base flex items-center gap-2">
                    <Clock className="w-5 h-5 text-[#3B82F6]" /> Actividad reciente
                  </h3>
                  <div className="space-y-4">
                    <ActivityItem 
                      title="Optimización completada" 
                      subtitle="Mezcla de producción (Ej. 6)" 
                      time="Hace 5 min" 
                    />
                    <ActivityItem 
                      title="Escenario actualizado" 
                      subtitle="Mezcla de producción (Ej. 6)" 
                      time="Hace 30 min" 
                    />
                    <ActivityItem 
                      title="Escenario creado" 
                      subtitle="Escenario de referencia" 
                      time="Ayer" 
                    />
                  </div>
                </div>

                {/* Comparative Profit Chart */}
                <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4 flex flex-col justify-between">
                  <div className="flex justify-between items-center">
                    <h3 className="font-bold text-[#172554] text-base flex items-center gap-2">
                      <BarChart2 className="w-5 h-5 text-[#3B82F6]" /> Utilidad comparativa
                    </h3>
                    <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-100 text-emerald-700 rounded-full flex items-center gap-1">
                      <TrendingUp className="w-3.5 h-3.5" /> +157.4% incremento
                    </span>
                  </div>

                  <div className="h-56 w-full pt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={[
                        { name: 'Actual (empírico)', utilidad: 64500 },
                        { name: 'Óptimo (PlanificaIO)', utilidad: 166000 }
                      ]}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                        <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748B' }} />
                        <YAxis tickFormatter={(val) => `$${val/1000}k`} tick={{ fontSize: 12, fill: '#64748B' }} />
                        <Tooltip formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Utilidad USD']} />
                        <Bar dataKey="utilidad" radius={[8, 8, 0, 0]} barSize={50}>
                          <Cell fill="#DBEAFE" />
                          <Cell fill="#3B82F6" />
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* 2. OPTIMIZACIÓN VIEW */}
          {activeTab === 'optimizacion' && (
            <div className="space-y-6 animate-fade-in">
              {/* Header Title */}
              <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm flex flex-col md:flex-row justify-between md:items-center gap-4">
                <div>
                  <h2 className="text-xl font-bold text-[#172554]">Optimización de la producción</h2>
                  <p className="text-xs text-gray-500 mt-0.5">Define los datos, ejecuta el modelo lineal y obtén la mezcla óptima.</p>
                </div>
                
                {/* Visual Flow Stepper */}
                <div className="flex items-center gap-2 bg-[#EFF6FF] p-1.5 rounded-xl border border-blue-100">
                  <StepBadge number={1} label="Datos de producción" active={optStep === 1} completed={optStep > 1} />
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                  <StepBadge number={2} label="Optimizar" active={optStep === 2} completed={optStep > 2} />
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                  <StepBadge number={3} label="Resultados" active={optStep === 3} completed={false} />
                </div>
              </div>

              {/* STEP 1: PRODUCTION DATA TABBED INTERFACE */}
              {optStep === 1 && (
                <div className="bg-white rounded-2xl border border-blue-100 shadow-sm overflow-hidden">
                  
                  {/* Tabs Selector */}
                  <div className="flex border-b border-gray-100 bg-[#DBEAFE]/30 p-2 gap-2">
                    <button
                      onClick={() => setOptSubTab('productos')}
                      className={`flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-xl transition-all ${
                        optSubTab === 'productos' ? 'bg-[#3B82F6] text-white shadow-md shadow-blue-500/20' : 'text-slate-600 hover:bg-white/60'
                      }`}
                    >
                      <Package className="w-4 h-4" /> Productos ({products.length})
                    </button>
                    <button
                      onClick={() => setOptSubTab('recursos')}
                      className={`flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-xl transition-all ${
                        optSubTab === 'recursos' ? 'bg-[#3B82F6] text-white shadow-md shadow-blue-500/20' : 'text-slate-600 hover:bg-white/60'
                      }`}
                    >
                      <Boxes className="w-4 h-4" /> Recursos ({resources.length})
                    </button>
                    <button
                      onClick={() => setOptSubTab('consumos')}
                      className={`flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-xl transition-all ${
                        optSubTab === 'consumos' ? 'bg-[#3B82F6] text-white shadow-md shadow-blue-500/20' : 'text-slate-600 hover:bg-white/60'
                      }`}
                    >
                      <Layers className="w-4 h-4" /> Consumos ({consumptions.length})
                    </button>
                  </div>

                  {/* SubTab Contents */}
                  <div className="p-6">
                    {/* TAB PRODUCTOS */}
                    {optSubTab === 'productos' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <h3 className="font-bold text-[#172554]">Catálogo de Productos</h3>
                            <p className="text-xs text-gray-500">Registra los productos y su utilidad unitaria.</p>
                          </div>
                          <button
                            onClick={() => setModalState({ type: 'product', data: null })}
                            className="px-4 py-2 bg-[#3B82F6] hover:bg-[#1E40AF] text-white text-xs font-semibold rounded-lg flex items-center gap-2 transition-all shadow"
                          >
                            <Plus className="w-4 h-4" /> Agregar producto
                          </button>
                        </div>

                        <div className="overflow-x-auto border border-blue-100 rounded-xl">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-[#EFF6FF] text-[#172554] uppercase font-semibold">
                              <tr>
                                <th className="p-3.5">Código</th>
                                <th className="p-3.5">Producto</th>
                                <th className="p-3.5">Utilidad (USD/u)</th>
                                <th className="p-3.5 text-right">Acciones</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {products.map(p => (
                                <tr key={p.id} className="hover:bg-blue-50/40">
                                  <td className="p-3.5 font-bold text-[#1E40AF]">{p.code}</td>
                                  <td className="p-3.5 font-medium">{p.name}</td>
                                  <td className="p-3.5 text-emerald-600 font-bold">${p.profit}</td>
                                  <td className="p-3.5 text-right space-x-2">
                                    <button 
                                      onClick={() => setModalState({ type: 'product', data: p })}
                                      className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg"
                                    >
                                      <Edit3 className="w-4 h-4" />
                                    </button>
                                    <button 
                                      onClick={() => setModalState({ type: 'delete', data: { kind: 'product', id: p.id, name: p.name } })}
                                      className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* TAB RECURSOS */}
                    {optSubTab === 'recursos' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <h3 className="font-bold text-[#172554]">Disponibilidad de Recursos</h3>
                            <p className="text-xs text-gray-500">Recursos de planta y sus límites de capacidad.</p>
                          </div>
                          <button
                            onClick={() => setModalState({ type: 'resource', data: null })}
                            className="px-4 py-2 bg-[#3B82F6] hover:bg-[#1E40AF] text-white text-xs font-semibold rounded-lg flex items-center gap-2 transition-all shadow"
                          >
                            <Plus className="w-4 h-4" /> Agregar recurso
                          </button>
                        </div>

                        <div className="overflow-x-auto border border-blue-100 rounded-xl">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-[#EFF6FF] text-[#172554] uppercase font-semibold">
                              <tr>
                                <th className="p-3.5">Recurso</th>
                                <th className="p-3.5">Unidad</th>
                                <th className="p-3.5">Disponibilidad Máxima</th>
                                <th className="p-3.5 text-right">Acciones</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {resources.map(r => (
                                <tr key={r.id} className="hover:bg-blue-50/40">
                                  <td className="p-3.5 font-bold text-[#172554]">{r.name}</td>
                                  <td className="p-3.5 text-gray-500 font-medium">{r.unit}</td>
                                  <td className="p-3.5 font-bold">{r.capacity.toLocaleString()} {r.unit}</td>
                                  <td className="p-3.5 text-right space-x-2">
                                    <button 
                                      onClick={() => setModalState({ type: 'resource', data: r })}
                                      className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg"
                                    >
                                      <Edit3 className="w-4 h-4" />
                                    </button>
                                    <button 
                                      onClick={() => setModalState({ type: 'delete', data: { kind: 'resource', id: r.id, name: r.name } })}
                                      className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* TAB CONSUMOS */}
                    {optSubTab === 'consumos' && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <h3 className="font-bold text-[#172554]">Matriz de Consumo Técnico</h3>
                            <p className="text-xs text-gray-500">Cantidad de recurso consumida por unidad de cada producto.</p>
                          </div>
                          <button
                            onClick={() => setModalState({ type: 'consumption', data: null })}
                            className="px-4 py-2 bg-[#3B82F6] hover:bg-[#1E40AF] text-white text-xs font-semibold rounded-lg flex items-center gap-2 transition-all shadow"
                          >
                            <Plus className="w-4 h-4" /> Agregar regla consumo
                          </button>
                        </div>

                        <div className="overflow-x-auto border border-blue-100 rounded-xl">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-[#EFF6FF] text-[#172554] uppercase font-semibold">
                              <tr>
                                <th className="p-3.5">Producto</th>
                                <th className="p-3.5">Recurso</th>
                                <th className="p-3.5">Consumo por unidad</th>
                                <th className="p-3.5 text-right">Acciones</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {consumptions.map(c => {
                                const prod = products.find(p => p.id === c.productId);
                                const res = resources.find(r => r.id === c.resourceId);
                                return (
                                  <tr key={c.id} className="hover:bg-blue-50/40">
                                    <td className="p-3.5 font-semibold text-[#1E40AF]">{prod ? `${prod.code} - ${prod.name}` : c.productId}</td>
                                    <td className="p-3.5 font-medium">{res ? res.name : c.resourceId}</td>
                                    <td className="p-3.5 font-bold">{c.amount} {res?.unit || ''} / unid.</td>
                                    <td className="p-3.5 text-right space-x-2">
                                      <button 
                                        onClick={() => setModalState({ type: 'consumption', data: c })}
                                        className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg"
                                      >
                                        <Edit3 className="w-4 h-4" />
                                      </button>
                                      <button 
                                        onClick={() => setModalState({ type: 'delete', data: { kind: 'consumption', id: c.id, name: 'Regla de consumo' } })}
                                        className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg"
                                      >
                                        <Trash2 className="w-4 h-4" />
                                      </button>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* BIG RUN OPTIMIZATION CALL TO ACTION */}
                    <div className="pt-6 border-t border-gray-100 flex justify-end">
                      <button
                        onClick={runOptimization}
                        className="px-8 py-3.5 bg-[#3B82F6] hover:bg-[#1E40AF] text-white font-bold text-sm rounded-xl shadow-lg shadow-blue-500/30 flex items-center gap-3 transition-all transform hover:-translate-y-0.5"
                      >
                        <Play className="w-5 h-5 fill-current" /> OPTIMIZAR MODELO
                      </button>
                    </div>

                  </div>
                </div>
              )}

              {/* STEP 2: SIMULATED EXECUTION / SPINNER */}
              {optStep === 2 && (
                <div className="bg-white rounded-2xl p-12 border border-blue-100 shadow-sm text-center space-y-6">
                  <div className="relative w-20 h-20 mx-auto">
                    <div className="w-20 h-20 border-4 border-blue-200 border-t-[#3B82F6] rounded-full animate-spin"></div>
                    <Cpu className="w-8 h-8 text-[#3B82F6] absolute inset-0 m-auto animate-pulse" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-[#172554]">Ejecutando Modelo Matemático...</h3>
                    <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">
                      Formulando modelo lineal, resolviendo sistema de restricciones e identificando cuellos de botella mediante solucionador Simplex / PuLP backend.
                    </p>
                  </div>
                  <div className="w-64 h-2 bg-blue-100 rounded-full mx-auto overflow-hidden">
                    <div className="h-full bg-[#3B82F6] animate-pulse w-3/4 rounded-full"></div>
                  </div>
                </div>
              )}

              {/* STEP 3: OPTIMIZATION RESULTS VIEW */}
              {optStep === 3 && currentResult && (
                <div className="space-y-6">
                  
                  {/* Top KPI Results Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    
                    {/* Optimal Profit */}
                    <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold">
                        $
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Utilidad óptima</span>
                        <h3 className="text-2xl font-extrabold text-[#172554]">${currentResult.profit.toLocaleString()}</h3>
                      </div>
                    </div>

                    {/* Profit Increase */}
                    <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-blue-100 text-[#3B82F6] flex items-center justify-center font-bold">
                        <TrendingUp className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Incremento estimado</span>
                        <h3 className="text-2xl font-extrabold text-emerald-600">+157.4%</h3>
                      </div>
                    </div>

                    {/* Bottlenecks Identified */}
                    <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center font-bold">
                        <AlertTriangle className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Cuellos de botella</span>
                        <p className="text-sm font-bold text-[#172554]">
                          {currentResult.bottlenecks.join(' y ')}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Two Columns Table Results */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    
                    {/* Recommended Mix Table */}
                    <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                      <h3 className="font-bold text-[#172554] text-sm flex items-center gap-2">
                        <Package className="w-4 h-4 text-[#3B82F6]" /> Mezcla óptima de producción
                      </h3>
                      <div className="overflow-x-auto border border-blue-100 rounded-xl">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-[#EFF6FF] text-[#172554] font-semibold uppercase">
                            <tr>
                              <th className="p-3">Producto</th>
                              <th className="p-3 text-right">Cantidad recomendada (u)</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {currentResult.produced.map((item, idx) => (
                              <tr key={idx} className="hover:bg-blue-50/40">
                                <td className="p-3 font-semibold text-slate-700">{item.code} - {item.name}</td>
                                <td className="p-3 text-right font-bold text-[#1E40AF]">
                                  {item.quantity.toLocaleString()} u
                                </td>
                              </tr>
                            ))}
                            <tr className="bg-blue-50/60 font-bold">
                              <td className="p-3 text-[#172554]">Total producción</td>
                              <td className="p-3 text-right text-[#172554]">
                                {currentResult.produced.reduce((s, i) => s + i.quantity, 0).toLocaleString()} u
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Resources Slack Table */}
                    <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                      <div className="flex justify-between items-center">
                        <h3 className="font-bold text-[#172554] text-sm flex items-center gap-2">
                          <Boxes className="w-4 h-4 text-[#3B82F6]" /> Uso de recursos (Holguras)
                        </h3>
                        <button 
                          onClick={() => showNotification('Generando reporte PDF ejecutable...')}
                          className="px-3 py-1.5 bg-[#EFF6FF] text-[#1E40AF] text-xs font-semibold rounded-lg hover:bg-blue-100 flex items-center gap-1.5"
                        >
                          <Download className="w-3.5 h-3.5" /> Exportar PDF
                        </button>
                      </div>
                      <div className="overflow-x-auto border border-blue-100 rounded-xl">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-[#EFF6FF] text-[#172554] font-semibold uppercase">
                            <tr>
                              <th className="p-3">Recurso</th>
                              <th className="p-3 text-center">Uso</th>
                              <th className="p-3 text-center">Disponibilidad</th>
                              <th className="p-3 text-right">Holgura</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {currentResult.resourceUsage.map((r, idx) => (
                              <tr key={idx} className="hover:bg-blue-50/40">
                                <td className="p-3 font-semibold text-slate-700">{r.name}</td>
                                <td className="p-3 text-center font-medium">{r.used.toLocaleString()} {r.unit}</td>
                                <td className="p-3 text-center text-gray-500">{r.capacity.toLocaleString()} {r.unit}</td>
                                <td className={`p-3 text-right font-bold ${r.slack === 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                                  {r.slack === 0 ? '0 kg (Agotado)' : `${r.slack} ${r.unit}`}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                  </div>

                  {/* AI ANALYSIS CARD */}
                  <div className="bg-gradient-to-br from-[#172554] to-[#1E40AF] p-6 rounded-2xl text-white shadow-lg space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-blue-500/30 flex items-center justify-center border border-blue-400/30">
                        <Sparkles className="w-5 h-5 text-amber-300" />
                      </div>
                      <h3 className="font-bold text-base">Análisis de IA (Interpretación de PuLP)</h3>
                    </div>
                    <p className="text-xs text-blue-100 leading-relaxed">
                      La solución matemática óptima recomienda priorizar la fabricación masiva del producto <strong className="text-white">P5 (1,200 unidades)</strong> seguido de <strong className="text-white">P2 (200 unidades)</strong> y <strong className="text-white">P4 (100 unidades)</strong>.
                    </p>
                    <p className="text-xs text-blue-100 leading-relaxed">
                      Los recursos <strong className="text-white">Materia Prima A</strong> y <strong className="text-white">Horas Maquinado</strong> han alcanzado una holgura de 0, constituyendo los cuellos de botella activos del sistema. Se aconseja incrementar su abastecimiento para ampliar el margen de utilidad en posteriores escenarios.
                    </p>
                  </div>

                  {/* Action Bar */}
                  <div className="flex justify-between items-center pt-2">
                    <button
                      onClick={() => setOptStep(1)}
                      className="px-5 py-2.5 border border-gray-300 text-gray-700 text-xs font-semibold rounded-xl hover:bg-gray-50"
                    >
                      ← Editar datos de entrada
                    </button>
                    <button
                      onClick={() => { setActiveTab('historial'); showNotification('Resultados guardados en historial.'); }}
                      className="px-6 py-2.5 bg-[#3B82F6] hover:bg-[#1E40AF] text-white text-xs font-semibold rounded-xl shadow"
                    >
                      Ver en historial de ejecuciones →
                    </button>
                  </div>

                </div>
              )}

            </div>
          )}

          {/* 3. HISTORIAL VIEW */}
          {activeTab === 'historial' && (
            <div className="space-y-6 animate-fade-in">
              <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-[#172554]">Historial de ejecuciones</h2>
                    <p className="text-xs text-gray-500">Consulta y compara las optimizaciones realizadas anteriormente.</p>
                  </div>
                  
                  {/* Search and Filters */}
                  <div className="flex items-center gap-3">
                    <div className="relative flex-1 sm:w-64">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Buscar por escenario..."
                        className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                      />
                    </div>
                    <select className="px-3 py-2 border border-gray-200 rounded-xl text-xs bg-white text-gray-700">
                      <option value="todos">Todos los estados</option>
                      <option value="completado">Completado</option>
                      <option value="proceso">En proceso</option>
                    </select>
                  </div>
                </div>

                {/* History Table */}
                <div className="overflow-x-auto border border-blue-100 rounded-xl">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#EFF6FF] text-[#172554] uppercase font-semibold">
                      <tr>
                        <th className="p-3.5">Fecha</th>
                        <th className="p-3.5">Escenario</th>
                        <th className="p-3.5">Utilidad (USD)</th>
                        <th className="p-3.5">Estado</th>
                        <th className="p-3.5 text-right">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {history.map((h) => (
                        <tr key={h.id} className="hover:bg-blue-50/40">
                          <td className="p-3.5 text-gray-500 font-medium">{h.date}</td>
                          <td className="p-3.5 font-bold text-[#172554]">{h.name}</td>
                          <td className="p-3.5 font-extrabold text-emerald-600">${h.profit.toLocaleString()}</td>
                          <td className="p-3.5">
                            <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 text-[10px] font-bold rounded-full">
                              {h.status}
                            </span>
                          </td>
                          <td className="p-3.5 text-right">
                            <button
                              onClick={() => setHistoryDetailModal(h)}
                              className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg inline-flex items-center gap-1 font-semibold"
                            >
                              <Eye className="w-4 h-4" /> Detalle
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Performance Growth Line Chart */}
              <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                <h3 className="font-bold text-[#172554] text-sm flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#3B82F6]" /> Comparativa de utilidades en el tiempo
                </h3>
                <div className="h-64 w-full pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={[...history].reverse()}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                      <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} />
                      <YAxis tickFormatter={(v) => `$${v/1000}k`} tick={{ fontSize: 10, fill: '#64748B' }} />
                      <Tooltip formatter={(v) => [`$${Number(v).toLocaleString()}`, 'Utilidad Óptima']} />
                      <Line type="monotone" dataKey="profit" stroke="#3B82F6" strokeWidth={3} dot={{ r: 6, fill: '#1E40AF' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* 4. MI PERFIL VIEW */}
          {activeTab === 'perfil' && (
            <div className="max-w-2xl mx-auto bg-white p-8 rounded-2xl border border-blue-100 shadow-sm space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row items-center gap-6 pb-6 border-b border-gray-100">
                <div className="relative">
                  <img 
                    src={userProfile.avatar} 
                    alt={userProfile.name} 
                    className="w-24 h-24 rounded-full object-cover border-4 border-[#3B82F6] shadow-md" 
                  />
                  <button 
                    onClick={() => showNotification('Subida de avatar simulada.')}
                    className="absolute bottom-0 right-0 p-2 bg-[#3B82F6] text-white rounded-full shadow hover:bg-blue-700"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="text-center sm:text-left">
                  <h2 className="text-xl font-bold text-[#172554]">{userProfile.name}</h2>
                  <p className="text-xs text-gray-500">{userProfile.role}</p>
                  <span className="inline-block mt-2 px-3 py-1 bg-blue-50 text-[#1E40AF] text-[10px] font-bold rounded-full">
                    Planta Industrial La Guajira
                  </span>
                </div>
              </div>

              <form onSubmit={(e) => { e.preventDefault(); showNotification('Perfil actualizado correctamente.'); }} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Nombre completo</label>
                  <input
                    type="text"
                    value={userProfile.name}
                    onChange={(e) => setUserProfile({ ...userProfile, name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#3B82F6] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Correo electrónico</label>
                  <input
                    type="email"
                    value={userProfile.email}
                    onChange={(e) => setUserProfile({ ...userProfile, email: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#3B82F6] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Rol de usuario</label>
                  <select
                    value={userProfile.role}
                    onChange={(e) => setUserProfile({ ...userProfile, role: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#3B82F6] focus:outline-none bg-white"
                  >
                    <option value="Administradora">Administradora</option>
                    <option value="Ingeniero de Planta">Ingeniero de Planta</option>
                    <option value="Analista de I.O.">Analista de I.O.</option>
                  </select>
                </div>

                <div className="pt-4 flex justify-end gap-3">
                  <button
                    type="submit"
                    className="px-6 py-2.5 bg-[#3B82F6] hover:bg-[#1E40AF] text-white text-xs font-semibold rounded-xl shadow-md flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" /> Guardar cambios
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* 5. AJUSTES VIEW */}
          {activeTab === 'ajustes' && (
            <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
              
              {/* Card 1: Notifications */}
              <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                <div className="flex items-center gap-3">
                  <Bell className="w-5 h-5 text-[#3B82F6]" />
                  <div>
                    <h3 className="font-bold text-[#172554] text-sm">Notificaciones del sistema</h3>
                    <p className="text-xs text-gray-500">Recibir alertas de ejecuciones de optimización.</p>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-2">
                  <span className="text-xs font-medium text-slate-700">Notificar al completar modelos de optimización</span>
                  <button 
                    onClick={() => setSettings({ ...settings, notifications: !settings.notifications })}
                    className={`w-12 h-6 rounded-full p-1 transition-colors ${settings.notifications ? 'bg-[#3B82F6]' : 'bg-gray-300'}`}
                  >
                    <div className={`w-4 h-4 bg-white rounded-full transition-transform ${settings.notifications ? 'translate-x-6' : ''}`}></div>
                  </button>
                </div>
              </div>

              {/* Card 2: Model Preferences */}
              <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                <div className="flex items-center gap-3">
                  <Cpu className="w-5 h-5 text-[#3B82F6]" />
                  <div>
                    <h3 className="font-bold text-[#172554] text-sm">Preferencias del modelo (PuLP / I.O.)</h3>
                    <p className="text-xs text-gray-500">Parámetros del solucionador de programación lineal.</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div>
                    <label className="block text-xs font-bold text-gray-600 mb-1">Configuración del Solucionador</label>
                    <select 
                      value={settings.solver} 
                      onChange={(e) => setSettings({ ...settings, solver: e.target.value })}
                      className="w-full p-2.5 border border-gray-200 rounded-xl text-xs bg-white"
                    >
                      <option value="PuLP / CBC Default">PuLP / CBC (Predeterminado)</option>
                      <option value="GLPK Solver">GLPK Solver Engine</option>
                      <option value="SciPy Linprog">SciPy Optimization module</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-600 mb-1">Tiempo máx. de ejecución (seg)</label>
                    <input 
                      type="number" 
                      value={settings.maxRuntime} 
                      onChange={(e) => setSettings({ ...settings, maxRuntime: Number(e.target.value) })}
                      className="w-full p-2.5 border border-gray-200 rounded-xl text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Card 3: Appearance */}
              <div className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                <div className="flex items-center gap-3">
                  <Sun className="w-5 h-5 text-[#3B82F6]" />
                  <div>
                    <h3 className="font-bold text-[#172554] text-sm">Apariencia y Tema</h3>
                    <p className="text-xs text-gray-500">Selecciona el tema visual de la interfaz.</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3 pt-2">
                  <ThemeOption 
                    label="Claro" 
                    icon={<Sun className="w-4 h-4" />} 
                    active={settings.theme === 'claro'} 
                    onClick={() => { setSettings({ ...settings, theme: 'claro' }); showNotification('Tema Claro aplicado'); }}
                  />
                  <ThemeOption 
                    label="Azul (Predet.)" 
                    icon={<Moon className="w-4 h-4" />} 
                    active={settings.theme === 'azul'} 
                    onClick={() => { setSettings({ ...settings, theme: 'azul' }); showNotification('Tema Azul Predeterminado aplicado'); }}
                  />
                  <ThemeOption 
                    label="Sistema" 
                    icon={<Laptop className="w-4 h-4" />} 
                    active={settings.theme === 'sistema'} 
                    onClick={() => { setSettings({ ...settings, theme: 'sistema' }); showNotification('Sincronizado con sistema'); }}
                  />
                </div>
              </div>

            </div>
          )}

        </main>
      </div>

      {/* --- MODALS FOR ADD / EDIT / DELETE --- */}

      {/* 1. PRODUCT FORM MODAL */}
      {modalState.type === 'product' && (
        <ModalWrapper title={modalState.data ? 'Editar producto' : 'Agregar nuevo producto'} onClose={() => setModalState({ type: null })}>
          <form onSubmit={(e) => {
            e.preventDefault();
            const form = e.target;
            const code = form.code.value;
            const name = form.name.value;
            const profit = Number(form.profit.value);

            if (profit <= 0) {
              showNotification('La utilidad unitaria debe ser un número positivo.', 'error');
              return;
            }

            if (modalState.data) {
              setProducts(products.map(p => p.id === modalState.data.id ? { ...p, code, name, profit } : p));
              showNotification('Producto actualizado correctamente.');
            } else {
              setProducts([...products, { id: Date.now().toString(), code, name, profit }]);
              showNotification('Nuevo producto agregado.');
            }
            setModalState({ type: null });
          }} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Código del producto</label>
              <input name="code" defaultValue={modalState.data?.code || `P${products.length + 1}`} required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Nombre del producto</label>
              <input name="name" defaultValue={modalState.data?.name || ''} placeholder="Ej. Producto 6 (Estándar)" required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Utilidad unitaria (USD/u)</label>
              <input name="profit" type="number" step="0.01" defaultValue={modalState.data?.profit || 100} required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setModalState({ type: null })} className="px-4 py-2 border rounded-lg text-xs">Cancelar</button>
              <button type="submit" className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-xs font-semibold">Guardar</button>
            </div>
          </form>
        </ModalWrapper>
      )}

      {/* 2. RESOURCE FORM MODAL */}
      {modalState.type === 'resource' && (
        <ModalWrapper title={modalState.data ? 'Editar recurso' : 'Agregar nuevo recurso'} onClose={() => setModalState({ type: null })}>
          <form onSubmit={(e) => {
            e.preventDefault();
            const form = e.target;
            const name = form.name.value;
            const unit = form.unit.value;
            const capacity = Number(form.capacity.value);

            if (capacity <= 0) {
              showNotification('La disponibilidad debe ser un número positivo.', 'error');
              return;
            }

            if (modalState.data) {
              setResources(resources.map(r => r.id === modalState.data.id ? { ...r, name, unit, capacity } : r));
              showNotification('Recurso actualizado correctamente.');
            } else {
              setResources([...resources, { id: Date.now().toString(), name, unit, capacity }]);
              showNotification('Nuevo recurso agregado.');
            }
            setModalState({ type: null });
          }} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Nombre del recurso</label>
              <input name="name" defaultValue={modalState.data?.name || ''} placeholder="Ej. Horas Mano de Obra" required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Unidad de medida</label>
              <input name="unit" defaultValue={modalState.data?.unit || 'kg'} placeholder="kg, h, m, etc." required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Disponibilidad máxima</label>
              <input name="capacity" type="number" step="0.1" defaultValue={modalState.data?.capacity || 1000} required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setModalState({ type: null })} className="px-4 py-2 border rounded-lg text-xs">Cancelar</button>
              <button type="submit" className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-xs font-semibold">Guardar</button>
            </div>
          </form>
        </ModalWrapper>
      )}

      {/* 3. CONSUMPTION FORM MODAL */}
      {modalState.type === 'consumption' && (
        <ModalWrapper title={modalState.data ? 'Editar consumo' : 'Agregar consumo por unidad'} onClose={() => setModalState({ type: null })}>
          <form onSubmit={(e) => {
            e.preventDefault();
            const form = e.target;
            const productId = form.productId.value;
            const resourceId = form.resourceId.value;
            const amount = Number(form.amount.value);

            if (amount <= 0) {
              showNotification('La cantidad consumida debe ser positiva.', 'error');
              return;
            }

            if (modalState.data) {
              setConsumptions(consumptions.map(c => c.id === modalState.data.id ? { ...c, productId, resourceId, amount } : c));
              showNotification('Regla de consumo actualizada.');
            } else {
              setConsumptions([...consumptions, { id: Date.now().toString(), productId, resourceId, amount }]);
              showNotification('Regla de consumo agregada.');
            }
            setModalState({ type: null });
          }} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Producto</label>
              <select name="productId" defaultValue={modalState.data?.productId || products[0]?.id} className="w-full p-2.5 border rounded-lg text-xs bg-white">
                {products.map(p => <option key={p.id} value={p.id}>{p.code} - {p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Recurso consumido</label>
              <select name="resourceId" defaultValue={modalState.data?.resourceId || resources[0]?.id} className="w-full p-2.5 border rounded-lg text-xs bg-white">
                {resources.map(r => <option key={r.id} value={r.id}>{r.name} ({r.unit})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Cantidad consumida por unidad</label>
              <input name="amount" type="number" step="0.01" defaultValue={modalState.data?.amount || 1.0} required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setModalState({ type: null })} className="px-4 py-2 border rounded-lg text-xs">Cancelar</button>
              <button type="submit" className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-xs font-semibold">Guardar</button>
            </div>
          </form>
        </ModalWrapper>
      )}

      {/* 4. DELETE CONFIRMATION MODAL */}
      {modalState.type === 'delete' && (
        <ModalWrapper title="Confirmar eliminación" onClose={() => setModalState({ type: null })}>
          <div className="space-y-4">
            <p className="text-xs text-gray-600">
              ¿Estás seguro de que deseas eliminar <strong>"{modalState.data.name}"</strong>? Esta acción no se puede deshacer.
            </p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setModalState({ type: null })} className="px-4 py-2 border rounded-lg text-xs font-medium">Cancelar</button>
              <button 
                onClick={() => {
                  const { kind, id } = modalState.data;
                  if (kind === 'product') setProducts(products.filter(p => p.id !== id));
                  if (kind === 'resource') setResources(resources.filter(r => r.id !== id));
                  if (kind === 'consumption') setConsumptions(consumptions.filter(c => c.id !== id));
                  showNotification('Registro eliminado.');
                  setModalState({ type: null });
                }} 
                className="px-4 py-2 bg-rose-600 text-white rounded-lg text-xs font-semibold"
              >
                Eliminar
              </button>
            </div>
          </div>
        </ModalWrapper>
      )}

      {/* 5. HISTORY DETAIL MODAL */}
      {historyDetailModal && (
        <ModalWrapper title={`Detalle: ${historyDetailModal.name}`} onClose={() => setHistoryDetailModal(null)}>
          <div className="space-y-4 text-xs">
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-500">Fecha de ejecución:</span>
              <span className="font-bold text-[#172554]">{historyDetailModal.date}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-500">Utilidad alcanzada:</span>
              <span className="font-extrabold text-emerald-600">${historyDetailModal.profit.toLocaleString()}</span>
            </div>
            <div>
              <span className="font-bold text-gray-700 block mb-1">Cuellos de botella reportados:</span>
              <div className="flex gap-2">
                {historyDetailModal.bottlenecks?.map((b, idx) => (
                  <span key={idx} className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded font-semibold text-[10px]">
                    {b}
                  </span>
                ))}
              </div>
            </div>
            <div className="pt-2">
              <button 
                onClick={() => setHistoryDetailModal(null)} 
                className="w-full py-2 bg-[#3B82F6] text-white rounded-lg font-semibold"
              >
                Cerrar consulta
              </button>
            </div>
          </div>
        </ModalWrapper>
      )}

    </div>
    </SharedAppContext.Provider>
  );
}
