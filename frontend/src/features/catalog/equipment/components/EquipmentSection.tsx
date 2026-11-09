import { Box, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { FONT_MONO } from "@/styles/theme";
import type { Equipment, EquipmentCategory } from "../../types";
import { EquipmentTile, type TileState } from "./EquipmentTile";

function tileState(saved: boolean, selected: boolean): TileState {
  if (saved) return selected ? "owned" : "removing";
  return selected ? "adding" : "off";
}

type EquipmentSectionProps = {
  category: EquipmentCategory;
  items: Equipment[];
  saved: ReadonlySet<number>;
  selected: ReadonlySet<number>;
  onToggle: (id: number) => void;
};

export function EquipmentSection({
  category,
  items,
  saved,
  selected,
  onToggle,
}: EquipmentSectionProps) {
  const { t } = useTranslation("catalog");
  const titleId = `equipment-${category}`;
  const selectedCount = items.filter((item) => selected.has(item.id)).length;

  return (
    <Stack component="section" aria-labelledby={titleId} spacing={1.25}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "baseline" }}>
        <Typography id={titleId} variant="overline" color="text.secondary" component="h2">
          {t(`equipmentCategories.${category}`)}
        </Typography>
        <Typography sx={{ fontFamily: FONT_MONO, fontSize: 12, color: "text.secondary" }}>
          {selectedCount}/{items.length}
        </Typography>
      </Stack>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "repeat(2, minmax(0, 1fr))",
            sm: "repeat(auto-fill, minmax(160px, 1fr))",
          },
          gap: 1.5,
        }}
      >
        {items.map((item) => (
          <EquipmentTile
            key={item.id}
            item={item}
            state={tileState(saved.has(item.id), selected.has(item.id))}
            onToggle={() => onToggle(item.id)}
          />
        ))}
      </Box>
    </Stack>
  );
}
