import { apiList, apiRequest, clearAccessToken, setAccessToken } from './services/api';
import { lazy, Suspense, useState, useEffect, useCallback } from 'react';
import { 
  LayoutDashboard, 
  Cpu, 
  History, 
  User, 
  Settings, 
  LogOut, 
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
  Eye, 
  Save, 
  AlertTriangle, 
  X, 
  Lock, 
  Mail, 
  BarChart2, 
  ArrowUpRight,
  Download,
  Clock,
  RefreshCw
} from 'lucide-react';
const problemStorageKey = (id) => `planificai_problem_${id}`;
const ProfitChart = lazy(() => import('./components/ProfitChart'));

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isRestoring, setIsRestoring] = useState(true);
  const [authMode, setAuthMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [workspaceId, setWorkspaceId] = useState(() => localStorage.getItem('planificai_workspace'));
  const [problemId, setProblemId] = useState(null);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [workspaces, setWorkspaces] = useState([]);
  const [problems, setProblems] = useState([]);
  const [members, setMembers] = useState([]);

  const [registerData, setRegisterData] = useState({
    nombre: '',
    apellido: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [activeTab, setActiveTab] = useState('inicio');
  const [toast, setToast] = useState(null);
  const [userProfile, setUserProfile] = useState({
    name: '',
    username: '',
    email: '',
    role: ''
  });
  const [products, setProducts] = useState([]);
  const [resources, setResources] = useState([]);
  const [consumptions, setConsumptions] = useState([]);
  const [history, setHistory] = useState([]);
  const [historyQuery, setHistoryQuery] = useState('');
  const [historyStatus, setHistoryStatus] = useState('all');
  const [optStep, setOptStep] = useState(1);
  const [optSubTab, setOptSubTab] = useState('productos');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);
  const [modalState, setModalState] = useState({ type: null, data: null });
  const [historyDetailModal, setHistoryDetailModal] = useState(null);
  const [recoveryUsername, setRecoveryUsername] = useState('');
  const [passwordChange, setPasswordChange] = useState({
    current_password: '',
    new_password: '',
    new_password_confirm: ''
  });
  const [memberForm, setMemberForm] = useState({ username: '', rol: 'EDITOR' });

  const showNotification = useCallback((msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  const canWrite = ['OWNER', 'ADMIN', 'EDITOR'].includes(userProfile.role);
  const canManageMembers = ['OWNER', 'ADMIN'].includes(userProfile.role);
  const activeProblem = problems.find((item) => Number(item.id) === Number(problemId));
  const productsWithoutPositiveConsumption = activeProblem?.sentido_objetivo === 'MAXIMIZAR'
    ? products.filter((product) => product.profit > 0 && !consumptions.some(
      (consumption) => consumption.productId === product.id && consumption.amount > 0
    ))
    : [];
  const visibleHistory = history.filter((item) => (
    item.name.toLowerCase().includes(historyQuery.trim().toLowerCase())
    && (historyStatus === 'all' || item.status === historyStatus)
  ));

  const clearLocalSession = useCallback(() => {
    clearAccessToken();
    localStorage.removeItem('planificai_access');
    localStorage.removeItem('planificai_refresh');
    localStorage.removeItem('planificai_workspace');
    Object.keys(localStorage)
      .filter((key) => key.startsWith('planificai_problem_'))
      .forEach((key) => localStorage.removeItem(key));
    setWorkspaceId(null);
    setProblemId(null);
    setWorkspaces([]);
    setProblems([]);
    setMembers([]);
    setProducts([]);
    setResources([]);
    setConsumptions([]);
    setHistory([]);
    setCurrentResult(null);
    setUserProfile({ name: '', username: '', email: '', role: '' });
    setHistoryQuery('');
    setHistoryStatus('all');
    setPasswordChange({
      current_password: '',
      new_password: '',
      new_password_confirm: ''
    });
    setIsAuthenticated(false);
    setPassword('');
    setAuthMode('login');
  }, []);

  const loadBackendData = useCallback(async (selectedWorkspaceId, preferredProblemId) => {
    if (!selectedWorkspaceId) throw new Error('Selecciona un Workspace válido.');
    const previousWorkspaceId = localStorage.getItem('planificai_workspace');
    setIsLoadingData(true);
    localStorage.setItem('planificai_workspace', String(selectedWorkspaceId));
    try {
      const [problemItems, workspaceMembers] = await Promise.all([
        apiList('/api/problemas/'),
        apiList(`/api/workspaces/${selectedWorkspaceId}/miembros/`)
      ]);
      const savedProblemId = preferredProblemId
        ?? localStorage.getItem(problemStorageKey(selectedWorkspaceId));
      const problem = problemItems.find((item) => Number(item.id) === Number(savedProblemId))
        || problemItems[0]
        || null;

      if (!problem) {
        setWorkspaceId(String(selectedWorkspaceId));
        setProblems(problemItems);
        setMembers(workspaceMembers);
        setProblemId(null);
        setProducts([]);
        setResources([]);
        setConsumptions([]);
        setHistory([]);
        setCurrentResult(null);
        localStorage.removeItem(problemStorageKey(selectedWorkspaceId));
        return { historyItems: [], problemItems };
      }

      const [productData, resourceData, consumptionData, executionData] = await Promise.all([
        apiList(`/api/productos/?problema=${problem.id}`),
        apiList(`/api/recursos/?problema=${problem.id}`),
        apiList(`/api/consumos/?problema=${problem.id}`),
        apiList(`/api/ejecuciones/?problema=${problem.id}`)
      ]);
      const productItems = productData.map((item) => ({
        id: Number(item.id),
        code: item.codigo,
        name: item.nombre,
        description: item.descripcion,
        profit: Number(item.utilidad_unitaria)
      }));
      const resourceItems = resourceData.map((item) => ({
        id: Number(item.id),
        name: item.nombre,
        unit: item.unidad_medida,
        capacity: Number(item.disponibilidad)
      }));
      const consumptionItems = consumptionData.map((item) => ({
        id: Number(item.id),
        productId: Number(item.producto),
        resourceId: Number(item.recurso),
        amount: Number(item.cantidad_por_unidad)
      }));

      const historyItems = await Promise.all(executionData.map(async (execution) => {
        const [productResults, resourceResults] = await Promise.all([
          apiList(`/api/resultados-productos/?ejecucion=${execution.id}`),
          apiList(`/api/resultados-recursos/?ejecucion=${execution.id}`)
        ]);

        const producedItems = productResults.map((item) => {
          const product = productItems.find(({ id }) => id === Number(item.producto));
          return {
            id: Number(item.producto),
            code: product?.code || String(item.producto),
            name: item.nombre_producto,
            quantity: Number(item.cantidad),
            profit: Number(item.utilidad_unitaria),
            totalProfit: Number(item.utilidad_aportada)
          };
        });
        const resourceUsage = resourceResults.map((item) => ({
          id: Number(item.recurso),
          name: item.nombre_recurso,
          unit: item.unidad_medida,
          capacity: Number(item.disponibilidad),
          used: Number(item.consumo_total),
          slack: Number(item.holgura),
          isBottleneck: item.estado_uso === 'AGOTADO'
        }));

        return {
          id: `E-${execution.id}`,
          executionId: Number(execution.id),
          date: new Date(execution.fecha_inicio).toLocaleString('es-ES'),
          name: `${problem.nombre} · Ejecución ${execution.id}`,
          profit: execution.utilidad_total === null ? null : Number(execution.utilidad_total),
          errorMessage: execution.mensaje_error || '',
          producedItems,
          produced: producedItems,
          resourceUsage,
          solverStatus: execution.estado_solver,
          solverName: execution.solver_nombre,
          bottlenecks: resourceUsage.filter((item) => item.isBottleneck).map((item) => item.name),
          status: execution.estado_proceso === 'ERROR'
            ? 'Error'
            : execution.estado_solver === 'Optimal'
              ? 'Completado'
              : execution.estado_solver || execution.estado_proceso
        };
      }));
      historyItems.sort((a, b) => b.executionId - a.executionId);

      setWorkspaceId(String(selectedWorkspaceId));
      setProblems(problemItems);
      setMembers(workspaceMembers);
      setProblemId(Number(problem.id));
      setProducts(productItems);
      setResources(resourceItems);
      setConsumptions(consumptionItems);
      setHistory(historyItems);
      setCurrentResult(historyItems.find((item) => item.status === 'Completado') || null);
      localStorage.setItem(problemStorageKey(selectedWorkspaceId), String(problem.id));
      return { historyItems, problemItems };
    } catch (error) {
      if (error.status === 400 || error.status === 401) {
        clearLocalSession();
      } else {
        if (previousWorkspaceId) {
          localStorage.setItem('planificai_workspace', previousWorkspaceId);
        } else {
          localStorage.removeItem('planificai_workspace');
        }
        setWorkspaceId(previousWorkspaceId || null);
      }
      throw error;
    } finally {
      setIsLoadingData(false);
    }
  }, [clearLocalSession]);

  useEffect(() => {
    const handleAuthenticationExpired = () => {
      const hadWorkspace = Boolean(localStorage.getItem('planificai_workspace'));
      clearLocalSession();
      setIsRestoring(false);
      if (hadWorkspace) showNotification('La sesión venció. Inicia sesión nuevamente.', 'error');
    };
    window.addEventListener('planificai:auth-expired', handleAuthenticationExpired);

    const restoreSession = async () => {
      try {
        const [profile, memberships] = await Promise.all([
          apiRequest('/api/auth/perfil/'),
          apiList('/api/workspaces/')
        ]);
        const workspaceItems = memberships;
        const storedWorkspaceId = Number(localStorage.getItem('planificai_workspace'));
        const selected = workspaceItems.find((item) => Number(item.workspace_id) === storedWorkspaceId)
          || workspaceItems[0];
        setUserProfile({
          name: `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || profile.username,
          username: profile.username,
          email: profile.email,
          role: selected?.rol || ''
        });
        setWorkspaces(workspaceItems);
        setIsAuthenticated(true);
        if (selected) {
          await loadBackendData(selected.workspace_id);
        } else {
          showNotification('Tu cuenta no tiene acceso a ningún Workspace.', 'error');
        }
      } catch (error) {
        clearAccessToken();
        if (error.status !== 400 && error.status !== 401) {
          showNotification(error.message, 'error');
        }
      } finally {
        setIsRestoring(false);
      }
    };

    localStorage.removeItem('planificai_access');
    localStorage.removeItem('planificai_refresh');
    restoreSession();

    return () => {
      window.removeEventListener('planificai:auth-expired', handleAuthenticationExpired);
    };
  }, [clearLocalSession, loadBackendData, showNotification]);

  const runOptimization = async () => {
    if (!problemId) {
      showNotification('Crea o selecciona un problema antes de optimizar.', 'error');
      return;
    }
    if (!canWrite) {
      showNotification('Tu rol solo permite consultar este Workspace.', 'error');
      return;
    }
    if (!problems.find((item) => Number(item.id) === Number(problemId))?.estado
      || problems.find((item) => Number(item.id) === Number(problemId))?.estado !== 'LISTO') {
      showNotification('El problema debe estar en estado LISTO para optimizarse.', 'error');
      return;
    }
    if (!products.length || !resources.length || !consumptions.length) {
      showNotification('Agrega productos, recursos y consumos antes de optimizar.', 'error');
      return;
    }
    if (productsWithoutPositiveConsumption.length) {
      setOptSubTab('consumos');
      showNotification(
        'Registra un consumo positivo para cada producto rentable antes de maximizar.',
        'error'
      );
      return;
    }

    setIsOptimizing(true);
    setOptStep(2);
    try {
      const execution = await apiRequest(`/api/problemas/${problemId}/ejecutar/`, {
        method: 'POST',
        body: JSON.stringify({})
      });
      const { historyItems } = await loadBackendData(workspaceId, problemId);
      if (execution.estado_proceso !== 'TERMINADO' || execution.estado_solver !== 'Optimal') {
        const solverMessage = execution.estado_solver === 'Unbounded'
          ? 'El modelo no tiene un límite superior. Revisa que cada producto rentable consuma algún recurso.'
          : `El solver terminó con estado ${execution.estado_solver || execution.estado_proceso}.`;
        throw new Error(execution.mensaje_error || solverMessage);
      }
      const result = historyItems.find((item) => item.executionId === Number(execution.id));
      if (!result) throw new Error('La ejecución terminó, pero no se encontraron sus resultados.');
      setCurrentResult(result);
      showNotification('Optimización ejecutada y resultados cargados desde el servidor.');
      setOptStep(3);
    } catch (error) {
      showNotification(error.message, 'error');
      setOptStep(1);
    } finally {
      setIsOptimizing(false);
    }
  };

  const switchWorkspace = async (nextWorkspaceId) => {
    const membership = workspaces.find(
      (item) => Number(item.workspace_id) === Number(nextWorkspaceId)
    );
    if (!membership || Number(nextWorkspaceId) === Number(workspaceId)) return;

    try {
      await loadBackendData(membership.workspace_id);
      setUserProfile((current) => ({ ...current, role: membership.rol }));
      setOptStep(1);
    } catch (error) {
      showNotification(error.message, 'error');
    }
  };

  const selectProblem = async (nextProblemId) => {
    try {
      await loadBackendData(workspaceId, Number(nextProblemId));
      setOptStep(1);
    } catch (error) {
      showNotification(error.message, 'error');
    }
  };

  const closeSession = async () => {
    setIsSaving(true);
    try {
      await apiRequest('/api/auth/cerrar-sesion/', { method: 'POST' });
      clearLocalSession();
      showNotification('Sesión cerrada.');
    } catch (error) {
      showNotification(error.message, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const addWorkspaceMember = async (event) => {
    event.preventDefault();
    if (!canManageMembers || !memberForm.username.trim()) {
      showNotification('Escribe un username y confirma que tu rol puede administrar miembros.', 'error');
      return;
    }

    setIsSaving(true);
    try {
      const createdMember = await apiRequest(`/api/workspaces/${workspaceId}/miembros/`, {
        method: 'POST',
        body: JSON.stringify({
          username: memberForm.username.trim(),
          rol: memberForm.rol
        })
      });
      setMembers((current) => [...current, createdMember].sort((a, b) => a.username.localeCompare(b.username)));
      setMemberForm({ username: '', rol: 'EDITOR' });
      showNotification('Miembro agregado.');
    } catch (error) {
      showNotification(error.message, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const updateMemberRole = async (member, rol) => {
    setIsSaving(true);
    try {
      const updated = await apiRequest(
        `/api/workspaces/${workspaceId}/miembros/${member.id}/`,
        { method: 'PATCH', body: JSON.stringify({ rol }) }
      );
      setMembers((current) => current.map((item) => item.id === updated.id ? updated : item));
      showNotification('Rol actualizado.');
    } catch (error) {
      showNotification(error.message, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const removeWorkspaceMember = async (member) => {
    setIsSaving(true);
    try {
      await apiRequest(`/api/workspaces/${workspaceId}/miembros/${member.id}/`, {
        method: 'DELETE'
      });
      setMembers((current) => current.filter((item) => item.id !== member.id));
      showNotification('Miembro retirado del Workspace.');
    } catch (error) {
      showNotification(error.message, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const transferWorkspaceOwnership = async (member) => {
    if (userProfile.role !== 'OWNER') return;
    setIsSaving(true);
    try {
      const newOwner = await apiRequest(`/api/workspaces/${workspaceId}/transferir-propiedad/`, {
        method: 'POST',
        body: JSON.stringify({ username: member.username })
      });
      setMembers((current) => current.map((item) => (
        Number(item.id) === Number(newOwner.id)
          ? newOwner
          : item.rol === 'OWNER' ? { ...item, rol: 'ADMIN' } : item
      )));
      setWorkspaces((current) => current.map((item) => (
        Number(item.workspace_id) === Number(workspaceId)
          ? { ...item, rol: 'ADMIN' }
          : item
      )));
      setUserProfile((current) => ({ ...current, role: 'ADMIN' }));
      showNotification('Propiedad transferida.');
    } catch (error) {
      showNotification(error.message, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const saveProblem = async (event) => {
    event.preventDefault();
    if (!canWrite || !workspaceId) {
      showNotification('Tu rol no permite modificar problemas.', 'error');
      return;
    }

    const formData = new FormData(event.currentTarget);
    const nombre = String(formData.get('nombre') || '').trim();
    if (!nombre) {
      showNotification('El nombre del problema es obligatorio.', 'error');
      return;
    }

    const payload = {
      nombre,
      descripcion: String(formData.get('descripcion') || '').trim(),
      sentido_objetivo: String(formData.get('sentido_objetivo')),
      estado: String(formData.get('estado'))
    };
    setIsSaving(true);
    try {
      const problem = modalState.data
        ? await apiRequest(`/api/problemas/${modalState.data.id}/`, {
          method: 'PATCH',
          body: JSON.stringify(payload)
        })
        : await apiRequest('/api/problemas/', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
      if (modalState.data) {
        setProblems((current) => current.map((item) => (
          Number(item.id) === Number(problem.id) ? problem : item
        )));
        setHistory((current) => current.map((item) => ({
          ...item,
          name: `${problem.nombre} · Ejecución ${item.executionId}`
        })));
      } else {
        setProblems((current) => [...current, problem]);
        setProblemId(Number(problem.id));
        localStorage.setItem(problemStorageKey(workspaceId), String(problem.id));
        setProducts([]);
        setResources([]);
        setConsumptions([]);
        setHistory([]);
        setCurrentResult(null);
      }
      setModalState({ type: null, data: null });
      showNotification(modalState.data ? 'Problema actualizado.' : 'Problema creado.');
    } catch (error) {
      showNotification(error.message, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  if (isRestoring) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#EFF6FF] text-[#172554]">
        <RefreshCw className="w-6 h-6 animate-spin mr-3" />
        Restaurando sesión...
      </div>
    );
  }

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
        {isLoadingData && (
          <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/30 backdrop-blur-sm" role="status">
            <div className="flex items-center gap-3 rounded-xl bg-white px-5 py-4 font-semibold text-[#172554] shadow-xl">
              <RefreshCw className="w-5 h-5 animate-spin" />
              Cargando datos del Workspace...
            </div>
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
              <form
                onSubmit={async (e) => {
                  e.preventDefault();

                  if (!email.trim() || !password.trim()) {
                    showNotification('Completa todos los campos.', 'error');
                    return;
                  }
                  setIsSaving(true);
                  try {
                    const tokens = await apiRequest('/api/token/', {
                      method: 'POST',
                      body: JSON.stringify({ username: email.trim(), password })
                    });
                    setAccessToken(tokens.access);

                    const [profile, memberships] = await Promise.all([
                      apiRequest('/api/auth/perfil/'),
                      apiList('/api/workspaces/')
                    ]);
                    const workspaceItems = memberships;
                    if (workspaceItems.length === 0) throw new Error('No tienes un Workspace asignado.');
                    const savedWorkspaceId = Number(localStorage.getItem('planificai_workspace'));
                    const selected = workspaceItems.find(
                      (item) => Number(item.workspace_id) === savedWorkspaceId
                    ) || workspaceItems[0];
                    setUserProfile({
                      name: `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || profile.username,
                      username: profile.username,
                      email: profile.email,
                      role: selected.rol
                    });
                    setWorkspaces(workspaceItems);
                    await loadBackendData(selected.workspace_id);
                    setIsAuthenticated(true);
                    showNotification(`¡Bienvenido/a, ${profile.username}!`);
                  } catch (error) {
                    let cleanupError = null;
                    try {
                      await apiRequest('/api/auth/cerrar-sesion/', { method: 'POST' });
                    } catch (logoutError) {
                      cleanupError = logoutError;
                    }
                    clearAccessToken();
                    showNotification(
                      cleanupError
                        ? `${error.message} No se pudo cerrar la sesión remota: ${cleanupError.message}`
                        : error.message,
                      'error'
                    );
                  } finally {
                    setIsSaving(false);
                  }
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Nombre de usuario
                  </label>

                  <div className="relative">
                    <Mail className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />

                    <input
                      type="text"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="usuario123"
                      autoComplete="username"
                      required
                      className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Contraseña
                  </label>

                  <div className="relative">
                    <Lock className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />

                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Ingresa tu contraseña"
                      autoComplete="current-password"
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

                <div className="flex justify-end text-xs">
                  <button
                    type="button"
                    onClick={() => setAuthMode('recovery')}
                    className="text-[#3B82F6] font-semibold hover:underline"
                  >
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={isSaving}
                  className="w-full py-3 bg-[#3B82F6] hover:bg-[#1E40AF] disabled:opacity-50 text-white font-semibold rounded-lg shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
                >
                  {isSaving ? 'Validando...' : 'Ingresar'} <ArrowUpRight className="w-4 h-4" />
                </button>
              </form>
            ) : authMode === 'register' ? (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const { nombre, apellido, username, email: registrationEmail, password: newPassword, confirmPassword } = registerData;

                  if (![nombre, apellido, username, registrationEmail, newPassword, confirmPassword].every((value) => value.trim())) {
                    showNotification('Completa todos los campos.', 'error');
                    return;
                  }
                  if (newPassword !== confirmPassword) {
                    showNotification('Las contraseñas no coinciden.', 'error');
                    return;
                  }

                  setIsSaving(true);
                  try {
                    const response = await apiRequest('/api/auth/registro/', {
                      method: 'POST',
                      body: JSON.stringify({
                        username: username.trim(),
                        email: registrationEmail.trim(),
                        first_name: nombre.trim(),
                        last_name: apellido.trim(),
                        password: newPassword,
                        password_confirm: confirmPassword
                      })
                    });
                    setEmail(username.trim());
                    setPassword('');
                    setAuthMode('login');
                    showNotification(response.detail || 'Cuenta creada. Ya puedes iniciar sesión.');
                  } catch (error) {
                    showNotification(error.message, 'error');
                  } finally {
                    setIsSaving(false);
                  }
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Nombre
                  </label>

                  <input
                    type="text"
                    value={registerData.nombre}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, nombre: e.target.value })
                    }
                    placeholder="Ingresa tu nombre"
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Apellido
                  </label>

                  <input
                    type="text"
                    value={registerData.apellido}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, apellido: e.target.value })
                    }
                    placeholder="Ingresa tu apellido"
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Nombre de usuario
                  </label>

                  <input
                    type="text"
                    value={registerData.username}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, username: e.target.value })
                    }
                    placeholder="Ej. usuario123"
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Correo electrónico
                  </label>

                  <input
                    type="email"
                    value={registerData.email}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, email: e.target.value })
                    }
                    placeholder="ejemplo@correo.com"
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Rol en la empresa
                  </label>

                  <select
                    value={registerData.rol}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, rol: e.target.value })
                    }
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  >
                    <option value="Administradora">Administradora</option>
                    <option value="Ingeniero de Planta">Ingeniero de Planta</option>
                    <option value="Analista de I.O.">Analista de I.O.</option>
                    <option value="Operador">Operador</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Contraseña
                  </label>

                  <input
                    type="password"
                    value={registerData.password}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, password: e.target.value })
                    }
                    placeholder="Mínimo 8 caracteres"
                    minLength={8}
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Confirmar contraseña
                  </label>

                  <input
                    type="password"
                    value={registerData.confirmPassword}
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        confirmPassword: e.target.value
                      })
                    }
                    placeholder="Repite tu contraseña"
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSaving}
                  className="w-full py-3 bg-[#3B82F6] hover:bg-[#1E40AF] disabled:opacity-50 text-white font-semibold rounded-lg shadow-lg shadow-blue-500/25 transition-all mt-2"
                >
                  {isSaving ? 'Creando cuenta...' : 'Crear cuenta'}
                </button>
              </form>
            ) : (
              <form
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (!recoveryUsername.trim()) {
                    showNotification('Escribe tu nombre de usuario.', 'error');
                    return;
                  }
                  setIsSaving(true);
                  try {
                    const response = await apiRequest('/api/auth/recuperar-contrasena/', {
                      method: 'POST',
                      body: JSON.stringify({ username: recoveryUsername.trim() })
                    });
                    showNotification(response.detail);
                    setAuthMode('login');
                  } catch (error) {
                    showNotification(error.message, 'error');
                  } finally {
                    setIsSaving(false);
                  }
                }}
                className="space-y-4"
              >
                <p className="text-sm text-gray-600">Ingresa tu username. Si la cuenta puede recuperar el acceso, enviaremos instrucciones al correo registrado.</p>
                <input
                  value={recoveryUsername}
                  onChange={(event) => setRecoveryUsername(event.target.value)}
                  autoComplete="username"
                  required
                  placeholder="Nombre de usuario"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm"
                />
                <button
                  type="submit"
                  disabled={isSaving}
                  className="w-full py-3 bg-[#3B82F6] disabled:opacity-50 text-white font-semibold rounded-lg"
                >
                  {isSaving ? 'Enviando...' : 'Enviar instrucciones'}
                </button>
                <button type="button" onClick={() => setAuthMode('login')} className="w-full text-sm text-blue-700">
                  Volver al inicio de sesión
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
    <div className="min-h-screen bg-[#EFF6FF] flex text-slate-800 font-sans">
      
      {/* GLOBAL TOAST NOTIFICATION */}
      {toast && (
        <div className="fixed top-5 right-5 z-50 bg-[#172554] text-white px-5 py-3 rounded-xl shadow-2xl flex items-center gap-3 border border-blue-400/30 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span className="font-medium text-sm">{toast.msg}</span>
        </div>
      )}
      {isLoadingData && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/30 backdrop-blur-sm" role="status">
          <div className="flex items-center gap-3 rounded-xl bg-white px-5 py-4 font-semibold text-[#172554] shadow-xl">
            <RefreshCw className="w-5 h-5 animate-spin" />
            Cargando datos del Workspace...
          </div>
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
            <div className="w-10 h-10 rounded-full bg-[#3B82F6] flex items-center justify-center font-bold">
              {userProfile.name.slice(0, 1).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{userProfile.name}</p>
              <p className="text-[11px] text-blue-300 truncate">{userProfile.role}</p>
            </div>
            <button 
              onClick={closeSession}
              disabled={isSaving}
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

          <div className="flex items-center gap-2">
            <select
              aria-label="Workspace activo"
              value={workspaceId || ''}
              onChange={(event) => switchWorkspace(event.target.value)}
              disabled={isLoadingData || workspaces.length === 0}
              className="max-w-48 px-3 py-2 border border-blue-100 rounded-lg text-xs bg-white disabled:opacity-50"
            >
              {workspaces.map((workspace) => (
                <option key={workspace.workspace_id} value={workspace.workspace_id}>
                  {workspace.nombre} ({workspace.rol})
                </option>
              ))}
            </select>
            <select
              aria-label="Problema activo"
              value={problemId || ''}
              onChange={(event) => selectProblem(event.target.value)}
              disabled={isLoadingData || problems.length === 0}
              className="max-w-48 px-3 py-2 border border-blue-100 rounded-lg text-xs bg-white disabled:opacity-50"
            >
              {problems.length === 0 && <option value="">Sin problemas</option>}
              {problems.map((problem) => (
                <option key={problem.id} value={problem.id}>{problem.nombre}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setModalState({ type: 'problem', data: null })}
              disabled={!canWrite || isLoadingData}
              title={!canWrite ? 'Tu rol no permite crear problemas' : 'Crear problema'}
              className="px-3 py-2 bg-[#DBEAFE] text-blue-800 rounded-lg text-xs font-semibold disabled:opacity-40"
            >
              <Plus className="w-4 h-4 inline mr-1" /> Problema
            </button>
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
                  <h2 className="text-2xl font-bold">
                    Bienvenido/a, {userProfile.name.split(' ')[0]}
                  </h2>
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
                  value={currentResult ? `$${currentResult.profit.toLocaleString()}` : '—'}
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
                    {history.slice(0, 3).map((execution) => (
                      <ActivityItem
                        key={execution.id}
                        title={`Ejecución ${execution.status}`}
                        subtitle={execution.name}
                        time={execution.date}
                      />
                    ))}
                    {history.length === 0 && (
                      <p className="text-sm text-gray-500">Aún no hay ejecuciones para este problema.</p>
                    )}
                  </div>
                </div>

                <Suspense fallback={<div className="h-80 animate-pulse rounded-2xl bg-white" role="status">Cargando gráfico...</div>}>
                  <ProfitChart chartType="bar" history={history} />
                </Suspense>

              </div>
            </div>
          )}

          {/* 2. OPTIMIZACIÓN VIEW */}
          {activeTab === 'optimizacion' && (
            <div className="space-y-6 animate-fade-in">
              <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-[#172554] to-blue-800 p-6 text-white shadow-xl sm:p-8">
                <div aria-hidden="true" className="absolute -right-16 -top-24 h-64 w-64 rounded-full border-[32px] border-white/5" />
                <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                  <div className="min-w-0">
                    <div className="inline-flex items-center gap-2 rounded-full border border-blue-300/20 bg-white/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-blue-100">
                      <Cpu className="h-3.5 w-3.5" /> Planificación de producción
                    </div>
                    <h2 className="mt-4 text-2xl font-bold tracking-tight sm:text-3xl">Optimización de la producción</h2>
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-blue-100">
                      Define productos, recursos y consumos para encontrar una mezcla de producción rentable y viable.
                    </p>
                    {activeProblem && (
                      <div className="mt-5 flex flex-wrap gap-2">
                        <span className="max-w-full truncate rounded-lg border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-semibold" title={activeProblem.nombre}>
                          {activeProblem.nombre}
                        </span>
                        <span className="rounded-lg border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-blue-100">
                          {activeProblem.estado}
                        </span>
                        <span className="rounded-lg border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-blue-100">
                          {activeProblem.sentido_objetivo}
                        </span>
                      </div>
                    )}
                  </div>
                  {activeProblem && (
                    <div className="flex shrink-0 flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => setModalState({ type: 'problem', data: activeProblem })}
                        disabled={!canWrite}
                        className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-xs font-semibold text-white transition-colors hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <Edit3 className="h-4 w-4" /> Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => setModalState({
                          type: 'delete',
                          data: { kind: 'problem', id: activeProblem.id, name: activeProblem.nombre }
                        })}
                        disabled={!canWrite}
                        className="inline-flex items-center gap-2 rounded-xl border border-rose-300/30 bg-rose-500/10 px-4 py-2.5 text-xs font-semibold text-rose-100 transition-colors hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <Trash2 className="h-4 w-4" /> Eliminar
                      </button>
                    </div>
                  )}
                </div>
              </section>

              <div className="grid grid-cols-1 gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm sm:grid-cols-3 sm:p-4">
                <StepBadge number={1} label="Datos de producción" active={optStep === 1} completed={optStep > 1} />
                <StepBadge number={2} label="Optimizar" active={optStep === 2} completed={optStep > 2} />
                <StepBadge number={3} label="Resultados" active={optStep === 3} completed={false} />
              </div>

              {!activeProblem && (
                <div className="bg-white p-8 rounded-2xl border border-blue-100 text-center text-sm text-gray-600">
                  No hay problemas en este Workspace. Usa «Problema» para crear uno; los datos solo se cargan desde el backend.
                </div>
              )}

              {/* STEP 1: PRODUCTION DATA TABBED INTERFACE */}
              {activeProblem && optStep === 1 && (
                <div className="bg-white rounded-2xl border border-blue-100 shadow-sm overflow-hidden">
                  
                  {/* Tabs Selector */}
                  <div className="border-b border-slate-100 bg-slate-50/70 px-3 pt-3 sm:px-6">
                    <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setOptSubTab('productos')}
                      aria-pressed={optSubTab === 'productos'}
                      className={`flex min-w-0 items-center justify-center gap-1.5 rounded-t-xl border px-2 py-3 text-[11px] font-semibold transition-all sm:justify-start sm:gap-2.5 sm:px-4 sm:text-sm ${
                        optSubTab === 'productos' ? 'border-blue-200 border-b-white bg-white text-blue-800 shadow-sm' : 'border-transparent text-slate-500 hover:bg-white/70 hover:text-slate-800'
                      }`}
                    >
                      <Package className="h-4 w-4 shrink-0" />
                      <span className="truncate">Productos</span>
                      <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${optSubTab === 'productos' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-500'}`}>{products.length}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setOptSubTab('recursos')}
                      aria-pressed={optSubTab === 'recursos'}
                      className={`flex min-w-0 items-center justify-center gap-1.5 rounded-t-xl border px-2 py-3 text-[11px] font-semibold transition-all sm:justify-start sm:gap-2.5 sm:px-4 sm:text-sm ${
                        optSubTab === 'recursos' ? 'border-blue-200 border-b-white bg-white text-blue-800 shadow-sm' : 'border-transparent text-slate-500 hover:bg-white/70 hover:text-slate-800'
                      }`}
                    >
                      <Boxes className="h-4 w-4 shrink-0" />
                      <span className="truncate">Recursos</span>
                      <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${optSubTab === 'recursos' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-500'}`}>{resources.length}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setOptSubTab('consumos')}
                      aria-pressed={optSubTab === 'consumos'}
                      className={`flex min-w-0 items-center justify-center gap-1.5 rounded-t-xl border px-2 py-3 text-[11px] font-semibold transition-all sm:justify-start sm:gap-2.5 sm:px-4 sm:text-sm ${
                        optSubTab === 'consumos' ? 'border-blue-200 border-b-white bg-white text-blue-800 shadow-sm' : 'border-transparent text-slate-500 hover:bg-white/70 hover:text-slate-800'
                      }`}
                    >
                      <Layers className="h-4 w-4 shrink-0" />
                      <span className="truncate">Consumos</span>
                      <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${optSubTab === 'consumos' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-500'}`}>{consumptions.length}</span>
                    </button>
                    </div>
                  </div>

                  {/* SubTab Contents */}
                  <div className="p-4 sm:p-6">
                    {/* TAB PRODUCTOS */}
                    {optSubTab === 'productos' && (
                      <div className="space-y-4">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <h3 className="text-base font-bold text-slate-900">Catálogo de productos</h3>
                            <p className="mt-1 text-sm text-slate-500">Registra cada producto y su utilidad unitaria.</p>
                          </div>
                          <button
                            onClick={() => setModalState({ type: 'product', data: null })}
                            disabled={!canWrite}
                            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <Plus className="w-4 h-4" /> Agregar producto
                          </button>
                        </div>

                        <div className="overflow-x-auto rounded-2xl border border-slate-200 shadow-sm">
                          <table className="w-full text-left text-xs sm:text-sm">
                            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                              <tr>
                                <th className="p-3.5">Código</th>
                                <th className="p-3.5">Producto</th>
                                <th className="p-3.5">Utilidad (USD/u)</th>
                                <th className="p-3.5 text-right">Acciones</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {products.length === 0 && (
                                <tr>
                                  <td colSpan={4} className="px-4 py-10 text-center">
                                    <Package className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                                    <p className="text-sm font-semibold text-slate-700">Aún no hay productos</p>
                                    <p className="mt-1 text-xs text-slate-500">Agrega productos para definir qué se va a fabricar.</p>
                                  </td>
                                </tr>
                              )}
                              {products.map(p => (
                                <tr key={p.id} className="hover:bg-blue-50/40">
                                  <td className="p-3.5 font-bold text-[#1E40AF]">{p.code}</td>
                                  <td className="p-3.5 font-medium">{p.name}</td>
                                  <td className="p-3.5 text-emerald-600 font-bold">${p.profit}</td>
                                  <td className="p-3.5 text-right space-x-2">
                                    <button 
                                      onClick={() => setModalState({ type: 'product', data: p })}
                                      disabled={!canWrite}
                                      className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg"
                                    >
                                      <Edit3 className="w-4 h-4" />
                                    </button>
                                    <button 
                                      onClick={() => setModalState({ type: 'delete', data: { kind: 'product', id: p.id, name: p.name } })}
                                      disabled={!canWrite}
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
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <h3 className="text-base font-bold text-slate-900">Disponibilidad de recursos</h3>
                            <p className="mt-1 text-sm text-slate-500">Define la capacidad disponible en planta.</p>
                          </div>
                          <button
                            onClick={() => setModalState({ type: 'resource', data: null })}
                            disabled={!canWrite}
                            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <Plus className="w-4 h-4" /> Agregar recurso
                          </button>
                        </div>

                        <div className="overflow-x-auto rounded-2xl border border-slate-200 shadow-sm">
                          <table className="w-full text-left text-xs sm:text-sm">
                            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                              <tr>
                                <th className="p-3.5">Recurso</th>
                                <th className="p-3.5">Unidad</th>
                                <th className="p-3.5">Disponibilidad Máxima</th>
                                <th className="p-3.5 text-right">Acciones</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {resources.length === 0 && (
                                <tr>
                                  <td colSpan={4} className="px-4 py-10 text-center">
                                    <Boxes className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                                    <p className="text-sm font-semibold text-slate-700">Aún no hay recursos</p>
                                    <p className="mt-1 text-xs text-slate-500">Agrega los límites de capacidad disponibles.</p>
                                  </td>
                                </tr>
                              )}
                              {resources.map(r => (
                                <tr key={r.id} className="hover:bg-blue-50/40">
                                  <td className="p-3.5 font-bold text-[#172554]">{r.name}</td>
                                  <td className="p-3.5 text-gray-500 font-medium">{r.unit}</td>
                                  <td className="p-3.5 font-bold">{r.capacity.toLocaleString()} {r.unit}</td>
                                  <td className="p-3.5 text-right space-x-2">
                                    <button 
                                      onClick={() => setModalState({ type: 'resource', data: r })}
                                      disabled={!canWrite}
                                      className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg"
                                    >
                                      <Edit3 className="w-4 h-4" />
                                    </button>
                                    <button 
                                      onClick={() => setModalState({ type: 'delete', data: { kind: 'resource', id: r.id, name: r.name } })}
                                      disabled={!canWrite}
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
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <h3 className="text-base font-bold text-slate-900">Reglas de consumo</h3>
                            <p className="mt-1 text-sm text-slate-500">Indica cuánto recurso requiere cada unidad de producto.</p>
                          </div>
                          <button
                            onClick={() => setModalState({ type: 'consumption', data: null })}
                            disabled={!canWrite || products.length === 0 || resources.length === 0}
                            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <Plus className="w-4 h-4" /> Agregar regla consumo
                          </button>
                        </div>

                        <div className="overflow-x-auto rounded-2xl border border-slate-200 shadow-sm">
                          <table className="w-full text-left text-xs sm:text-sm">
                            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                              <tr>
                                <th className="p-3.5">Producto</th>
                                <th className="p-3.5">Recurso</th>
                                <th className="p-3.5">Consumo por unidad</th>
                                <th className="p-3.5 text-right">Acciones</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {consumptions.length === 0 && (
                                <tr>
                                  <td colSpan={4} className="px-4 py-10 text-center">
                                    <Layers className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                                    <p className="text-sm font-semibold text-slate-700">Aún no hay reglas de consumo</p>
                                    <p className="mt-1 text-xs text-slate-500">Relaciona cada producto con los recursos que utiliza.</p>
                                  </td>
                                </tr>
                              )}
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
                                        disabled={!canWrite}
                                        className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg"
                                      >
                                        <Edit3 className="w-4 h-4" />
                                      </button>
                                      <button 
                                        onClick={() => setModalState({ type: 'delete', data: { kind: 'consumption', id: c.id, name: 'Regla de consumo' } })}
                                        disabled={!canWrite}
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
                    {productsWithoutPositiveConsumption.length > 0 && (
                      <div className="mb-6 flex flex-col gap-4 rounded-xl border border-amber-200 bg-amber-50 p-4 sm:flex-row sm:items-start sm:justify-between" role="alert">
                        <div className="flex gap-3">
                          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
                          <div>
                            <p className="text-sm font-semibold text-amber-900">
                              La producción no tiene un límite superior para todos los productos.
                            </p>
                            <p className="mt-1 text-sm text-amber-800">
                              En un problema de maximización, cada producto con utilidad positiva debe consumir al menos un recurso.
                            </p>
                            <p className="mt-2 text-sm font-medium text-amber-900">
                              Revisa: {productsWithoutPositiveConsumption.map((product) => product.code || product.name).join(', ')}
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setOptSubTab('consumos')}
                          className="shrink-0 rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm font-semibold text-amber-900 transition-colors hover:bg-amber-100"
                        >
                          Revisar consumos
                        </button>
                      </div>
                    )}
                    <div className="mt-8 flex flex-col gap-4 border-t border-slate-200 pt-6 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-900">Resumen de datos</h3>
                        <p className="mt-1 text-xs text-slate-500">
                          {products.length} productos · {resources.length} recursos · {consumptions.length} reglas de consumo
                        </p>
                      </div>
                      <button
                        onClick={runOptimization}
                        disabled={!canWrite || !products.length || !resources.length || !consumptions.length || productsWithoutPositiveConsumption.length > 0 || isOptimizing}
                        className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-bold text-white shadow-md shadow-blue-900/15 transition-all hover:-translate-y-0.5 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0"
                      >
                        {isOptimizing
                          ? <RefreshCw className="h-4 w-4 animate-spin" />
                          : <Play className="h-4 w-4 fill-current" />}
                        Ejecutar optimización
                      </button>
                    </div>

                  </div>
                </div>
              )}

              {/* STEP 2: BACKEND OPTIMIZATION IN PROGRESS */}
              {optStep === 2 && (
                <div className="space-y-6 rounded-3xl border border-blue-100 bg-gradient-to-br from-white to-blue-50 p-8 text-center shadow-sm sm:p-12" role="status" aria-live="polite">
                  <div className="relative mx-auto h-20 w-20">
                    <div className="h-20 w-20 animate-spin rounded-full border-4 border-blue-100 border-t-blue-600"></div>
                    <Cpu className="absolute inset-0 m-auto h-8 w-8 animate-pulse text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900">Calculando el plan de producción</h3>
                    <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
                      El motor está evaluando la utilidad y las restricciones de recursos. Esto puede tardar unos segundos.
                    </p>
                  </div>
                  <div className="mx-auto h-2 max-w-sm overflow-hidden rounded-full bg-blue-100">
                    <div className="h-full w-3/4 animate-pulse rounded-full bg-blue-600"></div>
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
                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Solver</span>
                        <h3 className="text-xl font-extrabold text-[#172554]">{currentResult.solverName || '—'}</h3>
                        <p className="text-xs text-gray-500">{currentResult.solverStatus}</p>
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
                          {currentResult.bottlenecks.length
                            ? currentResult.bottlenecks.join(' y ')
                            : 'Sin recursos agotados'}
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
                          onClick={() => window.print()}
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
                                  {r.slack === 0 ? `0 ${r.unit} (Agotado)` : `${r.slack} ${r.unit}`}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                  </div>

                  <div className="bg-gradient-to-br from-[#172554] to-[#1E40AF] p-6 rounded-2xl text-white shadow-lg space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-blue-500/30 flex items-center justify-center border border-blue-400/30">
                        <CheckCircle2 className="w-5 h-5 text-emerald-300" />
                      </div>
                      <h3 className="font-bold text-base">Resumen de la ejecución</h3>
                    </div>
                    <p className="text-xs text-blue-100 leading-relaxed">
                      El solver {currentResult.solverName || 'del backend'} terminó con estado {currentResult.solverStatus}.
                      Se registraron {currentResult.produced.length} resultados de producto y {currentResult.resourceUsage.length} resultados de recurso.
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
                      onClick={() => setActiveTab('historial')}
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
                        value={historyQuery}
                        onChange={(event) => setHistoryQuery(event.target.value)}
                        className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                      />
                    </div>
                    <select
                      value={historyStatus}
                      onChange={(event) => setHistoryStatus(event.target.value)}
                      className="px-3 py-2 border border-gray-200 rounded-xl text-xs bg-white text-gray-700"
                    >
                      <option value="all">Todos los estados</option>
                      <option value="Completado">Completado</option>
                      <option value="Error">Error</option>
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
                      {visibleHistory.map((h) => (
                        <tr key={h.id} className="hover:bg-blue-50/40">
                          <td className="p-3.5 text-gray-500 font-medium">{h.date}</td>
                          <td className="p-3.5 font-bold text-[#172554]">{h.name}</td>
                          <td className="p-3.5 font-extrabold text-emerald-600">
                            {h.profit === null ? '—' : `$${h.profit.toLocaleString()}`}
                          </td>
                          <td className="p-3.5">
                            <span className={`px-2.5 py-1 text-[10px] font-bold rounded-full ${
                              h.status === 'Completado'
                                ? 'bg-emerald-100 text-emerald-700'
                                : h.status === 'Error'
                                  ? 'bg-rose-100 text-rose-700'
                                  : 'bg-amber-100 text-amber-700'
                            }`}>
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
                      {visibleHistory.length === 0 && (
                        <tr>
                          <td colSpan="5" className="p-5 text-center text-gray-500">No hay ejecuciones que coincidan.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <Suspense fallback={<div className="h-80 animate-pulse rounded-2xl bg-white" role="status">Cargando gráfico...</div>}>
                <ProfitChart chartType="line" history={visibleHistory} />
              </Suspense>
            </div>
          )}

          {/* 4. MI PERFIL VIEW */}
          {activeTab === 'perfil' && (
            <div className="max-w-2xl mx-auto bg-white p-8 rounded-2xl border border-blue-100 shadow-sm space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row items-center gap-6 pb-6 border-b border-gray-100">
                <div className="w-24 h-24 rounded-full bg-[#3B82F6] text-white flex items-center justify-center text-3xl font-bold border-4 border-blue-100 shadow-md">
                  {userProfile.name.slice(0, 1).toUpperCase()}
                </div>
                <div className="text-center sm:text-left">
                  <h2 className="text-xl font-bold text-[#172554]">{userProfile.name}</h2>
                  <p className="text-xs text-gray-500">{userProfile.role}</p>
                  <span className="inline-block mt-2 px-3 py-1 bg-blue-50 text-[#1E40AF] text-[10px] font-bold rounded-full">
                    {workspaces.find((item) => Number(item.workspace_id) === Number(workspaceId))?.nombre || 'Workspace'}
                  </span>
                </div>
              </div>

              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const nameParts = userProfile.name.trim().split(/\s+/);
                  if (!userProfile.name.trim()) {
                    showNotification('El nombre es obligatorio.', 'error');
                    return;
                  }
                  setIsSaving(true);
                  try {
                    const profile = await apiRequest('/api/auth/perfil/', {
                      method: 'PATCH',
                      body: JSON.stringify({
                        first_name: nameParts.shift() || '',
                        last_name: nameParts.join(' ')
                      })
                    });
                    setUserProfile((current) => ({
                      ...current,
                      name: `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || profile.username
                    }));
                    showNotification('Perfil actualizado correctamente.');
                  } catch (error) {
                    showNotification(error.message, 'error');
                  } finally {
                    setIsSaving(false);
                  }
                }}
                className="space-y-4"
              >
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
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">
                    Nombre de usuario
                  </label>

                  <input
                    type="text"
                    value={userProfile.username}
                    disabled
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-medium bg-gray-50 text-gray-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Correo electrónico</label>
                  <input
                    type="email"
                    value={userProfile.email}
                    disabled
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-medium bg-gray-50 text-gray-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Rol de usuario</label>
                  <input
                    type="text"
                    value={userProfile.role}
                    disabled
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-medium bg-gray-50 text-gray-500"
                  />
                </div>

                <div className="pt-4 flex justify-end gap-3">
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-6 py-2.5 bg-[#3B82F6] hover:bg-[#1E40AF] text-white text-xs font-semibold rounded-xl shadow-md flex items-center gap-2 disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" /> {isSaving ? 'Guardando...' : 'Guardar cambios'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* 5. AJUSTES VIEW */}
          {activeTab === 'ajustes' && (
            <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
              <section className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                <div>
                  <h3 className="font-bold text-[#172554]">Miembros del Workspace</h3>
                  <p className="text-xs text-gray-500">
                    Los permisos se aplican y validan también en el backend.
                  </p>
                </div>

                {canManageMembers && (
                  <form onSubmit={addWorkspaceMember} className="flex flex-col sm:flex-row gap-2">
                    <input
                      value={memberForm.username}
                      onChange={(event) => setMemberForm({ ...memberForm, username: event.target.value })}
                      placeholder="Username existente"
                      autoComplete="off"
                      required
                      className="flex-1 px-3 py-2 border rounded-lg text-sm"
                    />
                    <select
                      value={memberForm.rol}
                      onChange={(event) => setMemberForm({ ...memberForm, rol: event.target.value })}
                      className="px-3 py-2 border rounded-lg text-sm bg-white"
                    >
                      {userProfile.role === 'OWNER' && <option value="ADMIN">ADMIN</option>}
                      <option value="EDITOR">EDITOR</option>
                      <option value="VIEWER">VIEWER</option>
                    </select>
                    <button
                      type="submit"
                      disabled={isSaving}
                      className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-sm disabled:opacity-50"
                    >
                      Agregar miembro
                    </button>
                  </form>
                )}

                {!canManageMembers && (
                  <p className="text-xs text-gray-500">Tu rol puede consultar miembros, pero no administrarlos.</p>
                )}

                <div className="overflow-x-auto border rounded-xl">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-[#EFF6FF] text-[#172554]">
                      <tr>
                        <th className="p-3">Username</th>
                        <th className="p-3">Rol</th>
                        {canManageMembers && <th className="p-3 text-right">Acciones</th>}
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {members.map((member) => {
                        const isOwner = member.rol === 'OWNER';
                        const isOtherAdmin = userProfile.role === 'ADMIN'
                          && member.rol === 'ADMIN'
                          && member.username !== userProfile.username;
                        const canChange = canManageMembers && !isOwner && !isOtherAdmin;
                        return (
                          <tr key={member.id}>
                            <td className="p-3">{member.username}</td>
                            <td className="p-3">
                              <select
                                value={member.rol}
                                disabled={!canChange || isSaving}
                                onChange={(event) => updateMemberRole(member, event.target.value)}
                                className="px-2 py-1 border rounded bg-white disabled:bg-gray-50"
                              >
                                {member.rol === 'OWNER' && <option value="OWNER">OWNER</option>}
                                {(userProfile.role === 'OWNER' || member.rol === 'ADMIN')
                                  && <option value="ADMIN">ADMIN</option>}
                                <option value="EDITOR">EDITOR</option>
                                <option value="VIEWER">VIEWER</option>
                              </select>
                            </td>
                            {canManageMembers && (
                              <td className="p-3 text-right space-x-2">
                                {userProfile.role === 'OWNER' && !isOwner && (
                                  <button
                                    type="button"
                                    disabled={isSaving}
                                    onClick={() => {
                                      if (window.confirm(`¿Transferir la propiedad a ${member.username}?`)) {
                                        transferWorkspaceOwnership(member);
                                      }
                                    }}
                                    className="text-blue-700 disabled:opacity-40"
                                  >
                                    Transferir propiedad
                                  </button>
                                )}
                                <button
                                  type="button"
                                  disabled={!canChange || isSaving}
                                  onClick={() => removeWorkspaceMember(member)}
                                  className="text-rose-600 disabled:opacity-40"
                                >
                                  Retirar
                                </button>
                              </td>
                            )}
                          </tr>
                        );
                      })}
                      {members.length === 0 && (
                        <tr>
                          <td className="p-3 text-gray-500" colSpan={canManageMembers ? 3 : 2}>
                            {isLoadingData ? 'Cargando miembros...' : 'No hay miembros para mostrar.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="bg-white p-6 rounded-2xl border border-blue-100 shadow-sm space-y-4">
                <div>
                  <h3 className="font-bold text-[#172554]">Cambiar contraseña</h3>
                  <p className="text-xs text-gray-500">Al actualizarla, la sesión actual se cerrará.</p>
                </div>
                <form
                  onSubmit={async (event) => {
                    event.preventDefault();
                    const { current_password, new_password, new_password_confirm } = passwordChange;
                    if (!current_password || !new_password || !new_password_confirm) {
                      showNotification('Completa todos los campos.', 'error');
                      return;
                    }
                    if (new_password !== new_password_confirm) {
                      showNotification('Las contraseñas nuevas no coinciden.', 'error');
                      return;
                    }
                    setIsSaving(true);
                    try {
                      const response = await apiRequest('/api/auth/cambiar-contrasena/', {
                        method: 'POST',
                        body: JSON.stringify(passwordChange)
                      });
                      let logoutFailure = null;
                      try {
                        await apiRequest('/api/auth/cerrar-sesion/', { method: 'POST' });
                      } catch (error) {
                        logoutFailure = error;
                      }
                      clearLocalSession();
                      setPasswordChange({
                        current_password: '',
                        new_password: '',
                        new_password_confirm: ''
                      });
                      showNotification(logoutFailure
                        ? `${response.detail} No se pudo limpiar la cookie de sesión: ${logoutFailure.message}`
                        : response.detail);
                    } catch (error) {
                      showNotification(error.message, 'error');
                    } finally {
                      setIsSaving(false);
                    }
                  }}
                  className="grid gap-3"
                >
                  {[
                    ['current_password', 'Contraseña actual'],
                    ['new_password', 'Nueva contraseña'],
                    ['new_password_confirm', 'Confirmar contraseña nueva']
                  ].map(([field, label]) => (
                    <label key={field} className="grid gap-1 text-xs font-semibold text-gray-600">
                      {label}
                      <input
                        type="password"
                        value={passwordChange[field]}
                        onChange={(event) => setPasswordChange({ ...passwordChange, [field]: event.target.value })}
                        autoComplete={field === 'current_password' ? 'current-password' : 'new-password'}
                        minLength={field === 'current_password' ? undefined : 8}
                        maxLength={128}
                        required
                        className="w-full px-3 py-2 border rounded-lg text-sm font-normal"
                      />
                    </label>
                  ))}
                  <button type="submit" disabled={isSaving} className="justify-self-end px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-sm disabled:opacity-50">
                    {isSaving ? 'Actualizando...' : 'Actualizar contraseña'}
                  </button>
                </form>
              </section>
            </div>
          )}

        </main>
      </div>

      {/* --- MODALS FOR ADD / EDIT / DELETE --- */}

      {modalState.type === 'problem' && (
        <ModalWrapper
          title={modalState.data ? 'Editar problema' : 'Crear problema'}
          onClose={() => setModalState({ type: null, data: null })}
        >
          <form onSubmit={saveProblem} className="space-y-4">
            <label className="block text-xs font-bold text-gray-600">
              Nombre
              <input
                name="nombre"
                defaultValue={modalState.data?.nombre || ''}
                maxLength={150}
                required
                className="mt-1 w-full p-2.5 border rounded-lg text-sm font-normal"
              />
            </label>
            <label className="block text-xs font-bold text-gray-600">
              Descripción
              <textarea
                name="descripcion"
                defaultValue={modalState.data?.descripcion || ''}
                className="mt-1 w-full p-2.5 border rounded-lg text-sm font-normal"
                rows="3"
              />
            </label>
            <label className="block text-xs font-bold text-gray-600">
              Objetivo
              <select
                name="sentido_objetivo"
                defaultValue={modalState.data?.sentido_objetivo || 'MAXIMIZAR'}
                className="mt-1 w-full p-2.5 border rounded-lg text-sm font-normal bg-white"
              >
                <option value="MAXIMIZAR">Maximizar</option>
                <option value="MINIMIZAR">Minimizar</option>
              </select>
            </label>
            <label className="block text-xs font-bold text-gray-600">
              Estado
              <select
                name="estado"
                defaultValue={modalState.data?.estado || 'BORRADOR'}
                className="mt-1 w-full p-2.5 border rounded-lg text-sm font-normal bg-white"
              >
                <option value="BORRADOR">Borrador</option>
                <option value="LISTO">Listo para optimizar</option>
                <option value="ARCHIVADO">Archivado</option>
              </select>
            </label>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setModalState({ type: null, data: null })} className="px-4 py-2 border rounded-lg text-xs">
                Cancelar
              </button>
              <button type="submit" disabled={isSaving} className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-xs font-semibold disabled:opacity-50">
                {isSaving ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </ModalWrapper>
      )}

      {/* 1. PRODUCT FORM MODAL */}
      {modalState.type === 'product' && (
        <ModalWrapper title={modalState.data ? 'Editar producto' : 'Agregar nuevo producto'} onClose={() => setModalState({ type: null })}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            const code = String(formData.get('code') || '').trim();
            const name = String(formData.get('name') || '').trim();
            const description = String(formData.get('description') || '').trim();
            const profitValue = String(formData.get('profit') || '');
            const profit = Number(profitValue);

            if (!code || !name || !profitValue || !Number.isFinite(profit) || profit < 0) {
              showNotification('Ingresa código y nombre, y una utilidad válida no negativa.', 'error');
              return;
            }

            setIsSaving(true);
            try {
              const payload = {
                problema: Number(problemId),
                codigo: code,
                nombre: name,
                descripcion: description,
                utilidad_unitaria: profit,
                activo: true
              };
              const savedProduct = modalState.data
                ? await apiRequest(`/api/productos/${modalState.data.id}/`, { method: 'PATCH', body: JSON.stringify(payload) })
                : await apiRequest('/api/productos/', { method: 'POST', body: JSON.stringify(payload) });
              const product = {
                id: Number(savedProduct.id),
                code: savedProduct.codigo,
                name: savedProduct.nombre,
                description: savedProduct.descripcion,
                profit: Number(savedProduct.utilidad_unitaria)
              };
              setProducts((current) => modalState.data
                ? current.map((item) => (item.id === product.id ? product : item))
                : [...current, product]);
              showNotification(modalState.data ? 'Producto actualizado.' : 'Producto creado.');
              setModalState({ type: null });
            } catch (error) {
              showNotification(error.message, 'error');
            } finally {
              setIsSaving(false);
            }
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
              <label className="block text-xs font-bold text-gray-600 mb-1">Descripción</label>
              <textarea name="description" defaultValue={modalState.data?.description || ''} className="w-full p-2.5 border rounded-lg text-xs" rows="2" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Utilidad unitaria (USD/u)</label>
              <input name="profit" type="number" min="0" step="0.01" defaultValue={modalState.data?.profit ?? 0} required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setModalState({ type: null })} className="px-4 py-2 border rounded-lg text-xs">Cancelar</button>
              <button type="submit" disabled={!canWrite || isSaving} className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-xs font-semibold disabled:opacity-50">{isSaving ? 'Guardando...' : 'Guardar'}</button>
            </div>
          </form>
        </ModalWrapper>
      )}

      {/* 2. RESOURCE FORM MODAL */}
      {modalState.type === 'resource' && (
        <ModalWrapper title={modalState.data ? 'Editar recurso' : 'Agregar nuevo recurso'} onClose={() => setModalState({ type: null })}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            const name = String(formData.get('name') || '').trim();
            const unit = String(formData.get('unit') || '').trim();
            const capacityValue = String(formData.get('capacity') || '');
            const capacity = Number(capacityValue);

            if (!name || !unit || !capacityValue || !Number.isFinite(capacity) || capacity < 0) {
              showNotification('Ingresa nombre, unidad y una disponibilidad válida no negativa.', 'error');
              return;
            }

            setIsSaving(true);
            try {
              const payload = {
                problema: Number(problemId),
                nombre: name,
                unidad_medida: unit,
                disponibilidad: capacity,
                activo: true
              };
              const savedResource = modalState.data
                ? await apiRequest(`/api/recursos/${modalState.data.id}/`, { method: 'PATCH', body: JSON.stringify(payload) })
                : await apiRequest('/api/recursos/', { method: 'POST', body: JSON.stringify(payload) });
              const resource = {
                id: Number(savedResource.id),
                name: savedResource.nombre,
                unit: savedResource.unidad_medida,
                capacity: Number(savedResource.disponibilidad)
              };
              setResources((current) => modalState.data
                ? current.map((item) => (item.id === resource.id ? resource : item))
                : [...current, resource]);
              showNotification(modalState.data ? 'Recurso actualizado.' : 'Recurso creado.');
              setModalState({ type: null });
            } catch (error) {
              showNotification(error.message, 'error');
            } finally {
              setIsSaving(false);
            }
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
              <input name="capacity" type="number" min="0" step="0.01" defaultValue={modalState.data?.capacity ?? 0} required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setModalState({ type: null })} className="px-4 py-2 border rounded-lg text-xs">Cancelar</button>
              <button type="submit" disabled={!canWrite || isSaving} className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-xs font-semibold disabled:opacity-50">{isSaving ? 'Guardando...' : 'Guardar'}</button>
            </div>
          </form>
        </ModalWrapper>
      )}

      {/* 3. CONSUMPTION FORM MODAL */}
      {modalState.type === 'consumption' && (
        <ModalWrapper title={modalState.data ? 'Editar consumo' : 'Agregar consumo por unidad'} onClose={() => setModalState({ type: null })}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            const productId = Number(formData.get('productId'));
            const resourceId = Number(formData.get('resourceId'));
            const amountValue = String(formData.get('amount') || '');
            const amount = Number(amountValue);

            if (!products.some((item) => item.id === productId)
              || !resources.some((item) => item.id === resourceId)
              || !amountValue
              || !Number.isFinite(amount)
              || amount < 0) {
              showNotification('Selecciona un producto y recurso de este problema e ingresa una cantidad válida no negativa.', 'error');
              return;
            }

            setIsSaving(true);
            try {
              const payload = {
                producto: productId,
                recurso: resourceId,
                cantidad_por_unidad: amount
              };
              const savedConsumption = modalState.data
                ? await apiRequest(`/api/consumos/${modalState.data.id}/`, { method: 'PATCH', body: JSON.stringify(payload) })
                : await apiRequest('/api/consumos/', { method: 'POST', body: JSON.stringify(payload) });
              const consumption = {
                id: Number(savedConsumption.id),
                productId: Number(savedConsumption.producto),
                resourceId: Number(savedConsumption.recurso),
                amount: Number(savedConsumption.cantidad_por_unidad)
              };
              setConsumptions((current) => modalState.data
                ? current.map((item) => (item.id === consumption.id ? consumption : item))
                : [...current, consumption]);
              showNotification(modalState.data ? 'Consumo actualizado.' : 'Consumo creado.');
              setModalState({ type: null });
            } catch (error) {
              showNotification(error.message, 'error');
            } finally {
              setIsSaving(false);
            }
          }} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Producto</label>
              <select name="productId" defaultValue={modalState.data?.productId ?? products[0]?.id ?? ''} required className="w-full p-2.5 border rounded-lg text-xs bg-white">
                {products.map(p => <option key={p.id} value={p.id}>{p.code} - {p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Recurso consumido</label>
              <select name="resourceId" defaultValue={modalState.data?.resourceId ?? resources[0]?.id ?? ''} required className="w-full p-2.5 border rounded-lg text-xs bg-white">
                {resources.map(r => <option key={r.id} value={r.id}>{r.name} ({r.unit})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-600 mb-1">Cantidad consumida por unidad</label>
              <input name="amount" type="number" min="0" step="0.0001" defaultValue={modalState.data?.amount ?? 0} required className="w-full p-2.5 border rounded-lg text-xs" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setModalState({ type: null })} className="px-4 py-2 border rounded-lg text-xs">Cancelar</button>
              <button type="submit" disabled={!canWrite || isSaving || !products.length || !resources.length} className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg text-xs font-semibold disabled:opacity-50">{isSaving ? 'Guardando...' : 'Guardar'}</button>
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
                onClick={async () => {
                  const { kind, id } = modalState.data;
                  if (!canWrite) {
                    showNotification('Tu rol no permite eliminar registros.', 'error');
                    return;
                  }
                  setIsSaving(true);
                  try {
                    if (kind === 'product') {
                      await apiRequest(`/api/productos/${id}/`, { method: 'DELETE' });
                      setProducts((current) => current.filter((item) => item.id !== Number(id)));
                      setConsumptions((current) => current.filter((item) => item.productId !== Number(id)));
                    } else if (kind === 'resource') {
                      await apiRequest(`/api/recursos/${id}/`, { method: 'DELETE' });
                      setResources((current) => current.filter((item) => item.id !== Number(id)));
                      setConsumptions((current) => current.filter((item) => item.resourceId !== Number(id)));
                    } else if (kind === 'consumption') {
                      await apiRequest(`/api/consumos/${id}/`, { method: 'DELETE' });
                      setConsumptions((current) => current.filter((item) => item.id !== Number(id)));
                    } else if (kind === 'problem') {
                      await apiRequest(`/api/problemas/${id}/`, { method: 'DELETE' });
                      setModalState({ type: null, data: null });
                      const remainingProblems = problems.filter((item) => Number(item.id) !== Number(id));
                      setProblems(remainingProblems);
                      if (Number(problemId) === Number(id)) {
                        setProblemId(null);
                        setProducts([]);
                        setResources([]);
                        setConsumptions([]);
                        setHistory([]);
                        setCurrentResult(null);
                        localStorage.removeItem(problemStorageKey(workspaceId));
                        if (remainingProblems.length) {
                          await loadBackendData(workspaceId, remainingProblems[0].id);
                        }
                      }
                    }
                    showNotification(kind === 'problem' ? 'Problema eliminado.' : 'Registro eliminado.');
                    setModalState({ type: null, data: null });
                  } catch (error) {
                    showNotification(error.message, 'error');
                  } finally {
                    setIsSaving(false);
                  }
                }} 
                disabled={!canWrite || isSaving}
                className="px-4 py-2 bg-rose-600 text-white rounded-lg text-xs font-semibold disabled:opacity-50"
              >
                {isSaving ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </ModalWrapper>
      )}

      {/* 5. HISTORY DETAIL MODAL */}
      {historyDetailModal && (
        <ModalWrapper title={`Detalle: ${historyDetailModal.name}`} onClose={() => setHistoryDetailModal(null)}>
          <div className="space-y-4 text-xs max-h-[70vh] overflow-y-auto">
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-500">Fecha de ejecución:</span>
              <span className="font-bold text-[#172554]">{historyDetailModal.date}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-500">Utilidad alcanzada:</span>
              <span className="font-extrabold text-emerald-600">
                {historyDetailModal.profit === null ? '—' : `$${historyDetailModal.profit.toLocaleString()}`}
              </span>
            </div>
            {historyDetailModal.errorMessage && (
              <p className="text-rose-700">{historyDetailModal.errorMessage}</p>
            )}
            <div>
              <span className="font-bold text-gray-700 block mb-1">Cuellos de botella reportados:</span>
              <div className="flex gap-2">
                {historyDetailModal.bottlenecks?.map((b, idx) => (
                  <span key={idx} className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded font-semibold text-[10px]">
                    {b}
                  </span>
                ))}
                {historyDetailModal.bottlenecks?.length === 0 && (
                  <span className="text-gray-500">Sin recursos agotados.</span>
                )}
              </div>
            </div>
            <section>
              <h4 className="font-bold text-gray-700 mb-1">Resultados de productos</h4>
              {historyDetailModal.producedItems?.length ? (
                <div className="overflow-x-auto border rounded-lg">
                  <table className="w-full text-left">
                    <thead className="bg-[#EFF6FF]">
                      <tr><th className="p-2">Producto</th><th className="p-2 text-right">Cantidad</th><th className="p-2 text-right">Utilidad</th></tr>
                    </thead>
                    <tbody className="divide-y">
                      {historyDetailModal.producedItems.map((item) => (
                        <tr key={item.id}>
                          <td className="p-2">{item.code} · {item.name}</td>
                          <td className="p-2 text-right">{item.quantity.toLocaleString()}</td>
                          <td className="p-2 text-right">${item.totalProfit.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : <p className="text-gray-500">Esta ejecución no tiene resultados de productos.</p>}
            </section>
            <section>
              <h4 className="font-bold text-gray-700 mb-1">Resultados de recursos</h4>
              {historyDetailModal.resourceUsage?.length ? (
                <div className="overflow-x-auto border rounded-lg">
                  <table className="w-full text-left">
                    <thead className="bg-[#EFF6FF]">
                      <tr><th className="p-2">Recurso</th><th className="p-2 text-right">Uso</th><th className="p-2 text-right">Disponible</th><th className="p-2 text-right">Holgura</th></tr>
                    </thead>
                    <tbody className="divide-y">
                      {historyDetailModal.resourceUsage.map((item) => (
                        <tr key={item.id}>
                          <td className="p-2">{item.name}</td>
                          <td className="p-2 text-right">{item.used.toLocaleString()} {item.unit}</td>
                          <td className="p-2 text-right">{item.capacity.toLocaleString()} {item.unit}</td>
                          <td className="p-2 text-right">{item.slack.toLocaleString()} {item.unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : <p className="text-gray-500">Esta ejecución no tiene resultados de recursos.</p>}
            </section>
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
  );
}

// --- REUSABLE HELPER COMPONENTS ---

function NavItem({ icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold transition-all ${
        active 
          ? 'bg-[#3B82F6] text-white shadow-lg shadow-blue-500/30' 
          : 'text-blue-200 hover:bg-blue-900/40 hover:text-white'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function KPICard({ title, value, badge, icon, bgColor, textColor = 'text-[#172554]', titleColor = 'text-gray-500' }) {
  return (
    <div className={`${bgColor} p-6 rounded-2xl border border-blue-100 shadow-sm flex items-center justify-between`}>
      <div>
        <span className={`text-xs font-semibold uppercase tracking-wider ${titleColor}`}>{title}</span>
        <div className="flex items-baseline gap-2 mt-1">
          <h3 className={`text-2xl font-extrabold ${textColor}`}>{value}</h3>
          {badge && <span className="text-xs font-bold text-emerald-300 bg-blue-900/40 px-2 py-0.5 rounded-full">{badge}</span>}
        </div>
      </div>
      <div className="p-3 bg-[#EFF6FF] rounded-xl">{icon}</div>
    </div>
  );
}

function ActivityItem({ title, subtitle, time }) {
  return (
    <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-blue-50/50 transition-colors">
      <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-[#172554] truncate">{title}</p>
        <p className="text-[11px] text-gray-500 truncate">{subtitle}</p>
      </div>
      <span className="text-[10px] text-gray-400 shrink-0">{time}</span>
    </div>
  );
}

function StepBadge({ number, label, active, completed }) {
  const tone = active
    ? 'border-blue-200 bg-blue-50'
    : completed
      ? 'border-emerald-200 bg-emerald-50'
      : 'border-slate-100 bg-slate-50';
  const markerTone = active
    ? 'bg-blue-600 text-white'
    : completed
      ? 'bg-emerald-600 text-white'
      : 'border border-slate-200 bg-white text-slate-400';
  const labelTone = active
    ? 'text-slate-900'
    : completed
      ? 'text-emerald-900'
      : 'text-slate-500';

  return (
    <div
      aria-current={active ? 'step' : undefined}
      className={`flex min-w-0 items-center gap-3 rounded-xl border px-3 py-3 transition-colors sm:px-4 ${tone}`}
    >
      <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-bold ${markerTone}`}>
        {completed ? <CheckCircle2 className="h-5 w-5" /> : number}
      </span>
      <span className="min-w-0">
        <span className="block text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Paso {number}</span>
        <span className={`block truncate text-sm font-semibold ${labelTone}`}>{label}</span>
      </span>
    </div>
  );
}

function ModalWrapper({ title, children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-blue-100 overflow-hidden animate-fade-in">
        <div className="px-6 py-4 bg-[#172554] text-white flex justify-between items-center">
          <h3 className="font-bold text-sm">{title}</h3>
          <button onClick={onClose} className="text-blue-200 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}