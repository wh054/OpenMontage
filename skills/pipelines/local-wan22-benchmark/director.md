# Local Wan 2.2 14B benchmark

This beta pipeline is limited to the user's requested local AMD feasibility, timing and quality test. Read `.agents/skills/comfyui/SKILL.md` before generation. The user has authorized downloading the model stack via the local proxy and generating one approximately five-second test; retain their existing ROCm packages and Qwen configuration.

## Assets

Announce the exact FP8 high/low-noise models and whether LightX2V acceleration is used. Four-step acceleration is a separate quality/speed tradeoff and must not be reported as full multi-step Wan quality. Discover the provider via the registry; strictly select comfyui_video through video_selector. Use the native video temporal latent, explicit output node and project-local output path. Save the exact workflow, seed and model hashes. Record in_progress before execution. Capture service events and GPU/RAM samples; separate downloading, model preparation, sampling-node wall times and total execution. Never infer performance from an installation check or from a cached export. Surface memory or backend failures without a silent model/provider substitution.

For the user's authorized runtime optimization comparison, preserve the baseline project and identical prompts, seed, sampling parameters, models, LoRAs and frame dimensions. Normal VRAM mode is selected by removing `--lowvram` in this ComfyUI version; it permits GPU text encoding while retaining partial video-model offload. Project-local staged native UNET loader wrappers may add dependencies and release finished stages before loading the next model; they must delegate unchanged loading to ComfyUI and never alter conditioning or latents. Record first-run and revised trials separately. Serialize runner jobs, reject a busy external queue, and release models after completion or failure only when the server queue is idle. Distinguish actual phase-release evidence from system RAM minima, which can be affected by background apps and different initial free memory.

## Compose

Generate 81 frames at 16 FPS for the valid temporal shape, then use FFmpeg to deliver exactly five seconds (80 frames). Decode and inspect the real output, including temporal consistency, body/limb structure, movement, exposure and color. Write asset_manifest and render_report checkpoints and retain first-run timing. Show the clip and compare honestly to the prior 1.3B test; resolution, duration and step count differ, so it is not a controlled model-only benchmark.
