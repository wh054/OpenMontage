# Local Wan 2.1 deployment validation

Use only for the user-authorized low-resolution local AMD integration test. This beta test pipeline has no creative proposal or publication stage.

## Assets stage

Read `.agents/skills/comfyui/SKILL.md`. Discover `comfyui_video` through the registry. Confirm ComfyUI `/system_stats` reports the AMD GPU and HIP PyTorch. Preserve existing ROCm packages and model files. Fetch only the authorized official Wan 2.1 1.3B model stack through the requested proxy and verify hashes.

Record user authorization, model, seed, sampler, workflow hash, resolution, frame count, silent-audio choice and zero API cost in project artifacts. Use a temporal video latent with batch_size=1. Submit the exported API workflow through the registered provider, with explicit output_node and project-local output_path. Do not silently switch model, provider or precision. Write in_progress before generation and failed on error; completed requires a schema-valid asset_manifest and successful media retrieval.

## Compose stage

This is a single-shot test, so retain the generated clip without a second creative renderer. Verify dimensions, frame count, frame rate, duration and codec using FFprobe, decode the video, and sample frames to check actual motion and colors. Copy the verified clip into the project's renders directory and write a schema-valid render_report. Report measured generation time separately from download/startup time. Do not label the test passed based only on metadata or a successful HTTP response.
