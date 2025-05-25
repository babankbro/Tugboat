import math
from datetime import datetime, timedelta

# ฟังก์ชันคำนวณระยะทางระหว่างจุดสองจุดโดยใช้สูตร Haversine
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # รัศมีของโลกเป็นกิโลเมตร
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # ระยะทางเป็นกิโลเมตร

# ฟังก์ชันจัดเรียงเรือบรรทุกสินค้าตามระยะทางจากเรือลากจูง
def sort_barges_by_distance(tugboat_lat, tugboat_lng, barges, barges_infos):
    # คำนวณระยะทางและเก็บในรูปแบบ tuple (barge, distance)
    barges_with_distance = []
    for barge in barges:
        binfo = barges_infos[barge.barge_id][-1]
        blocation = binfo['location']

        distance = haversine(tugboat_lat, tugboat_lng, blocation[0], blocation[1])
        barges_with_distance.append((barge, distance))

    # จัดเรียงตามระยะทางจากน้อยไปหามาก
    barges_with_distance.sort(key=lambda x: x[1])

    # แยก barge ออกจากระยะทางหลังการจัดเรียง
    sorted_barges = [barge for barge, distance in barges_with_distance]
    return sorted_barges

def sort_barges_by_river_distance(river_km, barges):
    barges_with_distance = []
    for barge in barges:
        distance = abs(barge.river_km - river_km)
        barges_with_distance.append((barge, distance))

    # จัดเรียงตามระยะทางจากน้อยไปหามาก
    barges_with_distance.sort(key=lambda x: x[1])

    # แยก barge ออกจากระยะทางหลังการจัดเรียง
    sorted_barges = [barge for barge, distance in barges_with_distance]
    return sorted_barges



def get_previous_quarter_hour(dt: datetime) -> datetime:
    if dt.minute % 15 == 0:  # If it's already a quarter hour
        return dt
    minute = (dt.minute // 15) * 15  # Round down to the nearest quarter
    return dt.replace(minute=minute, second=0, microsecond=0)

def get_next_quarter_hour(dt: datetime) -> datetime:
    if dt.minute % 15 == 0 and dt.second == 0 and dt.microsecond == 0:  # Check if exactly at quarter hour
        return dt
    minute = ((dt.minute // 15) + 1) * 15
    if minute == 60:
        dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        dt = dt.replace(minute=minute, second=0, microsecond=0)
    return dt