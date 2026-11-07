import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import { Link as RouterLink } from "react-router";

import { Logo } from "@/components/brand/Logo.tsx";
import { NAV_ITEMS } from "@/components/navigation/navItems";
import { useActiveNavIndex } from "@/components/navigation/useActiveNavIndex";
import { UserCard } from "@/components/navigation/UserCard";

export const SIDE_NAV_WIDTH = 240;

export function SideNav() {
  const active = useActiveNavIndex();
  return (
    <Drawer
      variant="permanent"
      component="nav"
      aria-label="Main"
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
      <List
        disablePadding
        sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}
      >
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
              <ListItemIcon sx={{ minWidth: 36, color: "inherit" }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                slotProps={{
                  primary: { sx: { fontSize: 14, fontWeight: "inherit" } },
                }}
              />{" "}
            </ListItemButton>
          );
        })}
      </List>
      <Box sx={{ mt: "auto" }}>
        <UserCard />
      </Box>
    </Drawer>
  );
}
