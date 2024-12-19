import os
import logging
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from video_processor import VideoProcessor, Config
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"Python路径: {sys.path}")
    sys.exit(1)

def main():
    try:
        # 加载配置
        config = Config.load_config()
        print("配置加载成功")
        
        # 创建处理器实例
        processor = VideoProcessor(config)
        print("处理器初始化成功")
        
        # 视频文件信息
        video_name = "11_沟通状态的权利模式（平等、共识）.mp4"
        video_path = os.path.join(config.downloads_dir, video_name)
        video_path = str(Path(video_path).resolve())  # 转换为绝对路径
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        print(f"找到视频文件: {video_path}")
        print("开始处理视频...")
        
        # 处理视频
        transcript = processor.process_video(video_path)
        
        if transcript:
            print("\n转录成功！")
            print("\n转录文本:")
            print("-" * 80)
            print(transcript)
            print("-" * 80)
        else:
            print("\n转录失败！")
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 