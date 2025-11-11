import requests
from PIL import Image
import io
import numpy as np
import colorsys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def analyze_image(image_url):
    """分析图片的蓝色像素情况"""
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
        
        total_pixels = len(pixels)
        blue_count = len(blue_pixels)
        blue_ratio = blue_count / total_pixels if total_pixels > 0 else 0
        
        print(f"\n图片: {image_url}")
        print(f"总像素数: {total_pixels}")
        print(f"蓝色像素数: {blue_count} ({blue_ratio*100:.2f}%)")
        
        if blue_count > 0:
            # 检查HSV分布
            hsv_values = []
            for pixel in blue_pixels[:1000]:  # 只检查前1000个
                r, g, b = pixel
                r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
                h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
                hsv_values.append((h * 360, s, v))
            
            if hsv_values:
                hsv_array = np.array(hsv_values)
                print(f"HSV统计 (蓝色像素):")
                print(f"  色相范围: {hsv_array[:, 0].min():.1f} - {hsv_array[:, 0].max():.1f}")
                print(f"  饱和度范围: {hsv_array[:, 1].min():.2f} - {hsv_array[:, 1].max():.2f}")
                print(f"  亮度范围: {hsv_array[:, 2].min():.2f} - {hsv_array[:, 2].max():.2f}")
        
        return blue_count
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return 0

# 测试几张没有检测到蓝色的图片
test_urls = [
    "https://images.metmuseum.org/CRDImages/as/original/29628.jpg",  # ID 2
    "https://images.metmuseum.org/CRDImages/as/original/28225.jpg",  # ID 4
    "https://images.metmuseum.org/CRDImages/as/original/5559.jpg",    # ID 5
    "https://images.metmuseum.org/CRDImages/as/original/194368.jpg", # ID 11
    "https://images.metmuseum.org/CRDImages/as/original/29172.jpg",  # ID 13
]

for url in test_urls:
    analyze_image(url)





