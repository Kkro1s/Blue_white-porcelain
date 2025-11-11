import requests
from PIL import Image
import io
import numpy as np
import colorsys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def analyze_image_colors(image_url):
    """详细分析图片的颜色分布"""
    try:
        response = requests.get(image_url, timeout=15, verify=False)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        max_size = 400
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        img_array = np.array(image)
        pixels = img_array.reshape(-1, 3)
        
        # 分析所有像素的HSV
        hsv_list = []
        blueish_pixels = []  # B值最大的像素
        
        for pixel in pixels:
            r, g, b = pixel
            r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
            h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
            h_degrees = h * 360
            hsv_list.append((h_degrees, s, v))
            
            # 收集B值最大的像素（可能是蓝色）
            if b > r and b > g:
                blueish_pixels.append((r, g, b, h_degrees, s, v))
        
        hsv_array = np.array(hsv_list)
        
        print(f"\n图片: {image_url}")
        print(f"总像素数: {len(pixels)}")
        print(f"B值最大的像素数: {len(blueish_pixels)}")
        
        if len(blueish_pixels) > 0:
            blueish_array = np.array(blueish_pixels)
            print(f"\nB值最大的像素的HSV统计:")
            print(f"  色相范围: {blueish_array[:, 3].min():.1f} - {blueish_array[:, 3].max():.1f}")
            print(f"  饱和度范围: {blueish_array[:, 4].min():.2f} - {blueish_array[:, 4].max():.2f}")
            print(f"  亮度范围: {blueish_array[:, 5].min():.2f} - {blueish_array[:, 5].max():.2f}")
            
            # 检查在200-260度范围内的
            in_range = blueish_array[(blueish_array[:, 3] >= 200) & (blueish_array[:, 3] <= 260)]
            print(f"\n色相在200-260度的B值最大像素数: {len(in_range)}")
            if len(in_range) > 0:
                print(f"  这些像素的平均饱和度: {in_range[:, 4].mean():.2f}")
                print(f"  这些像素的平均亮度: {in_range[:, 5].mean():.2f}")
        
        print(f"\n全部像素的HSV统计:")
        print(f"  色相范围: {hsv_array[:, 0].min():.1f} - {hsv_array[:, 0].max():.1f}")
        print(f"  饱和度范围: {hsv_array[:, 1].min():.2f} - {hsv_array[:, 1].max():.2f}")
        print(f"  亮度范围: {hsv_array[:, 2].min():.2f} - {hsv_array[:, 2].max():.2f}")
        
    except Exception as e:
        print(f"错误: {str(e)}")

# 测试几张图片
test_urls = [
    "https://images.metmuseum.org/CRDImages/as/original/29628.jpg",  # ID 2
    "https://images.metmuseum.org/CRDImages/as/original/5559.jpg",    # ID 5
]

for url in test_urls:
    analyze_image_colors(url)





