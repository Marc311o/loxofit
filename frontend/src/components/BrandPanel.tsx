import { Box, Stack, Typography, useMediaQuery } from "@mui/material";

import { Logo } from "@/components/brand/Logo";
import { RotatingTiles } from "@/components/brand/RotatingTiles";
import { VolumeShowcase } from "@/components/brand/VolumeShowcase";
import { FONT_DISPLAY } from "@/styles/theme";

/** Dark brand area of the auth screens: a header band on phones, a half-screen panel on desktop. */
export function BrandPanel() {
  const animate = !useMediaQuery("(prefers-reduced-motion: reduce)");

  return (
    <Box
      sx={{
        bgcolor: "primary.dark",
        color: "#F3F4F1",
        px: { xs: 3, md: 8 },
        pt: { xs: 6, md: 7 },
        pb: { xs: 3.5, md: 7 },
        borderRadius: { xs: "0 0 32px 32px", md: 0 },
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        gap: { xs: 3.5, md: 6 },
      }}
    >
      <Logo inverted />

      <Stack spacing={4} sx={{ maxWidth: 460}}>
        <Typography
          sx={{
            display: { xs: "none", md: "block" },
            fontFamily: FONT_DISPLAY,
            fontSize: 44,
            fontWeight: 600,
            lineHeight: 1.1,
            letterSpacing: "-0.02em",
          }}
        >
          Every muscle gets the volume it needs. Not more.
        </Typography>
        <VolumeShowcase animate={animate} />
        <Box sx={{ display: { xs: "none", md: "block" } }}>
          <RotatingTiles animate={animate} />
        </Box>
      </Stack>

      <Typography
        sx={{
          display: { xs: "none", md: "block" },
          fontSize: 14,
          color: "#A9CFC4",
        }}
      >
        Plans checked against MEV, MAV and MRV, set by set.
      </Typography>
    </Box>
  );
}
