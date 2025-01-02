import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import yaml
import sys
import whisper
import torch
from pydub import AudioSegment
import pandas as pd
from text_processor import TextProcessor

@dataclass
class Config:
    """配置类，用于存储应用程序配置"""
    downloads_dir: str
    mp3_dir: str
    logs_dir: str
    output_dir: str
    asr_api: Dict[str, Any]
    openai_api: Dict[str, Any]
    deepseek_api: Dict[str, Any]

    @classmethod
    def load_config(cls, config_path: str = "config.yaml") -> 'Config':
        """从YAML文件加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                return cls(
                    downloads_dir=config_data.get('downloads_dir', 'downloads'),
                    mp3_dir=config_data.get('mp3_dir', 'mp3'),
                    logs_dir=config_data.get('logs_dir', 'logs'),
                    output_dir=config_data.get('output_dir', 'output'),
                    asr_api=config_data.get('asr_api', {
                        'provider': 'whisper',
                        'model': 'base',
                        'language': 'zh'
                    }),
                    openai_api=config_data.get('openai_api', {
                        'api_key': ''
                    }),
                    deepseek_api=config_data.get('deepseek_api', {
                        'api_key': ''
                    })
                )
        except FileNotFoundError:
            logging.error("配置文件不存在，使用默认配置")
            return cls(
                downloads_dir='downloads',
                mp3_dir='mp3',
                logs_dir='logs',
                output_dir='output',
                asr_api={
                    'provider': 'whisper',
                    'model': 'base',
                    'language': 'zh'
                },
                openai_api={
                    'api_key': ''
                },
                deepseek_api={
                    'api_key': ''
                }
            )

class VideoProcessor:
    """视频处理类，处理视频转录相关操作"""

    def __init__(self, config: Config):
        self.config = config
        self._setup_logging()
        self._setup_directories()
        self._setup_asr_model()
        self._setup_text_processor()

    def _setup_directories(self) -> None:
        """确保所需目录存在"""
        for dir_path in [self.config.downloads_dir, self.config.mp3_dir, 
                        self.config.logs_dir, self.config.output_dir]:
            os.makedirs(dir_path, exist_ok=True)

    def _setup_logging(self) -> None:
        """配置日志系统"""
        log_file = os.path.join(self.config.logs_dir, 'video_processor.log')
        os.makedirs(self.config.logs_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logging.info("视频处理器初始化完成")

    def _setup_asr_model(self) -> None:
        """初始化ASR模型"""
        try:
            if self.config.asr_api['provider'] == 'whisper':
                self.model = whisper.load_model(self.config.asr_api['model'])
            else:
                raise ValueError(f"不支持的ASR提供商: {self.config.asr_api['provider']}")
        except Exception as e:
            logging.error(f"ASR模型初始化失败: {e}")
            raise

    def _setup_text_processor(self) -> None:
        """初始化文本处理器"""
        try:
            if self.config.deepseek_api['api_key']:
                self.text_processor = TextProcessor(self.config.deepseek_api['api_key'])
                logging.info("文本处理器初始化完成")
            else:
                self.text_processor = None
                logging.warning("未配置DeepSeek API密钥，文本优化功能将被禁用")
        except Exception as e:
            logging.error(f"文本处理器初始化失败: {e}")
            self.text_processor = None

    def convert_video_to_mp3(self, video_path: str) -> str:
        """将视频文件转换为MP3格式"""
        try:
            video_name = Path(video_path).stem
            mp3_path = os.path.join(self.config.mp3_dir, f"{video_name}.mp3")
            
            if os.path.exists(mp3_path):
                logging.info(f"MP3文件已存在: {mp3_path}")
                return mp3_path

            logging.info(f"开始转换视频到MP3: {video_path}")
            logging.info(f"目标MP3路径: {mp3_path}")
            
            # 使用pydub转换视频音频到MP3
            try:
                audio = AudioSegment.from_file(video_path)
                logging.info("成功读取视频文件")
                audio.export(mp3_path, format="mp3")
                logging.info("成功导出MP3文件")
            except Exception as e:
                logging.error(f"音频处理失败: {str(e)}")
                raise
            
            if not os.path.exists(mp3_path):
                raise FileNotFoundError(f"MP3文件未能成功创建: {mp3_path}")
            
            logging.info(f"视频转换为MP3成功: {mp3_path}")
            return mp3_path
        except Exception as e:
            logging.error(f"视频转换MP3失败: {e}")
            raise

    def call_asr_api(self, mp3_path: str) -> str:
        """
        调用ASR API进行语音识别
        
        Args:
            mp3_path: MP3文件路径

        Returns:
            str: 转录文本
        """
        try:
            if self.config.asr_api['provider'] == 'whisper':
                logging.info(f"开始使用Whisper处理音频: {mp3_path}")
                result = self.model.transcribe(
                    mp3_path,
                    language=self.config.asr_api['language']
                )
                logging.info("Whisper处理完成")
                return result["text"]
            else:
                raise ValueError(f"不支持的ASR提供商: {self.config.asr_api['provider']}")
        except Exception as e:
            logging.error(f"语音识别失败: {e}")
            raise

    def _save_to_excel(self, video_name: str, transcript: str, optimized: str = None, summary: str = None) -> None:
        """保存转录结果到Excel文件"""
        excel_path = os.path.join(self.config.output_dir, "transcripts.xlsx")
        
        # 读取现有的Excel文件（如果存在）
        if os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path)
            except Exception as e:
                logging.error(f"读取Excel文件失败: {e}")
                df = pd.DataFrame(columns=['视频名称', '转录时间', '原始转录', '优化转录', '内容总结'])
        else:
            df = pd.DataFrame(columns=['视频名称', '转录时间', '原始转录', '优化转录', '内容总结'])
        
        # 添加新的记录
        new_row = {
            '视频名称': video_name,
            '转录时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '原始转录': transcript,
            '优化转录': optimized if optimized else '',
            '内容总结': summary if summary else ''
        }
        
        # 如果已存在相同视频名称的记录，则更新它
        if video_name in df['视频名称'].values:
            df.loc[df['视频名称'] == video_name] = new_row
        else:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # 保存到Excel
        try:
            df.to_excel(excel_path, index=False, engine='openpyxl')
            logging.info(f"转录结果已保存到Excel: {excel_path}")
        except Exception as e:
            logging.error(f"保存Excel文件失败: {e}")
            raise

    def process_video(self, video_path: str) -> Optional[str]:
        """
        处理单个视频的转录
        
        Args:
            video_path: 视频文件路径

        Returns:
            Optional[str]: 转录文本，如果失败则返回None
        """
        logging.info(f"开始处理视频: {video_path}")
        
        if not os.path.exists(video_path):
            logging.error(f"视频文件不存在: {video_path}")
            return None

        try:
            # 转换视频到MP3
            mp3_path = self.convert_video_to_mp3(video_path)
            logging.info(f"视频已转换为MP3: {mp3_path}")
            
            # 调用ASR API进行转录
            logging.info("开始语音识别...")
            transcript = self.call_asr_api(mp3_path)
            logging.info("语音识别完成")
            
            # 处理转录文本
            optimized = None
            summary = None
            if self.text_processor and transcript:
                logging.info("开始处理转录文本...")
                try:
                    result = self.text_processor.process_transcript(transcript)
                    optimized = result.get("optimized")
                    summary = result.get("summary")
                    logging.info("文本处理完成")
                except Exception as e:
                    logging.error(f"处理转录文本时出错: {e}")
            
            # 保存转录文本
            video_name = Path(video_path).stem
            self._save_to_excel(video_name, transcript, optimized, summary)
            
            # 同时保存到单独的文本文件
            transcript_dir = os.path.join(self.config.output_dir, "transcripts")
            os.makedirs(transcript_dir, exist_ok=True)
            
            # 保存原始转录
            transcript_path = os.path.join(transcript_dir, f"{video_name}.txt")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            
            # 如果有优化后的文本，保存到单独文件
            if optimized:
                optimized_path = os.path.join(transcript_dir, f"{video_name}_optimized.txt")
                with open(optimized_path, "w", encoding="utf-8") as f:
                    f.write(optimized)
            
            # 如果有总结，保存到单独文件
            if summary:
                summary_path = os.path.join(transcript_dir, f"{video_name}_summary.txt")
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(summary)
            
            logging.info(f"转录文本已保存到: {transcript_path}")
            return transcript

        except Exception as e:
            logging.error(f"处理视频时出错: {str(e)}")
            return None
