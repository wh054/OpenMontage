# Wan 2.1 本地 AMD 接入

此配置使用 Windows 原生 ComfyUI + ROCm，在 RX 9070 XT 上运行 Wan 2.1 T2V 1.3B。OpenMontage 通过本机 HTTP 接口提交工作流并下载视频，不在自身 Python 环境中安装 PyTorch。

## 目录与环境

- 推理 Python：`E:\Qwen-Image-2.1\.venv\Scripts\python.exe`
- ComfyUI 源码：`E:\Qwen-Image-2.1\ComfyUI`
- 视频模型：`E:\OpenMontage\.runtime\wan21\models`
- ROCm：保留已有 `torch==2.9.1+rocm7.2.1`、Python 3.12.10。
- 模型目录通过独立的 extra-model-paths 配置传入；不改原 Qwen 启动脚本、模型和约束文件。
- 本地端点：`http://127.0.0.1:8188`；`.env` 中配置 `COMFYUI_VIDEO_SERVER_URL`。
- 修改前 `.env` 备份：`.runtime\wan21\backups\.env-before-wan21`。

## 下载与启动

以上绝对路径是本机验证实例。其他机器可通过 `-ComfyRoot`、`-ComfyPython` 指向已有 ComfyUI/ROCm 环境，或设置 `OPENMONTAGE_COMFY_ROOT`、`OPENMONTAGE_COMFY_PYTHON`。启动时会自动生成当前克隆位置的模型路径配置；不安装或替换 GPU 包。模型、环境、项目成片和诊断记录均为本地文件，不随仓库上传。

```powershell
cd E:\OpenMontage
.\Download-Wan21.ps1
.\Start-Wan21.ps1
```

下载仅走 `http://127.0.0.1:7890`，支持分段续传，并核对 Hugging Face 官方 LFS SHA-256。三个模型总计 9,828,025,775 字节。下载清单为 `.runtime\wan21\download-manifest.json`。

`Start-Wan21.ps1` 在当前终端前台运行服务，关闭该终端即可停止自己启动的服务。遇到端口已占用会停止并提示，不会终止现有程序。启动时关闭云端 API 节点，使用 PyTorch attention，并关闭 pinned memory。

停止本套配置启动的服务：`.\Stop-Wan21.ps1`。它会核对端口所属进程和独立模型配置路径，避免停止其他 ComfyUI 实例。

## 验证样片

- 项目：`projects\wan21-amd-validation`
- 工作流：`workflows\wan21-1.3b-lowres-api.json`，API 格式。
- 管线：`pipeline_defs\local-wan21-validation.yaml`，仅用于单镜头部署验证。
- 参数：416×240、49 帧、16 FPS、30 步、CFG 6、uni_pc/simple、shift 8、seed 42。
- 内容：红色帆船驶过蓝色湖面；无配音和音乐。
- 原始输出：`projects\wan21-amd-validation\assets\video\wan21-lowres.mp4`。
- 验证后的成片：`projects\wan21-amd-validation\renders\wan21-amd-verified.mp4`。
- 看板：`http://127.0.0.1:4750/p/wan21-amd-validation`。

首段帆船样片完成了生成和回传，但主体运动较弱，已保留并在报告中标注。最终运动验证使用第二个项目：

- 成片：`projects\wan21-amd-motion-validation\renders\wan21-amd-verified.mp4`
- 看板：`http://127.0.0.1:4750/p/wan21-amd-motion-validation`
- 工作流：`workflows\wan21-1.3b-motion-api.json`
- 实测：512×288、49 帧、16 FPS、约 3.06 秒，H.264 无声 MP4。
- 服务端执行 117.12 秒，工具提交及回传约 120.18 秒；不含首次下载时间。这是本次样片结果，不代表其他分辨率或长片性能。
- 采样期间观测到的 PyTorch 显存保留量峰值约 13.18 GiB；这是间隔采样值，不是严格的显存上限。
- 全部帧解码通过，抽帧能看到狗的位置、腿部和尾巴连续变化。狗实际向左行走，与提示词要求向右相反，毛发高光偏亮；本次通过的是接入和运动生成验证。
- 原有 Python 软件包清单、ROCm 约束文件、Qwen 启动脚本与测试前一致。

在已有验证项目里重复第二份工作流的工具调用：

```powershell
.\Run-Wan21.ps1 -Project wan21-amd-motion-validation -Workflow workflows\wan21-1.3b-motion-api.json
```

该命令会更新项目当前工具输入、结果及视频；如需保留多个独立版本，应由助手先初始化新项目和 checkpoint。下次也可直接在聊天中描述需求，并指定使用本地 Wan 2.1。

已修正当前 ComfyUI 的保存节点 API 参数：`format` 使用字符串 `mp4`，嵌套选项使用扁平键 `format.codec: h264`，不能直接传入嵌套 JSON 对象。首轮的保存错误及修正后的重试记录均保留在首个项目中。

`Run-Wan21.ps1` 是一次已准备工作流的工具调用入口，通过注册表的 `video_selector` 严格指定 `comfyui_video`，不允许切换云端或其他模型。项目规划、阶段 checkpoint 和目视验收由助手执行，脚本不会自行做创作决策。重新生成前应由助手建立项目和 assets checkpoint。

长任务超时时先看 ComfyUI 队列及历史，使用同一个 prompt_id 恢复等待，避免重复提交：

```powershell
.\Run-Wan21.ps1 -ResumePromptId '<原任务的 prompt_id>'
```

## 能力检测说明

项目的默认 `comfyui_video` 能力检测按自带的 Wan 2.2 14B 模型栈检查，因此仅安装 Wan 2.1 时可能显示 `degraded`。自定义工作流加明确输出节点可以通过 selector 运行；本方案使用输出节点 `50`，不为消除提示而额外下载 14B 模型。

自定义工作流中的提示词、尺寸、帧数、seed、采样参数必须直接写入图中；仅改变外层工具参数不会自动改写任意自定义工作流。

## 验证证据

模型下载、服务日志和环境快照保存在 `.runtime\wan21`；实际工具输入、结果、工作流来源及阶段记录保存在验证项目目录。最终状态以该项目的 `artifacts\render_report.json` 为准，下载完成或接口返回成功本身不代表画质通过。
