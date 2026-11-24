import { useState } from "react";
import { Box, Stack, Typography, useTheme } from "@mui/material";
import { useTranslation } from "react-i18next";

import { MUSCLE_GROUPS, type MuscleGroup } from "../types";
import { BODY_MAP_VIEWBOX, DECOR_PATHS, MUSCLE_PATHS } from "./bodyMapPaths";

const COLORS = {
  decor: "#E6EBE7",
  idle: "#C9D1CD",
  hover: "#8FBFB0",
};

type BodyMapProps = {
  selected: MuscleGroup | null;
  onSelect: (group: MuscleGroup | null) => void;
};

export function BodyMap({ selected, onSelect }: BodyMapProps) {
  const { t } = useTranslation("catalog");
  const theme = useTheme();
  const [hovered, setHovered] = useState<MuscleGroup | null>(null);

  const caption = hovered ?? selected;

  const fillFor = (group: MuscleGroup) =>
    group === selected
      ? theme.palette.primary.main
      : group === hovered
        ? COLORS.hover
        : COLORS.idle;

  return (
    <Stack spacing={0.75}>
      <Box
        component="svg"
        viewBox={BODY_MAP_VIEWBOX}
        aria-hidden
        sx={{ width: "100%", display: "block" }}
      >
        <g fill={COLORS.decor} pointerEvents="none">
          {DECOR_PATHS.map((d) => (
            <path key={d} d={d} />
          ))}
        </g>
        {MUSCLE_GROUPS.map((group) => (
          <g
            key={group}
            fill={fillFor(group)}
            onClick={() => onSelect(group === selected ? null : group)}
            onPointerEnter={() => setHovered(group)}
            onPointerLeave={() => setHovered(null)}
            style={{ cursor: "pointer", transition: "fill 150ms" }}
          >
            {MUSCLE_PATHS[group].map((d) => (
              <path key={d} d={d} />
            ))}
          </g>
        ))}
      </Box>

      {/* The figures sit in the left and right half of the drawing. */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          textAlign: "center",
        }}
      >
        <Typography variant="overline" color="text.secondary">
          {t("filters.bodyFront")}
        </Typography>
        <Typography variant="overline" color="text.secondary">
          {t("filters.bodyBack")}
        </Typography>
      </Box>

      {/* Fixed-height caption, so hovering never shifts the layout. */}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ textAlign: "center", minHeight: 20 }}
      >
        {caption ? t(`muscleGroups.${caption}`) : t("filters.bodyHint")}
      </Typography>
    </Stack>
  );
}
