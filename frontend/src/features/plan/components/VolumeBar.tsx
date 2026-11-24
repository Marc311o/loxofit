import { Box, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { FONT_MONO, zoneColors } from "@/styles/theme";

/** Colors for the dark analysis panel and for light cards. */
const PALETTES = {
  dark: { track: "#2A5A52", range: "rgba(169, 207, 196, 0.22)", tick: "#A9CFC4", text: "#A9CFC4" },
  light: { track: "#E4EAE7", range: "rgba(29, 92, 82, 0.14)", tick: "#7F9A93", text: "#5B6965" },
} as const;

type Tone = keyof typeof PALETTES;

type VolumeBarProps = {
  volume: number;
  mev: number;
  mav: number;
  mrv: number;
  scale: number;
  color: string;
  tone?: Tone;
};

/**
 * Sets against the three landmarks: the productive range MEV-MAV is shaded,
 * MEV and MAV are thin ticks, MRV - the limit not to cross - a strong orange one.
 */
export function VolumeBar({ volume, mev, mav, mrv, scale, color, tone = "dark" }: VolumeBarProps) {
  const palette = PALETTES[tone];
  const pct = (value: number) => `${(Math.min(value, scale) / scale) * 100}%`;
  return (
    <Box sx={{ position: "relative", height: 8, borderRadius: 0.5, bgcolor: palette.track }}>
      <Box
        sx={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: pct(mev),
          width: `${((Math.min(mav, scale) - Math.min(mev, scale)) / scale) * 100}%`,
          bgcolor: palette.range,
        }}
      />
      <Box
        sx={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: 0,
          width: pct(volume),
          borderRadius: 0.5,
          bgcolor: color,
        }}
      />
      <Tick left={pct(mev)} color={palette.tick} width={1} />
      <Tick left={pct(mav)} color={palette.tick} width={1} />
      <Tick left={pct(mrv)} color={zoneColors.aboveMrv} width={2} tall />
    </Box>
  );
}

function Tick({
  left,
  color,
  width,
  tall = false,
}: {
  left: string;
  color: string;
  width: number;
  tall?: boolean;
}) {
  return (
    <Box
      aria-hidden
      sx={{
        position: "absolute",
        left,
        top: tall ? -3 : -1,
        bottom: tall ? -3 : -1,
        width: `${width}px`, // a bare 1 would mean 100% in sx
        bgcolor: color,
      }}
    />
  );
}

/** What the ticks and the shaded part of a VolumeBar mean. */
export function LandmarkLegend({ tone = "dark" }: { tone?: Tone }) {
  const { t } = useTranslation("plans");
  const palette = PALETTES[tone];
  const ticks = [
    { label: "MEV", color: palette.tick, width: 1 },
    { label: "MAV", color: palette.tick, width: 1 },
    { label: "MRV", color: zoneColors.aboveMrv, width: 2 },
  ];
  return (
    <Stack
      direction="row"
      useFlexGap
      sx={{
        alignItems: "center",
        flexWrap: "wrap",
        columnGap: 1.5,
        rowGap: 0.5,
        color: palette.text,
      }}
    >
      {ticks.map((tick) => (
        <Stack key={tick.label} direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
          <Box sx={{ width: `${tick.width}px`, height: 12, bgcolor: tick.color }} />
          <Typography sx={{ fontFamily: FONT_MONO, fontSize: 10 }}>{tick.label}</Typography>
        </Stack>
      ))}
      <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
        <Box
          sx={{
            width: 14,
            height: 8,
            bgcolor: palette.range,
            border: `1px solid ${palette.track}`,
          }}
        />
        <Typography sx={{ fontSize: 10 }}>{t("panel.range")}</Typography>
      </Stack>
    </Stack>
  );
}
