/** @format */

export const navigationByRole = {
  user: [
    { label: "Dashboard", path: "/dashboard" },
    { label: "New Analysis", path: "/analysis/new" },
    { label: "My Cases", path: "/my-cases" },
    { label: "Prediction History", path: "/history" },
    { label: "My Reports", path: "/reports" },
    { label: "Profile", path: "/profile" },
  ],

  clinician: [
    { label: "Dashboard", path: "/dashboard" },
    { label: "Patients", path: "/patients" },
    { label: "Cases", path: "/cases" },
    { label: "Reports", path: "/reports" },
  ],

  researcher: [
    { label: "Dashboard", path: "/dashboard" },
    { label: "Model Insights", path: "/model-insights" },
    { label: "Experiments", path: "/experiments" },
    { label: "Model Performance", path: "/model-performance" },
  ],

  admin: [
    { label: "Dashboard", path: "/dashboard" },
    { label: "Users", path: "/users" },
    { label: "Cases & Analyses", path: "/cases" },
    { label: "Model Usage", path: "/model-usage" },
    { label: "System Activity", path: "/activity" },
    { label: "Platform Health", path: "/system-health" },
    { label: "Settings", path: "/settings" },
  ],
};
