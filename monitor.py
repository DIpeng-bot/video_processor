import time
import os
import traceback
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from video_processor import VideoProcessor, Config
import logging

class VideoHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor
        self.processed_files = set()
        self.processing_files = set()  # 正在处理的文件
        self.temp_files = set()  # 跟踪.temp文件
        
        # 初始化时记录已存在的文件
        downloads_dir = Path(processor.config.downloads_dir)
        for file in downloads_dir.glob("*.[mM][pP]4"):
            self.processed_files.add(file.name)
        logging.info(f"初始化时发现 {len(self.processed_files)} 个已存在的视频文件")
    
    def _should_process_file(self, file_path):
        """检查文件是否应该被处理"""
        try:
            # 检查文件扩展名
            if file_path.suffix.lower() not in ['.mp4', '.mov', '.avi']:
                if file_path.suffix.lower() == '.temp':
                    self.temp_files.add(file_path.stem)  # 记录.temp文件
                logging.debug(f"跳过非视频文件: {file_path.name}")
                return False
                
            # 检查是否已处理
            if file_path.name in self.processed_files:
                logging.debug(f"跳过已处理的文件: {file_path.name}")
                return False
                
            # 检查是否正在处理
            if file_path.name in self.processing_files:
                logging.debug(f"文件正在处理中: {file_path.name}")
                return False
                
            # 检查文件是否存在
            if not file_path.exists():
                logging.error(f"文件不存在: {file_path}")
                return False
                
            return True
        except Exception as e:
            logging.error(f"检查文件时出错: {str(e)}")
            return False
    
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        logging.info(f"检测到新文件: {file_path.name}")
        
        if not self._should_process_file(file_path):
            return
            
        self._process_video(file_path)
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        logging.debug(f"检测到文件修改: {file_path.name}")
        
        if not self._should_process_file(file_path):
            return
            
        self._process_video(file_path)
    
    def on_moved(self, event):
        """处理文件重命名事件"""
        if event.is_directory:
            return
            
        src_path = Path(event.src_path)
        dest_path = Path(event.dest_path)
        
        # 如果是从.temp重命名为.mp4
        if src_path.suffix.lower() == '.temp' and dest_path.suffix.lower() == '.mp4':
            logging.info(f"检测到文件重命名: {src_path.name} -> {dest_path.name}")
            
            # 如果之前记录过这个.temp文件
            if src_path.stem in self.temp_files:
                self.temp_files.remove(src_path.stem)
                self._process_video(dest_path)
    
    def _process_video(self, file_path):
        """处理视频文件"""
        temp_path = None
        try:
            # 标记为正在处理
            self.processing_files.add(file_path.name)
            logging.info(f"开始处理文件: {file_path.name}")
            
            # 等待文件完全写入
            time.sleep(2)
            
            # 检查文件大小是否稳定
            initial_size = file_path.stat().st_size
            time.sleep(1)
            if initial_size != file_path.stat().st_size:
                logging.info(f"文件 {file_path.name} 仍在写入，稍后处理")
                self.processing_files.remove(file_path.name)
                return
            
            # 确保目录存在
            for dir_name in [self.processor.config.mp3_dir, self.processor.config.output_dir]:
                os.makedirs(dir_name, exist_ok=True)
            
            # 创建临时目录
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # 复制文件到临时目录
            temp_path = temp_dir / file_path.name
            try:
                shutil.copy2(file_path, temp_path)
                logging.info(f"已复制文件到临时目录: {temp_path}")
            except Exception as e:
                logging.error(f"复制文件失败: {str(e)}")
                raise
            
            # 处理视频
            logging.info(f"开始转录视频: {temp_path}")
            try:
                result = self.processor.process_video(str(temp_path))
                logging.info(f"转录结果: {result[:100] if result else None}")  # 只显示前100个字符
            except Exception as e:
                logging.error(f"转录过程出错: {str(e)}")
                logging.error(traceback.format_exc())
                raise
            
            if result:
                logging.info(f"视频 {file_path.name} 处理完成")
                self.processed_files.add(file_path.name)
            else:
                logging.error(f"视频 {file_path.name} 处理失败")
                
        except Exception as e:
            logging.error(f"处理视频时出错: {str(e)}")
            logging.error(traceback.format_exc())
        finally:
            # 清理临时文件
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                    logging.info(f"已删除临时文件: {temp_path}")
                except Exception as e:
                    logging.error(f"删除临时文件失败: {str(e)}")
            
            # 移除处理中标记
            if file_path.name in self.processing_files:
                self.processing_files.remove(file_path.name)

def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('monitor.log', encoding='utf-8')
        ]
    )
    
    # 加载配置
    try:
        config = Config.load_config()
        logging.info(f"配置加载成功: {config.__dict__}")
    except Exception as e:
        logging.error(f"加载配置失败: {str(e)}")
        return
    
    # 设置监控目录为本地downloads文件夹
    downloads_dir = Path(config.downloads_dir)
    downloads_dir.mkdir(exist_ok=True)  # 确保目录存在
    
    # 创建临时目录
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    logging.info(f"开始初始化...")
    
    try:
        # 初始化视频处理器
        processor = VideoProcessor(config)
        
        # 创建事件处理器
        event_handler = VideoHandler(processor)
        
        # 创建观察者
        observer = Observer()
        observer.schedule(event_handler, str(downloads_dir), recursive=False)
        
        # 启动监控
        observer.start()
        logging.info(f"开始监控目录: {downloads_dir}")
        
        # 检查现有文件
        existing_files = list(downloads_dir.glob("*.[mM][pP]4"))
        if existing_files:
            logging.info(f"发现 {len(existing_files)} 个现有视频文件待处理")
            for file_path in existing_files:
                if file_path.name not in event_handler.processed_files:
                    logging.info(f"处理现有视频: {file_path.name}")
                    event_handler._process_video(file_path)
        
        # 持续运行
        logging.info("监控程序正在运行中...")
        while True:
            time.sleep(1)
            
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        logging.error(traceback.format_exc())
    except KeyboardInterrupt:
        logging.info("监控已停止")
    finally:
        observer.stop()
        observer.join()
        
        # 清理临时目录
        try:
            shutil.rmtree("temp")
            logging.info("已清理临时目录")
        except Exception as e:
            logging.error(f"清理临时目录失败: {str(e)}")

if __name__ == "__main__":
    main() 