import { BottomNavigation, BottomNavigationAction, Paper } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router";

import { NAV_ITEMS } from "@/components/navigation/navItems";
import { useActiveNavIndex } from "@/components/navigation/useActiveNavIndex";

export function BottomNav() {
  const { t } = useTranslation("nav");
  const active = useActiveNavIndex();
  return (
    <Paper
      component="nav"
      aria-label={t("label")}
      square
      elevation={0}
      sx={{
        position: "fixed",
        insetInline: 0,
        bottom: 0,
        zIndex: "appBar",
        borderTop: 1,
        borderColor: "divider",
        pb: "env(safe-area-inset-bottom)",
      }}
    >
      <BottomNavigation showLabels value={active}>
        {NAV_ITEMS.map((item) => (
          <BottomNavigationAction
            key={item.to}
            label={t(`items.${item.id}`)}
            icon={item.icon}
            component={RouterLink}
            to={item.to}
          />
        ))}
      </BottomNavigation>
    </Paper>
  );
}
