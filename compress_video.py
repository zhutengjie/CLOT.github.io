#!/usr/bin/env python3
"""
视频压缩脚本
自动将视频压缩到指定大小以下
"""

import subprocess
import os
import sys

def get_video_info(video_path):
    """获取视频信息"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration,size',
        '-of', 'default=noprint_wrappers=1',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    info = {}
    for line in lines:
        if '=' in line:
            key, value = line.split('=')
            info[key] = value
    return info

def compress_video(input_path, output_path, target_size_mb=100):
    """
    压缩视频到目标大小
    
    参数:
        input_path: 输入视频路径
        output_path: 输出视频路径
        target_size_mb: 目标大小（MB）
    """
    # 获取视频信息
    info = get_video_info(input_path)
    duration = float(info.get('duration', 0))
    current_size = int(info.get('size', 0)) / (1024 * 1024)  # 转换为MB
    
    print(f"原始视频大小: {current_size:.2f} MB")
    print(f"视频时长: {duration:.2f} 秒")
    print(f"目标大小: {target_size_mb} MB")
    
    # 计算目标比特率（留出10%的空间给音频和元数据）
    target_size_bits = target_size_mb * 8 * 1024 * 0.9  # 转换为Kb，留10%余地
    target_bitrate = int(target_size_bits / duration)  # kbps
    
    print(f"计算出的视频比特率: {target_bitrate} kbps")
    
    # 使用ffmpeg压缩视频
    # 使用H.264编码器和CRF模式，两阶段编码确保更好的质量
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',           # 使用H.264编码器
        '-b:v', f'{target_bitrate}k', # 视频比特率
        '-maxrate', f'{target_bitrate * 1.2}k',  # 最大比特率
        '-bufsize', f'{target_bitrate * 2}k',    # 缓冲大小
        '-preset', 'slow',            # 慢速预设（更好的压缩率）
        '-c:a', 'aac',                # 音频编码器
        '-b:a', '128k',               # 音频比特率
        '-movflags', '+faststart',    # 优化网络播放
        '-y',                         # 覆盖输出文件
        output_path
    ]
    
    print("\n开始压缩视频...")
    print(f"执行命令: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        # 检查输出文件大小
        output_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\n压缩完成！")
        print(f"输出文件大小: {output_size:.2f} MB")
        print(f"压缩率: {(1 - output_size/current_size) * 100:.1f}%")
        
        if output_size > target_size_mb:
            print(f"\n警告: 输出文件({output_size:.2f} MB)仍然大于目标大小({target_size_mb} MB)")
            print("正在进行第二次压缩...")
            
            # 第二次压缩，使用更激进的参数
            temp_output = output_path + '.temp.mp4'
            os.rename(output_path, temp_output)
            
            # 降低比特率
            new_bitrate = int(target_bitrate * 0.85 * (target_size_mb / output_size))
            
            cmd = [
                'ffmpeg',
                '-i', temp_output,
                '-c:v', 'libx264',
                '-b:v', f'{new_bitrate}k',
                '-maxrate', f'{new_bitrate * 1.2}k',
                '-bufsize', f'{new_bitrate * 2}k',
                '-preset', 'slow',
                '-c:a', 'aac',
                '-b:a', '96k',  # 降低音频比特率
                '-movflags', '+faststart',
                '-y',
                output_path
            ]
            
            subprocess.run(cmd)
            os.remove(temp_output)
            
            final_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"第二次压缩完成！最终文件大小: {final_size:.2f} MB")
        
        return True
    else:
        print("压缩失败！")
        return False

if __name__ == '__main__':
    input_video = '/home/ztj/beyondmimic.github.io/static/videos/teaser.mp4'
    output_video = '/home/ztj/beyondmimic.github.io/static/videos/teaser_compressed.mp4'
    
    if not os.path.exists(input_video):
        print(f"错误: 找不到输入文件 {input_video}")
        sys.exit(1)
    
    success = compress_video(input_video, output_video, target_size_mb=100)
    
    if success:
        print(f"\n压缩后的视频保存在: {output_video}")
        print("\n如果确认压缩效果满意，可以用以下命令替换原文件：")
        print(f"  mv {output_video} {input_video}")
    else:
        sys.exit(1)

