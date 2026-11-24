import { Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router";

import { EmptyState } from "@/components/EmptyState";

export function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        minHeight: "100dvh",
        display: "grid",
        placeItems: "center",
        bgcolor: "background.default",
        p: 3,
      }}
    >
      <EmptyState
        title={t("notFound.title")}
        description={t("notFound.description")}
        action={
          <Button variant="contained" component={RouterLink} to="/">
            {t("notFound.backHome")}
          </Button>
        }
      />
    </Box>
  );
}
