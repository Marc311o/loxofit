import type { ReactNode } from "react";

export const MARK_BG = "#1D5C52";
export const MARK_FG = "#F3F4F1";
export const MARK_ACCENT = "#E8893A";

const FG = MARK_FG;
const ACC = MARK_ACCENT;

export const LOGO_VARIANTS = [
  "A",
  "B",
  "C",
  "D",
  "E",
  "F",
  "G",
  "H",
  "I",
  "J",
  "K",
  "L",
] as const;
export type LogoVariant = (typeof LOGO_VARIANTS)[number];

export const LOGO_VARIANT: LogoVariant = "B";
interface MarkDefinition {
  name: string;
  glyph: ReactNode;
}

const RING_SEGMENTS = [
  { stroke: FG, opacity: 0.35 },
  { stroke: FG, opacity: 0.55 },
  { stroke: FG, opacity: 0.78 },
  { stroke: FG, opacity: 1 },
  { stroke: ACC, opacity: 1 },
];

const GAUGE_ARCS = [
  {
    d: "M10 31 A14 14 0 0 1 13.67 21.56",
    stroke: FG,
    opacity: 0.35,
    cap: "round",
  },
  {
    d: "M14.56 20.67 A14 14 0 0 1 23.37 17.01",
    stroke: FG,
    opacity: 0.65,
    cap: "butt",
  },
  {
    d: "M24.63 17.01 A14 14 0 0 1 33.44 20.67",
    stroke: FG,
    opacity: 1,
    cap: "butt",
  },
  {
    d: "M34.33 21.56 A14 14 0 0 1 38 31",
    stroke: ACC,
    opacity: 1,
    cap: "round",
  },
] as const;

const HEATMAP_CELLS: [number, number, number | null][] = [
  [9.5, 9.5, 0.76],
  [20, 9.5, 1],
  [30.5, 9.5, null],
  [9.5, 20, 0.52],
  [20, 20, 0.76],
  [30.5, 20, 1],
  [9.5, 30.5, 0.28],
  [20, 30.5, 0.52],
  [30.5, 30.5, 0.76],
];

export const LOGO_MARKS: Record<LogoVariant, MarkDefinition> = {
  A: {
    name: "Słupki pod sufitem MRV",
    glyph: (
      <>
        <rect
          x="10.5"
          y="27"
          width="7"
          height="11"
          rx="3.5"
          fill={FG}
          fillOpacity={0.5}
        />
        <rect
          x="20.5"
          y="20"
          width="7"
          height="18"
          rx="3.5"
          fill={FG}
          fillOpacity={0.78}
        />
        <rect x="30.5" y="14" width="7" height="24" rx="3.5" fill={FG} />
        <rect x="9" y="9" width="30" height="2.6" rx="1.3" fill={ACC} />
      </>
    ),
  },
  B: {
    name: "Krzywa dawka-odpowiedź",
    glyph: (
      <>
        <path
          d="M10 37 C 16 37, 18 15, 36 14"
          fill="none"
          stroke={FG}
          strokeWidth={4.6}
          strokeLinecap="round"
        />
        <circle cx="36.5" cy="14" r="4" fill={ACC} />
      </>
    ),
  },
  C: {
    name: "Pierścień mezocyklu",
    glyph: (
      <g transform="rotate(-90 24 24)">
        {RING_SEGMENTS.map((segment, index) => (
          <circle
            key={index}
            cx="24"
            cy="24"
            r="13"
            fill="none"
            stroke={segment.stroke}
            strokeOpacity={segment.opacity}
            strokeWidth={5.5}
            strokeDasharray="13.14 68.55"
            strokeDashoffset={-index * 16.34}
          />
        ))}
      </g>
    ),
  },
  D: {
    name: "Talerz",
    glyph: (
      <>
        <circle
          cx="24"
          cy="24"
          r="12"
          fill="none"
          stroke={FG}
          strokeWidth={5}
        />
        <circle cx="24" cy="24" r="4.5" fill={ACC} />
      </>
    ),
  },
  E: {
    name: "Monogram L",
    glyph: (
      <>
        <rect x="13" y="10" width="7.5" height="28" rx="3.75" fill={FG} />
        <rect x="13" y="30.5" width="23" height="7.5" rx="3.75" fill={FG} />
        <circle cx="33" cy="15" r="4.2" fill={ACC} />
      </>
    ),
  },
  F: {
    name: "Słupki pod krzywą",
    glyph: (
      <>
        <rect
          x="9.5"
          y="30"
          width="6"
          height="8"
          rx="3"
          fill={FG}
          fillOpacity={0.5}
        />
        <rect
          x="17.5"
          y="21"
          width="6"
          height="17"
          rx="3"
          fill={FG}
          fillOpacity={0.7}
        />
        <rect
          x="25.5"
          y="16.5"
          width="6"
          height="21.5"
          rx="3"
          fill={FG}
          fillOpacity={0.88}
        />
        <rect x="33.5" y="15" width="6" height="23" rx="3" fill={FG} />
        <path
          d="M8 31 C 14 20, 22 14.5, 41 12.5"
          fill="none"
          stroke={ACC}
          strokeWidth={2.2}
          strokeLinecap="round"
        />
      </>
    ),
  },
  G: {
    name: "Schody z deloadem",
    glyph: (
      <>
        <path
          d="M9.5 35.5 H16 V28.5 H22.5 V21.5 H29 V14.5 H31"
          fill="none"
          stroke={FG}
          strokeWidth={4.2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M31 14.5 L38.5 29.5"
          fill="none"
          stroke={ACC}
          strokeWidth={4.2}
          strokeLinecap="round"
        />
      </>
    ),
  },
  H: {
    name: "Wydolność i zmęczenie",
    glyph: (
      <>
        <path
          d="M9 35 C 19 34, 27 20, 39 13"
          fill="none"
          stroke={FG}
          strokeWidth={4.2}
          strokeLinecap="round"
        />
        <path
          d="M9 34 C 13 14, 21 13, 25 22 S 33 35, 39 35"
          fill="none"
          stroke={ACC}
          strokeWidth={4.2}
          strokeLinecap="round"
        />
      </>
    ),
  },
  I: {
    name: "Wskaźnik stref",
    glyph: (
      <>
        {GAUGE_ARCS.map((arc) => (
          <path
            key={arc.d}
            d={arc.d}
            fill="none"
            stroke={arc.stroke}
            strokeOpacity={arc.opacity}
            strokeWidth={5}
            strokeLinecap={arc.cap}
          />
        ))}
        <line
          x1="24"
          y1="31"
          x2="27.5"
          y2="22.17"
          stroke={FG}
          strokeWidth={3}
          strokeLinecap="round"
        />
        <circle cx="24" cy="31" r="3.4" fill={FG} />
      </>
    ),
  },
  J: {
    name: "Heatmapa",
    glyph: (
      <>
        {HEATMAP_CELLS.map(([x, y, opacity]) => (
          <rect
            key={`${x}-${y}`}
            x={x}
            y={y}
            width="8.5"
            height="8.5"
            rx="2.6"
            fill={opacity === null ? ACC : FG}
            fillOpacity={opacity ?? 1}
          />
        ))}
      </>
    ),
  },
  K: {
    name: "Superkompensacja",
    glyph: (
      <>
        <line
          x1="9"
          y1="24"
          x2="39"
          y2="24"
          stroke={FG}
          strokeOpacity={0.38}
          strokeWidth={2}
          strokeDasharray="2.5 3"
          strokeLinecap="round"
        />
        <path
          d="M9 24 C 13 24, 14 34, 19 34 C 25 34, 27 14, 34 14"
          fill="none"
          stroke={FG}
          strokeWidth={4.2}
          strokeLinecap="round"
        />
        <circle cx="36" cy="14" r="3.8" fill={ACC} />
      </>
    ),
  },
  L: {
    name: "Hantel",
    glyph: (
      <g transform="rotate(-38 24 24)">
        <rect x="13" y="22.4" width="22" height="3.2" rx="1.6" fill={ACC} />
        <rect x="8.5" y="15" width="5.5" height="18" rx="2.75" fill={FG} />
        <rect
          x="14.8"
          y="18"
          width="3.6"
          height="12"
          rx="1.8"
          fill={FG}
          fillOpacity={0.75}
        />
        <rect x="34" y="15" width="5.5" height="18" rx="2.75" fill={FG} />
        <rect
          x="29.6"
          y="18"
          width="3.6"
          height="12"
          rx="1.8"
          fill={FG}
          fillOpacity={0.75}
        />
      </g>
    ),
  },
};
