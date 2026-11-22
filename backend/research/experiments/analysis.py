"""
Analysis of experiment results: summaries, statistical tests, figures for the thesis.

Used from analysis.ipynb - the notebook only calls these functions, so the analysis
can be reviewed in diffs and reused. Needs requirements-research.txt (pandas, scipy,
matplotlib).

Statistics
- within a scenario, every pair of algorithms: two-sided Mann-Whitney U test on the
  30 independent runs, p-values corrected with Holm's method, effect size as the
  Vargha-Delaney A12 (probability that a run of A beats a run of B; 0.5 - no difference,
  >= 0.71 / <= 0.29 - large);
- across scenarios: mean ranks of the algorithms and the Friedman test (Demsar 2006).
"""

import json
from collections.abc import Sequence
from itertools import combinations
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from scipy import stats

RESULTS_DIR = Path(__file__).parent / "results"
FIGURES_DIR = Path(__file__).parent / "figures"

# \the\textwidth of the thesis in points - replace with the value from the thesis.
TEXTWIDTH_PT = 426.8

FAMILY_ORDER = ["random", "greedy", "hill", "ga", "memetic"]
LABELS = {
    "random": "losowe",
    "greedy": "zachłanny",
    "hill": "hill climbing",
    "ga": "genetyczny",
    "memetic": "memetyczny",
}
COLORS = {
    "random": "#9e9e9e",
    "greedy": "#7f6a4f",
    "hill": "#2f6db5",
    "ga": "#d1662b",
    "memetic": "#3a8f5b",
}


# -- loading ---------------------------------------------------------------------------


def load(suite: str, results_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """runs, convergence and meta of one suite (compare / tune)."""
    folder = (results_dir or RESULTS_DIR) / suite
    runs = pd.read_csv(folder / "runs.csv")
    convergence = pd.read_csv(folder / "convergence.csv")
    meta_file = folder / "meta.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
    return runs, convergence, meta


# -- summaries -------------------------------------------------------------------------


def summary(runs: pd.DataFrame) -> pd.DataFrame:
    """Per scenario and algorithm: % of max (mean, sd, median, IQR, best), overtime,
    evaluations used and time per run."""
    pct = runs.groupby(["scenario", "family", "variant"])["pct_of_max"]
    table = pd.DataFrame(
        {
            "runs": pct.size(),
            "mean": pct.mean(),
            "sd": pct.std(),
            "median": pct.median(),
            "q1": pct.quantile(0.25),
            "q3": pct.quantile(0.75),
            "best": pct.max(),
        }
    )
    grouped = runs.groupby(["scenario", "family", "variant"])
    table["overtime_min"] = grouped["overtime_min"].mean()
    table["evaluations"] = grouped["evaluations"].mean()
    table["seconds"] = grouped["seconds"].mean()
    return table.reset_index()


def mean_ranks(runs: pd.DataFrame, by: str = "family") -> pd.DataFrame:
    """Rank of every algorithm in every scenario by mean score (1 - best), then the
    mean rank over scenarios. Ranks make scenarios of different scale comparable."""
    means = runs.groupby(["scenario", by])["pct_of_max"].mean().unstack(by)
    ranks = means.rank(axis=1, ascending=False)
    return pd.DataFrame({"mean_rank": ranks.mean(), "mean_pct": means.mean()}).sort_values(
        "mean_rank"
    )


def friedman(runs: pd.DataFrame, by: str = "family") -> tuple[float, float]:
    """Friedman test over scenarios (blocks) on the mean score of every algorithm."""
    means = runs.groupby(["scenario", by])["pct_of_max"].mean().unstack(by)
    statistic, p = stats.friedmanchisquare(*[means[c] for c in means.columns])
    return float(statistic), float(p)


# -- pairwise tests ----------------------------------------------------------------------


def a12(x: Sequence[float], y: Sequence[float]) -> float:
    """Vargha-Delaney A12: probability that a value from x is larger than one from y."""
    u = stats.mannwhitneyu(x, y, alternative="two-sided").statistic
    return float(u) / (len(x) * len(y))


def holm(p_values: Sequence[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (same order as given)."""
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for k, i in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - k) * p_values[i]))
        adjusted[i] = running
    return adjusted


def _mann_whitney_p(x: Sequence[float], y: Sequence[float]) -> float:
    return float(stats.mannwhitneyu(x, y, alternative="two-sided").pvalue)


def pairwise(runs: pd.DataFrame, by: str = "family") -> pd.DataFrame:
    """Every pair of algorithms within every scenario: Mann-Whitney U (Holm within the
    scenario) and A12. `a12` > 0.5 - the first algorithm tends to score higher."""
    rows = []
    for scenario, df in runs.groupby("scenario"):
        groups = {name: g["pct_of_max"].to_numpy() for name, g in df.groupby(by)}
        names = [n for n in FAMILY_ORDER if n in groups] + sorted(
            n for n in groups if n not in FAMILY_ORDER
        )
        pairs = list(combinations(names, 2))
        p = [_mann_whitney_p(groups[a], groups[b]) for a, b in pairs]
        for (a, b), p_raw, p_adj in zip(pairs, p, holm(p), strict=True):
            rows.append(
                {
                    "scenario": scenario,
                    "a": a,
                    "b": b,
                    "mean_a": groups[a].mean(),
                    "mean_b": groups[b].mean(),
                    "a12": a12(groups[a], groups[b]),
                    "p": p_raw,
                    "p_holm": p_adj,
                    "significant": p_adj < 0.05,
                }
            )
    return pd.DataFrame(rows)


# -- tuning ------------------------------------------------------------------------------


def tuning_table(runs: pd.DataFrame) -> pd.DataFrame:
    """Variants of every family ranked within the family: mean rank over the tuning
    scenarios (1 - the best variant in every scenario) and mean % of max."""
    tables = []
    for family, df in runs.groupby("family"):
        table = mean_ranks(df, by="variant").reset_index()
        table.insert(0, "family", family)
        tables.append(table)
    return pd.concat(tables, ignore_index=True)


def best_variants(runs: pd.DataFrame) -> pd.DataFrame:
    """The variant with the lowest mean rank in every family; ties - the higher mean."""
    table = tuning_table(runs).sort_values(
        ["family", "mean_rank", "mean_pct"], ascending=[True, True, False]
    )
    return table.groupby("family").head(1).reset_index(drop=True)


# -- figures -----------------------------------------------------------------------------


# Closest to the thesis font first; DejaVu Serif ships with matplotlib.
SERIF_FONTS = ["Latin Modern Roman", "CMU Serif", "DejaVu Serif"]


def _first_installed(names: Sequence[str]) -> str:
    installed = {f.name for f in font_manager.fontManager.ttflist}
    return next((name for name in names if name in installed), "DejaVu Serif")


def thesis_style(font_size: float = 9) -> None:
    """Matplotlib settings that fit a LaTeX thesis: serif font, small sizes, thin lines."""
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [_first_installed(SERIF_FONTS)],
            "mathtext.fontset": "cm",
            "font.size": font_size,
            "axes.labelsize": font_size,
            "axes.titlesize": font_size,
            "legend.fontsize": font_size - 1,
            "xtick.labelsize": font_size - 1,
            "ytick.labelsize": font_size - 1,
            "axes.linewidth": 0.6,
            "lines.linewidth": 1.2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.linewidth": 0.4,
            "grid.alpha": 0.5,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
        }
    )


def figsize(width: float = 1.0, ratio: float = 0.62) -> tuple[float, float]:
    """Figure size in inches: `width` - fraction of the text width, `ratio` - height / width."""
    inches = TEXTWIDTH_PT / 72.27 * width
    return inches, inches * ratio


def polish_number(x: float) -> str:
    """Decimal comma, a space between thousands (from 10 000 up), a real minus sign."""
    if float(x).is_integer():
        text = f"{abs(x):,.0f}".replace(",", " ") if abs(x) >= 10_000 else f"{abs(x):.0f}"
    else:
        text = f"{abs(x):g}".replace(".", ",")
    return ("−" if x < 0 else "") + text


_COMMA = FuncFormatter(lambda x, _: polish_number(x))


def _polish_numbers(ax) -> None:
    """Decimal comma on both axes, as Polish typography wants."""
    ax.xaxis.set_major_formatter(_COMMA)
    ax.yaxis.set_major_formatter(_COMMA)


SEARCH = ["hill", "ga", "memetic"]  # the three search methods, without the baselines


def boxplots(
    runs: pd.DataFrame,
    scenarios: Sequence[str] | None = None,
    families: Sequence[str] | None = None,
    cols: int = 2,
) -> Figure:
    """% of max of every algorithm (or only `families`), one panel per scenario."""
    if families is not None:
        runs = runs[runs["family"].isin(families)]
    names = list(scenarios or sorted(runs["scenario"].unique()))
    rows = -(-len(names) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=figsize(1.0, 0.36 * rows), squeeze=False)
    for ax, scenario in zip(axes.flat, names, strict=False):
        df = runs[runs["scenario"] == scenario]
        families = [f for f in FAMILY_ORDER if f in set(df["family"])]
        data = [df[df["family"] == f]["pct_of_max"] for f in families]
        box = ax.boxplot(data, vert=False, widths=0.6, patch_artist=True, showfliers=True,
                         flierprops={"markersize": 2}, medianprops={"color": "black"})  # fmt: skip
        for patch, family in zip(box["boxes"], families, strict=True):
            patch.set_facecolor(COLORS[family])
            patch.set_alpha(0.75)
        ax.set_yticks(range(1, len(families) + 1), [LABELS[f] for f in families])
        ax.invert_yaxis()
        ax.set_title(scenario)
        ax.set_xlabel("% maksimum")
        ax.grid(axis="y", visible=False)
        ax.xaxis.set_major_formatter(_COMMA)
    for ax in list(axes.flat)[len(names) :]:
        ax.set_visible(False)
    fig.tight_layout()
    return fig


def convergence(
    runs: pd.DataFrame,
    curves: pd.DataFrame,
    scenario: str,
    families: Sequence[str] | None = None,
) -> Figure:
    """Median best score so far (% of max) against evaluations, with the IQR band."""
    max_score = runs.loc[runs["scenario"] == scenario, "max_score"].iloc[0]
    df = curves[curves["scenario"] == scenario].assign(pct=lambda d: 100 * d["best"] / max_score)
    if families is not None:
        df = df[df["family"].isin(families)]
    fig, ax = plt.subplots(figsize=figsize(1.0, 0.5))
    for family in [f for f in FAMILY_ORDER if f in set(df["family"])]:
        g = df[df["family"] == family].groupby("evaluations")["pct"]
        median, q1, q3 = g.median(), g.quantile(0.25), g.quantile(0.75)
        ax.plot(median.index, median, color=COLORS[family], label=LABELS[family])
        ax.fill_between(median.index, q1, q3, color=COLORS[family], alpha=0.18, linewidth=0)
    ax.set_xlabel("liczba ocen funkcji celu")
    ax.set_ylabel("% maksimum")
    ax.set_title(scenario)
    ax.legend(loc="lower right", frameon=False)
    _polish_numbers(ax)
    fig.tight_layout()
    return fig


def ga_heatmap(tuning: pd.DataFrame) -> Figure:
    """Mean rank of the genetic algorithm variants: population x mutation, per crossover."""
    ga = tuning[tuning["family"] == "ga"].copy()
    parts = ga["variant"].str.extract(r"pop=(\d+) mut=([\d.]+) cx=(\w+)")
    ga["population"], ga["mutation"], ga["crossover"] = parts[0].astype(int), parts[1], parts[2]
    crossovers = sorted(ga["crossover"].unique())
    fig, axes = plt.subplots(
        1, len(crossovers), figsize=figsize(1.0, 0.36), squeeze=False, layout="constrained"
    )
    vmin, vmax = ga["mean_rank"].min(), ga["mean_rank"].max()
    for ax, crossover in zip(axes.flat, crossovers, strict=True):
        grid = ga[ga["crossover"] == crossover].pivot(index="population", columns="mutation",
                                                      values="mean_rank")  # fmt: skip
        image = ax.imshow(grid, cmap="viridis_r", vmin=vmin, vmax=vmax, aspect="auto")
        for (i, j), value in pd.DataFrame(grid.to_numpy()).stack().items():
            ax.text(j, i, f"{value:.1f}".replace(".", ","), ha="center", va="center",
                    color="white" if value > (vmin + vmax) / 2 else "black")  # fmt: skip
        ax.set_xticks(range(len(grid.columns)), [c.replace(".", ",") for c in grid.columns])
        ax.set_yticks(range(len(grid.index)), grid.index)
        ax.set_xlabel("prawdopodobieństwo mutacji")
        if ax is axes.flat[0]:
            ax.set_ylabel("populacja")
        ax.set_title(f"krzyżowanie: {'sesje' if crossover == 'session' else 'geny'}")
        ax.grid(False)
    fig.colorbar(image, ax=axes.ravel().tolist(), label="średnia ranga", shrink=0.9)
    return fig


def save(fig: Figure, name: str, folder: Path | None = None) -> Path:
    folder = folder or FIGURES_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.pdf"
    fig.savefig(path)
    return path


# -- LaTeX tables --------------------------------------------------------------------------


def latex_table(df: pd.DataFrame, decimals: int = 1, caption: str = "", label: str = "") -> str:
    """A booktabs table with decimal commas - paste into the thesis (\\usepackage{booktabs})."""

    def cell(value) -> str:
        if isinstance(value, float):
            return f"{value:.{decimals}f}".replace(".", ",").replace("-", "$-$")
        return str(value).replace("_", r"\_").replace("%", r"\%")

    head = " & ".join(cell(c) for c in df.columns) + r" \\"
    body = [" & ".join(cell(v) for v in row) + r" \\" for row in df.itertuples(index=False)]
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{caption}}}" if caption else "",
        rf"\label{{{label}}}" if label else "",
        rf"\begin{{tabular}}{{l{'r' * (len(df.columns) - 1)}}}",
        r"\toprule",
        head,
        r"\midrule",
        *body,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(line for line in lines if line)
