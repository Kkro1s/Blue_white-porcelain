import csv
import requests
from PIL import Image
import io
import numpy as np
from collections import Counter
from urllib.parse import urlparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import colorsys
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def is_blue_color(rgb):
    """
    判断一个RGB颜色是否属于蓝色范畴
    使用HSV色相来判断，蓝色通常在180-280度之间（包括青色和蓝紫色）
    """
    r, g, b = rgb
    # 转换为HSV（使用colorsys库确保准确性）
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    
    # 转换为0-360度的色相
    h_degrees = h * 360
    
    # 蓝色色相范围：200-260度（按用户要求）
    # 进一步放宽条件以检测更多蓝色：
    # - 饱和度 > 0.02（进一步降低，检测淡蓝色）
    # - 亮度 > 0.10（进一步降低，检测暗蓝色）
    # - 同时确保B值大于R和G值（这是蓝色的特征）
    # - 或者如果是灰度图（s接近0），但B值明显大于R和G，也可能是蓝色
    is_blue_hue = 200 <= h_degrees <= 260
    has_low_color = s > 0.02  # 进一步降低饱和度阈值
    is_bright_enough = v > 0.10  # 进一步降低亮度阈值
    is_blueish = b > r and b > g  # B值最大，确保是偏蓝的颜色
    
    # 对于灰度图或低饱和度的情况，如果B值大于R和G，也可能是蓝色调
    # 放宽条件：只要B值大于等于R和G，且饱和度很低，就认为是蓝色调
    is_grayish_blue = s <= 0.15 and b >= r and b >= g and (b > r or b > g)  # 灰度但B值更大或相等
    
    # 主要检测：标准的蓝色检测
    if is_blue_hue and has_low_color and is_bright_enough and is_blueish:
        return True
    
    # 次要检测：灰度蓝色调
    if is_grayish_blue:
        return True
    
    return False

def extract_blue_colors_from_image(image_url):
    """
    从图片URL下载图片并提取蓝色相关的RGB颜色及其比例
    """
    try:
        # 下载图片（跳过SSL证书验证以支持britishmuseum.org等网站）
        response = requests.get(image_url, timeout=15, verify=False)
        response.raise_for_status()
        
        # 打开图片
        image = Image.open(io.BytesIO(response.content))
        
        # 转换为RGB模式（如果不是的话）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 为了加快处理速度，如果图片太大则缩小（保持宽高比，最大边不超过800像素）
        max_size = 800
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 将图片转换为numpy数组
        img_array = np.array(image)
        
        # 获取所有像素的RGB值
        pixels = img_array.reshape(-1, 3)
        
        # 过滤出蓝色像素
        blue_pixels = []
        for pixel in pixels:
            if is_blue_color(pixel):
                blue_pixels.append(tuple(pixel))
        
        # 如果没有检测到蓝色，尝试提取B值最大的像素（作为蓝色调）
        if len(blue_pixels) == 0:
            # 提取所有B值大于等于R和G的像素
            blueish_pixels = []
            for pixel in pixels:
                r, g, b = pixel
                if b >= r and b >= g:  # B值最大或相等
                    blueish_pixels.append(tuple(pixel))
            
            if len(blueish_pixels) > 0:
                blue_pixels = blueish_pixels
            else:
                return {}
        
        # 统计每种蓝色的数量（对RGB值进行量化以减少颜色种类）
        # 使用较粗糙的量化（步长为32），以便更好地集中相似颜色，使主要颜色达到5%阈值
        quantized_pixels = []
        for r, g, b in blue_pixels:
            # 量化到32的倍数（0-255范围内），这样可以有8个级别
            q_r = (r // 32) * 32
            q_g = (g // 32) * 32
            q_b = (b // 32) * 32
            quantized_pixels.append((q_r, q_g, q_b))
        
        # 统计颜色频率
        color_counts = Counter(quantized_pixels)
        total_blue_pixels = len(blue_pixels)
        
        # 计算比例并过滤掉比例小于0.05的颜色
        # 如果没有颜色达到5%阈值，降低到3%以确保至少有一些颜色
        color_proportions = {}
        threshold = 0.05  # 首选阈值：5%
        
        for color, count in color_counts.items():
            proportion = count / total_blue_pixels
            if proportion >= threshold:
                color_proportions[color] = proportion
        
        # 如果没有任何颜色达到5%阈值，降低到3%
        if not color_proportions:
            threshold = 0.03
            for color, count in color_counts.items():
                proportion = count / total_blue_pixels
                if proportion >= threshold:
                    color_proportions[color] = proportion
        
        # 如果过滤后还有颜色，重新归一化比例
        if color_proportions:
            total_proportion = sum(color_proportions.values())
            if total_proportion > 0:
                color_proportions = {k: v / total_proportion for k, v in color_proportions.items()}
        
        return color_proportions
    
    except Exception as e:
        print(f"处理图片 {image_url} 时出错: {str(e)}")
        return {}

def format_rgb_color_string(color_proportions):
    """
    将颜色比例字典格式化为字符串
    格式：rgb(38, 90, 196): 0.2; rgb(38, 90, 176): 0.8
    """
    if not color_proportions:
        return ""
    
    # 按比例排序（从高到低）
    sorted_colors = sorted(color_proportions.items(), key=lambda x: x[1], reverse=True)
    
    formatted_parts = []
    for (r, g, b), proportion in sorted_colors:
        formatted_parts.append(f"rgb({int(r)}, {int(g)}, {int(b)}): {proportion:.2f}")
    
    return "; ".join(formatted_parts)

def process_single_image(row_data):
    """
    处理单张图片的函数，用于多线程
    """
    idx, total, row = row_data
    item_id = row.get('id', '')
    item_type = row.get('type', '')
    url = row.get('URL', '')
    
    if not url:
        return {
            'index': idx,
            'id': item_id,
            'type': item_type,
            'URL': url,
            'rgb_color': '',
            'status': 'skipped'
        }
    
    # 提取蓝色颜色
    color_proportions = extract_blue_colors_from_image(url)
    
    # 格式化颜色字符串
    rgb_color_string = format_rgb_color_string(color_proportions)
    
    return {
        'index': idx,
        'id': item_id,
        'type': item_type,
        'URL': url,
        'rgb_color': rgb_color_string,
        'status': 'completed',
        'blue_count': len(color_proportions)
    }

def process_csv(input_file, output_file, limit=None, max_workers=5):
    """
    处理CSV文件，提取蓝色信息（使用多线程加速）
    limit: 如果指定，只处理前limit行（用于测试）
    max_workers: 最大线程数
    """
    results_dict = {}  # 使用字典按索引存储结果
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if limit:
            rows = rows[:limit]
            print(f"测试模式：只处理前 {limit} 行")
        
        total_rows = len(rows)
        print(f"总共需要处理 {total_rows} 行数据（使用 {max_workers} 个线程）\n")
        
        # 准备任务数据
        tasks = []
        for idx, row in enumerate(rows, 1):
            tasks.append((idx, total_rows, row))
        
        # 使用线程池并行处理
        completed_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {executor.submit(process_single_image, task): task for task in tasks}
            
            # 处理完成的任务
            for future in as_completed(future_to_task):
                result = future.result()
                results_dict[result['index']] = result
                completed_count += 1
                
                if result['status'] == 'skipped':
                    print(f"[{completed_count}/{total_rows}] 跳过ID {result['id']}：没有URL")
                else:
                    print(f"[{completed_count}/{total_rows}] ID {result['id']} 完成，找到 {result['blue_count']} 种蓝色")
        
        # 按索引顺序整理结果
        results = []
        for idx in range(1, total_rows + 1):
            if idx in results_dict:
                result = results_dict[idx]
                results.append({
                    'id': result['id'],
                    'type': result['type'],
                    'URL': result['URL'],
                    'rgb_color': result['rgb_color']
                })
    
    # 写入新的CSV文件
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['id', 'type', 'URL', 'rgb_color']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n完成！结果已保存到 {output_file}")

if __name__ == "__main__":
    import sys
    
    input_file = "Processed_Data.csv"
    output_file = "color.csv"
    
    # 如果提供了命令行参数，使用测试模式（只处理前N行）
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"使用测试模式，只处理前 {limit} 行\n")
        except ValueError:
            print("无效的参数，将处理所有数据\n")
    
    process_csv(input_file, output_file, limit=limit)

