import { Stack, Typography } from "@mui/material";

import { LogoMark } from "@/components/brand/LogoMark.tsx";
import { FONT_DISPLAY } from "@/styles/theme";

type LogoProps = { inverted?: boolean; size?: number };

export function Logo({ inverted = false, size = 40 }: LogoProps) {
  return (
    <Stack direction="row" spacing={1.25} sx={{ alignItems: "center" }}>
      <LogoMark size={size} />
      <Typography
        component="span"
        sx={{
          fontFamily: FONT_DISPLAY,
          fontSize: size * 0.6,
          fontWeight: 600,
          letterSpacing: "-0.01em",
          color: inverted ? "#F3F4F1" : "text.primary",
        }}
      >
        loxofit
      </Typography>
    </Stack>
  );
}
