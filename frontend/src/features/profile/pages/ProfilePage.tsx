import { Card, CardContent, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { PageHeader } from "@/components/PageHeader";

export function ProfilePage() {
  const { t } = useTranslation(["common", "nav"]);

  return (
    <>
      <PageHeader title={t("nav:items.profile")} />
      <Card>
        <CardContent>
          <Stack
            direction="row"
            spacing={2}
            sx={{ alignItems: "center", justifyContent: "space-between" }}
          >
            <Typography sx={{ fontWeight: 600 }}>{t("language.label")}</Typography>
            <LanguageSwitcher />
          </Stack>
        </CardContent>
      </Card>
    </>
  );
}
