import os
from video_processor import VideoProcessor, Config

def main():
    # 加载配置
    config = Config.load_config()
    
    # 初始化视频处理器
    processor = VideoProcessor(config)
    
    # 获取视频文件列表
    video_files = [f for f in os.listdir(config.downloads_dir) 
                  if f.endswith(('.mp4', '.mov', '.avi'))]
    
    if not video_files:
        print("没有找到视频文件")
        return
    
    # 处理每个视频文件
    for video_file in video_files:
        video_path = os.path.join(config.downloads_dir, video_file)
        print(f"正在处理视频: {video_file}")
        result = processor.process_video(video_path)
        if result:
            print(f"视频 {video_file} 处理完成")
        else:
            print(f"视频 {video_file} 处理失败")

if __name__ == "__main__":
    main() 