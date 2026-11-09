import { useTranslation } from "react-i18next";
import { Outlet } from "react-router";

import { PageHeader } from "@/components/PageHeader";
import { CatalogSectionSwitcher } from "./components/CatalogSectionSwitcher";

export function CatalogLayout() {
  const { t } = useTranslation("catalog");

  return (
    <>
      <PageHeader title={t("title")} actions={<CatalogSectionSwitcher />} />
      <Outlet />
    </>
  );
}
