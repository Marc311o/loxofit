import CancelRounded from "@mui/icons-material/CancelRounded";
import CheckCircleRounded from "@mui/icons-material/CheckCircleRounded";
import RadioButtonUncheckedRounded from "@mui/icons-material/RadioButtonUncheckedRounded";
import { Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { MIN_PASSWORD_LENGTH, passwordRules } from "@/features/auth/validation";

type Props = { password: string; confirm: string; showErrors: boolean };

/** Live checklist: grey while typing, green when met, red after a failed submit. */
export function PasswordRules({ password, confirm, showErrors }: Props) {
  const { t } = useTranslation("auth");

  return (
    <Stack component="ul" spacing={0.75} sx={{ m: 0, p: 0, listStyle: "none" }} aria-live="polite">
      {passwordRules(password, confirm).map((rule) => {
        const color = rule.ok ? "primary.main" : showErrors ? "error.main" : "text.secondary";
        const Icon = rule.ok
          ? CheckCircleRounded
          : showErrors
            ? CancelRounded
            : RadioButtonUncheckedRounded;
        return (
          <Stack
            component="li"
            key={rule.id}
            direction="row"
            spacing={1}
            sx={{ alignItems: "center", color }}
          >
            <Icon sx={{ fontSize: 16 }} />
            <Typography sx={{ fontSize: 13, color: "inherit" }}>
              {t(`rules.${rule.id}`, { min: MIN_PASSWORD_LENGTH })}
            </Typography>
          </Stack>
        );
      })}
    </Stack>
  );
}
