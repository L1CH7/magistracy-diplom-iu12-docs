#!/usr/bin/env python3
import os
import csv
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def setup_plot():
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
    plt.rcParams['axes.edgecolor'] = '#cccccc'
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['figure.figsize'] = (8, 5)
    plt.rcParams['figure.dpi'] = 300

def generate_plots(csv_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Чтение CSV: {csv_file}")
    df = pd.read_csv(csv_file)
    time = df['SimTime']

    setup_plot()

    # 1. Green Zones (Свободные участки)
    plt.figure()
    plt.plot(time, df['GreenZones'], color='#2ca02c', linewidth=2.0, 
             label=r'Свободные участки: $N < C_{vis} + 0.3(C_{jam} - C_{vis})$')
    plt.title("Динамика свободных участков дорожной сети", fontsize=12, fontweight='bold')
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Количество ребер")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig_green_zones.png"))
    plt.close()

    # 2. Yellow, Red, and Black Zones Combined (Загруженные, перегруженные и заторные участки)
    plt.figure()
    # Отрисовываем черные зоны на самом нижнем слое (zorder=1), затем красные, затем желтые
    plt.plot(time, df['BlackZones'], color='#111111', linewidth=2.0, 
             label=r'Критические заторы: $N \geq 1.5 C_{jam}$', zorder=1)
    plt.plot(time, df['RedZones'], color='#d62728', linewidth=1.5, 
             label=r'Перегрузка: $C_{jam} \leq N < 1.5 C_{jam}$', zorder=2)
    plt.plot(time, df['YellowZones'], color='#bcbd22', linewidth=1.5, 
             label=r'Плотный трафик: $C_{vis} + 0.3(C_{jam} - C_{vis}) \leq N < C_{jam}$', zorder=3)
    
    plt.title("Динамика загруженных и заторных сегментов сети", fontsize=12, fontweight='bold')
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Количество ребер")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig_red_yellow_zones.png"))
    plt.close()

    # 3. Queues (Spawn and Reroute)
    plt.figure()
    spawn = np.array(df['WaitingSpawn'])
    spawn_masked = np.where(spawn > 100000, np.nan, spawn)
    plt.plot(time, spawn_masked, color='#9467bd', linewidth=2.0, linestyle='--', label='Очередь на спавн')
    plt.plot(time, df['WaitingReroute'], color='#ff7f0e', linewidth=2.0, label='Очередь MPR (Перестроения)')
    plt.title("Динамика очередей ожидания маршрута", fontsize=12, fontweight='bold')
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Количество агентов в очереди")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig_queues.png"))
    plt.close()

    # 4. Completed Trips (Завершенные поездки)
    plt.figure()
    plt.plot(time, df['CompletedTrips'], color='#8c564b', linewidth=2.0, label='Накопленные завершенные поездки')
    plt.title("Интегральная пропускная способность сети", fontsize=12, fontweight='bold')
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Завершенные поездки (ед.)")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig_completed_trips.png"))
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
    
    plt.title("Динамика Индекса Задержки TTI", fontsize=12, fontweight='bold')
    plt.xlabel("Время симуляции (с)")
    plt.ylabel("Индекс TTI")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#e0e0e0', loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig_tti.png"))
    plt.close()

    print(f"Успешно сгенерировано 5 графиков в папке: {output_dir}")

if __name__ == "__main__":
    csv_path = "/home/vaivanov/dev/bmstu/diplom-iu12-proj/magistracy-diplom-iu12/scripts/stats/run_02bca76a_bpr_on_prof_on_24b_300s_0a_1asf.csv"
    output_dir = "/home/vaivanov/dev/bmstu/diplom-iu12-proj/magistracy-diplom-iu12/docs/latex/assets/images"
    generate_plots(csv_path, output_dir)
