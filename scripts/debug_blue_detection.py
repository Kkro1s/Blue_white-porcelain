import requests
from PIL import Image
import io
import numpy as np
import colorsys

def rgb_to_hsv(rgb):
    """将RGB转换为HSV"""
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (h * 360, s, v)  # 转换为0-360度

def analyze_image(image_url):
    """分析图片的颜色分布"""
    try:
        response = requests.get(image_url, timeout=15, verify=False)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 缩小图片
        max_size = 400
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        img_array = np.array(image)
        pixels = img_array.reshape(-1, 3)
        
        # 分析所有像素的HSV值
        hsv_values = []
        blue_pixels = []
        for pixel in pixels:
            h, s, v = rgb_to_hsv(pixel)
            hsv_values.append((h, s, v))
            
            # 检查是否可能是蓝色
            if 180 <= h <= 280 and s > 0.1 and v > 0.1:
                blue_pixels.append(pixel)
        
        hsv_array = np.array(hsv_values)
        
        print(f"\n图片: {image_url}")
        print(f"总像素数: {len(pixels)}")
        print(f"可能的蓝色像素数: {len(blue_pixels)}")
        print(f"\nHSV统计:")
        print(f"  色相(H)范围: {hsv_array[:, 0].min():.1f} - {hsv_array[:, 0].max():.1f}")
        print(f"  饱和度(S)范围: {hsv_array[:, 1].min():.2f} - {hsv_array[:, 1].max():.2f}")
        print(f"  亮度(V)范围: {hsv_array[:, 2].min():.2f} - {hsv_array[:, 2].max():.2f}")
        
        # 检查蓝色范围的像素
        blue_h = hsv_array[(hsv_array[:, 0] >= 200) & (hsv_array[:, 0] <= 260)]
        if len(blue_h) > 0:
            print(f"\n色相在200-260度的像素数: {len(blue_h)}")
            print(f"  这些像素的平均饱和度: {blue_h[:, 1].mean():.2f}")
            print(f"  这些像素的平均亮度: {blue_h[:, 2].mean():.2f}")
        
        # 检查更宽的蓝色范围
        wide_blue = hsv_array[(hsv_array[:, 0] >= 180) & (hsv_array[:, 0] <= 280)]
        if len(wide_blue) > 0:
            print(f"\n色相在180-280度的像素数: {len(wide_blue)}")
            print(f"  这些像素的平均饱和度: {wide_blue[:, 1].mean():.2f}")
            print(f"  这些像素的平均亮度: {wide_blue[:, 2].mean():.2f}")
        
        # 检查可能的蓝色RGB值
        if len(blue_pixels) > 0:
            blue_array = np.array(blue_pixels)
            print(f"\n可能的蓝色RGB样本:")
            print(f"  R范围: {blue_array[:, 0].min()} - {blue_array[:, 0].max()}")
            print(f"  G范围: {blue_array[:, 1].min()} - {blue_array[:, 1].max()}")
            print(f"  B范围: {blue_array[:, 2].min()} - {blue_array[:, 2].max()}")
            print(f"  样本RGB值: {blue_array[:5].tolist()}")
        
    except Exception as e:
        print(f"错误: {str(e)}")

# 测试几张没有检测到蓝色的图片
test_urls = [
    "https://images.metmuseum.org/CRDImages/as/original/29628.jpg",  # ID 2
    "https://images.metmuseum.org/CRDImages/as/original/DP222234.jpg",  # ID 3
    "https://images.metmuseum.org/CRDImages/as/original/28225.jpg",  # ID 4
]

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

for url in test_urls:
    analyze_image(url)





