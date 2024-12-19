# 视频处理工具

这是一个用于处理视频文件并进行语音转录的工具。

## 功能特点

- 支持多种视频格式（mp4, mov, avi）
- 使用Whisper模型进行语音识别
- 自动保存转录结果到Excel文件
- 支持批量处理视频文件

## 目录结构

```
.
├── config.yaml          # 配置文件
├── main.py             # 主程序
├── downloads/          # 视频文件目录
├── output/            # 输出目录（Excel文件）
├── mp3/               # 音频文件目录
└── logs/              # 日志文件目录
```

## 配置说明

配置文件 `config.yaml` 包含以下设置：

- output_dir: 输出目录
- downloads_dir: 视频文件目录
- mp3_dir: 音频文件目录
- logs_dir: 日志文件目录
- asr_api:
  - provider: 语音识别提供商（whisper）
  - model: 模型名称
  - language: 识别语言

## 使用方法

1. 将需要处理的视频文件放入 `downloads` 目录
2. 运行程序：
   ```
   python main.py
   ```
3. 程序会自动处理所有视频文件，并将转录结果保存到 `output/transcriptions.xlsx`

## 输出格式

转录结果将保存在Excel文件中，包含以下列：
- 视频文件名
- 转录内容
- 处理时间

## 依赖项

- whisper
- pandas
- pyyaml

## 安装依赖

```bash
pip install openai-whisper pandas pyyaml
```