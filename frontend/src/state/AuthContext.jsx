import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "../api/services";
import { setCsrfToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    try { const current = await authApi.me(); setUser(current); return current; }
    catch { setUser(null); return null; }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { let alive = true; authApi.me().then((current) => { if (alive) setUser(current); }).catch(() => { if (alive) setUser(null); }).finally(() => { if (alive) setLoading(false); }); return () => { alive = false; }; }, []);

  const login = useCallback(async (credentials) => {
    const result = await authApi.login(credentials);
    setCsrfToken(result.csrf_token);
    setUser(result.user);
    return result.user;
  }, []);
  const register = useCallback((payload) => authApi.register(payload), []);
  const logout = useCallback(async () => {
    try { await authApi.logout(); } finally { setCsrfToken(""); setUser(null); }
  }, []);

  const value = useMemo(() => ({ user, loading, login, register, logout, reload: loadUser, setUser }), [user, loading, login, register, logout, loadUser]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
