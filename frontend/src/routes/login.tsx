import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { AuthLayout } from "@/features/auth/auth-layout";
import { LoginForm } from "@/features/auth/login-form";
import { useAuth } from "@/lib/auth/auth-context";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — Whitfield Fulfillment WMS" },
      { name: "description", content: "Sign in to Whitfield Fulfillment to receive, reserve, fulfill and trace inventory across Reno and Columbus." },
      { property: "og:title", content: "Sign in — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Operations, without the spreadsheet chaos." },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    if (isAuthenticated) navigate({ to: "/dashboard", replace: true });
  }, [isAuthenticated, navigate]);

  return (
    <AuthLayout>
      <LoginForm />
    </AuthLayout>
  );
}
