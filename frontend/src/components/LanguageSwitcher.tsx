import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";

import { changeLanguage, SUPPORTED_LANGUAGES, useLanguage, type Language } from "@/i18n";

export function LanguageSwitcher() {
  const { t } = useTranslation();
  const language = useLanguage();

  return (
    <ToggleButtonGroup
      exclusive
      size="small"
      value={language}
      onChange={(_, value: Language | null) => {
        if (value) void changeLanguage(value);
      }}
      aria-label={t("language.label")}
    >
      {SUPPORTED_LANGUAGES.map((option) => (
        <ToggleButton
          key={option}
          value={option}
          lang={option}
          aria-label={t(`language.${option}`)}
          sx={{ px: 1.5, py: 0.5, fontSize: 12, fontWeight: 600 }}
        >
          {option.toUpperCase()}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}
