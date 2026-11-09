import { useState, type SubmitEvent } from "react";
import LockOutlined from "@mui/icons-material/LockOutlined";
import MailOutlineRounded from "@mui/icons-material/MailOutlineRounded";
import { Button, Link, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useLocation, useNavigate } from "react-router";

import { TextInput } from "@/components/TextInput";
import { useLogin } from "@/features/auth/api";
import { errorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";

export function LoginPage() {
  const { t } = useTranslation("auth");
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
          if (error.code === "ACCOUNT_INACTIVE") toast.warning(errorMessage(error));
          else if (error.code !== "INVALID_CREDENTIALS") toast.error(errorMessage(error));
        },
      },
    );
  }

  return (
    <Stack component="form" onSubmit={handleSubmit} noValidate spacing={2.25}>
      <Stack spacing={0.5}>
        <Typography variant="h1">{t("login.title")}</Typography>
        <Typography color="text.secondary">{t("login.subtitle")}</Typography>
      </Stack>

      <TextInput
        label={t("login.email")}
        type="email"
        icon={<MailOutlineRounded />}
        placeholder={t("login.emailPlaceholder")}
        value={email}
        onChange={edit(setEmail)}
        autoComplete="email"
        autoFocus
        error={wrongCredentials}
        errorText={submitted && !email.trim() ? t("validation.emailRequired") : undefined}
      />
      <TextInput
        label={t("login.password")}
        password
        icon={<LockOutlined />}
        placeholder={t("login.passwordPlaceholder")}
        value={password}
        onChange={edit(setPassword)}
        autoComplete="current-password"
        error={wrongCredentials}
        errorText={
          wrongCredentials
            ? errorMessage(login.error)
            : submitted && !password
              ? t("validation.passwordRequired")
              : undefined
        }
      />

      <Button type="submit" variant="contained" size="large" loading={login.isPending}>
        {t("login.submit")}
      </Button>
      <Typography sx={{ textAlign: "center", color: "text.secondary" }}>
        {t("login.noAccount")}{" "}
        <Link component={RouterLink} to="/register" sx={{ fontWeight: 600 }}>
          {t("login.createOne")}
        </Link>
      </Typography>
    </Stack>
  );
}
