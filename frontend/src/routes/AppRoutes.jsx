/** @format */

import { Navigate, Route, Routes } from "react-router-dom";

import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import Dashboard from "../pages/Dashboard";
import ProtectedRoute from "./ProtectedRoute";
import CasesPage from "../pages/CasesPage";
import CreateCasePage from "../pages/CreateCasePage";

// Temporary pages until their features are implemented
import NewAnalysisPage from "../pages/NewAnalysisPage";
import PredictionHistoryPage from "../pages/PredictionHistoryPage";
import ReportsPage from "../pages/ReportsPage";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Authenticated routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analysis/new" element={<NewAnalysisPage />} />
        <Route path="/history" element={<PredictionHistoryPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/my-cases" element={<CasesPage />} />
        <Route path="/cases/new" element={<CreateCasePage />} />
      </Route>

      {/* Unknown routes */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
