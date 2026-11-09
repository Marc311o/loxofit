import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router";

import { Logo } from "@/components/brand/Logo";
// import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { NAV_ITEMS } from "@/components/navigation/navItems";
import { useActiveNavIndex } from "@/components/navigation/useActiveNavIndex";
import { UserCard } from "@/components/navigation/UserCard";

export const SIDE_NAV_WIDTH = 240;

export function SideNav() {
  const { t } = useTranslation("nav");
  const active = useActiveNavIndex();
  return (
    <Drawer
      variant="permanent"
      component="nav"
      aria-label={t("label")}
      sx={{
        width: SIDE_NAV_WIDTH,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: SIDE_NAV_WIDTH,
          boxSizing: "border-box",
          px: 1.75,
          py: 3,
          gap: 3.5,
        },
      }}
    >
      <Box sx={{ px: 1 }}>
        <Logo />
      </Box>
      <List disablePadding sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
        {NAV_ITEMS.map((item, index) => {
          const selected = index === active;
          return (
            <ListItemButton
              key={item.to}
              component={RouterLink}
              to={item.to}
              selected={selected}
              aria-current={selected ? "page" : undefined}
              sx={{
                borderRadius: 1,
                minHeight: 44,
                color: "text.secondary",
                "&.Mui-selected": {
                  bgcolor: "primary.light",
                  color: "primary.dark",
                  fontWeight: 600,
                },
                "&.Mui-selected:hover": { bgcolor: "primary.light" },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: "inherit" }}>{item.icon}</ListItemIcon>
              <ListItemText
                primary={t(`items.${item.id}`)}
                slotProps={{
                  primary: { sx: { fontSize: 14, fontWeight: "inherit" } },
                }}
              />
            </ListItemButton>
          );
        })}
      </List>
      <Stack spacing={1.5} sx={{ mt: "auto" }}>
        {/* LANGUAGE SWITCHER */}
        {/*<Box sx={{ px: 1 }}>*/}
        {/*  <LanguageSwitcher />*/}
        {/*</Box>*/}
        <UserCard />
      </Stack>
    </Drawer>
  );
}
