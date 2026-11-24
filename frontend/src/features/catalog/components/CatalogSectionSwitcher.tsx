import { Box, ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useLocation } from "react-router";

import { CATALOG_SECTIONS } from "../sections.tsx";

export function CatalogSectionSwitcher() {
  const { t } = useTranslation("catalog");
  const { pathname } = useLocation();
  const active =
    CATALOG_SECTIONS.find((section) => pathname.startsWith(`/catalog/${section.id}`))?.id ?? null;

  return (
    <ToggleButtonGroup exclusive size="small" value={active} aria-label={t("sections")}>
      {CATALOG_SECTIONS.map((section) => (
        <ToggleButton
          key={section.id}
          value={section.id}
          component={RouterLink}
          to={`/catalog/${section.id}`}
          aria-label={t(`tabs.${section.id}`)}
          aria-current={active === section.id ? "page" : undefined}
          sx={{
            gap: 1,
            px: { xs: 1.5, sm: 2 },
            fontWeight: 600,
            "&.Mui-selected, &.Mui-selected:hover": {
              bgcolor: "primary.light",
              color: "primary.dark",
            },
          }}
        >
          {section.icon}
          <Box component="span" sx={{ display: { xs: "none", sm: "inline" } }}>
            {t(`tabs.${section.id}`)}
          </Box>
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}
