import { useEffect, useId, useRef, useState, type PointerEvent } from "react";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useFormatNumber } from "@/i18n/useLocalized";
import { FONT_MONO } from "@/styles/theme";

/** [evaluations, score in %] at every improvement of the best plan. */
export type ConvergencePoint = [number, number];

type ConvergenceChartProps = {
  points: ConvergencePoint[];
  /** Right end of the x axis - the evaluation budget. */
  budget: number;
  /** Where the line ends: the current evaluation while running, the budget when done. */
  until: number;
  height?: number;
};

const PAD = { top: 10, right: 12, bottom: 22, left: 36 };
const MIN_WIDTH = 240;

/**
 * Best score so far against the evaluations spent - a step line, since the best
 * plan only changes when the search finds a better one. One series, so no legend:
 * the card title names it.
 */
export function ConvergenceChart({ points, budget, until, height = 160 }: ConvergenceChartProps) {
  const { t } = useTranslation("generator");
  const formatNumber = useFormatNumber();
  const titleId = useId();
  const [hover, setHover] = useState<number | null>(null);
  // Drawn at the real width, so the labels keep their size in a narrow card.
  const boxRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(600);
  useEffect(() => {
    const box = boxRef.current;
    if (!box) return;
    const observer = new ResizeObserver(([entry]) =>
      setWidth(Math.max(MIN_WIDTH, Math.round(entry.contentRect.width))),
    );
    observer.observe(box);
    return () => observer.disconnect();
  }, []);

  const values = points.map(([, pct]) => pct);
  // Zoom on the part that matters: from a round value below the worst point to 100%.
  const low = values.length > 0 ? Math.max(0, Math.floor((Math.min(...values) - 5) / 10) * 10) : 0;
  const high = 100;
  const ticks = yTicks(low, high);

  const plotW = width - PAD.left - PAD.right;
  const plotH = height - PAD.top - PAD.bottom;
  const x = (evaluations: number) => PAD.left + (Math.min(evaluations, budget) / budget) * plotW;
  const y = (pct: number) => PAD.top + (1 - (clamp(pct) - low) / (high - low)) * plotH;

  let path = "";
  points.forEach(([evaluations, pct], i) => {
    path += i === 0 ? `M${x(evaluations)},${y(pct)}` : `H${x(evaluations)}V${y(pct)}`;
  });
  if (points.length > 0) path += `H${x(until)}`;

  const last = points.at(-1);
  const hovered = hover !== null ? valueAt(points, hover) : undefined;

  const handleMove = (event: PointerEvent<SVGRectElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const ratio = (event.clientX - box.left) / box.width;
    setHover(Math.round(Math.max(0, Math.min(1, ratio)) * budget));
  };

  return (
    <Box ref={boxRef} sx={{ position: "relative" }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        role="img"
        aria-labelledby={titleId}
        style={{ display: "block", overflow: "visible" }}
      >
        <title id={titleId}>
          {last
            ? t("chart.summary", { score: Math.round(last[1]), evaluations: formatNumber(until) })
            : t("chart.title")}
        </title>
        {ticks.map((tick) => (
          <g key={tick}>
            <line
              x1={PAD.left}
              x2={width - PAD.right}
              y1={y(tick)}
              y2={y(tick)}
              stroke="#DCE2DD"
              strokeWidth={1}
            />
            <text
              x={PAD.left - 6}
              y={y(tick)}
              textAnchor="end"
              dominantBaseline="central"
              fontSize={10}
              fontFamily={FONT_MONO}
              fill="#5B6965"
            >
              {tick}%
            </text>
          </g>
        ))}
        {[0, budget / 2, budget].map((tick, i) => (
          <text
            key={tick}
            x={x(tick)}
            y={height - 4}
            textAnchor={i === 0 ? "start" : i === 2 ? "end" : "middle"}
            fontSize={10}
            fontFamily={FONT_MONO}
            fill="#5B6965"
          >
            {formatNumber(tick)}
          </text>
        ))}
        <path
          d={path}
          fill="none"
          stroke="#1D5C52"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {last && <circle cx={x(until)} cy={y(last[1])} r={4} fill="#1D5C52" />}
        {hovered !== undefined && hover !== null && (
          <g pointerEvents="none">
            <line
              x1={x(hover)}
              x2={x(hover)}
              y1={PAD.top}
              y2={PAD.top + plotH}
              stroke="#5B6965"
              strokeDasharray="3 3"
            />
            <circle
              cx={x(hover)}
              cy={y(hovered)}
              r={4}
              fill="#1D5C52"
              stroke="#FFFFFF"
              strokeWidth={2}
            />
          </g>
        )}
        <rect
          x={PAD.left}
          y={PAD.top}
          width={plotW}
          height={plotH}
          fill="transparent"
          onPointerMove={handleMove}
          onPointerLeave={() => setHover(null)}
        />
      </svg>
      {hovered !== undefined && hover !== null && hover <= until && (
        <Typography
          aria-hidden
          sx={{
            position: "absolute",
            top: 0,
            left: `${(x(hover) / width) * 100}%`,
            transform: hover > budget / 2 ? "translateX(calc(-100% - 8px))" : "translateX(8px)",
            px: 1,
            py: 0.5,
            borderRadius: 1,
            bgcolor: "primary.dark",
            color: "#F3F4F1",
            fontFamily: FONT_MONO,
            fontSize: 11,
            whiteSpace: "nowrap",
            pointerEvents: "none",
          }}
        >
          {t("chart.tooltip", {
            score: formatNumber(hovered, 1),
            evaluations: formatNumber(hover),
          })}
        </Typography>
      )}
    </Box>
  );
}

const clamp = (pct: number) => Math.max(0, Math.min(100, pct));

/** Best score at a given evaluation - the last improvement at or before it. */
function valueAt(points: ConvergencePoint[], evaluations: number): number | undefined {
  let value: number | undefined;
  for (const [e, pct] of points) {
    if (e > evaluations) break;
    value = pct;
  }
  return value;
}

/** 3-5 round ticks between low and high. */
function yTicks(low: number, high: number): number[] {
  const step = high - low >= 50 ? 25 : high - low >= 20 ? 10 : 5;
  const ticks: number[] = [];
  for (let v = Math.ceil(low / step) * step; v <= high; v += step) ticks.push(v);
  return ticks;
}
