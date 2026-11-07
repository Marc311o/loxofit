import { Box } from "@mui/material";
import { Outlet } from "react-router";

import { BrandPanel } from "@/components/BrandPanel";

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
          display: "flex",
          justifyContent: "center",
          alignItems: { md: "center" },
          px: 3,
          py: { xs: 4, md: 6 },
        }}
      >
        <Box sx={{ width: "100%", maxWidth: 400 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
