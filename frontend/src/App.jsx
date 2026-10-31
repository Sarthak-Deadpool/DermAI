import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { LoaderCircle } from "lucide-react";
import AppShell from "./components/AppShell";
import { useAuth } from "./state/AuthContext";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import CasesPage, { CreateCasePage } from "./pages/CasesPage";
import PatientsPage, { PatientDetailPage } from "./pages/PatientsPage";
import UploadPage from "./pages/UploadPage";
import { CaseDetailPage, ImageReviewPage } from "./pages/CasePages";
import ProfilePage from "./pages/ProfilePage";
import { AdminAuditPage, AdminUsersPage } from "./pages/AdminPages";

function AuthRequired() {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="flex min-h-screen items-center justify-center gap-2 text-sm text-[#77746c]"><LoaderCircle size={18} className="animate-spin"/>Opening your workspace…</div>;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace/>;
  return <Outlet/>;
}

function RoleRequired({ allow }) {
  const { user } = useAuth();
  return allow.includes(user?.role) ? <Outlet/> : <Navigate to="/app" replace/>;
}

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-[#f7f5f0]"/>;
  return <Navigate to={user ? "/app" : "/login"} replace/>;
}

function NotFound() { return <div className="grid min-h-screen place-items-center bg-[#f7f5f0] p-6 text-center"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#a25539]">DermAI</p><h1 className="display-serif mt-3 text-4xl">This page isn’t here</h1><p className="mt-2 text-sm text-[#77746c]">The link may be outdated, or the page may have moved.</p><a href="/app" className="mt-5 inline-block text-sm font-semibold text-[#a25539]">Return to workspace</a></div></div>; }

export default function App() {
  return <Routes>
    <Route path="/" element={<HomeRedirect/>}/>
    <Route path="/login" element={<AuthPage/>}/>
    <Route path="/register" element={<AuthPage mode="register"/>}/>
    <Route element={<AuthRequired/>}>
      <Route path="/app" element={<AppShell/>}>
        <Route index element={<DashboardPage/>}/>
        <Route element={<RoleRequired allow={["user", "clinician"]}/> }>
          <Route path="cases" element={<CasesPage/>}/>
          <Route path="cases/new" element={<CreateCasePage/>}/>
          <Route path="cases/:caseId" element={<CaseDetailPage/>}/>
          <Route path="cases/:caseId/images/:imageId" element={<ImageReviewPage/>}/>
          <Route path="upload" element={<UploadPage/>}/>
        </Route>
        <Route element={<RoleRequired allow={["clinician"]}/> }>
          <Route path="patients" element={<PatientsPage/>}/>
          <Route path="patients/:patientId" element={<PatientDetailPage/>}/>
        </Route>
        <Route element={<RoleRequired allow={["user", "clinician", "researcher", "data_scientist", "admin"]}/> }>
          <Route path="profile" element={<ProfilePage/>}/>
        </Route>
        <Route element={<RoleRequired allow={["admin"]}/> }>
          <Route path="admin/users" element={<AdminUsersPage/>}/>
          <Route path="admin/audit" element={<AdminAuditPage/>}/>
        </Route>
      </Route>
    </Route>
    <Route path="*" element={<NotFound/>}/>
  </Routes>;
}
