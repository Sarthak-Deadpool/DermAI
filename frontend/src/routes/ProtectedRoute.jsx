/** @format */

import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import authServices from "../services/authService"

export default function ProtectedRoute() {
  const location = useLocation();
  const [status, setStatus] = useState("checking");
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let active = true;

    async function verifySession() {
      setStatus("checking");

      try {
        await authServices.getCurrentUser();

        if (active) {
          setStatus("authenticated");
        }
      } catch (error) {
        if (!active) return;

        const statusCode = error.response?.status;

        if (statusCode === 401 || statusCode === 403) {
          setStatus("unauthenticated");
        } else {
          setStatus("error");
        }
      }
    }

    verifySession();

    return () => {
      active = false;
    };
  }, [retryCount]);

  if (status === "checking") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-600">Verifying your session...</p>
      </main>
    );
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (status === "error") {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 px-4">
        <p role="alert" className="text-center text-slate-700">
          Unable to verify your session. Please check your backend connection.
        </p>

        <button
          type="button"
          onClick={() => setRetryCount((count) => count + 1)}
          className="rounded-lg bg-cyan-600 px-5 py-2.5 font-semibold text-white hover:bg-cyan-700"
        >
          Try Again
        </button>
      </main>
    );
  }

  return <Outlet />;
}
