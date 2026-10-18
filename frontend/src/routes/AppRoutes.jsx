/** @format */

import { Navigate, Route, Routes } from "react-router-dom";

import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import DashboardPage from "../pages/Dashboard";
import CreateCasePage from "../pages/CreateCasePage";
import ProtectedRoute from "./ProtectedRoute";
import CaseWorkspacePage from "../pages/CaseWorkspace";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />

      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/create-case" element={<CreateCasePage />} />
        <Route path="/cases/:caseId" element={<CaseWorkspacePage/>} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
