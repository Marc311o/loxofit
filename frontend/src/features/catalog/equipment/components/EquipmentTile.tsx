import { useState } from "react";
import CheckRounded from "@mui/icons-material/CheckRounded";
import FitnessCenterRounded from "@mui/icons-material/FitnessCenterRounded";
import { Box, ButtonBase, Typography } from "@mui/material";
import { keyframes } from "@mui/material/styles";

import { useLanguage } from "@/i18n";
import { useLocalizedName } from "@/i18n/useLocalized";
import type { Equipment } from "../../types";

/** Saved and current selection combined - pending states get the moving dashed border. */
export type TileState = "owned" | "off" | "adding" | "removing";

const RADIUS = 20;
const STROKE = 2;
const DASH = 8;
const GAP = 6;
const PERIODS = 60;

const march = keyframes`
  to { stroke-dashoffset: -${DASH + GAP}; }
`;

function PendingBorder({ color }: { color: string }) {
  return (
    <Box
      component="svg"
      aria-hidden
      sx={{
        position: "absolute",
        inset: STROKE / 2,
        width: `calc(100% - ${STROKE}px)`,
        height: `calc(100% - ${STROKE}px)`,
        overflow: "visible",
        pointerEvents: "none",
        color,
      }}
    >
      <Box
        component="rect"
        width="100%"
        height="100%"
        rx={RADIUS - STROKE / 2}
        fill="none"
        stroke="currentColor"
        strokeWidth={STROKE}
        pathLength={PERIODS * (DASH + GAP)}
        strokeDasharray={`${DASH} ${GAP}`}
        sx={{
          animation: `${march} 0.6s linear infinite`,
          "@media (prefers-reduced-motion: reduce)": { animation: "none" },
        }}
      />
    </Box>
  );
}

function TileImage({ imageUrl }: { imageUrl: string | null }) {
  const [failed, setFailed] = useState(false);
  return (
    <Box
      sx={{
        aspectRatio: "1",
        borderRadius: "14px",
        overflow: "hidden",
        display: "grid",
        placeItems: "center",
        bgcolor: "background.default",
        color: "text.secondary",
      }}
    >
      {imageUrl && !failed ? (
        <Box
          component="img"
          src={imageUrl}
          alt=""
          loading="lazy"
          onError={() => setFailed(true)}
          sx={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      ) : (
        <FitnessCenterRounded sx={{ fontSize: 40, opacity: 0.6 }} />
      )}
    </Box>
  );
}

type EquipmentTileProps = {
  item: Equipment;
  state: TileState;
  onToggle: () => void;
};

export function EquipmentTile({ item, state, onToggle }: EquipmentTileProps) {
  const language = useLanguage();
  const localizedName = useLocalizedName();
  const selected = state === "owned" || state === "adding";
  const pending = state === "adding" || state === "removing";
  const nameId = `equipment-${item.id}-name`;

  return (
    <Box sx={{ position: "relative", borderRadius: `${RADIUS}px` }}>
      <ButtonBase
        role="checkbox"
        aria-checked={selected}
        aria-labelledby={nameId}
        onClick={onToggle}
        sx={(theme) => ({
          display: "flex",
          flexDirection: "column",
          alignItems: "stretch",
          justifyContent: "flex-start",
          width: "100%",
          height: "100%",
          textAlign: "left",
          p: 1.25,
          borderRadius: `${RADIUS}px`,
          bgcolor: "background.paper",
          border: "2px solid",
          borderColor: pending ? "transparent" : state === "owned" ? "primary.main" : "divider",
          transition: theme.transitions.create("border-color"),
          "&:hover": { bgcolor: "action.hover" },
          "&.Mui-focusVisible": {
            outline: `2px solid ${theme.palette.primary.main}`,
            outlineOffset: 2,
          },
        })}
      >
        <TileImage imageUrl={item.image_url} />
        <Typography id={nameId} sx={{ fontWeight: 600, lineHeight: 1.3, mt: 1.25, px: 0.5 }}>
          {localizedName(item)}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ px: 0.5, pb: 0.5 }}>
          {language === "pl" ? item.name_en : item.name_pl}
        </Typography>
      </ButtonBase>

      {pending && <PendingBorder color={state === "adding" ? "primary.main" : "text.disabled"} />}

      {selected && (
        <Box
          aria-hidden
          sx={{
            position: "absolute",
            top: 18,
            right: 18,
            width: 26,
            height: 26,
            borderRadius: "50%",
            display: "grid",
            placeItems: "center",
            bgcolor: "primary.main",
            color: "primary.contrastText",
            boxShadow: 1,
            pointerEvents: "none",
          }}
        >
          <CheckRounded sx={{ fontSize: 18 }} />
        </Box>
      )}
    </Box>
  );
}
