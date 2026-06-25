#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set premium academic style (300 DPI for publication quality)
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_theme(style="ticks")

def apply_font_sizes(fig_width, fig_height=5.5, nrows=1, ncols=1):
    """
    Глобально настраивает размеры шрифтов matplotlib в зависимости от размеров рисунка и сетки подграфиков.
    """
    scale = fig_width / 9.0
    if ncols > 1 or nrows > 1:
        # Для многопанельных рисунков делаем шрифт компактнее
        scale *= 0.75
        
    axes_label_size = int(round(12 * scale))
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': axes_label_size - 1,
        'axes.labelsize': axes_label_size,
        'axes.titlesize': int(round(13 * scale)),
        'xtick.labelsize': axes_label_size - 1,
        'ytick.labelsize': axes_label_size - 1,
        'legend.fontsize': axes_label_size,
        'legend.title_fontsize': axes_label_size,
        'figure.dpi': 300,
        'figure.figsize': (fig_width, fig_height)
    })

# Path constants
RUN_RESULTS_CSV = "/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/docs/latex/assets/data/data-router-benchmark-run_results-16.05.26-02:00.csv"
MT_RESULTS_CSV = "/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/docs/latex/assets/data/data-router-benchmark-multithreading_results.csv"
SIMULATION_CSV = "/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/docs/latex/assets/data/data-simulation-run_02bca76a_bpr_on_prof_on_24b_300s_0a_1asf.csv"
OUTPUT_DIR = "/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/docs/latex/assets/images"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Unified color palette, line styles, and markers
COLORS = {
    '2-ary': '#4A90E2',
    '4-ary': '#50E3C2',
    '8-ary': '#D0021B',  # Fin. solution: Red
    '16-ary': '#F5A623',
    'bucket': '#9013FE',
    'radix': '#7ED321',
    'delta': '#BD10E0'
}

LINE_STYLES = {
    '2-ary': '--',
    '4-ary': '-.',
    '8-ary': '-',
    '16-ary': ':',
    'delta': '--',
    'bucket': '-.',
    'radix': '-'
}

MARKERS = {
    '2-ary': 'o',
    '4-ary': 's',
    '8-ary': '^',
    '16-ary': 'D',
    'delta': 'X',
    'bucket': '*',
    'radix': 'p'
}

# Style configurations for the best combinations showdown
COMBO_STYLES = {
    'ALT + 8-ary': {'color': '#D0021B', 'linestyle': '-', 'marker': '^', 'linewidth': 2.8},
    'ALT + 4-ary': {'color': '#F5A623', 'linestyle': '-', 'marker': 's', 'linewidth': 2.0},
    'Bi-Dijkstra + delta': {'color': '#9013FE', 'linestyle': '--', 'marker': 'X', 'linewidth': 1.8},
    'Bi-Dijkstra + bucket': {'color': '#BD10E0', 'linestyle': '--', 'marker': '*', 'linewidth': 1.8},
    'Dijkstra + bucket': {'color': '#4A90E2', 'linestyle': ':', 'marker': '*', 'linewidth': 1.8},
    'Dijkstra + delta': {'color': '#50E3C2', 'linestyle': ':', 'marker': 'X', 'linewidth': 1.8},
    'A-Star + bucket': {'color': '#7ED321', 'linestyle': '-.', 'marker': '*', 'linewidth': 1.8},
    'A-Star + delta': {'color': '#FF5A5F', 'linestyle': '-.', 'marker': 'X', 'linewidth': 1.8}
}

def generate_alt_qps():
    print("📈 Plotting ALT QPS vs Complexity...")
    apply_font_sizes(9.0, 5.5)
    df = pd.read_csv(RUN_RESULTS_CSV)
    df = df[df['Queue'] != '8-ary-lazy'].copy()
    df = df[(df['Crashed'] == 0) & (df['Algorithm'] == 'ALT')].copy()
    
    # Request-based binning
    route_edges = df.groupby('RouteID')['PathEdges'].mean().reset_index()
    try:
        route_edges['Bucket'] = pd.qcut(route_edges['PathEdges'], q=10, labels=False, duplicates='drop')
    except ValueError:
        route_edges['Bucket'] = 0
    bucket_means = route_edges.groupby('Bucket', observed=False)['PathEdges'].mean().round().astype(int)
    route_to_bucket = dict(zip(route_edges['RouteID'], route_edges['Bucket']))
    df['Bucket'] = df['RouteID'].map(route_to_bucket)
    df['PathEdgesAvg'] = df['Bucket'].map(bucket_means)
    
    agg = df.groupby(['Queue', 'PathEdgesAvg'], observed=False)['TimeMs'].mean().reset_index()
    agg['QPS'] = 1000.0 / agg['TimeMs']
    x_values = sorted(list(bucket_means.values))
    
    plt.figure()
    for queue_name in ['2-ary', '4-ary', '8-ary', '16-ary', 'bucket', 'radix', 'delta']:
        queue_data = agg[agg['Queue'] == queue_name]
        if queue_data.empty:
            continue
        queue_data = queue_data.set_index('PathEdgesAvg').reindex(x_values).reset_index()
        
        plt.plot(
            queue_data['PathEdgesAvg'],
            queue_data['QPS'],
            label=f"Очередь {queue_name}",
            color=COLORS[queue_name],
            linestyle=LINE_STYLES[queue_name],
            marker=MARKERS[queue_name],
            linewidth=2.5 if queue_name == '8-ary' else 1.8,
            markersize=6,
            alpha=0.95
        )
        
    plt.yscale('log')
    plt.ylabel("QPS (запросов/с, лог. масштаб)")
    plt.xlabel("Сложность маршрута (число ребер пути)")
    plt.grid(True, which="both", linestyle='--', alpha=0.5)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "alt_qps_comparison.png"), bbox_inches='tight', pad_inches=0.02, dpi=300)
    plt.close()

def generate_hardware_cycles():
    print("📈 Plotting Hardware Cycles Comparison...")
    apply_font_sizes(9.0, 5.5)
    df = pd.read_csv(RUN_RESULTS_CSV)
    df = df[df['Crashed'] == 0]
    
    target_queues = ['2-ary', '4-ary', '8-ary', '16-ary', 'bucket', 'radix', 'delta']
    df_filtered = df[df['Queue'].isin(target_queues)].copy()
    
    agg = df_filtered.groupby('Queue')[['AvgPushCycles', 'AvgPopCycles']].mean().reset_index()
    agg = agg.set_index('Queue').reindex(target_queues).reset_index()
    
    melted = pd.melt(agg, id_vars=['Queue'], value_vars=['AvgPushCycles', 'AvgPopCycles'],
                      var_name='Operation', value_name='CpuCycles')
    melted['Operation'] = melted['Operation'].map({'AvgPushCycles': 'Вставка (Push)', 'AvgPopCycles': 'Извлечение (Pop)'})
    
    plt.figure()
    sns.barplot(
        data=melted,
        x='Queue',
        y='CpuCycles',
        hue='Operation',
        palette=['#4A90E2', '#D0021B'],
        edgecolor='black',
        linewidth=0.8
    )
    
    plt.ylabel("Среднее число тактов CPU (меньше — лучше)")
    plt.xlabel("Тип очереди приоритетов")
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.legend(title="Операция", frameon=True, facecolor='white', edgecolor='#e0e0e0')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "push_pop_cycles_comparison.png"), bbox_inches='tight', pad_inches=0.02, dpi=300)
    plt.close()

def generate_multithreading_scalability():
    print("📈 Plotting Multithreading Scalability...")
    apply_font_sizes(9.0, 5.5)
    df = pd.read_csv(MT_RESULTS_CSV)
    df = df[df['Mode'] != 'No-SMT-Affinity'].copy()
    
    plt.figure()
    
    # Calculate Ideal Linear Limit
    baseline_row = df[(df['Mode'] == 'SMT-Affinity') & (df['ThreadCount'] == 1)]
    baseline_rps = baseline_row['RPS'].iloc[0] if not baseline_row.empty else 639.92
    
    thread_counts = sorted(df['ThreadCount'].unique())
    ideal_rps = [t * baseline_rps for t in thread_counts]
    
    plt.plot(
        thread_counts,
        ideal_rps,
        linestyle='--',
        color='#9B9B9B',
        linewidth=1.8,
        label="Теоретический линейный предел"
    )
    
    mode_labels = {
        'No-Affinity': 'Без привязки (планировщик ОС)',
        'SMT-Affinity': 'С привязкой к ядрам (CPU Affinity)'
    }
    
    for mode in ['No-Affinity', 'SMT-Affinity']:
        mode_data = df[df['Mode'] == mode].sort_values('ThreadCount')
        if mode_data.empty:
            continue
        plt.plot(
            mode_data['ThreadCount'],
            mode_data['RPS'],
            marker='o' if mode == 'SMT-Affinity' else 's',
            linewidth=2.2,
            label=mode_labels[mode],
            color='#D0021B' if mode == 'SMT-Affinity' else '#4A90E2'
        )
        
    plt.xlabel("Число вычислительных потоков")
    plt.ylabel("Пропускная способность (запросов в секунду, RPS)")
    plt.xticks(thread_counts)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "multithreading_scalability.png"), bbox_inches='tight', pad_inches=0.02, dpi=300)
    plt.close()

def generate_best_combinations():
    print("📈 Plotting Ultimate Best Combinations Showdown with markers...")
    apply_font_sizes(11.5, 5.5)
    df = pd.read_csv(RUN_RESULTS_CSV)
    df = df[df['Queue'] != '8-ary-lazy'].copy()
    df = df[df['Crashed'] == 0].copy()
    
    # Request-based binning
    route_edges = df.groupby('RouteID')['PathEdges'].mean().reset_index()
    try:
        route_edges['Bucket'] = pd.qcut(route_edges['PathEdges'], q=10, labels=False, duplicates='drop')
    except ValueError:
        route_edges['Bucket'] = 0
    bucket_means = route_edges.groupby('Bucket', observed=False)['PathEdges'].mean().round().astype(int)
    route_to_bucket = dict(zip(route_edges['RouteID'], route_edges['Bucket']))
    df['Bucket'] = df['RouteID'].map(route_to_bucket)
    df['PathEdgesAvg'] = df['Bucket'].map(bucket_means)
    x_values = sorted(list(bucket_means.values))
    
    # Dynamically select TOP-2 queues (strictly '8-ary' and '4-ary' for ALT)
    best_combos = []
    for algo in df['Algorithm'].unique():
        algo_df = df[df['Algorithm'] == algo]
        if algo == 'ALT':
            best_combos.append(('ALT', '8-ary'))
            best_combos.append(('ALT', '4-ary'))
        else:
            mean_time = algo_df.groupby('Queue')['TimeMs'].mean().sort_values(ascending=True)
            top_queues = mean_time.index[:2].tolist()
            for q in top_queues:
                best_combos.append((algo, q))
            
    print("  [Динамический отбор лучших комбинаций по QPS]:", best_combos)
    
    combo_names = [f"{algo} + {queue}" for algo, queue in best_combos]
    df_filtered = df[(df['Algorithm'].astype(str) + " + " + df['Queue'].astype(str)).isin(combo_names)].copy()
    
    agg = df_filtered.groupby(['Algorithm', 'Queue', 'PathEdgesAvg'], observed=False)['TimeMs'].mean().reset_index()
    agg['QPS'] = 1000.0 / agg['TimeMs']
    agg['Combo'] = agg['Algorithm'].astype(str) + " + " + agg['Queue'].astype(str)
    
    plt.figure()
    lines = []
    
    for combo in combo_names:
        parts = combo.split(' + ')
        algo, queue = parts[0], parts[1]
        
        combo_data = agg[agg['Combo'] == combo]
        if combo_data.empty:
            continue
        combo_data = combo_data.set_index('PathEdgesAvg').reindex(x_values).reset_index()
        
        valid_qps = combo_data['QPS'].dropna()
        last_qps = valid_qps.iloc[-1] if not valid_qps.empty else 0.0
        style_cfg = COMBO_STYLES.get(combo, {'color': '#333333', 'linestyle': '-', 'marker': 'o', 'linewidth': 1.5})
        
        line, = plt.plot(
            combo_data['PathEdgesAvg'],
            combo_data['QPS'],
            color=style_cfg['color'],
            linestyle=style_cfg['linestyle'],
            marker=style_cfg['marker'],
            linewidth=style_cfg['linewidth'],
            markersize=6,
            alpha=0.95
        )
        lines.append((last_qps, line, combo))
        
    lines.sort(key=lambda x: x[0], reverse=True)
    handles = [item[1] for item in lines]
    labels = [item[2] for item in lines]
    
    plt.yscale('log')
    plt.ylabel("QPS (запросов/с, лог. масштаб)")
    plt.xlabel("Сложность маршрута (число ребер пути)")
    plt.grid(True, which="both", linestyle='--', alpha=0.5)
    
    plt.legend(
        handles, labels,
        title="Лучшие комбинации\n(Алгоритм + Очередь)",
        frameon=True, facecolor='white', edgecolor='#e0e0e0',
        loc='upper right'
    )
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "best_combinations_comparison.png"), bbox_inches='tight', pad_inches=0.02, dpi=300)
    plt.close()

def generate_queue_overhead_trend():
    print("📈 Plotting Queue Overhead Trend Bar Chart...")
    apply_font_sizes(9.0, 5.5)
    df = pd.read_csv(RUN_RESULTS_CSV)
    df = df[df['Queue'] != '8-ary-lazy'].copy()
    df = df[df['Crashed'] == 0].copy()
    
    df['QueueOverheadPct'] = (df['QueueTimeMs'] / df['TimeMs']) * 100.0
    df['QueueOverheadPct'] = df['QueueOverheadPct'].clip(0, 100)
    
    agg = df.groupby('Queue', observed=False)['QueueOverheadPct'].mean().reset_index()
    agg = agg.sort_values(by='QueueOverheadPct', ascending=False)
    
    plt.figure()
    bars = plt.bar(
        agg['Queue'],
        agg['QueueOverheadPct'],
        color='#4A90E2',
        edgecolor='black',
        linewidth=0.8,
        width=0.55
    )
    
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.0,
            height + 0.5,
            f"{height:.1f}%",
            ha='center', va='bottom',
            fontweight='bold', fontsize=9, color='#333333'
        )
        
    plt.ylabel("Доля времени выполнения (%)")
    plt.xlabel("Тип очереди приоритетов")
    plt.ylim(0, max(agg['QueueOverheadPct']) + 12)
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "queue_overhead_trend.png"), bbox_inches='tight', pad_inches=0.02, dpi=300)
    plt.close()

def generate_accuracy_comparison():
    print("📈 Plotting 2x2 Accuracy Comparison (4 Algos) Chart...")
    apply_font_sizes(15.0, 12.0, nrows=2, ncols=2)
    df = pd.read_csv(RUN_RESULTS_CSV)
    df = df[df['Queue'] != '8-ary-lazy'].copy()
    df = df[df['Crashed'] == 0].copy()
    
    if 'RelativeErrorPct' not in df.columns:
        print("⚠️ Skipping Accuracy Chart: RelativeErrorPct not in CSV")
        return
        
    # Request-based binning
    route_edges = df.groupby('RouteID')['PathEdges'].mean().reset_index()
    try:
        route_edges['Bucket'] = pd.qcut(route_edges['PathEdges'], q=10, labels=False, duplicates='drop')
    except ValueError:
        route_edges['Bucket'] = 0
    bucket_means = route_edges.groupby('Bucket', observed=False)['PathEdges'].mean().round().astype(int)
    route_to_bucket = dict(zip(route_edges['RouteID'], route_edges['Bucket']))
    df['Bucket'] = df['RouteID'].map(route_to_bucket)
    df['PathEdgesAvg'] = df['Bucket'].map(bucket_means)
    x_values = sorted(list(bucket_means.values))
    
    agg = df.groupby(['Algorithm', 'Queue', 'PathEdgesAvg'], observed=False)['RelativeErrorPct'].mean().reset_index()
    
    # Grid 2x2: A-Star, ALT, Bi-Dijkstra, Dijkstra
    algorithms = ['A-Star', 'ALT', 'Bi-Dijkstra', 'Dijkstra']
    fig, axes = plt.subplots(2, 2)
    axes = axes.flatten()
    
    for idx, algo in enumerate(algorithms):
        ax = axes[idx]
        algo_data = agg[agg['Algorithm'] == algo]
        
        for queue_name in ['2-ary', '4-ary', '8-ary', '16-ary', 'bucket', 'radix', 'delta']:
            queue_data = algo_data[algo_data['Queue'] == queue_name]
            if queue_data.empty:
                continue
                
            queue_data = queue_data.set_index('PathEdgesAvg').reindex(x_values).reset_index()
            
            ax.plot(
                queue_data['PathEdgesAvg'],
                queue_data['RelativeErrorPct'],
                label=f"Очередь {queue_name}",
                color=COLORS[queue_name],
                linestyle=LINE_STYLES[queue_name],
                marker=MARKERS[queue_name],
                linewidth=2.5 if queue_name == '8-ary' else 1.8,
                markersize=6,
                alpha=0.95
            )
            
        ax.set_title(algo, fontweight='bold', pad=10)
        ax.set_ylabel("Относительная погрешность (%)")
        ax.set_xlabel("Сложность маршрута (число ребер пути)")
        ax.grid(True, which="both", linestyle='--', alpha=0.5)
        
        if idx == 0:
            ax.legend(title="Типы очередей", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0', loc='upper right')
            
    plt.tight_layout()
    
    # Save directly as accuracy_comparison-4-algos.png
    plt.savefig(os.path.join(OUTPUT_DIR, "accuracy_comparison-4-algos.png"), bbox_inches='tight', pad_inches=0.02, dpi=300)
    plt.close()

def generate_simulation_plots():
    print(f"📈 Plotting Simulation Metrics from CSV: {SIMULATION_CSV}")
    apply_font_sizes(9.0, 5.5)
    df = pd.read_csv(SIMULATION_CSV)
    time = df['SimTime']
    
    # 1. Green Zones (Свободные участки)
    plt.figure()
    plt.plot(time, df['GreenZones'], color='#2ca02c', linewidth=2.0, 
             label=r'Свободные участки: $N < C_{vis} + 0.3(C_{jam} - C_{vis})$')
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Количество ребер")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_green_zones.png"), bbox_inches='tight', pad_inches=0.02)
    plt.close()

    # 2. Yellow, Red, and Black Zones Combined (Загруженные, перегруженные и заторные участки)
    plt.figure()
    plt.plot(time, df['BlackZones'], color='#111111', linewidth=2.0, 
             label=r'Критические заторы: $N \geq 1.5 C_{jam}$', zorder=1)
    plt.plot(time, df['RedZones'], color='#d62728', linewidth=1.5, 
             label=r'Перегрузка: $C_{jam} \leq N < 1.5 C_{jam}$', zorder=2)
    plt.plot(time, df['YellowZones'], color='#bcbd22', linewidth=1.5, 
             label=r'Плотный трафик: $C_{vis} + 0.3(C_{jam} - C_{vis}) \leq N < C_{jam}$', zorder=3)
    
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Количество ребер")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_red_yellow_zones.png"), bbox_inches='tight', pad_inches=0.02)
    plt.close()

    # 3. Queues (Spawn and Reroute)
    plt.figure()
    spawn = np.array(df['WaitingSpawn'])
    spawn_masked = np.where(spawn > 100000, np.nan, spawn)
    plt.plot(time, spawn_masked, color='#9467bd', linewidth=2.0, linestyle='--', label='Очередь на спавн')
    plt.plot(time, df['WaitingReroute'], color='#ff7f0e', linewidth=2.0, label='Очередь MPR (Перестроения)')
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Количество агентов в очереди")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_queues.png"), bbox_inches='tight', pad_inches=0.02)
    plt.close()

    # 4. Completed Trips (Завершенные поездки)
    plt.figure()
    plt.plot(time, df['CompletedTrips'], color='#8c564b', linewidth=2.0, label='Накопленные завершенные поездки')
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Завершенные поездки (ед.)")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_completed_trips.png"), bbox_inches='tight', pad_inches=0.02)
    plt.close()

    # 5. TTI с дисперсией (скользящее среднее + стандартное отклонение)
    plt.figure()
    window = 600 # 10 минут для сглаживания высокочастотных шумов
    rolling_mean = df['TTI'].rolling(window=window, center=True, min_periods=1).mean()
    rolling_std = df['TTI'].rolling(window=window, center=True, min_periods=1).std()
    
    lower_bound = (rolling_mean - rolling_std).clip(lower=1.0)
    upper_bound = rolling_mean + rolling_std
    
    line_color = '#0b4f8a'   # Темно-синий
    fill_color = '#4A90E2'   # Полупрозрачный синий
    
    plt.fill_between(time, lower_bound, upper_bound, color=fill_color, alpha=0.15, 
                     label=r'Локальные колебания TTI ($\pm\sigma$)')
    plt.plot(time, lower_bound, color=line_color, linestyle=':', linewidth=0.5, alpha=0.4)
    plt.plot(time, upper_bound, color=line_color, linestyle=':', linewidth=0.5, alpha=0.4)
    plt.plot(time, rolling_mean, color=line_color, linewidth=2.0, label='Скользящее среднее TTI')
    plt.axhline(1.0, color='#d62728', linestyle='--', linewidth=1.0, alpha=0.7, 
                label='Порог свободного движения (TTI = 1.0)')
    
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Индекс TTI")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_tti.png"), bbox_inches='tight', pad_inches=0.02)
    plt.close()

def main():
    print("🎨 Generating high-performance scientific thesis charts with unified style...")
    generate_alt_qps()
    generate_hardware_cycles()
    generate_multithreading_scalability()
    generate_best_combinations()
    generate_queue_overhead_trend()
    generate_accuracy_comparison()
    generate_simulation_plots()
    print("🎉 All thesis charts generated successfully inside assets/images!")

if __name__ == "__main__":
    main()
