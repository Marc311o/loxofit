import { Box } from "@mui/material";
import { Outlet } from "react-router";

import { BrandPanel } from "@/components/BrandPanel";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export function AuthLayout() {
  return (
    <Box
      sx={{
        minHeight: "100dvh",
        bgcolor: "background.default",
        display: "grid",
        gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
        gridTemplateRows: { xs: "auto 1fr", md: "1fr" },
      }}
    >
      <BrandPanel />
      <Box
        sx={{
          position: "relative",
          display: "flex",
          justifyContent: "center",
          alignItems: { md: "center" },
          px: 3,
          pt: { xs: 9, md: 6 },
          pb: { xs: 4, md: 6 },
        }}
      >
        <Box sx={{ position: "absolute", top: { xs: 20, md: 24 }, right: 24 }}>
          <LanguageSwitcher />
        </Box>
        <Box sx={{ width: "100%", maxWidth: 400 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
