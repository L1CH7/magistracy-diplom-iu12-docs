#!/usr/bin/env python3
import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy.stats import kurtosis, pearsonr
from matplotlib.lines import Line2D

# Academic plot settings for IEEE Publications
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8,
    'figure.titlesize': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'grid.linestyle': ':',
    'grid.alpha': 0.6,
    'axes.edgecolor': '#333333'
})

# Strict queue display names definition as required
QUEUE_DISPLAY_NAMES = {
    '2-ary': 'Simd2AryHeap',
    '4-ary': 'Simd4AryHeap',
    '8-ary': 'Simd8AryHeap',
    '16-ary': 'Simd16AryHeap',
    'bucket': 'SimdBucketQueue',
    'radix': 'SimdRadixHeap',
    'quickheap': 'SimdQuickHeap'
}

def main():
    csv_path = '/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/docs/data/logs/benchmarks/stats/run_results_750_routes_8_queues_9_algos.csv'
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} was not found!")
        sys.exit(1)

    def format_w(w):
        if abs(w - 1.0) < 0.01: return "1.0"
        if abs(w - 1.05) < 0.01: return "1.05"
        if abs(w - 1.10) < 0.01: return "1.10"
        if abs(w - 1.15) < 0.01: return "1.15"
        if abs(w - 1.20) < 0.01: return "1.2"
        return f"{w:.2f}"

    print(f"Loading dataset: {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Pre-process columns
    df['QPS'] = 1000.0 / np.where(df['TimeMs'] == 0, 0.001, df['TimeMs'])
    df['Tortuosity'] = df['PathLengthM'] / np.where(df['EuclideanDistanceM'] == 0, 1.0, df['EuclideanDistanceM'])
    df['QueueOverheadPct'] = (df['QueueTimeMs'] / df['TimeMs']) * 100.0
    
    algorithms = sorted(df['Algorithm'].unique())
    queues = sorted(df['Queue'].unique())
    
    # Create output directory for plots
    assets_dir = '/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/docs/latex/assets'
    os.makedirs(assets_dir, exist_ok=True)
    
    # Color mappings for the 7 active queues (delta queue removed, radix gets a distinct purple)
    queue_colors = {
        '2-ary': '#A2C2E8',      # Light Blue
        '4-ary': '#5B9BD5',      # Medium Light Blue
        '8-ary': '#2F5597',      # Medium Dark Blue
        '16-ary': '#1F3864',     # Dark Blue
        'bucket': '#A9D08E',     # Light Green
        'radix': '#7030A0',      # Distinct Purple/Violet
        'quickheap': '#ED7D31'   # Amber/Orange
    }
    queue_markers = {
        '2-ary': 'o',
        '4-ary': 's',
        '8-ary': 'D',
        '16-ary': 'v',
        'bucket': 'p',
        'radix': 'h',
        'quickheap': '^'
    }
    queue_linestyles = {
        '2-ary': '-',
        '4-ary': '-',
        '8-ary': '-',
        '16-ary': '-',
        'bucket': '--',
        'radix': ':',
        'quickheap': '-.'
    }
    
    all_queues = ['2-ary', '4-ary', '8-ary', '16-ary', 'bucket', 'radix', 'quickheap']
    
    # -------------------------------------------------------------------------
    # PART 1: COMPILING exhaustive_statistical_audit.txt
    # -------------------------------------------------------------------------
    audit = []
    audit.append("=======================================================================")
    audit.append("EXHAUSTIVE ADVANCED STATISTICAL AUDIT (72 ALGO-QUEUE COMBINATIONS)")
    audit.append("=======================================================================\n")
    
    audit.append("--- SECTION 1: ADVANCED QUALITY & HARDWARE STRAIN METRICS ---")
    audit.append(
        f"{'Algorithm':<15} | {'Queue':<12} | {'Mean(ms)':<8} | {'p50(ms)':<7} | {'p99(ms)':<7} | {'p99.9':<6} | "
        f"{'Kurtosis':<8} | {'Inflation':<9} | {'GhostDens':<9} | {'Reopen(rho)':<11} | {'Tort-Time corr':<14} | {'Roughness':<9}"
    )
    audit.append("-" * 130)

    stats_dict = {}

    for algo in algorithms:
        stats_dict[algo] = {}
        for q in queues:
            sub = df[(df['Algorithm'] == algo) & (df['Queue'] == q)].copy()
            if sub.empty:
                continue
            
            times = sub['TimeMs']
            mean_t = times.mean()
            p50 = np.percentile(times, 50)
            p99 = np.percentile(times, 99)
            p999 = np.percentile(times, 99.9)
            
            # Kurtosis (Excess)
            kurt = kurtosis(times, fisher=True) if len(times) > 3 else 0.0
            
            # Inflation = PushCount / PopCount
            mean_push = sub['PushCount'].mean()
            mean_pop = sub['PopCount'].mean()
            inflation = mean_push / mean_pop if mean_pop > 0 else 1.0
            
            # GhostDensity = (Push + Pop - 2*VisitedNodes) / VisitedNodes
            mean_nodes = sub['VisitedNodes'].mean()
            ghost_density = (mean_push + mean_pop - 2 * mean_nodes) / mean_nodes if mean_nodes > 0 else 0.0
            
            # ReopeningIndex (rho) = PopCount / VisitedNodes
            reopen_index = mean_pop / mean_nodes if mean_nodes > 0 else 1.0
            
            # Correlation between Tortuosity and QueueOverheadPct
            sub_clean = sub.dropna(subset=['Tortuosity', 'QueueOverheadPct'])
            if len(sub_clean) > 5 and sub_clean['Tortuosity'].std() > 0 and sub_clean['QueueOverheadPct'].std() > 0:
                corr_val, _ = pearsonr(sub_clean['Tortuosity'], sub_clean['QueueOverheadPct'])
            else:
                corr_val = 0.0
            
            # Roughness = p99 / p50
            roughness = p99 / p50 if p50 > 0 else 0.0
            
            stats_dict[algo][q] = {
                'mean_t': mean_t, 'p50': p50, 'p99': p99, 'p999': p999,
                'kurt': kurt, 'inflation': inflation, 'ghost_density': ghost_density,
                'reopen_index': reopen_index, 'corr_val': corr_val, 'roughness': roughness,
                'qps': sub['QPS'].mean()
            }
            
            audit.append(
                f"{algo:<15} | {q:<12} | {mean_t:<8.3f} | {p50:<7.3f} | {p99:<7.3f} | {p999:<6.3f} | "
                f"{kurt:<8.3f} | {inflation:<9.3f} | {ghost_density:<9.3f} | {reopen_index:<11.3f} | {corr_val:<14.4f} | {roughness:<9.3f}"
            )
        audit.append("-" * 130)
    audit.append("\n")

    # SECTION 2: COMPLEXITY EXPONENTS
    audit.append("--- SECTION 2: SCALING COMPLEXITY LAWS ---")
    audit.append(
        f"{'Algorithm':<15} | {'Queue':<12} | {'Time Exponent(alpha)':<20} | {'Time R2':<8} | "
        f"{'Cycle Exponent(beta)':<20} | {'Cycle R2':<8}"
    )
    audit.append("-" * 90)

    scaling_laws = {}
    for algo in algorithms:
        scaling_laws[algo] = {}
        for q in queues:
            sub = df[(df['Algorithm'] == algo) & (df['Queue'] == q)].copy()
            sub = sub[(sub['TimeMs'] > 0) & (sub['PathEdges'] > 0) & (sub['AvgPopCycles'] > 0) & (sub['VisitedNodes'] > 0)]
            if len(sub) < 15:
                continue
            
            # alpha: log(TimeMs) ~ log(PathEdges)
            log_L = np.log(sub['PathEdges'])
            log_T = np.log(sub['TimeMs'])
            X_L = sm.add_constant(log_L)
            model_L = sm.OLS(log_T, X_L).fit()
            alpha = model_L.params['PathEdges']
            r2_L = model_L.rsquared
            
            # beta: log(AvgPopCycles) ~ log(VisitedNodes)
            log_N = np.log(sub['VisitedNodes'])
            log_C = np.log(sub['AvgPopCycles'])
            X_N = sm.add_constant(log_N)
            model_C = sm.OLS(log_C, X_N).fit()
            beta = model_C.params['VisitedNodes']
            r2_C = model_C.rsquared
            
            scaling_laws[algo][q] = {'alpha': alpha, 'r2_L': r2_L, 'beta': beta, 'r2_C': r2_C}
            
            audit.append(
                f"{algo:<15} | {q:<12} | {alpha:<20.4f} | {r2_L:<8.4f} | {beta:<20.4f} | {r2_C:<8.4f}"
            )
        audit.append("-" * 90)
    audit.append("\n")

    # SECTION 3: PARAMETRIC SENSITIVITY ELASTICITY
    audit.append("--- SECTION 3: PARAMETRIC SENSITIVITY ELASTICITY ---")
    audit.append("Elasticity = (% Change in QPS) / (% Change in Weight w from base w=1.0)")
    audit.append(f"{'Core Algorithm':<15} | {'Queue':<12} | {'w = 1.05':<10} | {'w = 1.10':<10} | {'w = 1.15':<10} | {'w = 1.2':<10}")
    audit.append("-" * 75)

    elasticities_data = {}
    for core in ['A-Star', 'ALT']:
        elasticities_data[core] = {}
        for q in queues:
            base_algo = f"{core} w=1.0"
            if base_algo not in stats_dict or q not in stats_dict[base_algo]:
                continue
            qps_1_0 = stats_dict[base_algo][q]['qps']
            if qps_1_0 == 0 or np.isnan(qps_1_0):
                continue
            
            elasticities_data[core][q] = {}
            elasticities = {}
            for w in [1.05, 1.10, 1.15, 1.2]:
                target_algo = f"{core} w={format_w(w)}"
                if target_algo in stats_dict and q in stats_dict[target_algo]:
                    qps_w = stats_dict[target_algo][q]['qps']
                    pct_qps = (qps_w - qps_1_0) / qps_1_0
                    pct_w = (w - 1.0) / 1.0
                    val = pct_qps / pct_w
                    elasticities[w] = val
                    elasticities_data[core][q][w] = val
                else:
                    elasticities[w] = np.nan
                    
            audit.append(f"{core:<15} | {q:<12} | {elasticities[1.05]:<10.4f} | {elasticities[1.10]:<10.4f} | {elasticities[1.15]:<10.4f} | {elasticities[1.2]:<10.4f}")
        audit.append("-" * 75)
    audit.append("\n")

    # Save textual audit report
    audit_file = '/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/docs/data/logs/exhaustive_statistical_audit.txt'
    with open(audit_file, 'w') as f:
        f.write("\n".join(audit))
    print(f"Saved: {audit_file}")

    # =========================================================================
    # FIGURE 1: ghost_reopening_cascade.png (1x2 Facet Grid)
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.5))
    w_vals = [1.0, 1.05, 1.10, 1.15, 1.2]

    # Panel A: Reopening Index rho for ALT core across 7 queues
    for q in all_queues:
        y_vals = []
        for w in w_vals:
            algo = f'ALT w={format_w(w)}'
            val = stats_dict[algo][q]['reopen_index'] if algo in stats_dict and q in stats_dict[algo] else 1.0
            y_vals.append(val)
        ax1.plot(w_vals, y_vals, marker=queue_markers[q], linestyle=queue_linestyles[q], color=queue_colors[q], label=QUEUE_DISPLAY_NAMES[q], linewidth=1.8, markersize=6)
    
    ax1.set_xlabel('Heuristic Weight ($w$)')
    ax1.set_ylabel('Node Re-opening Index ($\\rho = \\text{PopCount} / U$)')
    ax1.set_title('A. Explore Re-opening Storm (\\rho) - ALT')
    ax1.set_xticks(w_vals)
    ax1.set_xticklabels([format_w(w) for w in w_vals])
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(ncol=2, fontsize=7.5)

    # Panel B: Ghost Node Density for ALT core across 7 queues
    for q in all_queues:
        y_vals = []
        for w in w_vals:
            algo = f'ALT w={format_w(w)}'
            val = stats_dict[algo][q]['ghost_density'] if algo in stats_dict and q in stats_dict[algo] else 0.0
            y_vals.append(val)
        ax2.plot(w_vals, y_vals, marker=queue_markers[q], linestyle=queue_linestyles[q], color=queue_colors[q], label=QUEUE_DISPLAY_NAMES[q], linewidth=1.8, markersize=6)

    ax2.set_xlabel('Heuristic Weight ($w$)')
    ax2.set_ylabel('Ghost Node Density')
    ax2.set_title('B. Memory Pollution Profile (Ghost Node Density) - ALT')
    ax2.set_xticks(w_vals)
    ax2.set_xticklabels([format_w(w) for w in w_vals])
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(ncol=2, fontsize=7.5)

    plt.tight_layout()
    fig1_path = os.path.join(assets_dir, 'ghost_reopening_cascade.png')
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"Saved: {fig1_path}")

    # =========================================================================
    # FIGURE 2: hardware_strain_matrix.png (1x2 Facet Grid)
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8))
    x_indices = np.arange(len(all_queues))
    width = 0.35

    # Panel A: Roughness Grouped Bar Chart (ALT w=1.0 vs A-Star w=1.2) for 7 queues
    roughness_alt = [stats_dict['ALT w=1.0'][q]['roughness'] if 'ALT w=1.0' in stats_dict and q in stats_dict['ALT w=1.0'] else 0.0 for q in all_queues]
    roughness_astar = [stats_dict['A-Star w=1.2'][q]['roughness'] if 'A-Star w=1.2' in stats_dict and q in stats_dict['A-Star w=1.2'] else 0.0 for q in all_queues]

    rects1 = ax1.bar(x_indices - width/2, roughness_alt, width, label='ALT w=1.0', color='#8EA9DB', edgecolor='#1F3864', alpha=0.9)
    rects2 = ax1.bar(x_indices + width/2, roughness_astar, width, label='A* w=1.2', color='#F4B183', edgecolor='#7F6000', alpha=0.9)

    ax1.set_ylabel('Roughness Factor ($p99 / p50$)')
    ax1.set_title('A. Latency Tail Roughness (Jitter Profile)')
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels([QUEUE_DISPLAY_NAMES[q] for q in all_queues], rotation=25, ha='right')
    ax1.grid(axis='y', linestyle=':', alpha=0.6)
    ax1.legend()

    # Panel B: Excess Kurtosis Grouped Bar Chart for 7 queues
    kurt_alt = [stats_dict['ALT w=1.0'][q]['kurt'] if 'ALT w=1.0' in stats_dict and q in stats_dict['ALT w=1.0'] else 0.0 for q in all_queues]
    kurt_astar = [stats_dict['A-Star w=1.2'][q]['kurt'] if 'A-Star w=1.2' in stats_dict and q in stats_dict['A-Star w=1.2'] else 0.0 for q in all_queues]

    rects3 = ax2.bar(x_indices - width/2, kurt_alt, width, label='ALT w=1.0', color='#8EA9DB', edgecolor='#1F3864', alpha=0.9)
    rects4 = ax2.bar(x_indices + width/2, kurt_astar, width, label='A* w=1.2', color='#F4B183', edgecolor='#7F6000', alpha=0.9)

    ax2.set_ylabel('Excess Kurtosis')
    ax2.set_title('B. Microarchitectural Latency Kurtosis')
    ax2.set_xticks(x_indices)
    ax2.set_xticklabels([QUEUE_DISPLAY_NAMES[q] for q in all_queues], rotation=25, ha='right')
    ax2.grid(axis='y', linestyle=':', alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    fig2_path = os.path.join(assets_dir, 'hardware_strain_matrix.png')
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"Saved: {fig2_path}")

    # =========================================================================
    # FIGURE 3: complexity_elasticity_facets.png (1x2 Facet Grid)
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8))
    
    # Panel A: Algorithmic complexity exponent bar chart with color gradients and gaps
    algo_steps = [
        'Dijkstra',
        'A-Star w=1.0', 'A-Star w=1.05', 'A-Star w=1.10', 'A-Star w=1.15', 'A-Star w=1.2',
        'ALT w=1.0', 'ALT w=1.05', 'ALT w=1.10', 'ALT w=1.15', 'ALT w=1.2'
    ]
    
    x_coords = [0, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12]
    
    # We extract values for the Simd8AryHeap representing the core algorithms' exploration behavior
    alpha_vals = [scaling_laws[algo]['8-ary']['alpha'] if algo in scaling_laws and '8-ary' in scaling_laws[algo] else 0.0 for algo in algo_steps]
    
    # Color gradients:
    # Dijkstra: Gray (#7F7F7F)
    # A-Star: Red to Orange gradient
    # ALT: Green to Blue gradient
    bar_colors = [
        '#7F7F7F',  # Dijkstra
        '#800000', '#C00000', '#E25050', '#ED7D31', '#FFC000',  # A-Star
        '#2E401A', '#548235', '#A9D08E', '#4A90E2', '#1F3864'   # ALT
    ]
    
    rects = ax1.bar(x_coords, alpha_vals, color=bar_colors, edgecolor='black', alpha=0.9, width=0.6)
    
    # Label each bar with its heuristic weight directly at the top of the bar
    weight_labels = [
        '-',
        '1.0', '1.05', '1.10', '1.15', '1.2',
        '1.0', '1.05', '1.10', '1.15', '1.2'
    ]
    for rect, label in zip(rects, weight_labels):
        h = rect.get_height()
        ax1.text(rect.get_x() + rect.get_width()/2.0, h + 0.05, label, ha='center', va='bottom', fontsize=8, fontweight='semibold')
        
    ax1.set_xlim(-1, 13)
    ax1.set_ylim(0, 3.0)
    ax1.set_xticks([0, 4, 10])
    ax1.set_xticklabels(['Dijkstra', 'A* ($w$)', 'ALT ($w$)'], fontsize=10, fontweight='bold')
    ax1.set_ylabel('Complexity Exponent ($\\alpha$)')
    ax1.set_title('A. Empirical Complexity Exponent ($\\alpha$)')
    ax1.grid(axis='y', linestyle=':', alpha=0.5)

    # Panel B: QPS Elasticity Profiles against steps [1.05, 1.10, 1.15, 1.2] for A-Star and ALT
    # Baselines: 8-ary SIMD, Radix Heap, and Bucket Queue
    w_steps = [1.05, 1.10, 1.15, 1.2]
    configs_elasticity = [
        ('A-Star', '8-ary', 'A* (Simd8AryHeap)', '#2F5597', 'o--', 1.5),
        ('A-Star', 'radix', 'A* (SimdRadixHeap)', '#7030A0', 's--', 1.5),
        ('A-Star', 'bucket', 'A* (SimdBucketQueue)', '#A9D08E', 'd--', 1.5),
        ('ALT', '8-ary', 'ALT (Simd8AryHeap)', '#2F5597', 'o-', 2.0),
        ('ALT', 'radix', 'ALT (SimdRadixHeap)', '#7030A0', 's-', 2.0),
        ('ALT', 'bucket', 'ALT (SimdBucketQueue)', '#A9D08E', 'd-', 2.0)
    ]
    
    for core, q, label, color, style, lwidth in configs_elasticity:
        y_vals = []
        for w in w_steps:
            val = np.nan
            if core in elasticities_data and q in elasticities_data[core] and w in elasticities_data[core][q]:
                val = elasticities_data[core][q][w]
            y_vals.append(val)
        ax2.plot(w_steps, y_vals, style, color=color, label=label, linewidth=lwidth, markersize=6)

    ax2.set_xlabel('Heuristic Weight Step ($w$)')
    ax2.set_ylabel('Sensitivity Elasticity')
    ax2.set_title('B. Parametric Throughput Elasticity')
    ax2.set_xticks(w_steps)
    ax2.set_xticklabels([format_w(w) for w in w_steps])
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(fontsize=7.5)

    plt.tight_layout()
    fig3_path = os.path.join(assets_dir, 'complexity_elasticity_facets.png')
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print(f"Saved: {fig3_path}")
    
    print("All paper plots generated successfully!")

if __name__ == '__main__':
    main()
