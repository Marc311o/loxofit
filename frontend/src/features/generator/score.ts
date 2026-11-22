import type { ConvergencePoint } from "./components/ConvergenceChart";

/** A raw score as % of the best possible one - the same scale as the plan analysis. */
export function scorePct(score: number, maxScore: number): number {
  if (maxScore <= 0) return 0;
  return Math.min(100, Math.max(0, (score / maxScore) * 100));
}

/** The run's history on the % scale of the chart. */
export function historyPoints(history: [number, number][], maxScore: number): ConvergencePoint[] {
  return history.map(([evaluations, score]) => [evaluations, scorePct(score, maxScore)]);
}