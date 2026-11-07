import type { ReactNode } from "react";
import FitnessCenterRounded from "@mui/icons-material/FitnessCenterRounded";
import HomeOutlined from "@mui/icons-material/HomeOutlined";
import LayersOutlined from "@mui/icons-material/LayersOutlined";
import PersonOutlined from "@mui/icons-material/PersonOutlined";
import SearchRounded from "@mui/icons-material/SearchRounded";

export type NavItem = {
  label: string;
  to: string;
  icon: ReactNode;
  exact?: boolean;
};

export const NAV_ITEMS: NavItem[] = [
  { label: "Start", to: "/", icon: <HomeOutlined />, exact: true },
  { label: "Plans", to: "/plans", icon: <LayersOutlined /> },
  { label: "Workout", to: "/workout", icon: <FitnessCenterRounded /> },
  { label: "Catalog", to: "/catalog", icon: <SearchRounded /> },
  { label: "Profile", to: "/profile", icon: <PersonOutlined /> },
];
