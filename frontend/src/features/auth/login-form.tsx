import { useNavigate } from "@tanstack/react-router";
import { Check, Eye, EyeOff, Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Credentials } from "@/lib/api/auth";
import { errorMessage } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { DEMO_ACCOUNTS } from "@/lib/constants/demo-accounts";

export function LoginForm() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const form = useForm<Credentials>({
    defaultValues: { email: "owner@whitfield.com", password: "whitfield" },
  });
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDemo, setSelectedDemo] = useState<string | null>("owner@whitfield.com");
  const emailField = form.register("email", { required: true });
  const passwordField = form.register("password", { required: true });

  const handleSubmit = form.handleSubmit(async ({ email, password }) => {
    setSubmitting(true);
    setError(null);
    try {
      await signIn(email, password);
      toast.success("Signed in to Whitfield");
      navigate({ to: "/dashboard" });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <div>
      <h1 className="text-[28px] leading-tight font-semibold tracking-tight">Welcome back</h1>
      <p className="mt-1.5 text-sm text-muted-foreground">Sign in to Whitfield Fulfillment</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            {...emailField}
            onChange={(e) => {
              emailField.onChange(e);
              setSelectedDemo(null);
            }}
            className="h-11 rounded-xl"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              {...passwordField}
              onChange={(e) => {
                passwordField.onChange(e);
                setSelectedDemo(null);
              }}
              className="h-11 rounded-xl pr-11"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute top-1/2 right-2 -translate-y-1/2 rounded-lg p-2 text-muted-foreground hover:text-foreground"
            >
              {showPassword ? (
                <EyeOff className="size-4" aria-hidden />
              ) : (
                <Eye className="size-4" aria-hidden />
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <Checkbox id="remember" defaultChecked /> Remember me
          </label>
          <button type="button" className="text-sm text-primary hover:underline">
            Forgot password?
          </button>
        </div>

        {error ? (
          <p
            role="alert"
            className="rounded-xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {error}
          </p>
        ) : null}

        <Button
          type="submit"
          disabled={submitting}
          className="grad-brand h-11 w-full rounded-xl text-white"
        >
          {submitting ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
          Sign in
        </Button>
      </form>

      <div className="mt-8 rounded-2xl border border-border/80 bg-surface/80 p-3 shadow-sm">
        <div className="mb-3 border-b border-border/70 pb-3">
          <p className="text-sm font-medium text-foreground">Demo Accounts</p>
          <p className="mt-1 text-xs text-muted-foreground">Quickly fill test credentials</p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {DEMO_ACCOUNTS.map((account) => {
            const Icon = account.icon;
            const selected = selectedDemo === account.email;
            return (
              <button
                key={account.email}
                type="button"
                onClick={() => {
                  form.setValue("email", account.email, { shouldDirty: true });
                  form.setValue("password", account.password, { shouldDirty: true });
                  setSelectedDemo(account.email);
                  setError(null);
                }}
                className={`flex min-w-0 items-start gap-2 rounded-xl border px-2.5 py-2 text-left transition ${
                  selected
                    ? "border-primary/70 bg-primary/10 shadow-[0_0_0_1px_hsl(var(--primary)/0.18)]"
                    : "border-border/80 bg-background/35 hover:border-primary/45 hover:bg-primary/5"
                }`}
              >
                <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="size-4" aria-hidden />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-xs font-medium text-foreground sm:text-sm">
                    {account.label}
                  </span>
                  <span className="mt-0.5 block text-[11px] leading-tight text-muted-foreground">
                    {account.description}
                  </span>
                </span>
                {selected ? <Check className="size-4 text-primary" aria-hidden /> : null}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
