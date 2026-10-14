import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import apiClient from "../../api/client";
import Input from "../common/Input";
import Button from "../common/Button";
import AuthLayout from "../layout/AuthLayout";

function LoginForm({ onLogin }) {
    const navigate = useNavigate();

    const [form, setForm] = useState({
        email: "",
        password: "",
    });

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    function handleChange(event) {
        setForm({
            ...form,
            [event.target.name]: event.target.value,
        });
    }

    async function handleSubmit(event) {
        event.preventDefautl();
        setError("");
        setLoading(true);

        try {
            const response = await apiClient.post("/auth/login", form);
            const token = response.data.access_token;

            const userResponse = await apiClient.get("/auth/me", {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            })
            
            onLogin(token, userResponse.data);
            navigate("/dashboard");

        } catch (err){ const detail = err.response?.data?.detail;
        setError(
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((item) => item.msg).join(", ")
              : "Login failed. Please check your details and try again."
        );
      } finally {
        setLoading(false);
      }
    }
  
    return (
      <AuthLayout
        title="Welcome back"
        subtitle="Sign in to access your DermAI workspace."
      >
        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            id="email"
            name="email"
            label="Email address"
            type="email"
            value={form.email}
            onChange={handleChange}
            autoComplete="email"
          />
  
          <Input
            id="password"
            name="password"
            label="Password"
            type="password"
            value={form.password}
            onChange={handleChange}
            autoComplete="current-password"
          />
  
          {error && (
            <p role="alert" className="text-sm text-red-400">
              {error}
            </p>
          )}
  
          <Button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
  
        <p className="mt-6 text-center text-sm text-slate-400">
          Don't have an account?{" "}
          <Link
            to="/register"
            className="font-medium text-cyan-400 hover:text-cyan-300"
          >
            Create account
          </Link>
        </p>
      </AuthLayout>
    );
}
  
  export default LoginForm;
