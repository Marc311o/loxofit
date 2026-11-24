import { Box, useMediaQuery, type Theme } from "@mui/material";
import { Outlet } from "react-router";

import { BottomNav } from "@/components/navigation/BottomNav";
import { SideNav } from "@/components/navigation/SideNav";

export function AppLayout() {
  const isDesktop = useMediaQuery((theme: Theme) => theme.breakpoints.up("md"));

  return (
    <Box
      sx={{
        display: "flex",
        minHeight: "100dvh",
        bgcolor: "background.default",
      }}
    >
      {isDesktop && <SideNav />}
      <Box
        component="main"
        sx={{
          flex: 1,
          minWidth: 0,
          px: { xs: 2.5, md: 5 },
          pt: { xs: 3.5, md: 4.5 },
          pb: { xs: "calc(88px + env(safe-area-inset-bottom))", md: 6 },
        }}
      >
        <Box sx={{ maxWidth: 1140, mx: "auto" }}>
          <Outlet />
        </Box>
      </Box>
      {!isDesktop && <BottomNav />}
    </Box>
  );
}
