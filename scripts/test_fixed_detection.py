import requests
from PIL import Image
import io
import numpy as np
from collections import Counter
import colorsys

def is_blue_color(rgb):
    """修复后的蓝色检测函数"""
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

def test_image(image_url):
    """测试单张图片"""
    try:
        response = requests.get(image_url, timeout=15, verify=False)
        response.raise_for_status()
        
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
        
        print(f"\n图片: {image_url}")
        print(f"总像素数: {len(pixels)}")
        print(f"蓝色像素数: {len(blue_pixels)}")
        
        if len(blue_pixels) > 0:
            quantized_pixels = []
            for r, g, b in blue_pixels:
                q_r = (r // 16) * 16
                q_g = (g // 16) * 16
                q_b = (b // 16) * 16
                quantized_pixels.append((q_r, q_g, q_b))
            
            color_counts = Counter(quantized_pixels)
            total_blue_pixels = len(blue_pixels)
            
            color_proportions = {}
            threshold = 0.05
            for color, count in color_counts.items():
                proportion = count / total_blue_pixels
                if proportion >= threshold:
                    color_proportions[color] = proportion
            
            if color_proportions:
                total_proportion = sum(color_proportions.values())
                if total_proportion > 0:
                    color_proportions = {k: v / total_proportion for k, v in color_proportions.items()}
            
            print(f"找到 {len(color_proportions)} 种蓝色（比例>=5%）")
            for (r, g, b), prop in sorted(color_proportions.items(), key=lambda x: x[1], reverse=True):
                print(f"  rgb({int(r)}, {int(g)}, {int(b)}): {prop:.2f}")
        else:
            print("未找到蓝色像素")
        
    except Exception as e:
        print(f"错误: {str(e)}")

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 测试之前检测不到的图片
test_urls = [
    "https://images.metmuseum.org/CRDImages/as/original/DP222234.jpg",  # ID 3 - 应该有蓝色
    "https://images.metmuseum.org/CRDImages/as/original/28225.jpg",  # ID 4 - 可能是灰度图
    "https://images.metmuseum.org/CRDImages/as/original/29628.jpg",  # ID 2 - 可能是灰度图
]

for url in test_urls:
    test_image(url)





