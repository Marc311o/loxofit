import { useMemo, type ReactNode } from "react";
import CssBaseline from "@mui/material/CssBaseline";
import { enUS, plPL } from "@mui/material/locale";
import { createTheme, ThemeProvider as MuiThemeProvider } from "@mui/material/styles";

import { useLanguage, type Language } from "@/i18n";
import { theme } from "@/styles/theme";

const MUI_LOCALES = { en: enUS, pl: plPL } satisfies Record<Language, object>;

export function ThemeProvider({ children }: { children: ReactNode }) {
  const language = useLanguage();
  const localizedTheme = useMemo(() => createTheme(theme, MUI_LOCALES[language]), [language]);

  return (
    <MuiThemeProvider theme={localizedTheme}>
      <CssBaseline />
      {children}
    </MuiThemeProvider>
  );
}
