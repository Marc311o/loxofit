import { Box, Stack, Typography } from "@mui/material";
import { keyframes } from "@mui/material/styles";
import { useTranslation } from "react-i18next";

import { useFormatNumber } from "@/i18n/useLocalized";
import { useCycle } from "@/lib/useCycle";
import { FONT_MONO } from "@/styles/theme";

const SCALE = 22; // sets shown at full bar width
const MRV = 16;
/** Keys in `brand.muscles`. */
const MUSCLES = ["chest", "lats", "quads", "glutes"] as const;

type Week = {
  /** 1-based week number; deload weeks are labelled separately. */
  number: number;
  rir: number;
  deload?: boolean;
  sets: Record<(typeof MUSCLES)[number], number>;
};

// One mesocycle of the example plan - volume grows, glutes cross MRV in W4, deload drops it.
const WEEKS: Week[] = [
  {
    number: 1,
    rir: 3,
    sets: { chest: 7.5, lats: 9, quads: 9.5, glutes: 13.5 },
  },
  {
    number: 2,
    rir: 2,
    sets: { chest: 8.5, lats: 10.5, quads: 11, glutes: 15.5 },
  },
  {
    number: 3,
    rir: 2,
    sets: { chest: 10, lats: 12, quads: 12.5, glutes: 18 },
  },
  {
    number: 4,
    rir: 1,
    sets: { chest: 11.5, lats: 13.5, quads: 14, glutes: 20.5 },
  },
  {
    number: 5,
    rir: 4,
    deload: true,
    sets: { chest: 4, lats: 4.5, quads: 5, glutes: 7 },
  },
];
const STATIC_WEEK = 2;

const fadeIn = keyframes`from { opacity: 0; transform: translateY(3px); } to { opacity: 1; transform: none; }`;

function barColor(sets: number, deload: boolean): string {
  if (deload || sets < 4) return "#8FA39C";
  if (sets <= 13) return "#7FC2AE";
  if (sets <= MRV) return "#A9CFC4";
  return "#E8893A";
}

const NO_MOTION = {
  "@media (prefers-reduced-motion: reduce)": {
    transition: "none",
    animation: "none",
  },
};

export function VolumeShowcase({ animate }: { animate: boolean }) {
  const cycled = useCycle(WEEKS.length, 2600, !animate);
  const index = animate ? cycled : STATIC_WEEK;
  const week = WEEKS[index];
  const { t } = useTranslation("brand");
  const formatNumber = useFormatNumber();
  const weekLabel = week.deload ? t("deload") : t("week", { number: week.number });

  return (
    <Box
      sx={{
        bgcolor: "#1A4D45",
        borderRadius: 2,
        p: 2.5,
        display: "flex",
        flexDirection: "column",
        gap: 1.75,
      }}
    >
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="overline" sx={{ color: "#A9CFC4" }}>
          {t("effectiveSets")}
        </Typography>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <Stack direction="row" spacing={0.5} aria-hidden>
            {WEEKS.map((w, i) => (
              <Box
                key={w.number}
                sx={{
                  width: i === index ? 16 : 6,
                  height: 6,
                  borderRadius: 3,
                  bgcolor: i === index ? "#F3F4F1" : "#2F665D",
                  transition: "width 400ms ease, background-color 400ms ease",
                  ...NO_MOTION,
                }}
              />
            ))}
          </Stack>
          <Typography
            key={week.number}
            sx={{
              minWidth: 92,
              textAlign: "right",
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: "#E4F1EC",
              animation: `${fadeIn} 400ms ease`,
              ...NO_MOTION,
            }}
          >
            {weekLabel.toUpperCase()} · RIR {week.rir}
          </Typography>
        </Stack>
      </Stack>

      {MUSCLES.map((name) => {
        const sets = week.sets[name];
        return (
          <Stack key={name} direction="row" spacing={1.75} sx={{ alignItems: "center" }}>
            <Typography sx={{ width: 84, fontSize: 13, color: "#E4F1EC" }}>
              {t(`muscles.${name}`)}
            </Typography>
            <Box
              sx={{
                position: "relative",
                flex: 1,
                height: 8,
                borderRadius: 4,
                bgcolor: "#2A5A52",
              }}
            >
              <Box
                sx={{
                  position: "absolute",
                  top: 0,
                  bottom: 0,
                  left: 0,
                  width: `${(sets / SCALE) * 100}%`,
                  borderRadius: 4,
                  bgcolor: barColor(sets, Boolean(week.deload)),
                  transition:
                    "width 900ms cubic-bezier(0.2, 0.8, 0.2, 1), background-color 600ms ease",
                  ...NO_MOTION,
                }}
              />
              <Box
                sx={{
                  position: "absolute",
                  left: `${(MRV / SCALE) * 100}%`,
                  top: -3,
                  bottom: -3,
                  width: 2,
                  borderRadius: 1,
                  bgcolor: "#E8893A",
                }}
              />
            </Box>
            <Typography
              key={`${name}-${sets}`}
              sx={{
                width: 34,
                textAlign: "right",
                fontFamily: FONT_MONO,
                fontSize: 12,
                color: "#E4F1EC",
                animation: `${fadeIn} 400ms ease`,
                ...NO_MOTION,
              }}
            >
              {formatNumber(sets)}
            </Typography>
          </Stack>
        );
      })}
    </Box>
  );
}
