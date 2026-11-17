import { createContext, useContext } from 'react';

/** Shared integration contract for feature modules developed by teammates. */
export const SharedAppContext = createContext(null);

export function useSharedApp() {
  const context = useContext(SharedAppContext);
  if (!context) throw new Error('useSharedApp debe usarse dentro de PlanificaIO.');
  return context;
}
