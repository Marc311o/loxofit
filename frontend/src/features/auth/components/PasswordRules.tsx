import CheckCircleRounded from "@mui/icons-material/CheckCircleRounded";
import RadioButtonUncheckedRounded from "@mui/icons-material/RadioButtonUncheckedRounded";
import CancelRounded from "@mui/icons-material/CancelRounded";
import { Stack, Typography } from "@mui/material";

import { passwordRules } from "@/features/auth/validation";

type Props = { password: string; confirm: string; showErrors: boolean };

/** Live checklist: grey while typing, green when met, red after a failed submit. */
export function PasswordRules({ password, confirm, showErrors }: Props) {
  return (
    <Stack
      component="ul"
      spacing={0.75}
      sx={{ m: 0, p: 0, listStyle: "none" }}
      aria-live="polite"
    >
      {passwordRules(password, confirm).map((rule) => {
        const color = rule.ok
          ? "primary.main"
          : showErrors
            ? "error.main"
            : "text.secondary";
        const Icon = rule.ok
          ? CheckCircleRounded
          : showErrors
            ? CancelRounded
            : RadioButtonUncheckedRounded;
        return (
          <Stack
            component="li"
            key={rule.label}
            direction="row"
            spacing={1}
            sx={{ alignItems: "center", color }}
          >
            <Icon sx={{ fontSize: 16 }} />
            <Typography sx={{ fontSize: 13, color: "inherit" }}>
              {rule.label}
            </Typography>
          </Stack>
        );
      })}
    </Stack>
  );
}
