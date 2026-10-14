import { Navigate, Route, Routes } from "react-router-dom";

function AppRoutes() {
    return (
   
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />

          <Route path="/login" element={<div>Login</div>} />
          <Route
            path="/register"
            element={<div>Register page will be added here</div>}
          />

          <Route
            path="/dashboard"
            element={<div>Dashboard will be added here</div>}
          />

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
     
    );

}

export default AppRoutes