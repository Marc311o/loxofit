import { useState, type SubmitEvent } from "react";
import LockOutlined from "@mui/icons-material/LockOutlined";
import MailOutlineRounded from "@mui/icons-material/MailOutlineRounded";
import { Button, Link, Stack, Typography } from "@mui/material";
import { Link as RouterLink, useLocation, useNavigate } from "react-router";

import { TextInput } from "@/components/TextInput";
import { useLogin } from "@/features/auth/api";
import { toast } from "@/lib/toast.ts";
import { errorMessage } from "@/lib/api.ts";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const login = useLogin();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? "/";

  const wrongCredentials = login.error?.code === "INVALID_CREDENTIALS";

  const edit = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    if (login.isError) login.reset();
  };

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    setSubmitted(true);
    if (!email.trim() || !password) return;
    login.mutate(
      { email: email.trim(), password },
      {
        onSuccess: () => navigate(from, { replace: true }),
        onError: (error) => {
          if (error.code === "ACCOUNT_INACTIVE")
            toast.warning("This account is disabled.");
          else if (error.code !== "INVALID_CREDENTIALS")
            toast.error(errorMessage(error));
        },
      },
    );
  }

  return (
    <Stack component="form" onSubmit={handleSubmit} noValidate spacing={2.25}>
      <Stack spacing={0.5}>
        <Typography variant="h1">Welcome back</Typography>
        <Typography color="text.secondary">
          Log in to continue your mesocycle.
        </Typography>
      </Stack>

      <TextInput
        label="Email"
        type="email"
        icon={<MailOutlineRounded />}
        placeholder="john.doe@email.com"
        value={email}
        onChange={edit(setEmail)}
        autoComplete="email"
        autoFocus
        error={wrongCredentials}
        errorText={submitted && !email.trim() ? "Enter your email." : undefined}
      />
      <TextInput
        label="Password"
        password
        icon={<LockOutlined />}
        placeholder={"password"}
        value={password}
        onChange={edit(setPassword)}
        autoComplete="current-password"
        error={wrongCredentials}
        errorText={
          wrongCredentials
            ? "Wrong email or password."
            : submitted && !password
              ? "Enter your password."
              : undefined
        }
      />

      <Button
        type="submit"
        variant="contained"
        size="large"
        loading={login.isPending}
      >
        Log in
      </Button>
      <Typography sx={{ textAlign: "center", color: "text.secondary" }}>
        No account yet?{" "}
        <Link component={RouterLink} to="/register" sx={{ fontWeight: 600 }}>
          Create one
        </Link>
      </Typography>
    </Stack>
  );
}
