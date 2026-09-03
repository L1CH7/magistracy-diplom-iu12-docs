#!/usr/bin/env python3
import os
import csv
import sys
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_figures():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "data", "logs", "R-D-2.5"))
    output_dir = os.path.abspath(os.path.join(script_dir, "..", "assets", "images"))
    
    os.makedirs(output_dir, exist_ok=True)
    
    file1 = os.path.join(log_dir, "run_27-07-2026_170h_130s_conttimer_7c555245_bpr_on_prof_on_24b_300s_70000a_1asf.csv")
    file2 = os.path.join(log_dir, "run_28-07-2026_48h_300s_conttimer_740a967b_bpr_on_prof_on_24b_300s_70000a_1asf.csv")
    
    if not os.path.exists(file1) or not os.path.exists(file2):
        print(f"Error: Could not find telemetry files in {log_dir}")
        sys.exit(1)
        
    def load_and_filter_24h(filepath, start_hour, end_hour):
        data = {
            "SimTime": [], "TTI": [], "ActiveAgents": [], "WaitingReroute": [],
            "CompletedTrips": [], "BlackZones": [], "RedZones": [], "YellowZones": [],
            "GreenZones": [], "VirtualBuffer": [], "WaitingSpillbackQueue": [], "WaitingSpawn": []
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
                    data["BlackZones"].append(float(row["BlackZones"]))
                    data["RedZones"].append(float(row["RedZones"]))
                    data["YellowZones"].append(float(row["YellowZones"]))
                    data["GreenZones"].append(float(row.get("GreenZones", 0)))
                    data["VirtualBuffer"].append(float(row.get("VirtualBuffer", 0)))
                    data["WaitingSpillbackQueue"].append(float(row.get("WaitingSpillbackQueue", 0)))
                    data["WaitingSpawn"].append(float(row.get("WaitingSpawn", 0)))
                    
        for k in data:
            data[k] = np.array(data[k])
        return data

    # Extract last 24h cycle
    # For 170h test (file1): day 7 -> 144h to 168h
    # For 48h test (file2): day 2 -> 24h to 48h
    d1 = load_and_filter_24h(file1, 144.0, 168.0)
    d2 = load_and_filter_24h(file2, 24.0, 48.0)

    # Configure plot styling
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
    plt.rcParams['axes.edgecolor'] = '#444444'
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['grid.color'] = '#cccccc'
    plt.rcParams['grid.linestyle'] = ':'

    # ---------------------------------------------------------
    # Figure 1: Travel Time Index (TTI) Comparison over 24h cycle
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.plot(d1["SimTime"], d1["TTI"], color='#1f77b4', linewidth=2.0, label='Конфигурация 1 (130 с conttimer, TTI_avg = 1.89)')
    ax.plot(d2["SimTime"], d2["TTI"], color='#d62728', linewidth=2.0, linestyle='--', label='Конфигурация 2 (300 с conttimer, TTI_avg = 2.25)')
    ax.axhline(1.0, color='gray', linestyle='-.', linewidth=0.8, alpha=0.7, label='Свободный поток (TTI = 1.0)')

    ax.set_title("Динамика индекса задержки TTI на установившемся 24-часовом цикле", fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel("Часы суток (ч)", fontsize=11)
    ax.set_ylabel("Коэффициент TTI", fontsize=11)
    ax.set_xlim(0, 24)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=10)

    plt.tight_layout()
    fig_tti_path = os.path.join(output_dir, "fig_tti_24h.png")
    plt.savefig(fig_tti_path, bbox_inches='tight')
    plt.close()
    print(f"[+] Saved {fig_tti_path}")

    # ---------------------------------------------------------
    # Figure 2: Queue Accumulation Breakdown (2 Panels: 130s vs 300s)
    # ---------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), dpi=300, sharex=True)

    # Panel A: 130s conttimer queues
    ax1.plot(d1["SimTime"], d1["WaitingSpillbackQueue"], color='#d62728', linewidth=2.0, label='Застряли на физической сети (v = 0 км/ч)')
    ax1.plot(d1["SimTime"], d1["VirtualBuffer"], color='#9467bd', linewidth=1.8, label='Виртуальный буфер SUMO (телепортация)')
    ax1.plot(d1["SimTime"], d1["WaitingReroute"], color='#ff7f0e', linewidth=1.5, linestyle='--', label='Очередь перестроения MPR')
    ax1.plot(d1["SimTime"], d1["WaitingSpawn"], color='#bcbd22', linewidth=1.2, linestyle=':', label='Очередь спавна')

    ax1.set_title("а) Структура очередей заторов при T_teleport = 130 с (Конфигурация 1)", fontsize=11, fontweight='bold', pad=8)
    ax1.set_ylabel("Количество агентов (ед)", fontsize=10)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    # Panel B: 300s conttimer queues
    ax2.plot(d2["SimTime"], d2["WaitingSpillbackQueue"], color='#d62728', linewidth=2.0, label='Застряли на физической сети (v = 0 км/ч)')
    ax2.plot(d2["SimTime"], d2["VirtualBuffer"], color='#9467bd', linewidth=1.8, label='Виртуальный буфер SUMO (телепортация)')
    ax2.plot(d2["SimTime"], d2["WaitingReroute"], color='#ff7f0e', linewidth=1.5, linestyle='--', label='Очередь перестроения MPR')
    ax2.plot(d2["SimTime"], d2["WaitingSpawn"], color='#bcbd22', linewidth=1.2, linestyle=':', label='Очередь спавна')

    ax2.set_title("б) Структура очередей заторов при T_teleport = 300 с (Конфигурация 2)", fontsize=11, fontweight='bold', pad=8)
    ax2.set_xlabel("Часы суток (ч)", fontsize=11)
    ax2.set_ylabel("Количество агентов (ед)", fontsize=10)
    ax2.set_xlim(0, 24)
    ax2.set_xticks(np.arange(0, 25, 3))
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    fig_queues_path = os.path.join(output_dir, "fig_queues_24h.png")
    plt.savefig(fig_queues_path, bbox_inches='tight')
    plt.close()
    print(f"[+] Saved {fig_queues_path}")

    # ---------------------------------------------------------
    # Figure 3: Road Network Congestion Breakdown (Red/Yellow/Black)
    # ---------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), dpi=300, sharex=True)

    # Panel A: 130s conttimer zones
    ax1.plot(d1["SimTime"], d1["RedZones"], color='#d62728', linewidth=1.8, label='Красные зоны (100% емкости ребра)')
    ax1.plot(d1["SimTime"], d1["YellowZones"], color='#e377c2', linewidth=1.5, linestyle='--', label='Желтые зоны (плотный поток)')
    ax1.plot(d1["SimTime"], d1["BlackZones"], color='#800080', linewidth=1.5, linestyle=':', label='Черные зоны (заторы узлов)')

    ax1.set_title("а) Загруженность ребер сети при T_teleport = 130 с (Конфигурация 1)", fontsize=11, fontweight='bold', pad=8)
    ax1.set_ylabel("Количество ребер сети", fontsize=10)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    # Panel B: 300s conttimer zones
    ax2.plot(d2["SimTime"], d2["RedZones"], color='#d62728', linewidth=1.8, label='Красные зоны (100% емкости ребра)')
    ax2.plot(d2["SimTime"], d2["YellowZones"], color='#e377c2', linewidth=1.5, linestyle='--', label='Желтые зоны (плотный поток)')
    ax2.plot(d2["SimTime"], d2["BlackZones"], color='#800080', linewidth=1.5, linestyle=':', label='Черные зоны (заторы узлов)')

    ax2.set_title("б) Загруженность ребер сети при T_teleport = 300 с (Конфигурация 2)", fontsize=11, fontweight='bold', pad=8)
    ax2.set_xlabel("Часы суток (ч)", fontsize=11)
    ax2.set_ylabel("Количество ребер сети", fontsize=10)
    ax2.set_xlim(0, 24)
    ax2.set_xticks(np.arange(0, 25, 3))
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    fig_zones_path = os.path.join(output_dir, "fig_zones_24h.png")
    plt.savefig(fig_zones_path, bbox_inches='tight')
    plt.close()
    print(f"[+] Saved {fig_zones_path}")

    print("All 24h figures successfully generated!")

if __name__ == "__main__":
    generate_figures()
