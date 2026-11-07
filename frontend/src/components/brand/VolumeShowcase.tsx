import { Box, Stack, Typography } from "@mui/material";
import { keyframes } from "@mui/material/styles";

import { useCycle } from "@/lib/useCycle";
import { FONT_MONO } from "@/styles/theme";

const SCALE = 22; // sets shown at full bar width
const MRV = 16;
const MUSCLES = ["Chest", "Lats", "Quads", "Glutes"] as const;

type Week = {
  label: string;
  rir: number;
  deload?: boolean;
  sets: Record<(typeof MUSCLES)[number], number>;
};

// One mesocycle of the example plan - volume grows, glutes cross MRV in W4, deload drops it.
const WEEKS: Week[] = [
  {
    label: "W1",
    rir: 3,
    sets: { Chest: 7.5, Lats: 9, Quads: 9.5, Glutes: 13.5 },
  },
  {
    label: "W2",
    rir: 2,
    sets: { Chest: 8.5, Lats: 10.5, Quads: 11, Glutes: 15.5 },
  },
  {
    label: "W3",
    rir: 2,
    sets: { Chest: 10, Lats: 12, Quads: 12.5, Glutes: 18 },
  },
  {
    label: "W4",
    rir: 1,
    sets: { Chest: 11.5, Lats: 13.5, Quads: 14, Glutes: 20.5 },
  },
  {
    label: "Deload",
    rir: 4,
    deload: true,
    sets: { Chest: 4, Lats: 4.5, Quads: 5, Glutes: 7 },
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
      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center" }}
      >
        <Typography variant="overline" sx={{ color: "#A9CFC4" }}>
          Effective sets
        </Typography>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <Stack direction="row" spacing={0.5} aria-hidden>
            {WEEKS.map((w, i) => (
              <Box
                key={w.label}
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
            key={week.label}
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
            {week.label.toUpperCase()} · RIR {week.rir}
          </Typography>
        </Stack>
      </Stack>

      {MUSCLES.map((name) => {
        const sets = week.sets[name];
        return (
          <Stack
            key={name}
            direction="row"
            spacing={1.75}
            sx={{ alignItems: "center" }}
          >
            <Typography sx={{ width: 56, fontSize: 13, color: "#E4F1EC" }}>
              {name}
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
              {sets}
            </Typography>
          </Stack>
        );
      })}
    </Box>
  );
}
