import { Box, useTheme } from "@mui/material";

import { DECOR_PATHS, MUSCLE_FIGURES, MUSCLE_PATHS } from "./bodyMapPaths";

/** The whole silhouette; whatever lies outside the crop is simply not visible. */
const BODY_PATHS = [...DECOR_PATHS, ...Object.values(MUSCLE_PATHS).flat()];

type MuscleFigureProps = {
  code: string;
  size?: number;
};

/** Square close-up of the body with one muscle highlighted - the muscle's "photo". */
export function MuscleFigure({ code, size = 72 }: MuscleFigureProps) {
  const theme = useTheme();
  const figure = MUSCLE_FIGURES[code];

  return (
    <Box
      sx={{
        width: size,
        height: size,
        flexShrink: 0,
        borderRadius: "16px",
        overflow: "hidden",
        bgcolor: "background.default",
      }}
    >
      {figure && (
        <Box
          component="svg"
          viewBox={figure.crop}
          aria-hidden
          sx={{ width: "100%", height: "100%", display: "block" }}
        >
          <g fill={theme.palette.divider}>
            {BODY_PATHS.map((d) => (
              <path key={d} d={d} />
            ))}
          </g>
          <g fill={theme.palette.primary.main}>
            {figure.paths.map((d) => (
              <path key={d} d={d} />
            ))}
          </g>
        </Box>
      )}
    </Box>
  );
}
