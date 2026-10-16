/** @format */

import { useState } from "react";
import { Link } from "react-router-dom";
import Input from "../common/Input";
import Button from "../common/Button";
import authService from "../../services/authService";
import RoleDropdown from "../common/RoleDropdown";

const initialFormData = {
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
  role: "user",
};

const roles = [
  { value: "user", label: "Patient / General User" },
  { value: "clinician", label: "Dermatologist / Clinician" },
  { value: "researcher", label: "Medical Researcher" },
  { value: "data_scientist", label: "Data Scientist / ML Engineer" },
];

export default function RegisterForm() {
  const [formData, setFormData] = useState(initialFormData);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

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
    setSuccess("");

    if (formData.username.trim().length < 3) {
      setError("Username must contain at least 3 characters.");
      return;
    }

    if (formData.password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const response = await authService.register({
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password,
        role: formData.role,
      });

      setSuccess(`Account created successfully for ${response.username}.`);

      setFormData(initialFormData);
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((item) => item.msg).join(", ")
            : "Unable to create your account. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  const compactInputClass =
    "w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20";

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <Input
        id="username"
        name="username"
        label="Full name"
        value={formData.username}
        onChange={handleChange}
        placeholder="Enter your name"
        autoComplete="username"
        minLength={3}
        maxLength={50}
      />

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

      <RoleDropdown
        id="role"
        name="role"
        value={formData.role}
        onChange={handleChange}
        options={roles}
        required
      />

      <div className="space-y-1.5">
        <label
          htmlFor="password"
          className="block text-sm font-medium text-slate-700"
        >
          Password
        </label>

        <div className="relative">
          <input
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            value={formData.password}
            onChange={handleChange}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            minLength={8}
            required
            className={`${compactInputClass} pr-16`}
          />

          <button
            type="button"
            onClick={() => setShowPassword((value) => !value)}
            className="absolute inset-y-0 right-3 text-sm font-medium text-cyan-700 hover:text-cyan-900"
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      <div className="space-y-1.5">
        <label
          htmlFor="confirmPassword"
          className="block text-sm font-medium text-slate-700"
        >
          Confirm password
        </label>

        <div className="relative">
          <input
            id="confirmPassword"
            name="confirmPassword"
            type={showConfirmPassword ? "text" : "password"}
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Re-enter your password"
            autoComplete="new-password"
            minLength={8}
            required
            className={`${compactInputClass} pr-16`}
          />

          <button
            type="button"
            onClick={() => setShowConfirmPassword((value) => !value)}
            className="absolute inset-y-0 right-3 text-sm font-medium text-cyan-700 hover:text-cyan-900"
          >
            {showConfirmPassword ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {error}
        </p>
      )}

      {success && (
        <p
          role="status"
          className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700"
        >
          {success}
        </p>
      )}

      <Button type="submit" disabled={loading} className="py-2.5">
        {loading ? "Creating account..." : "Create account"}
      </Button>

      <p className="pt-1 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link
          to="/login"
          className="font-semibold text-cyan-700 hover:text-cyan-900"
        >
          Sign in
        </Link>
      </p>
    </form>
  );
}
