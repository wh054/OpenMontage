# 本地运行说明

部署位置：`E:\OpenMontage`。Windows 原生 Python 3.10 独立环境，无需 Docker。

## 打开应用

在项目目录的 PowerShell 中运行：

```powershell
.\Start-OpenMontage.ps1
```

Backlot 看板：http://127.0.0.1:4750 。该命令会检查服务是否已运行，然后打开浏览器。

Remotion Studio：http://127.0.0.1:4751 。重启编辑器时运行下面命令，并保持窗口打开：

```powershell
.\Start-Remotion.ps1
```

## 在当前 PowerShell 中使用制作工具

```powershell
. .\Enter-OpenMontage.ps1
python -m backlot open
python render_demo.py --list
```

环境脚本将独立 Python 环境和项目内 FFmpeg 加入当前会话 PATH，并为 HyperFrames 配置浏览器和 FFmpeg 路径；不会修改系统或用户全局环境。

## 验证过的示例

```powershell
.\Render-Demo.ps1
```

官方 `code-to-screen` 示例输出：`projects\demos\renders\code-to-screen.mp4`。
已实际渲染并用 FFprobe 验证：H.264/AAC，1920×1080，30 FPS，约 25 秒；抽帧检查通过。

## 依赖与功能边界

- Python 基础依赖、Piper 离线语音组件：`.venv`。
- Remotion：`remotion-composer\node_modules`，按仓库 package-lock.json 安装。
- HyperFrames：通过官方 `npx hyperframes` 安装到 npm 缓存；环境诊断结果在 `.runtime\hyperframes-doctor.log`。
- FFmpeg/FFprobe：已从本机已有工具复制到 `.runtime\ffmpeg`，运行不依赖原目录。
- 渲染浏览器：`remotion-composer\node_modules\.remotion\chrome-headless-shell`，来自 Google Chrome for Testing。
- `.env` 已从模板创建，未填入任何云端 API 密钥。云端图像、视频、语音等生成能力需要配置相应服务。
- Piper 已安装；尚未下载或验证具体声音模型，首次使用相应声音时需要下载模型。
- 后续已接入本地 AMD ROCm / ComfyUI / Wan 2.1 1.3B 并实际生成短片，见 `WAN21-LOCAL.md`。Blender、Docker 等其他可选大型组件未安装。
- Wan 2.2 14B 双模型 FP8、GPU 文本编码与阶段卸载的实测配置见 `WAN22-LOCAL.md`。本机五秒测试从约 9 分 52 秒优化至约 5 分 55 秒，系统内存仍比较紧张。
- 本项目通过 AI 助手读取 AGENT_GUIDE.md 并驱动制作流程；Backlot 是制作看板，Remotion Studio 是合成预览编辑器。

## 诊断记录

`.runtime\preflight.json`：能力检查结果。
`.runtime\requirements-installed.txt`：当前 Python 依赖版本。
`.runtime\render-demo.log`：实际示例渲染日志。
`.runtime\backlot.stderr.log`：本次启动的看板日志。
`.runtime\remotion.stdout.log`、`.runtime\remotion.stderr.log`：本次启动的编辑器日志。

基础安装：`python -m venv .venv`，再用 `uv pip install --python .venv\Scripts\python.exe -r requirements.txt piper-tts`，并在 `remotion-composer` 中执行 `npm.cmd ci`。

本说明中的版本、绝对路径与实测结果是本机部署记录。仓库不会附带模型、`.env`、虚拟环境、FFmpeg 二进制或生成视频；其他机器需准备相应依赖。Wan 启动脚本支持指定现有 ComfyUI 及 ROCm Python 路径，运行配置会按当前克隆目录生成。视频执行工具需由项目助手先按对应 pipeline 初始化项目和 checkpoint。
