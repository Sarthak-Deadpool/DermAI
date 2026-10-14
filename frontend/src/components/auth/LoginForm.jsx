/** @format */

import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { Link } from "react-router-dom";

import Input from "../common/Input";
import Button from "../common/Button";

import authService from "../../services/authService";

export default function LoginForm() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await authService.login(formData);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to sign in. Please check your email and password.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Input
        id="email"
        name="email"
        label="Email address"
        type="email"
        value={formData.email}
        onChange={handleChange}
        placeholder="you@example.com"
        autoComplete="email"
      />

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label
            htmlFor="password"
            className="text-sm font-medium text-slate-700"
          >
            Password
          </label>

          <button
            type="button"
            onClick={() => setShowPassword((previous) => !previous)}
            className="text-sm font-medium text-cyan-700 hover:text-cyan-900"
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        </div>

        <Input
          id="password"
          name="password"
          type={showPassword ? "text" : "password"}
          value={formData.password}
          onChange={handleChange}
          placeholder="Enter your password"
          autoComplete="current-password"
        />
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </p>
      )}

      <Button type="submit" disabled={loading}>
        {loading ? "Signing in..." : "Sign in to DermAI"}
      </Button>

      <p className="text-center text-sm text-slate-600">
        Don't have an account?{" "}
        <Link
          to="/register"
          className="font-semibold text-cyan-700 hover:text-cyan-900"
        >
          Create an account
        </Link>
      </p>
    </form>
  );
}
