#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set premium academic style (300 DPI for publication quality)
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_theme(style="ticks")
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.dpi': 300
})

# Path constants
RUN_RESULTS_CSV = "/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/benchmarks/traffic-core/stats/run_results.csv"
MT_RESULTS_CSV = "/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/benchmarks/traffic-core/stats/multithreading_results.csv"
BPR_ON_CSV = "/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/scripts/stats/run_4f240105_bpr_on_prof_on_24b_300s_200000a_3asf.csv"
BPR_OFF_CSV = "/home/lich/dev/bmstu/diplom-iu12/magistracy-diplom-iu12/scripts/stats/run_45b62f84_bpr_off_prof_on_24b_300s_200000a_3asf.csv"
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
    'delta': '#BD10E0',
    'bpr_on': '#1f77b4',
    'bpr_off': '#d62728'
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
    
    plt.figure(figsize=(9, 5.5))
    x_values = sorted(list(bucket_means.values))
    
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
        
    plt.title("Производительность поиска пути ALT в зависимости от длины маршрута", fontweight='bold', pad=12)
    plt.yscale('log')
    plt.ylabel("Средняя производительность QPS (запросов/сек, лог. масштаб)", fontsize=11)
    plt.xlabel("Сложность маршрута (число ребер пути)", fontsize=11)
    plt.grid(True, which="both", linestyle='--', alpha=0.5)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "alt_qps_comparison.png"), dpi=300)
    plt.close()

def generate_hardware_cycles():
    print("📈 Plotting Hardware Cycles Comparison...")
    df = pd.read_csv(RUN_RESULTS_CSV)
    df = df[df['Crashed'] == 0]
    
    target_queues = ['2-ary', '4-ary', '8-ary', '16-ary', 'bucket', 'radix', 'delta']
    df_filtered = df[df['Queue'].isin(target_queues)].copy()
    
    agg = df_filtered.groupby('Queue')[['AvgPushCycles', 'AvgPopCycles']].mean().reset_index()
    agg = agg.set_index('Queue').reindex(target_queues).reset_index()
    
    melted = pd.melt(agg, id_vars=['Queue'], value_vars=['AvgPushCycles', 'AvgPopCycles'],
                     var_name='Operation', value_name='CpuCycles')
    melted['Operation'] = melted['Operation'].map({'AvgPushCycles': 'Вставка (Push)', 'AvgPopCycles': 'Извлечение (Pop)'})
    
    plt.figure(figsize=(9, 5.5))
    sns.barplot(
        data=melted,
        x='Queue',
        y='CpuCycles',
        hue='Operation',
        palette={'Вставка (Push)': '#4A90E2', 'Извлечение (Pop)': '#D0021B'},
        edgecolor='black',
        linewidth=0.8
    )
    
    plt.title("Аппаратная сложность: среднее число тактов CPU на операцию (Zen 3)", fontweight='bold', pad=12)
    plt.ylabel("Среднее число тактов CPU (меньше — лучше)", fontsize=11)
    plt.xlabel("Тип очереди приоритетов", fontsize=11)
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.legend(title="Операция", frameon=True, facecolor='white', edgecolor='#e0e0e0')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "push_pop_cycles_comparison.png"), dpi=300)
    plt.close()

def generate_multithreading_scalability():
    print("📈 Plotting Multithreading Scalability...")
    df = pd.read_csv(MT_RESULTS_CSV)
    df = df[df['Mode'] != 'No-SMT-Affinity'].copy()
    
    plt.figure(figsize=(9, 5.5))
    
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
        
    plt.title("Анализ многопоточной масштабируемости ядра (ALT + 8-ary)", fontweight='bold', pad=12)
    plt.xlabel("Число вычислительных потоков", fontsize=11)
    plt.ylabel("Пропускная способность (запросов в секунду, RPS)", fontsize=11)
    plt.xticks(thread_counts)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "multithreading_scalability.png"), dpi=300)
    plt.close()

def generate_best_combinations():
    print("📈 Plotting Ultimate Best Combinations Showdown with markers...")
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
    
    plt.figure(figsize=(11.5, 7))
    
    lines = []
    for combo in combo_names:
        combo_data = agg[agg['Combo'] == combo]
        if combo_data.empty:
            continue
        combo_data = combo_data.set_index('PathEdgesAvg').reindex(x_values).reset_index()
        
        valid_qps = combo_data['QPS'].dropna()
        last_qps = valid_qps.iloc[-1] if not valid_qps.empty else 0.0
        
        # Consistent style lookup from our custom combo style map
        style_cfg = COMBO_STYLES.get(combo, {'color': '#000000', 'linestyle': '-', 'marker': 'o', 'linewidth': 1.8})
        
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
    
    plt.title("Сравнение лучших комбинаций алгоритмов и очередей (QPS)", fontweight='bold', pad=15, fontsize=13)
    plt.yscale('log')
    plt.ylabel("Средняя производительность QPS (запросов/сек, лог. масштаб)", fontsize=11)
    plt.xlabel("Сложность маршрута (число ребер пути)", fontsize=11)
    plt.grid(True, which="both", linestyle='--', alpha=0.5)
    
    plt.legend(
        handles, labels,
        title="Лучшие комбинации\n(Алгоритм + Очередь)",
        title_fontsize=9, fontsize=8.5,
        frameon=True, facecolor='white', edgecolor='#e0e0e0',
        loc='upper left', bbox_to_anchor=(1.01, 1.0)
    )
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "best_combinations_comparison.png"), bbox_inches='tight', dpi=300)
    plt.close()

def generate_queue_overhead_trend():
    print("📈 Plotting Queue Overhead Trend Bar Chart...")
    df = pd.read_csv(RUN_RESULTS_CSV)
    df = df[df['Queue'] != '8-ary-lazy'].copy()
    df = df[df['Crashed'] == 0].copy()
    
    df['QueueOverheadPct'] = (df['QueueTimeMs'] / df['TimeMs']) * 100.0
    df['QueueOverheadPct'] = df['QueueOverheadPct'].clip(0, 100)
    
    agg = df.groupby('Queue', observed=False)['QueueOverheadPct'].mean().reset_index()
    agg = agg.sort_values(by='QueueOverheadPct', ascending=False)
    
    plt.figure(figsize=(9, 5.5))
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
        
    plt.title("Доля времени на операции с очередью приоритетов (меньше — лучше)", fontweight='bold', pad=12, fontsize=12)
    plt.ylabel("Доля времени выполнения (%)", fontsize=11)
    plt.xlabel("Тип очереди приоритетов", fontsize=11)
    plt.ylim(0, max(agg['QueueOverheadPct']) + 12)
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "queue_overhead_trend.png"), dpi=300)
    plt.close()

def generate_accuracy_comparison():
    print("📈 Plotting 2x2 Accuracy Comparison (4 Algos) Chart...")
    df = pd.read_csv(RUN_RESULTS_CSV)
    df = df[df['Queue'] != '8-ary-lazy'].copy()
    df = df[df['Crashed'] == 0].copy()
    
    if 'RelativeErrorPct' not in df.columns:
        print("⚠️ Skipping Accuracy Chart: RelativeErrorPct not in CSV")
        return
        
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
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
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
            
        ax.set_title(f"Алгоритм: {algo}", fontweight='bold', pad=10)
        ax.set_ylabel("Средняя относительная погрешность (%)")
        ax.set_xlabel("Сложность маршрута (число ребер пути)")
        ax.grid(True, which="both", linestyle='--', alpha=0.5)
        
        if idx == 0:
            ax.legend(title="Типы очередей", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
            
    plt.suptitle("Точность поиска пути (относительная погрешность в %) в зависимости от длины маршрута", fontweight='bold', y=0.98, fontsize=16)
    plt.tight_layout()
    
    # Save directly as accuracy_comparison-4-algos.png
    plt.savefig(os.path.join(OUTPUT_DIR, "accuracy_comparison-4-algos.png"), bbox_inches='tight', dpi=300)
    plt.close()

def generate_simulation_comparisons():
    print("📈 Plotting Simulation Comparisons (Strict Overlap)...")
    data_on = pd.read_csv(BPR_ON_CSV)
    data_off = pd.read_csv(BPR_OFF_CSV)
    
    t_start = max(data_on['SimTime'].min(), data_off['SimTime'].min())
    t_end = min(data_on['SimTime'].max(), data_off['SimTime'].max())
    
    df_on = data_on[(data_on['SimTime'] >= t_start) & (data_on['SimTime'] <= t_end)].sort_values('SimTime').copy()
    df_off = data_off[(data_off['SimTime'] >= t_start) & (data_off['SimTime'] <= t_end)].sort_values('SimTime').copy()
    
    # 1. TTI
    plt.figure(figsize=(9, 5.2))
    plt.plot(df_on['SimTime'], df_on['TTI'], color=COLORS['bpr_on'], linewidth=2.2, label='С BPR-регулированием (SO)')
    plt.plot(df_off['SimTime'], df_off['TTI'], color=COLORS['bpr_off'], linewidth=2.2, label='Без BPR-регулирования (UE)')
    plt.axhline(1.0, color='gray', linestyle='-.', linewidth=0.8, alpha=0.7, label='Свободный поток (TTI = 1.0)')
    
    plt.title("Динамика индекса задержки сети TTI в пиковые периоды", fontweight='bold', pad=12)
    plt.xlabel("Время симуляции (секунды)", fontsize=11)
    plt.ylabel("Коэффициент TTI (отношение реального времени к свободному)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "simulation_tti_comparison.png"), dpi=300)
    plt.close()
    
    # 2. Completed trips
    on_start_trips = df_on['CompletedTrips'].iloc[0]
    off_start_trips = df_off['CompletedTrips'].iloc[0]
    
    plt.figure(figsize=(9, 5.2))
    plt.plot(df_on['SimTime'], df_on['CompletedTrips'] - on_start_trips, color=COLORS['bpr_on'], linewidth=2.2, label='С BPR-регулированием (SO)')
    plt.plot(df_off['SimTime'], df_off['CompletedTrips'] - off_start_trips, color=COLORS['bpr_off'], linewidth=2.2, label='Без BPR-регулирования (UE)')
    
    plt.title("Накопленное количество завершенных поездок с начала затора", fontweight='bold', pad=12)
    plt.xlabel("Время симуляции (секунды)", fontsize=11)
    plt.ylabel("Количество завершенных поездок (автомобили)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "simulation_completed_comparison.png"), dpi=300)
    plt.close()
    
    # 3. MPR Queue
    plt.figure(figsize=(9, 5.2))
    plt.plot(df_on['SimTime'], df_on['WaitingReroute'], color=COLORS['bpr_on'], linewidth=2.2, label='С BPR-регулированием (SO)')
    plt.plot(df_off['SimTime'], df_off['WaitingReroute'], color=COLORS['bpr_off'], linewidth=2.2, label='Без BPR-регулирования (UE)')
    
    plt.title("Размер очереди динамического перестроения маршрутов (MPR)", fontweight='bold', pad=12)
    plt.xlabel("Время симуляции (секунды)", fontsize=11)
    plt.ylabel("Количество ТС в очереди на перерасчет (ед.)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "simulation_queue_comparison.png"), dpi=300)
    plt.close()

def main():
    print("🎨 Generating high-performance scientific thesis charts with unified style...")
    generate_alt_qps()
    generate_hardware_cycles()
    # generate_multithreading_scalability()
    generate_best_combinations()
    generate_queue_overhead_trend()
    generate_accuracy_comparison()
    # generate_simulation_comparisons()
    print("🎉 All thesis charts generated successfully inside assets/images!")

if __name__ == "__main__":
    main()
