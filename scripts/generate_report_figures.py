#!/usr/bin/env python3
import os
import csv
import sys
import glob
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OPACITY_SIGMA=0.30

def parse_args():
    parser = argparse.ArgumentParser(description="Генерация графиков отчета по 24-часовым циклам симуляции.")
    parser.add_argument("--smooth", action="store_true", default=True, help="Применять скользящее среднее (по умолчанию: включено).")
    parser.add_argument("--no-smooth", dest="smooth", action="store_false", help="Отключить сглаживание (строить сырые точки).")
    parser.add_argument("--window", type=int, default=15, help="Размер окна скользящего среднего (по умолчанию: 15 точек).")
    parser.add_argument("--opacity", type=float, default=OPACITY_SIGMA, help="Прозрачность (alpha) области дисперсии (по умолчанию: 0.20).")
    return parser.parse_args()

def rolling_stats(arr, window):
    if window <= 1 or len(arr) < window:
        return arr, np.zeros_like(arr)
    mean = np.zeros_like(arr)
    std = np.zeros_like(arr)
    half = window // 2
    n = len(arr)
    for i in range(n):
        s = max(0, i - half)
        e = min(n, i + half + 1)
        sub = arr[s:e]
        mean[i] = np.mean(sub)
        std[i] = np.std(sub)
    return mean, std

def generate_figures():
    args = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "data", "logs", "R-D-2.5"))
    output_dir = os.path.abspath(os.path.join(script_dir, "..", "assets", "images"))
    
    os.makedirs(output_dir, exist_ok=True)
    
    files1 = glob.glob(os.path.join(log_dir, "*170h_130s*bpr*.csv"))
    files2 = glob.glob(os.path.join(log_dir, "*48h_300s*bpr*.csv"))
    
    if not files1 or not files2:
        print(f"[-] Ошибка: не найдены CSV-файлы в {log_dir}")
        sys.exit(1)
        
    file1 = files1[0]
    file2 = files2[0]
        
    def load_and_filter_24h(filepath, start_hour, end_hour):
        data = {
            "SimTime": [], "TTI": [], "ActiveAgents": [], "WaitingReroute": [],
            "CompletedTrips": [], "VirtualBuffer": [], "WaitingSpillbackQueue": [], "WaitingSpawn": []
        }
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                t_sec = float(row["SimTime"])
                t_h = t_sec / 3600.0
                if start_hour <= t_h <= end_hour:
                    data["SimTime"].append(t_h - start_hour)
                    data["TTI"].append(float(row["TTI"]))
                    data["ActiveAgents"].append(float(row["ActiveAgents"]))
                    data["WaitingReroute"].append(float(row["WaitingReroute"]))
                    data["CompletedTrips"].append(float(row["CompletedTrips"]))
                    data["VirtualBuffer"].append(float(row.get("VirtualBuffer", 0)))
                    data["WaitingSpillbackQueue"].append(float(row.get("WaitingSpillbackQueue", 0)))
                    data["WaitingSpawn"].append(float(row.get("WaitingSpawn", 0)))
                    
        for k in data:
            data[k] = np.array(data[k])
        return data

    # Сутки 7 (144-168ч) для файла 130с, сутки 2 (24-48ч) для файла 300с
    d1 = load_and_filter_24h(file1, 144.0, 168.0)
    d2 = load_and_filter_24h(file2, 24.0, 48.0)

    w = args.window if args.smooth else 1
    opacity = args.opacity

    # Единая палитра и стили
    COLOR_CONF1 = '#1f77b4'       # Синий (Конфигурация 1 / 130 с)
    COLOR_CONF2 = '#d62728'       # Красный (Конфигурация 2 / 300 с)
    COLOR_TOTAL = '#222222'       # Угольно-черный (всего активных N_active)
    COLOR_FREE = '#2ca02c'        # Зеленый (Свободный поток S2)
    COLOR_QUEUE = '#d62728'       # Красный (Очередь затора S3)
    COLOR_BUFFER = '#9467bd'      # Фиолетовый (Виртуальный буфер SUMO S4)
    COLOR_ROUTER = '#ff7f0e'      # Оранжевый (Ожидание маршрутизации S1)

    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
    plt.rcParams['axes.edgecolor'] = '#444444'
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['grid.color'] = '#e0e0e0'
    plt.rcParams['grid.linestyle'] = '-'
    plt.rcParams['grid.linewidth'] = 0.5

    # ---------------------------------------------------------
    # Рисунок 1: Сравнение динамики TTI на суточном цикле (130с vs 300с)
    # ---------------------------------------------------------
    m1_tti, s1_tti = rolling_stats(d1["TTI"], w)
    m2_tti, s2_tti = rolling_stats(d2["TTI"], w)

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)
    ax.plot(d1["SimTime"], m1_tti, color=COLOR_CONF1, linewidth=2.0, linestyle='-', label='Конфигурация 1 (130 с, TTI_avg = 1.89)')
    if args.smooth:
        ax.fill_between(d1["SimTime"], np.maximum(1.0, m1_tti - s1_tti), m1_tti + s1_tti, 
                        color=COLOR_CONF1, alpha=opacity, edgecolor='none', linewidth=0)

    ax.plot(d2["SimTime"], m2_tti, color=COLOR_CONF2, linewidth=2.0, linestyle='-', label='Конфигурация 2 (300 с, TTI_avg = 2.25)')
    if args.smooth:
        ax.fill_between(d2["SimTime"], np.maximum(1.0, m2_tti - s2_tti), m2_tti + s2_tti, 
                        color=COLOR_CONF2, alpha=opacity, edgecolor='none', linewidth=0)

    ax.axhline(1.0, color='#7f7f7f', linewidth=1.0, linestyle='-', alpha=0.8, label='Эталон свободного потока (TTI = 1.00)')

    ax.set_title("Динамика индекса задержки TTI на установившемся 24-часовом цикле", fontsize=11, fontweight='bold', pad=10)
    ax.set_xlabel("Время суток (ч)", fontsize=10)
    ax.set_ylabel("Индекс задержки TTI", fontsize=10)
    ax.set_xlim(0, 24)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.grid(True)
    ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    fig_tti_path = os.path.join(output_dir, "fig_tti_24h.png")
    plt.savefig(fig_tti_path, bbox_inches='tight')
    plt.close()
    print(f"[+] Сохранен {fig_tti_path}")

    # ---------------------------------------------------------
    # Рисунок 2: Структура очередей заторов (2 панели: 130 с vs 300 с)
    # ---------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5), dpi=300, sharex=True)

    # Панель А: 130 с
    m1_q, s1_q = rolling_stats(d1["WaitingSpillbackQueue"], w)
    m1_b, s1_b = rolling_stats(d1["VirtualBuffer"], w)
    m1_r, s1_r = rolling_stats(d1["WaitingReroute"] + d1["WaitingSpawn"], w)

    ax1.plot(d1["SimTime"], m1_q, color=COLOR_QUEUE, linewidth=2.0, linestyle='-', label='Стояние в очереди затора S3')
    if args.smooth:
        ax1.fill_between(d1["SimTime"], np.maximum(0, m1_q - s1_q), m1_q + s1_q, 
                        color=COLOR_QUEUE, alpha=opacity, edgecolor='none', linewidth=0)

    ax1.plot(d1["SimTime"], m1_b, color=COLOR_BUFFER, linewidth=1.8, linestyle='-', label='Виртуальный буфер SUMO S4')
    if args.smooth:
        ax1.fill_between(d1["SimTime"], np.maximum(0, m1_b - s1_b), m1_b + s1_b, 
                        color=COLOR_BUFFER, alpha=opacity, edgecolor='none', linewidth=0)

    ax1.plot(d1["SimTime"], m1_r, color=COLOR_ROUTER, linewidth=1.6, linestyle='-', label='Ожидание назначения маршрута S1')

    ax1.set_title("а) Динамика очередей и буфера заторов при таймауте 130 с (Конфигурация 1)", fontsize=10.5, fontweight='bold', pad=8)
    ax1.set_ylabel("Количество ТС (ед)", fontsize=10)
    ax1.grid(True)
    ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    # Панель Б: 300 с
    m2_q, s2_q = rolling_stats(d2["WaitingSpillbackQueue"], w)
    m2_b, s2_b = rolling_stats(d2["VirtualBuffer"], w)
    m2_r, s2_r = rolling_stats(d2["WaitingReroute"] + d2["WaitingSpawn"], w)

    ax2.plot(d2["SimTime"], m2_q, color=COLOR_QUEUE, linewidth=2.0, linestyle='-', label='Стояние в очереди затора S3')
    if args.smooth:
        ax2.fill_between(d2["SimTime"], np.maximum(0, m2_q - s2_q), m2_q + s2_q, 
                        color=COLOR_QUEUE, alpha=opacity, edgecolor='none', linewidth=0)

    ax2.plot(d2["SimTime"], m2_b, color=COLOR_BUFFER, linewidth=1.8, linestyle='-', label='Виртуальный буфер SUMO S4')
    if args.smooth:
        ax2.fill_between(d2["SimTime"], np.maximum(0, m2_b - s2_b), m2_b + s2_b, 
                        color=COLOR_BUFFER, alpha=opacity, edgecolor='none', linewidth=0)

    ax2.plot(d2["SimTime"], m2_r, color=COLOR_ROUTER, linewidth=1.6, linestyle='-', label='Ожидание назначения маршрута S1')

    ax2.set_title("б) Динамика очередей и буфера заторов при таймауте 300 с (Конфигурация 2)", fontsize=10.5, fontweight='bold', pad=8)
    ax2.set_xlabel("Время суток (ч)", fontsize=10)
    ax2.set_ylabel("Количество ТС (ед)", fontsize=10)
    ax2.set_xlim(0, 24)
    ax2.set_xticks(np.arange(0, 25, 3))
    ax2.grid(True)
    ax2.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    fig_queues_path = os.path.join(output_dir, "fig_queues_24h.png")
    plt.savefig(fig_queues_path, bbox_inches='tight')
    plt.close()
    print(f"[+] Сохранен {fig_queues_path}")

    # ---------------------------------------------------------
    # Рисунок 3: Распределение агентов по дискретным состояниям автомата
    # ---------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5), dpi=300, sharex=True)

    d1_waiting_route = d1["WaitingSpawn"] + d1["WaitingReroute"]
    d1_free_flow = np.maximum(0, d1["ActiveAgents"] - d1["WaitingSpillbackQueue"] - d1["VirtualBuffer"] - d1_waiting_route)

    d2_waiting_route = d2["WaitingSpawn"] + d2["WaitingReroute"]
    d2_free_flow = np.maximum(0, d2["ActiveAgents"] - d2["WaitingSpillbackQueue"] - d2["VirtualBuffer"] - d2_waiting_route)

    # Панель А: 130 с
    m1_act, _ = rolling_stats(d1["ActiveAgents"], w)
    m1_ff, s1_ff = rolling_stats(d1_free_flow, w)
    m1_q, s1_q = rolling_stats(d1["WaitingSpillbackQueue"], w)
    m1_b, s1_b = rolling_stats(d1["VirtualBuffer"], w)
    m1_wr, _ = rolling_stats(d1_waiting_route, w)

    ax1.plot(d1["SimTime"], m1_act, color=COLOR_TOTAL, linewidth=2.2, linestyle='-', label='Всего активных на сети (N_active)')
    ax1.plot(d1["SimTime"], m1_ff, color=COLOR_FREE, linewidth=2.0, linestyle='-', label='Свободный поток S2 (движение со скоростью BPR)')
    if args.smooth:
        ax1.fill_between(d1["SimTime"], np.maximum(0, m1_ff - s1_ff), m1_ff + s1_ff, 
                        color=COLOR_FREE, alpha=opacity, edgecolor='none', linewidth=0)

    ax1.plot(d1["SimTime"], m1_q, color=COLOR_QUEUE, linewidth=1.8, linestyle='-', label='Очередь затора S3 (простой на стоп-линии)')
    if args.smooth:
        ax1.fill_between(d1["SimTime"], np.maximum(0, m1_q - s1_q), m1_q + s1_q, 
                        color=COLOR_QUEUE, alpha=opacity, edgecolor='none', linewidth=0)

    ax1.plot(d1["SimTime"], m1_b, color=COLOR_BUFFER, linewidth=1.8, linestyle='-', label='Буфер SUMO S4 (разрешение взаимоблокировок)')
    if args.smooth:
        ax1.fill_between(d1["SimTime"], np.maximum(0, m1_b - s1_b), m1_b + s1_b, 
                        color=COLOR_BUFFER, alpha=opacity, edgecolor='none', linewidth=0)

    ax1.plot(d1["SimTime"], m1_wr, color=COLOR_ROUTER, linewidth=1.6, linestyle='-', label='Ожидание пути S1 (запрос маршрута)')

    ax1.set_title("а) Распределение агентов по состояниям при таймауте 130 с (Конфигурация 1)", fontsize=10.5, fontweight='bold', pad=8)
    ax1.set_ylabel("Количество ТС (ед)", fontsize=10)
    ax1.grid(True)
    ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    # Панель Б: 300 с
    m2_act, _ = rolling_stats(d2["ActiveAgents"], w)
    m2_ff, s2_ff = rolling_stats(d2_free_flow, w)
    m2_q, s2_q = rolling_stats(d2["WaitingSpillbackQueue"], w)
    m2_b, s2_b = rolling_stats(d2["VirtualBuffer"], w)
    m2_wr, _ = rolling_stats(d2_waiting_route, w)

    ax2.plot(d2["SimTime"], m2_act, color=COLOR_TOTAL, linewidth=2.2, linestyle='-', label='Всего активных на сети (N_active)')
    ax2.plot(d2["SimTime"], m2_ff, color=COLOR_FREE, linewidth=2.0, linestyle='-', label='Свободный поток S2 (движение со скоростью BPR)')
    if args.smooth:
        ax2.fill_between(d2["SimTime"], np.maximum(0, m2_ff - s2_ff), m2_ff + s2_ff, 
                        color=COLOR_FREE, alpha=opacity, edgecolor='none', linewidth=0)

    ax2.plot(d2["SimTime"], m2_q, color=COLOR_QUEUE, linewidth=1.8, linestyle='-', label='Очередь затора S3 (простой на стоп-линии)')
    if args.smooth:
        ax2.fill_between(d2["SimTime"], np.maximum(0, m2_q - s2_q), m2_q + s2_q, 
                        color=COLOR_QUEUE, alpha=opacity, edgecolor='none', linewidth=0)

    ax2.plot(d2["SimTime"], m2_b, color=COLOR_BUFFER, linewidth=1.8, linestyle='-', label='Буфер SUMO S4 (разрешение взаимоблокировок)')
    if args.smooth:
        ax2.fill_between(d2["SimTime"], np.maximum(0, m2_b - s2_b), m2_b + s2_b, 
                        color=COLOR_BUFFER, alpha=opacity, edgecolor='none', linewidth=0)

    ax2.plot(d2["SimTime"], m2_wr, color=COLOR_ROUTER, linewidth=1.6, linestyle='-', label='Ожидание пути S1 (запрос маршрута)')

    ax2.set_title("б) Распределение агентов по состояниям при таймауте 300 с (Конфигурация 2)", fontsize=10.5, fontweight='bold', pad=8)
    ax2.set_xlabel("Время суток (ч)", fontsize=10)
    ax2.set_ylabel("Количество ТС (ед)", fontsize=10)
    ax2.set_xlim(0, 24)
    ax2.set_xticks(np.arange(0, 25, 3))
    ax2.grid(True)
    ax2.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    fig_zones_path = os.path.join(output_dir, "fig_zones_24h.png")
    plt.savefig(fig_zones_path, bbox_inches='tight')
    plt.close()
    print(f"[+] Сохранен {fig_zones_path}")

if __name__ == "__main__":
    generate_figures()
