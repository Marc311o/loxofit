import type { ReactNode } from "react";
import FitnessCenterRounded from "@mui/icons-material/FitnessCenterRounded";
import HomeOutlined from "@mui/icons-material/HomeOutlined";
import LayersOutlined from "@mui/icons-material/LayersOutlined";
import PersonOutlined from "@mui/icons-material/PersonOutlined";
import SearchRounded from "@mui/icons-material/SearchRounded";

export type NavItem = {
  /** Key in `nav.items`. */
  id: "start" | "plans" | "workout" | "catalog" | "profile";
  to: string;
  icon: ReactNode;
  exact?: boolean;
};

export const NAV_ITEMS: NavItem[] = [
  { id: "start", to: "/", icon: <HomeOutlined />, exact: true },
  { id: "plans", to: "/plans", icon: <LayersOutlined /> },
  { id: "workout", to: "/workout", icon: <FitnessCenterRounded /> },
  { id: "catalog", to: "/catalog", icon: <SearchRounded /> },
  { id: "profile", to: "/profile", icon: <PersonOutlined /> },
];
