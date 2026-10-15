# Wan 2.2 14B 本地 AMD 测试

本次配置使用原有 `E:\Qwen-Image-2.1\.venv` 的 Windows ROCm 环境和 ComfyUI，不安装或替换 PyTorch。模型是 Wan 2.2 T2V A14B 高/低噪声 FP8，配合 LightX2V v1.1 四步 LoRA。四步加速的结果不能代表完整多步采样质量。

## 下载与服务

仓库只包含代码、工作流和说明。模型、生成视频、`.runtime`、`.venv`、`projects` 和 `.env` 都不会上传。新的克隆不会包含本次测试项目或本机诊断记录。

先按 `LOCAL-DEPLOYMENT.md` 准备 OpenMontage 环境，再在该环境安装可选观察依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-wan-local.txt
```

ComfyUI 继续使用已经可工作的 ROCm 环境。启动脚本支持 `-ComfyRoot`、`-ComfyPython`、`-Proxy`，也可通过 `OPENMONTAGE_COMFY_ROOT`、`OPENMONTAGE_COMFY_PYTHON` 指定前两项。未指定时沿用本机原路径 `E:\Qwen-Image-2.1\ComfyUI` 及其上一级的 `.venv`；不会重装 ROCm。`Initialize-WanRuntime.ps1` 在启动时根据当前克隆路径生成所需的 `.runtime\wan22\model_paths.yaml`，配置发生变化时先留备份。

在 `E:\OpenMontage` 下执行：

```powershell
.\Download-Wan22.ps1
.\Start-Wan22.ps1 1> .runtime\wan22\staged-server.stdout.log 2> .runtime\wan22\staged-server.stderr.log
```

下载仅走 `http://127.0.0.1:7890`，支持断点续传，四个新增模型合计约 31 GB，完成时逐个验证 SHA256。共享已有 Wan 2.1 的 UMT5 文本编码器和 VAE。校验清单位于 `.runtime\wan22\download-manifest.json`。

服务监听 `127.0.0.1:8188`，使用默认 NORMAL_VRAM 模式让文本编码运行在 GPU；视频模型仍按需分块卸载。关闭节点中间缓存和 smart memory，保留 1.5 GiB 显存。端口已占用时启动脚本会报错；先停止确认属于本项目的视频服务。`Stop-Wan22.ps1` 只停止命令行匹配本配置的服务，并等待端口释放。

## 已准备的测试

默认项目：`projects\wan22-amd-14b-staged`，原始基准保留在 `projects\wan22-amd-14b-benchmark`。提示词与之前的金毛行走样片一致；832×480、81 帧、16 FPS、seed 42、四步采样，原始时长 5.0625 秒。精确五秒成片裁去最后一帧，不做插帧或超分辨率。

这些运行器是 pipeline 的执行与观察工具。新克隆中应先让项目助手按 `local-wan22-benchmark` 初始化项目及 assets checkpoint，再运行；缺少 checkpoint 时会明确拒绝执行。上文项目名描述本机已验证的实例，并不意味着仓库附带成片或基准 JSON。

```powershell
.\Run-Wan22.ps1
.\.venv\Scripts\python.exe scripts\inspect_wan22.py
```

生成通过 OpenMontage 的 `video_selector → comfyui_video → 本地 ComfyUI`，限定 ComfyUI，禁止云端回退。再次运行会重新生成并覆盖本测试项目的观察记录；保留首次基准结果后再运行。

运行器使用操作系统文件锁拒绝重叠任务，同时检查外部 ComfyUI 队列。成功或失败退出时，仅在队列空闲时请求释放模型，并保存 `cleanup-result.json`。异常退出后锁由系统释放；服务器有在途任务时，后续运行仍会被队列检查拒绝。

`comfy_nodes\openmontage_memory` 通过本项目额外路径配置加载，原 ComfyUI 源码和 ROCm 包未改。两个轻量节点分别等待文本编码及高噪声采样完成，先卸载上一阶段再调用原生 UNETLoader，模型、条件、潜空间和采样参数不变。

`artifacts` 保存原始执行事件、显存/内存采样、带时间的服务日志、输入参数、生成结果和逐帧检查。脚本检查文件格式与帧差，实际画质仍须观看视频判断。

当前结果以项目看板和 `artifacts\benchmark-report.json` 为准。下载与生成耗时分开记录。与旧 1.3B 样片的分辨率、时长和采样步数不同，不能作为单独模型大小变量的严格性能对比。

## 首次实测结果（2026-10-16）

- RX 9070 XT / Windows 原生 ROCm 成功生成，未使用云端。
- 下载和 SHA256 校验共约 53 分 48 秒；约 31.04 GB。
- ComfyUI 执行 580.95 秒（9 分 41 秒），提交至取回文件 591.89 秒（9 分 52 秒）。
- CPU 文本编码共 260.83 秒；两个 GPU 采样阶段约 117 秒和 152 秒；VAE 解码约 19.81 秒。
- 每三秒观察到的 PyTorch 显存预留峰值 12.56 GiB；系统可用内存最低约 15.6 MiB，32 GB 系统内存非常紧张。这些是采样值，不保证捕获瞬时峰值。
- 原始 81 帧无声视频裁为 80 帧、16 FPS、精确 5 秒。直接复制 H264 视频流，不再次压缩。全部帧解码通过，看板播放至结尾。
- 抽帧可见毛发、曝光与整体结构优于旧 1.3B 低分辨率样片；金毛向右行走。镜头有跟随，未严格固定，细小脚步仍有合成感。
- 此结果是四步 FP8 配置的首次实测，不代表完整多步采样上限。旧 1.3B 样片为 512×288、约三秒、30 步，参数不同。
- ROCm 包列表及原 Qwen 启动、约束文件验证未变。

成片：`projects\wan22-amd-14b-benchmark\renders\wan22-amd-5s.mp4`。

## 优化对照实测（2026-10-16）

| 配置 | 文本编码 | 服务器执行 | 提交至取回 |
|---|---:|---:|---:|
| 原始 CPU 文本编码 | 260.83 秒 | 580.95 秒 | 591.89 秒 |
| GPU 文本编码、自动清理 | 4.23 秒 | 443.75 秒 | 451.28 秒 |
| GPU 文本编码、阶段卸载、自动清理 | 4.20 秒 | 342.04 秒 | 354.77 秒 |

最终单次实测总耗时约 5 分 55 秒，相较原版约缩短 40%；文本编码约快 62 倍。三个配置的提示词、模型、LoRA、seed、分辨率、帧数和采样参数一致，比较工具会校验此约束；全部为重启服务后真实执行，无节点缓存命中。

阶段卸载版与第一轮 GPU 编码版的 80 帧解码像素完全相同。与原 CPU 编码版不逐像素相同，抽帧画面质量相当；CPU/GPU 数值路径不同，不能承诺相同 seed 跨设备计算完全一致。

采样观察到最终显存预留峰值 12.45 GiB；系统可用内存最低仍约 114 MiB。模型切换卸载点可用内存从约 820 MiB 回升至约 2449 MiB，进程 RSS 释放约 708 MiB。结束后自动清理，显存预留约 0.125 GiB、可用内存约 15.38 GiB。推理中的内存压力依然存在，不能当作已经解决容量限制。

每种配置仅一次实测，初始可用内存、系统和文件缓存不同；耗时是本机本次结果，不能把所有差异单独归因于阶段卸载。内存最低值不是严格控制条件下的峰值对比。

最终项目：`projects\wan22-amd-14b-staged`。`artifacts\comparison-report.json`、`before-after.jpg`、执行事件及阶段卸载日志保留全部证据。复核对比：

```powershell
.\.venv\Scripts\python.exe scripts\compare_wan22.py
```

改动前的启动脚本、运行器及模型路径配置备份在 `.runtime\wan22\backups\optimize-20261016-010804`。停止本视频服务后可恢复备份；新增节点仅在本项目的额外路径配置中注册。
