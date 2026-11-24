import { Box, Stack, Typography } from "@mui/material";
import { keyframes } from "@mui/material/styles";
import { useTranslation } from "react-i18next";

import { useCycle } from "@/lib/useCycle";
import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";

/** Keys in `brand.tiles`; the texts live in the locale files. */
const TILES = [
  { id: "today" },
  { id: "score" },
  { id: "progression" },
  { id: "warning", accent: true },
  { id: "deload" },
] as const;

const enter = keyframes`from { opacity: 0; transform: translateY(14px) scale(0.98); } to { opacity: 1; transform: none; }`;

const NO_MOTION = {
  "@media (prefers-reduced-motion: reduce)": { animation: "none" },
};

/** A small deck of app "moments" that rotates - decoration only, hidden from screen readers. */
export function RotatingTiles({ animate }: { animate: boolean }) {
  const { t } = useTranslation("brand");
  const index = useCycle(TILES.length, 3200, !animate);
  const tile = TILES[index];

  return (
    <Box aria-hidden sx={{ position: "relative", height: 112 }}>
      {/* the deck behind */}
      <Box
        sx={{
          position: "absolute",
          inset: "10px 18px -6px",
          borderRadius: 2,
          bgcolor: "#1A4D45",
          transform: "rotate(-3deg)",
        }}
      />
      <Box
        sx={{
          position: "absolute",
          inset: "6px 8px -2px",
          borderRadius: 2,
          bgcolor: "#21564D",
          transform: "rotate(2deg)",
        }}
      />

      <Box
        key={index}
        sx={{
          position: "absolute",
          inset: 0,
          borderRadius: 2,
          bgcolor: "#F3F4F1",
          color: "#14211E",
          px: 2.5,
          py: 2,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 0.5,
          boxShadow: "0 12px 32px rgba(0, 0, 0, 0.18)",
          animation: `${enter} 500ms cubic-bezier(0.2, 0.8, 0.2, 1)`,
          ...NO_MOTION,
        }}
      >
        <Typography
          sx={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "accent" in tile ? "#B85C1E" : "#5B6965",
          }}
        >
          {t(`tiles.${tile.id}.overline`)}
        </Typography>
        <Typography sx={{ fontFamily: FONT_DISPLAY, fontSize: 22, fontWeight: 600 }}>
          {t(`tiles.${tile.id}.title`)}
        </Typography>
        <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
          <Typography sx={{ fontSize: 13, color: "#5B6965" }}>
            {t(`tiles.${tile.id}.caption`)}
          </Typography>
          <Stack direction="row" spacing={0.5}>
            {TILES.map((item, i) => (
              <Box
                key={item.id}
                sx={{
                  width: 6,
                  height: 6,
                  borderRadius: 2,
                  bgcolor: i === index ? "#1D5C52" : "#C9D1CD",
                }}
              />
            ))}
          </Stack>
        </Stack>
      </Box>
    </Box>
  );
}
