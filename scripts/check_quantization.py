import requests
from PIL import Image
import io
import numpy as np
from collections import Counter
import colorsys

def is_blue_color(rgb):
    r, g, b = rgb
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    h_degrees = h * 360
    
    is_blue_hue = 200 <= h_degrees <= 260
    has_color = s > 0.05
    is_bright_enough = v > 0.15
    is_blueish = b > r and b > g
    
    if is_blue_hue and has_color and is_bright_enough and is_blueish:
        return True
    return False

url = "https://images.metmuseum.org/CRDImages/as/original/DP222234.jpg"

response = requests.get(url, timeout=15, verify=False)
image = Image.open(io.BytesIO(response.content))
if image.mode != 'RGB':
    image = image.convert('RGB')

max_size = 800
if max(image.size) > max_size:
    ratio = max_size / max(image.size)
    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
    image = image.resize(new_size, Image.Resampling.LANCZOS)

img_array = np.array(image)
pixels = img_array.reshape(-1, 3)

blue_pixels = []
for pixel in pixels:
    if is_blue_color(pixel):
        blue_pixels.append(tuple(pixel))

print(f"蓝色像素总数: {len(blue_pixels)}")

# 量化 - 使用32步长
quantized_pixels = []
for r, g, b in blue_pixels:
    q_r = (r // 32) * 32
    q_g = (g // 32) * 32
    q_b = (b // 32) * 32
    quantized_pixels.append((q_r, q_g, q_b))

color_counts = Counter(quantized_pixels)
total_blue_pixels = len(blue_pixels)

print(f"\n量化后的不同颜色数: {len(color_counts)}")
print(f"\n前20种最常见的颜色及其比例:")

for i, (color, count) in enumerate(color_counts.most_common(20), 1):
    proportion = count / total_blue_pixels
    print(f"{i}. rgb{color}: {proportion:.4f} ({count}/{total_blue_pixels})")

# 检查有多少颜色达到5%阈值
threshold = 0.05
above_threshold = {color: count for color, count in color_counts.items() if count / total_blue_pixels >= threshold}
print(f"\n达到5%阈值的颜色数: {len(above_threshold)}")

# 检查不同阈值的情况
for thresh in [0.01, 0.02, 0.03, 0.05, 0.10]:
    above = {color: count for color, count in color_counts.items() if count / total_blue_pixels >= thresh}
    total_prop = sum(count / total_blue_pixels for count in above.values())
    print(f"阈值 {thresh*100}%: {len(above)} 种颜色，覆盖 {total_prop*100:.1f}% 的蓝色像素")

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

