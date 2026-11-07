import { createTheme } from "@mui/material/styles";

export const FONT_DISPLAY = '"Space Grotesk", "Inter", sans-serif';
export const FONT_MONO = '"JetBrains Mono", ui-monospace, monospace';

/** Volume zones relative to MEV / MAV / MRV - shared by every volume bar. */
export const zoneColors = {
  belowMev: "#C9D1CD",
  mevMav: "#4C9A86",
  mavMrv: "#1D5C52",
  aboveMrv: "#D27A2C",
} as const;

export const theme = createTheme({
  palette: {
    primary: {
      main: "#1D5C52",
      dark: "#12403A",
      light: "#DDEBE6",
      contrastText: "#FFFFFF",
    },
    warning: { main: "#D27A2C", dark: "#B85C1E", light: "#F7E6D8" },
    background: { default: "#F3F4F1", paper: "#FFFFFF" },
    text: { primary: "#14211E", secondary: "#5B6965" },
    divider: "#DCE2DD",
    error: { main: "#C62828", light: "#FDECEA" },
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: '"Inter", system-ui, sans-serif',
    h1: {
      fontFamily: FONT_DISPLAY,
      fontWeight: 600,
      fontSize: "1.875rem",
      letterSpacing: "-0.01em",
    },
    h2: { fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: "1.5rem" },
    h3: { fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: "1.125rem" },
    overline: {
      fontFamily: FONT_MONO,
      fontSize: "0.6875rem",
      letterSpacing: "0.08em",
      lineHeight: 1.6,
    },
    button: { textTransform: "none", fontWeight: 600 },
  },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 14, minHeight: 44 },
        sizeLarge: { minHeight: 52, fontSize: "1rem" },
      },
    },
    MuiCard: {
      defaultProps: { variant: "outlined" },
      styleOverrides: { root: { borderRadius: 20 } },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { borderRadius: 12, backgroundColor: "#FFFFFF" },
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: { marginInline: 4, marginTop: 6, fontSize: 12, lineHeight: 1.4 },
      },
    },
  },
});
