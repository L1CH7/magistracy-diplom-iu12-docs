#!/usr/bin/env python3
"""
IEEE paper figure generator.
Produces 7 single-panel figures from benchmark audit data.

Changes vs v1:
  - SimdDelta removed everywhere (implementation identical to SimdBucket)
  - Added fig_cluster_qps: QPS vs PathEdges bins at ALT w=1.0
  - All figures carry a directional annotation (higher / lower is better)

Output: docs/latex/assets/fig_*.png
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib import rcParams

OUT_DIR = '/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/docs/latex/assets'
os.makedirs(OUT_DIR, exist_ok=True)

# ── IEEE style ───────────────────────────────────────────────────────────────
rcParams.update({
    'font.family':      'serif',
    'font.serif':       ['Times New Roman', 'DejaVu Serif'],
    'font.size':        7,
    'axes.titlesize':   7,
    'axes.labelsize':   7,
    'xtick.labelsize':  6,
    'ytick.labelsize':  6,
    'legend.fontsize':  6,
    'figure.dpi':       300,
    'axes.linewidth':   0.6,
    'lines.linewidth':  1.1,
    'lines.markersize': 4,
    'axes.spines.top':  False,
    'axes.spines.right':False,
    'grid.linewidth':   0.4,
    'grid.alpha':       0.5,
})

# Colour palette — colour-blind-safe, print-distinguishable
C = {
    '8ary':      '#2166ac',   # blue   — Simd8Ary (canonical d-ary representative)
    '4ary':      '#4393c3',
    '16ary':     '#92c5de',
    '2ary':      '#d1e5f0',
    'radix':     '#d6604d',   # red    — SimdRadix
    'bucket':    '#4d9221',   # green  — SimdBucket (= SimdDelta, merged)
    'quickheap': '#878787',   # grey   — SimdQuick
    'dijkstra':  '#762a83',   # purple
    'astar':     '#de77ae',   # pink
    'alt':       '#2166ac',   # blue
}

# Queue display labels — delta removed
QUEUE_LABELS = {
    '2-ary':     'Simd2Ary',
    '4-ary':     'Simd4Ary',
    '8-ary':     'Simd8Ary',
    '16-ary':    'Simd16Ary',
    'bucket':    'SimdBucket',
    'quickheap': 'SimdQuick',
    'radix':     'SimdRadix',
}

QUEUES_ORDER = ['2-ary', '4-ary', '8-ary', '16-ary', 'bucket', 'quickheap', 'radix']

SINGLE_COL = (3.5, 2.4)   # IEEE single-column width in inches


# ── Data (exhaustive_statistical_audit.txt, Section 1) ──────────────────────
# Delta omitted — its numbers are within rounding of bucket
ALT_W10 = {
    '2-ary':     dict(mean_ms=4.014, rho=1.101, ghost=0.347, roughness=8.415,  kurt=13.282),
    '4-ary':     dict(mean_ms=3.859, rho=1.102, ghost=0.355, roughness=8.380,  kurt=12.647),
    '8-ary':     dict(mean_ms=3.913, rho=1.103, ghost=0.360, roughness=8.498,  kurt=12.384),
    '16-ary':    dict(mean_ms=3.876, rho=1.104, ghost=0.364, roughness=8.193,  kurt=15.086),
    'bucket':    dict(mean_ms=3.990, rho=1.108, ghost=0.331, roughness=12.924, kurt=41.227),
    'quickheap': dict(mean_ms=3.436, rho=1.117, ghost=0.391, roughness=9.096,  kurt=15.983),
    'radix':     dict(mean_ms=2.938, rho=1.146, ghost=0.456, roughness=9.042,  kurt=20.137),
}

# ALT weight sweep metrics (Section 1)
W_VALS = [1.0, 1.05, 1.10, 1.15, 1.20]
ALT_RADIX_VS_W  = dict(mean_ms=[2.938, 9.779,  13.616, 17.941, 22.660],
                        ghost  =[0.456, 0.152,  0.125,  0.104,  0.089],
                        rho    =[1.146, 1.042,  1.034,  1.028,  1.022])
ALT_8ARY_VS_W   = dict(mean_ms=[3.913, 3.329,  3.716,  3.995,  4.371],
                        ghost  =[0.360, 0.437,  0.403,  0.376,  0.346],
                        rho    =[1.103, 1.173,  1.167,  1.161,  1.151])
ALT_BUCKET_VS_W = dict(mean_ms=[3.990, 5.712,  6.053,  6.625,  7.247],
                        ghost  =[0.331, 0.266,  0.262,  0.244,  0.235],
                        rho    =[1.108, 1.101,  1.106,  1.103,  1.101])
ALT_QUICK_VS_W  = dict(mean_ms=[3.436, 3.507,  3.957,  4.186,  4.584],
                        ghost  =[0.391, 0.444,  0.405,  0.373,  0.344],
                        rho    =[1.117, 1.175,  1.169,  1.160,  1.151])

# QPS elasticity (Section 3) — delta removed
W_ELAST = [1.05, 1.10, 1.15, 1.20]
ALT_ELAST = {
    '16-ary':    [ 7.749,  4.356,  3.309,  3.005],
    '2-ary':     [ 7.309,  3.989,  3.231,  2.786],
    '4-ary':     [ 7.613,  4.203,  3.498,  2.809],
    '8-ary':     [ 7.267,  4.078,  3.365,  2.661],
    'bucket':    [-0.229,  0.339,  0.601,  0.350],
    'quickheap': [ 2.794,  1.182,  1.553,  1.227],
    'radix':     [-3.578, -2.011, -1.473, -1.395],
}

# Complexity exponents α (Section 2) — delta removed
ALPHA = {
    'Dijkstra': {'2-ary':2.1412,'4-ary':2.1215,'8-ary':2.1276,'16-ary':2.1161,
                 'bucket':2.0741,'quickheap':2.0992,'radix':2.0728},
    'A*':       {'2-ary':2.4908,'4-ary':2.4880,'8-ary':2.4787,'16-ary':2.4805,
                 'bucket':2.4320,'quickheap':2.4379,'radix':2.4519},
    'ALT':      {'2-ary':1.8019,'4-ary':1.7953,'8-ary':1.8080,'16-ary':1.8042,
                 'bucket':1.7879,'quickheap':1.7579,'radix':1.6881},
}

# ALT w=1.0 QPS by PathEdges bin (exhaustive_trend_report.txt, Section 3)
# NaN = no data in that bin for this queue
_nan = float('nan')
BINS_LABELS  = ['0-30','30-60','60-100','100-150','150-200','200-300','300-450','450-600']
BINS_MIDPTS  = [15, 45, 80, 125, 175, 250, 375, 525]
ALT_W10_QPS_BY_BIN = {
    '8-ary':     [22583, 27572, 3240, 1764,  886, 531, 328, 228],
    'radix':     [26563, 32522, 4284, 2333, 1218, 738, 502, 270],
    'bucket':    [_nan,  25396, 4003, 2180, 1123, 678, 441, 273],
    'quickheap': [39334, 25530, 3805, 2022,  995, 627, 392, 251],
    '16-ary':    [18888, 23238, 3307, 1842,  885, 523, 333, 209],
}


# ── Helper ───────────────────────────────────────────────────────────────────
def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, bbox_inches='tight', pad_inches=0.03)
    plt.close(fig)
    print(f'  saved → {path}')

def _bar_color(q):
    if q == 'bucket':       return C['bucket']
    if q == 'radix':        return C['radix']
    if q == 'quickheap':    return C['quickheap']
    if q == '16-ary':       return C['16ary']
    if q == '4-ary':        return C['4ary']
    if q == '2-ary':        return C['2ary']
    return C['8ary']  # 8-ary

def _dir_note(ax, text, loc='upper right'):
    """Add a directional annotation (higher/lower is better)."""
    props = dict(boxstyle='round,pad=0.2', facecolor='#f0f0f0',
                 edgecolor='#aaaaaa', linewidth=0.5, alpha=0.8)
    ax.annotate(text, xy=(0, 1) if 'upper' in loc else (1, 0),
                xycoords='axes fraction',
                xytext=(0.02, 0.96) if 'upper left' in loc else
                       (0.98, 0.96) if 'upper right' in loc else (0.98, 0.04),
                textcoords='axes fraction',
                ha='right' if 'right' in loc else 'left',
                va='top' if 'upper' in loc else 'bottom',
                fontsize=5, bbox=props)


# ────────────────────────────────────────────────────────────────────────────
# FIG 1: α complexity exponents — microarchitectural isomorphism
# ────────────────────────────────────────────────────────────────────────────
def fig_algo_complexity():
    fig, ax = plt.subplots(figsize=SINGLE_COL)
    x     = np.arange(len(QUEUES_ORDER))
    width = 0.26

    algo_cfg = [
        ('Dijkstra', C['dijkstra'], -width),
        ('A*',       C['astar'],    0),
        ('ALT',      C['alt'],      +width),
    ]
    for algo, color, offset in algo_cfg:
        vals = [ALPHA[algo][q] for q in QUEUES_ORDER]
        ax.bar(x + offset, vals, width=width, color=color,
               label=algo, edgecolor='white', linewidth=0.3)
        mn = np.mean(vals)
        ax.hlines(mn, x[0]+offset-width/2, x[-1]+offset+width/2,
                  colors=color, linestyles='--', linewidth=0.8, alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels([QUEUE_LABELS[q] for q in QUEUES_ORDER],
                       rotation=32, ha='right', fontsize=5.2)
    ax.set_ylabel(r'Complexity exponent $\alpha$')
    ax.set_ylim(1.5, 2.75)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.legend(loc='upper right', frameon=False)
    ax.grid(axis='y')
    ax.set_title(r'Search-space exponent $\alpha$ (lower $\alpha$ = smaller search frontier)')
    _dir_note(ax, '↓ lower α is better', 'upper left')
    fig.tight_layout()
    save(fig, 'fig_algo_complexity.png')


# ────────────────────────────────────────────────────────────────────────────
# FIG 2: QPS elasticity vs w — shows radix collapse and d-ary gain
# ────────────────────────────────────────────────────────────────────────────
def fig_param_elasticity():
    fig, ax = plt.subplots(figsize=SINGLE_COL)

    lines_cfg = [
        ('8-ary',     C['8ary'],      '-o',  'Simd8Ary (d-ary representative)'),
        ('radix',     C['radix'],     '-s',  'SimdRadix'),
        ('bucket',    C['bucket'],    '-^',  'SimdBucket'),
        ('quickheap', C['quickheap'], '-D',  'SimdQuick'),
    ]
    for key, color, fmt, label in lines_cfg:
        ax.plot(W_ELAST, ALT_ELAST[key], fmt, color=color, label=label,
                markerfacecolor='white', markeredgewidth=0.8)

    ax.axhline(0, color='black', linewidth=0.6, linestyle=':')
    ax.fill_between(W_ELAST, 0,  10, alpha=0.04, color='green')
    ax.fill_between(W_ELAST, -5, 0,  alpha=0.04, color='red')
    ax.text(1.195, 0.5,  'QPS gain', fontsize=5, color='#4d9221', ha='right', va='bottom')
    ax.text(1.195, -0.5, 'QPS loss', fontsize=5, color='#d6604d', ha='right', va='top')
    ax.set_xlabel(r'Heuristic weight $w$')
    ax.set_ylabel(r'QPS elasticity $\varepsilon_w = \Delta\%\,QPS\,/\,\Delta\%\,w$')
    ax.set_xticks(W_ELAST)
    ax.set_ylim(-5, 10)
    ax.legend(loc='upper right', frameon=False, fontsize=5.2)
    ax.grid(axis='y')
    ax.set_title(r'ALT throughput elasticity under weight sweep')
    fig.tight_layout()
    save(fig, 'fig_param_elasticity.png')


# ────────────────────────────────────────────────────────────────────────────
# FIG 3: Re-opening index ρ vs w
# ρ = PopCount / VisitedNodes; ρ = 1.0 means zero re-openings
# Radix ρ DROPS → corrupted search terminates early
# ────────────────────────────────────────────────────────────────────────────
def fig_reopen_index():
    fig, ax = plt.subplots(figsize=SINGLE_COL)

    ax.plot(W_VALS, ALT_RADIX_VS_W['rho'],  '-s', color=C['radix'],     label='SimdRadix',
            markerfacecolor='white', markeredgewidth=0.8)
    ax.plot(W_VALS, ALT_8ARY_VS_W['rho'],   '-o', color=C['8ary'],      label='Simd8Ary',
            markerfacecolor='white', markeredgewidth=0.8)
    ax.plot(W_VALS, ALT_BUCKET_VS_W['rho'], '-^', color=C['bucket'],    label='SimdBucket',
            markerfacecolor='white', markeredgewidth=0.8)
    ax.plot(W_VALS, ALT_QUICK_VS_W['rho'],  '-D', color=C['quickheap'], label='SimdQuick',
            markerfacecolor='white', markeredgewidth=0.8)

    ax.axhline(1.0, color='black', linewidth=0.5, linestyle=':', alpha=0.5)
    ax.text(1.195, 1.002, 'ρ=1: no re-openings', fontsize=5, ha='right', alpha=0.6)

    ax.set_xlabel(r'Heuristic weight $w$')
    ax.set_ylabel(r'$\rho = N_{\mathrm{pop}}\,/\,N_{\mathrm{visited}}$')
    ax.set_xticks(W_VALS)
    ax.legend(loc='center left', frameon=False, fontsize=5.5)
    ax.grid(axis='y')
    ax.set_title(r'Re-opening index $\rho$ under ALT weight sweep')
    ax.annotate('RadixHeap: search\nterminates early',
                xy=(1.05, ALT_RADIX_VS_W['rho'][1]),
                xytext=(1.10, 1.050),
                fontsize=5, color=C['radix'],
                arrowprops=dict(arrowstyle='->', color=C['radix'], lw=0.6))
    _dir_note(ax, 'ρ closer to 1.0 = fewer wasted pops', 'upper right')
    fig.tight_layout()
    save(fig, 'fig_reopen_index.png')


# ────────────────────────────────────────────────────────────────────────────
# FIG 4: Radix monotonicity collapse
# Left axis:  mean latency (ms)         — lower is better
# Right axis: ghost-node density        — higher is better (= productive search)
# ────────────────────────────────────────────────────────────────────────────
def fig_radix_collapse():
    fig, ax1 = plt.subplots(figsize=SINGLE_COL)
    ax2 = ax1.twinx()

    l1, = ax1.plot(W_VALS, ALT_RADIX_VS_W['mean_ms'], '-s', color=C['radix'],
                   label='SimdRadix latency (ms)', markerfacecolor='white', markeredgewidth=0.8)
    l2, = ax1.plot(W_VALS, ALT_8ARY_VS_W['mean_ms'],  '-o', color=C['8ary'],
                   label='Simd8Ary latency (ms)',  markerfacecolor='white', markeredgewidth=0.8)
    l3, = ax2.plot(W_VALS, ALT_RADIX_VS_W['ghost'],  '--s', color=C['radix'],  alpha=0.55,
                   label='SimdRadix ghost density', markerfacecolor='white', markeredgewidth=0.8)
    l4, = ax2.plot(W_VALS, ALT_8ARY_VS_W['ghost'],   '--o', color=C['8ary'],   alpha=0.55,
                   label='Simd8Ary ghost density',  markerfacecolor='white', markeredgewidth=0.8)

    ax1.set_xlabel(r'Heuristic weight $w$')
    ax1.set_ylabel('Mean latency (ms)  ↓ lower is better', color='black', fontsize=6.5)
    ax2.set_ylabel('Ghost-node density  ↑ higher = richer search', color='#888888', fontsize=5.5)
    ax2.tick_params(axis='y', colors='#888888', labelsize=5.5)
    ax1.set_xticks(W_VALS)
    ax1.grid(axis='y')
    all_h = [l1, l2, l3, l4]
    ax1.legend(all_h, [h.get_label() for h in all_h],
               loc='upper left', frameon=False, fontsize=5)
    ax1.set_title('SimdRadix monotonicity collapse under weight sweep')
    fig.tight_layout()
    save(fig, 'fig_radix_collapse.png')


# ────────────────────────────────────────────────────────────────────────────
# FIG 5: Tail latency roughness (p99/p50) at ALT w=1.0
# p99/p50 = 1.0 means perfectly deterministic; higher = heavier tail
# ────────────────────────────────────────────────────────────────────────────
def fig_tail_roughness():
    fig, ax = plt.subplots(figsize=SINGLE_COL)

    labels = [QUEUE_LABELS[q] for q in QUEUES_ORDER]
    vals   = [ALT_W10[q]['roughness'] for q in QUEUES_ORDER]
    colors = [_bar_color(q) for q in QUEUES_ORDER]

    ax.barh(labels, vals, color=colors, edgecolor='white', linewidth=0.4)
    ax.axvline(1.0, color='black', linewidth=0.5, linestyle=':', alpha=0.5)
    ax.text(1.05, -0.4, 'p99=p50\n(ideal)', fontsize=5, alpha=0.55, va='bottom')
    ax.set_xlabel(r'Tail roughness $p_{99}/p_{50}$  — lower is better')
    ax.set_title(r'Tail latency roughness at ALT $w=1.0$')
    ax.grid(axis='x')

    patches = [
        mpatches.Patch(color=C['8ary'],      label='d-ary heaps'),
        mpatches.Patch(color=C['radix'],      label='SimdRadix'),
        mpatches.Patch(color=C['quickheap'],  label='SimdQuick'),
        mpatches.Patch(color=C['bucket'],     label='SimdBucket'),
    ]
    ax.legend(handles=patches, frameon=False, fontsize=5, loc='lower right')
    _dir_note(ax, '← lower is better', 'upper right')
    fig.tight_layout()
    save(fig, 'fig_tail_roughness.png')


# ────────────────────────────────────────────────────────────────────────────
# FIG 6: Excess kurtosis at ALT w=1.0
# Excess kurtosis = 0 is Gaussian; > 0 means heavy upper tail (burst latency)
# ────────────────────────────────────────────────────────────────────────────
def fig_excess_kurtosis():
    fig, ax = plt.subplots(figsize=SINGLE_COL)

    labels = [QUEUE_LABELS[q] for q in QUEUES_ORDER]
    vals   = [ALT_W10[q]['kurt'] for q in QUEUES_ORDER]
    colors = [_bar_color(q) for q in QUEUES_ORDER]

    ax.barh(labels, vals, color=colors, edgecolor='white', linewidth=0.4)
    ax.axvline(0, color='black', linewidth=0.5, linestyle=':', alpha=0.5)
    ax.text(0.5, -0.4, 'Gaussian\n(κ=0)', fontsize=5, alpha=0.55, va='bottom')

    # annotate bucket outlier
    bkt_v = ALT_W10['bucket']['kurt']
    bkt_y = labels.index(QUEUE_LABELS['bucket'])
    ax.annotate(f'{bkt_v:.0f}×', xy=(bkt_v, bkt_y), xytext=(bkt_v - 8, bkt_y + 0.45),
                fontsize=5.5, color=C['bucket'], fontweight='bold')

    ax.set_xlabel(r'Excess kurtosis  — lower is better (0 = Gaussian)')
    ax.set_title(r'Excess kurtosis at ALT $w=1.0$')
    ax.grid(axis='x')
    patches = [
        mpatches.Patch(color=C['8ary'],      label='d-ary heaps'),
        mpatches.Patch(color=C['radix'],      label='SimdRadix'),
        mpatches.Patch(color=C['quickheap'],  label='SimdQuick'),
        mpatches.Patch(color=C['bucket'],     label='SimdBucket'),
    ]
    ax.legend(handles=patches, frameon=False, fontsize=5, loc='lower right')
    _dir_note(ax, '← lower is better', 'upper right')
    fig.tight_layout()
    save(fig, 'fig_excess_kurtosis.png')


# ────────────────────────────────────────────────────────────────────────────
# FIG 7: QPS vs PathEdges at ALT w=1.0 — replaces the K-Means cluster table
# X-axis: path length in edges (bin midpoints)
# Y-axis: QPS (log scale)   ↑ higher is better
# ────────────────────────────────────────────────────────────────────────────
def fig_cluster_qps():
    fig, ax = plt.subplots(figsize=(3.5, 2.7))

    lines_cfg = [
        ('radix',     C['radix'],     '-s',  'SimdRadix',  1.5),
        ('8-ary',     C['8ary'],      '-o',  'Simd8Ary',   1.0),
        ('bucket',    C['bucket'],    '-^',  'SimdBucket', 1.0),
        ('quickheap', C['quickheap'], '-D',  'SimdQuick',  0.8),
        ('16-ary',    C['16ary'],     '--v', 'Simd16Ary',  0.8),
    ]

    x = np.array(BINS_MIDPTS)

    for key, color, fmt, label, lw in lines_cfg:
        y = np.array(ALT_W10_QPS_BY_BIN[key], dtype=float)
        # mask NaN
        mask = ~np.isnan(y)
        ax.plot(x[mask], y[mask], fmt, color=color, label=label,
                linewidth=lw, markerfacecolor='white', markeredgewidth=0.8)

    # shade K-Means cluster regions (approximate edge-count ranges)
    ax.axvspan(30,  150, alpha=0.06, color='#2166ac', label='_nolegend_')
    ax.axvspan(150, 300, alpha=0.06, color='#4d9221', label='_nolegend_')
    ax.axvspan(300, 600, alpha=0.06, color='#d6604d', label='_nolegend_')

    # cluster labels
    ax.text(90,   1600, 'Localized\n(Cluster 2)', fontsize=4.5, ha='center',
            color='#2166ac', alpha=0.7, va='bottom')
    ax.text(225,  600,  'Regional\n(Cluster 0)', fontsize=4.5, ha='center',
            color='#4d9221', alpha=0.7, va='bottom')
    ax.text(450,  280,  'Megalopolis\n(Cluster 1)', fontsize=4.5, ha='center',
            color='#d6604d', alpha=0.7, va='bottom')

    ax.set_yscale('log')
    ax.set_xlabel('Path length (edges)  — proxy for routing complexity')
    ax.set_ylabel('Queries per second (QPS)  ↑ higher is better')
    ax.set_title('ALT $w=1.0$ throughput vs. path complexity')
    ax.set_xlim(0, 570)
    ax.set_xticks(BINS_MIDPTS)
    ax.set_xticklabels(BINS_LABELS, rotation=30, ha='right', fontsize=5.5)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda v, _: f'{int(v):,}' if v >= 1000 else f'{int(v)}'))
    ax.legend(loc='upper right', frameon=False, fontsize=5.5)
    ax.grid(axis='y', which='both', alpha=0.4)
    _dir_note(ax, '↑ higher QPS = better throughput', 'upper left')
    fig.tight_layout()
    save(fig, 'fig_cluster_qps.png')


# ── main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('Generating IEEE paper figures (v2 — delta removed, cluster QPS added)...')
    fig_algo_complexity()
    fig_param_elasticity()
    fig_reopen_index()
    fig_radix_collapse()
    fig_tail_roughness()
    fig_excess_kurtosis()
    fig_cluster_qps()
    print('Done. All figures saved to:', OUT_DIR)
