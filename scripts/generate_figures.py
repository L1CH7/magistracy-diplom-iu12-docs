#!/usr/bin/env python3
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Настройка академического стиля графиков для публикаций IEEE
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8.5,
    'figure.titlesize': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'grid.linestyle': ':',
    'grid.alpha': 0.6,
    'axes.edgecolor': '#333333'
})

# Определение путей к файлам данных
POSSIBLE_STATS_PATHS = [
    '../../benchmarks/traffic-core/stats/stats_summary.csv',
    '../data/logs/benchmarks/stats/stats_summary.csv',
    './docs/data/logs/benchmarks/stats/stats_summary.csv',
    './magistracy-diplom-iu12/docs/data/logs/benchmarks/stats/stats_summary.csv'
]

POSSIBLE_RUNS_PATHS = [
    '../../benchmarks/traffic-core/stats/run_results.csv',
    '../data/logs/benchmarks/stats/run_results_1500_routes_8_queues_9_algos.csv',
    './docs/data/logs/benchmarks/stats/run_results_1500_routes_8_queues_9_algos.csv',
    './magistracy-diplom-iu12/docs/data/logs/benchmarks/stats/run_results_1500_routes_8_queues_9_algos.csv'
]

def find_file(possible_paths):
    for path in possible_paths:
        if os.path.exists(path):
            return path
    # Попробуем найти относительно директории скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for path in possible_paths:
        abs_path = os.path.join(script_dir, path)
        if os.path.exists(abs_path):
            return abs_path
    return None

def main():
    stats_csv = find_file(POSSIBLE_STATS_PATHS)
    runs_csv = find_file(POSSIBLE_RUNS_PATHS)

    if not stats_csv:
        print("Error: stats_summary.csv not found!", file=sys.stderr)
        sys.exit(1)
    if not runs_csv:
        print("Error: run_results.csv not found!", file=sys.stderr)
        sys.exit(1)

    print(f"Using stats file: {stats_csv}")
    print(f"Using runs file: {runs_csv}")

    # Создаем папку assets/ рядом со скриптом, если ее нет
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, '../assets')
    os.makedirs(assets_dir, exist_ok=True)
    print(f"Output assets directory: {os.path.abspath(assets_dir)}")

    # Загружаем данные
    df_stats = pd.read_csv(stats_csv)
    df_runs = pd.read_csv(runs_csv)
    df_runs['QPS'] = 1000.0 / np.where(df_runs['TimeMs'] == 0, 0.001, df_runs['TimeMs'])

    # =========================================================================
    # РИСУНОК 1: Архитектурная матрица эффективности (Grid 2×2 Matrix)
    # =========================================================================
    fig, axs = plt.subplots(2, 2, figsize=(11.5, 8.5))
    
    queues_map = {
        '2-ary': '2-ary Heap',
        '8-ary': '8-ary SIMD',
        'bucket': 'Bucket Queue',
        'quickheap': 'QuickHeap (Rust)',
        'radix': 'Radix Heap'
    }
    target_queues = list(queues_map.keys())
    
    # --- ПАНЕЛЬ А: ALT w=1.0 QPS (Горизонтальный Bar Chart) ---
    alt_1_stats = df_stats[(df_stats['Algorithm'] == 'ALT w=1.0') & (df_stats['Queue'].isin(target_queues))].copy()
    alt_1_stats['QueueName'] = alt_1_stats['Queue'].map(queues_map)
    alt_1_stats = alt_1_stats.sort_values('QPS')
    
    axs[0, 0].barh(alt_1_stats['QueueName'], alt_1_stats['QPS'], color='#4A90E2', edgecolor='black', alpha=0.85, height=0.55)
    axs[0, 0].set_xlabel('Throughput (QPS)')
    axs[0, 0].set_title('A. Algorithmic Throughput under ALT w=1.0', fontsize=10.5, fontweight='bold')
    axs[0, 0].grid(axis='x', linestyle=':', alpha=0.6)
    for i, val in enumerate(alt_1_stats['QPS']):
        axs[0, 0].text(val + 5, i, f'{val:.1f}', va='center', fontsize=8.5, weight='bold')

    # --- ПАНЕЛЬ Б: Нормированные такты Push/Pop ---
    alt_1_norm = df_stats[(df_stats['Algorithm'] == 'ALT w=1.0') & (df_stats['Queue'].isin(target_queues))].copy()
    alt_1_norm['QueueName'] = alt_1_norm['Queue'].map(queues_map)
    alt_1_norm['log2N'] = np.log2(alt_1_norm['MeanNodes'])
    alt_1_norm['NormPush'] = alt_1_norm['MeanPushCycles'] / alt_1_norm['log2N']
    alt_1_norm['NormPop'] = alt_1_norm['MeanPopCycles'] / alt_1_norm['log2N']
    alt_1_norm['Queue'] = pd.Categorical(alt_1_norm['Queue'], categories=target_queues, ordered=True)
    alt_1_norm = alt_1_norm.sort_values('Queue')
    
    x = np.arange(len(target_queues))
    width = 0.35
    axs[0, 1].bar(x - width/2, alt_1_norm['NormPush'], width, label='Push Cost', color='#7ed6df', edgecolor='black', alpha=0.85)
    axs[0, 1].bar(x + width/2, alt_1_norm['NormPop'], width, label='Pop Cost', color='#50E3C2', edgecolor='black', alpha=0.85)
    axs[0, 1].set_xticks(x)
    axs[0, 1].set_xticklabels(alt_1_norm['QueueName'], rotation=15)
    axs[0, 1].set_ylabel('Cost Index [Cycles / log2(N)]')
    axs[0, 1].set_title('B. Priority Queue Microarchitectural Efficiency', fontsize=10.5, fontweight='bold')
    axs[0, 1].grid(axis='y', linestyle=':', alpha=0.6)
    axs[0, 1].legend()

    # --- ПАНЕЛЬ В: Оверхед очереди vs Взвешенность (ALT) ---
    w_vals = [1.0, 1.05, 1.15, 1.2]
    w_labels = ['1.0', '1.05', '1.15', '1.2']
    queues_lines = [
        ('radix', 'Radix Heap', '#E35050', 'o-'),
        ('8-ary', '8-ary SIMD Heap', '#9B51E0', 's--'),
        ('bucket', 'Bucket Queue', '#F5A623', 'd-.')
    ]
    for queue_id, label, color, style in queues_lines:
        overheads = []
        for w in w_vals:
            algo_name = f'ALT w={w}' if w != 1.0 else 'ALT w=1.0'
            row = df_stats[(df_stats['Algorithm'] == algo_name) & (df_stats['Queue'] == queue_id)]
            overheads.append(row['MeanOverheadPct'].values[0] if not row.empty else np.nan)
        axs[1, 0].plot(w_labels, overheads, style, color=color, linewidth=2, markersize=6, label=label)
    axs[1, 0].set_xlabel('Heuristic Weight (w)')
    axs[1, 0].set_ylabel('Queue Execution Overhead (%)')
    axs[1, 0].set_title('C. Queue Internal Overhead Scaling under ALT', fontsize=10.5, fontweight='bold')
    axs[1, 0].legend()
    axs[1, 0].grid(True, linestyle=':', alpha=0.6)

    # --- ПАНЕЛЬ Г: Парадокс взвешенности (Nodes vs w) ---
    alt_nodes = []
    astar_nodes = []
    for w in w_vals:
        algo_alt = f'ALT w={w}' if w != 1.0 else 'ALT w=1.0'
        row_alt = df_stats[(df_stats['Algorithm'] == algo_alt) & (df_stats['Queue'] == 'radix')]
        alt_nodes.append(row_alt['MeanNodes'].values[0] if not row_alt.empty else np.nan)
        
        algo_astar = f'A-Star w={w}'
        row_astar = df_stats[(df_stats['Algorithm'] == algo_astar) & (df_stats['Queue'] == 'radix')]
        astar_nodes.append(row_astar['MeanNodes'].values[0] if not row_astar.empty else np.nan)

    axs[1, 1].plot(w_labels, alt_nodes, '^--', color='#E35050', linewidth=2, markersize=7, label='ALT Core (Degradation)')
    axs[1, 1].plot(w_labels, astar_nodes, 'v-', color='#4A90E2', linewidth=2, markersize=7, label='A-Star Core (Optimization)')
    axs[1, 1].set_xlabel('Heuristic Weight (w)')
    axs[1, 1].set_ylabel('Mean Visited Edges (log scale)')
    axs[1, 1].set_yscale('log')
    axs[1, 1].set_title('D. The Weighting Paradox (Edge Exploration)', fontsize=10.5, fontweight='bold')
    axs[1, 1].legend()
    axs[1, 1].grid(True, which="both", linestyle=':', alpha=0.6)

    plt.tight_layout()
    fig1_path = os.path.join(assets_dir, 'ieee_integrated_evaluation.png')
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"Saved: {fig1_path}")

    # =========================================================================
    # РИСУНОК 2: Семейства QPS-гипербол и точки пересечения очередей
    # =========================================================================
    plt.figure(figsize=(9.0, 6.0))
    
    # Разбиваем PathEdges на мелкие интервалы для гладкой отрисовки кривых QPS
    bins_fine = np.arange(0, 620, 30)
    bin_centers = bins_fine[:-1] + 15
    df_runs['PathEdgesBin'] = pd.cut(df_runs['PathEdges'], bins=bins_fine)
    
    configs_hyperbolas = [
        ('ALT w=1.0', 'radix', 'ALT w=1.0 (Radix Heap)', '#14a44d', 'o', '-'),
        ('ALT w=1.0', '8-ary', 'ALT w=1.0 (8-ary SIMD)', '#3b71ca', 'v', '-'),
        ('ALT w=1.2', '8-ary', 'ALT w=1.2 (8-ary SIMD)', '#9B51E0', 's', '-.'),
        ('ALT w=1.2', 'radix', 'ALT w=1.2 (Radix Heap)', '#E35050', '^', '--'),
        ('A-Star w=1.0', 'bucket', 'A-Star w=1.0 (Bucket)', '#F5A623', 'd', '--'),
        ('A-Star w=1.0', '8-ary', 'A-Star w=1.0 (8-ary SIMD)', '#f1c40f', 'x', ':'),
        ('Dijkstra', 'bucket', 'Dijkstra (Bucket)', '#7f8c8d', '+', ':'),
        ('Dijkstra', '8-ary', 'Dijkstra (8-ary SIMD)', '#34495e', '*', ':')
    ]
    
    for algo, queue, label, color, marker, linestyle in configs_hyperbolas:
        sub = df_runs[(df_runs['Algorithm'] == algo) & (df_runs['Queue'] == queue)].copy()
        if sub.empty:
            continue
        # Считаем средний QPS в каждом бакете
        grouped = sub.groupby('PathEdgesBin', observed=True)['QPS'].mean()
        # Сопоставим с центрами бакетов
        qps_vals = [grouped.get(pd.Interval(bins_fine[i], bins_fine[i+1]), np.nan) for i in range(len(bins_fine)-1)]
        
        plt.plot(bin_centers, qps_vals, linestyle=linestyle, marker=marker, color=color, 
                 linewidth=1.8, markersize=5.5, label=label)
                 
    plt.yscale('log') # Логарифмическая шкала QPS идеально разделяет уровни алгоритмов
    plt.xlabel('Path Length (Number of Edge-Manes)')
    plt.ylabel('Routing Throughput (QPS, log scale)')
    plt.title('Hyperbolic QPS Scaling & Crossover Points in Edge-Based Space')
    plt.grid(True, which="both", linestyle=':', alpha=0.5)
    plt.legend(loc='best', framealpha=0.9)
    plt.tight_layout()
    
    fig2_path = os.path.join(assets_dir, 'qps_vs_path_length_hyperbolas.png')
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"Saved: {fig2_path}")

    # =========================================================================
    # РИСУНОК 3: Профилирование по длине маршрута с двойной осью Y (Dual Y-Axis)
    # =========================================================================
    bins_dual = [0, 100, 250, 500, np.inf]
    bin_labels_dual = ['0-100\n(Local)', '100-250\n(Sub-urban)', '250-500\n(Arterial)', '500+\n(Highway)']
    df_runs['PathLengthBin'] = pd.cut(df_runs['PathEdges'], bins=bins_dual, labels=bin_labels_dual)

    fig, ax1 = plt.subplots(figsize=(8.0, 5.0))
    ax2 = ax1.twinx()

    configs_dual = [
        ('ALT w=1.0', 'radix', 'ALT w=1.0 + Radix Heap', '#14a44d', 'o', '-'),
        ('ALT w=1.0', '8-ary', 'ALT w=1.0 + 8-ary SIMD', '#3b71ca', 's', '--'),
        ('A-Star w=1.2', 'bucket', 'A-Star w=1.2 + Bucket', '#E35050', '^', '-.')
    ]

    for algo, queue, label, color, marker, linestyle in configs_dual:
        sub_df = df_runs[(df_runs['Algorithm'] == algo) & (df_runs['Queue'] == queue)].copy()
        if sub_df.empty:
            continue
            
        grouped = sub_df.groupby('PathLengthBin', observed=True).agg({
            'TimeMs': 'mean',
            'RelativeErrorPct': 'mean'
        }).reset_index()
        
        ax1.plot(grouped['PathLengthBin'].astype(str), grouped['TimeMs'], 
                 marker=marker, color=color, linestyle=linestyle, linewidth=2, 
                 label=f'{label} (Time)')
                 
        ax2.plot(grouped['PathLengthBin'].astype(str), grouped['RelativeErrorPct'], 
                 marker=marker, color=color, linestyle=':', alpha=0.8, linewidth=1.2,
                 label=f'{label} (Error)')

    ax1.set_xlabel('Path Distance in Edge-Manes (Beijing/Moscow Scale)')
    ax1.set_ylabel('Mean Execution Time (ms)', color='black')
    ax2.set_ylabel('Mean Relative Error (MRE, %)', color='red')
    
    ax1.tick_params(axis='y', labelcolor='black')
    ax2.tick_params(axis='y', labelcolor='red')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)

    plt.title('Dual-Axis Performance Profile vs Journey Distance in Edge-Based Space')
    ax1.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()
    
    fig3_path = os.path.join(assets_dir, 'routing_profile_dual_axis.png')
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print(f"Saved: {fig3_path}")
    print("All IEEE figures generated successfully!")

if __name__ == '__main__':
    main()
