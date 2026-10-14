/** @format */

import AuthLayout from "../components/layout/AuthLayout";
import RegisterForm from "../components/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <AuthLayout
      title="Create your account"
      subtitle="Register to start organizing your DermAI research cases."
    >
      <RegisterForm />
    </AuthLayout>
  );
}
