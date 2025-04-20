import matplotlib.pyplot as plt
import numpy as np
from initialize_data import *
from read_data import *

data = initialize_data(carrier_df, station_df, order_df, tugboat_df, barge_df)
data_points, distances = create_station_points(data)

# Distances between stations (km)
#distances = [52, 11, 9, 13, 26, 22, 1, 1, 7, 10, 3, 4, 13, 13, 10, 2, 3, 1, 3, 1, 2, 1, 9, 6]

# Travel times between stations (hours) at 20 km/h
travel_times = [ 2.6, 0.55, 0.45, 0.65, 1.3, 1.1, 0.05, 0.05, 0.35, 0.5, 0.15, 0.2, 0.65, 0.65, 0.5, 0.1, 0.15, 0.05, 0.15, 0.05, 0.1, 0.05, 0.45, 0.3]
speeds = [d / t for d, t in zip(distances, travel_times)]  # คำนวณความเร็วเฉลี่ย (km/h)

# คำนวณ min/max date สำหรับ padding
all_dates = [p["enter_datetime"] for p in data_points] + [p["exit_datetime"] for p in data_points]
min_date = min(all_dates) - timedelta(minutes=3*60)
max_date = max(all_dates) + timedelta(minutes=3*60)

# ตั้งค่ากราฟแนวนอน
fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
ax.set_ylim(-1.5, 1.5)
ax.set_xlim(min_date, max_date)
ax.axhline(0, xmin=0.05, xmax=0.95, c='deeppink', zorder=1, linewidth=2)  # เส้นหลักของ timeline

# วาดจุดสำหรับแต่ละเหตุการณ์
for i, point in enumerate(data_points):
    ax.scatter(point["enter_datetime"], 0, s=200, c='palevioletred', zorder=2)
    ax.scatter(point["exit_datetime"], 0, s=200, c='palevioletred', zorder=2)
    
    # เส้นเชื่อมระหว่างจุด (ระยะเวลาทำงาน)
    ax.plot([point["enter_datetime"], point["exit_datetime"]], [0, 0], c='darkmagenta', linewidth=3, zorder=1)
    
    # ID ขนาดใหญ่ที่จุด
    ax.text(point["enter_datetime"], 0.2, f"{point['ID']}", fontsize=14, fontweight='bold', ha='center', va='bottom', color='black')

    # เส้นเชื่อมจุดไปที่ Label (Enter)
    ax.plot([point["enter_datetime"], point["enter_datetime"]], [0, 0.3], c='gray', linestyle='dotted', linewidth=1)
    ax.text(point["enter_datetime"], 0.4, f"{point['name']}\n{point['enter_datetime']:%d %b %Y %H:%M}",
            ha='center', fontfamily='serif', fontweight='bold', color='royalblue', fontsize=10)

    # เส้นเชื่อมจุดไปที่ Label (Exit)
    ax.plot([point["exit_datetime"], point["exit_datetime"]], [0, -0.3], c='gray', linestyle='dotted', linewidth=1)
    ax.text(point["exit_datetime"], -0.4, f"Exit {point['exit_datetime']:%d %b %Y %H:%M}",
            ha='center', fontfamily='serif', fontweight='bold', color='royalblue', fontsize=10)

    # แสดงข้อมูลระหว่างจุด (Travel) ถ้าไม่ใช่จุดสุดท้าย
    if i < len(distances):
        mid_time = point["exit_datetime"] + timedelta(hours=travel_times[i]) / 2  # เวลาตรงกลางระหว่างการเดินทาง
        ax.scatter(mid_time, 0, s=100, c='orange', zorder=2)

        # เส้นประจาก travel info ไปยัง timeline
        ax.plot([mid_time, mid_time], [0, -0.6], c='gray', linestyle='dashed', linewidth=1)

        # Label สำหรับ travel info
        ax.text(mid_time, -0.7, f"Travel {i+1}\nDistance: {distances[i]} km\nTime: {travel_times[i]} hr\nSpeed: {speeds[i]:.1f} km/h",
                ha='center', fontfamily='serif', fontweight='bold', color='darkgreen', fontsize=10)

# จัดการแกนและหัวข้อ
ax.spines["left"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title("Horizontal Travel Timeline with Travel Information", fontweight="bold", fontfamily='serif', fontsize=16, color='royalblue')

# แสดงผลลัพธ์
plt.show()
