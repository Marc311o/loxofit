import { useState, type SubmitEvent } from "react";
import BadgeOutlined from "@mui/icons-material/BadgeOutlined";
import LockOutlined from "@mui/icons-material/LockOutlined";
import MailOutlineRounded from "@mui/icons-material/MailOutlineRounded";
import { Alert, Button, Link, Stack, Typography } from "@mui/material";
import { Link as RouterLink, useNavigate } from "react-router";

import { TextInput } from "@/components/TextInput";
import { useRegister } from "@/features/auth/api";
import { PasswordRules } from "@/features/auth/components/PasswordRules";
import {
  validateRegister,
  type RegisterForm,
} from "@/features/auth/validation";
import { getFieldErrors } from "@/lib/api";

const EMPTY: RegisterForm = {
  email: "",
  displayName: "",
  password: "",
  confirm: "",
};

export function RegisterPage() {
  const [form, setForm] = useState<RegisterForm>(EMPTY);
  const [submitted, setSubmitted] = useState(false);
  const register = useRegister();
  const navigate = useNavigate();

  const errors = submitted ? validateRegister(form) : {};
  const server = getFieldErrors(register.error);
  const emailTaken = register.error?.code === "EMAIL_TAKEN";
  const unexpected =
    register.isError && !emailTaken && Object.keys(server).length === 0;

  const update = (field: keyof RegisterForm) => (value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    if (register.isError) register.reset();
  };

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    setSubmitted(true);
    if (Object.keys(validateRegister(form)).length > 0) return;
    register.mutate(
      {
        email: form.email.trim(),
        password: form.password,
        display_name: form.displayName.trim() || undefined,
      },
      { onSuccess: () => navigate("/", { replace: true }) },
    );
  }

  return (
    <Stack component="form" onSubmit={handleSubmit} noValidate spacing={2.25}>
      <Stack spacing={0.5}>
        <Typography variant="h1">Create account</Typography>
        <Typography color="text.secondary">
          Plans balanced for every muscle.
        </Typography>
      </Stack>

      {unexpected && (
        <Alert severity="error">
          Could not create the account. Try again in a moment.
        </Alert>
      )}

      <TextInput
        label="Email"
        type="email"
        icon={<MailOutlineRounded />}
        value={form.email}
        onChange={update("email")}
        autoComplete="email"
        autoFocus
        errorText={
          errors.email ??
          (emailTaken
            ? "An account with this email already exists."
            : server.email)
        }
      />
      <TextInput
        label="Name (optional)"
        icon={<BadgeOutlined />}
        value={form.displayName}
        onChange={update("displayName")}
        autoComplete="nickname"
        errorText={server.display_name}
      />
      <TextInput
        label="Password"
        password
        icon={<LockOutlined />}
        value={form.password}
        onChange={update("password")}
        autoComplete="new-password"
        error={Boolean(errors.password || server.password)}
      />
      <TextInput
        label="Confirm password"
        password
        icon={<LockOutlined />}
        value={form.confirm}
        onChange={update("confirm")}
        autoComplete="new-password"
        error={Boolean(errors.confirm)}
      />
      <PasswordRules
        password={form.password}
        confirm={form.confirm}
        showErrors={submitted}
      />

      <Button
        type="submit"
        variant="contained"
        size="large"
        loading={register.isPending}
      >
        Create account
      </Button>
      <Typography sx={{ textAlign: "center", color: "text.secondary" }}>
        Already have an account?{" "}
        <Link component={RouterLink} to="/login" sx={{ fontWeight: 600 }}>
          Log in
        </Link>
      </Typography>
    </Stack>
  );
}
