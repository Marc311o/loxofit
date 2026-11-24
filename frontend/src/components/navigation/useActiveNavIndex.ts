import { useLocation } from "react-router";

import { NAV_ITEMS } from "@/components/navigation/navItems";

/** Index of the nav item matching the current URL, or -1. */
export function useActiveNavIndex(): number {
  const { pathname } = useLocation();
  return NAV_ITEMS.findIndex((item) =>
    item.exact ? pathname === item.to : pathname.startsWith(item.to),
  );
}
