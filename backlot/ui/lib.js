// Shared helpers for the Backlot UI.

// Display labels only: checkpoint keys, filenames and project content stay intact.
const LABELS = {
  unknown: "未知", artifact: "制作资料", decision: "制作决策",
  research: "前期调研", proposal: "制作提案", idea: "创意构思", script: "脚本",
  scene_plan: "分镜规划", assets: "素材制作", edit: "剪辑", compose: "合成出片", publish: "发布",
  character_design: "角色设计", rig_plan: "角色绑定规划",
  character_spec: "角色设定", rig_spec: "绑定方案", action_timeline: "动作时间轴",
  pending: "未开始", in_progress: "进行中", awaiting_human: "待你审核", completed: "已完成", failed: "失败",
  research_brief: "调研摘要", proposal_packet: "制作提案", brief: "创意简报",
  asset_manifest: "素材清单", edit_decisions: "剪辑方案", render_report: "出片报告",
  final_review: "最终检查", publish_log: "发布记录", decision_log: "决策记录",
  source_media_review: "源素材检查", video_analysis_brief: "参考视频分析",
  "animated-explainer": "动画解说", "talking-head": "出镜讲解", "screen-demo": "屏幕演示",
  "clip-factory": "批量切片", "podcast-repurpose": "播客再创作", cinematic: "电影感短片",
  animation: "动画", "character-animation": "角色动画", hybrid: "混合制作",
  "avatar-spokesperson": "数字人口播", "localization-dub": "翻译配音",
  "documentary-montage": "纪实混剪", "framework-smoke": "框架验证",
  "local-wan21-validation": "本地 Wan 视频验证",
  "local-wan22-benchmark": "本地 Wan 2.2 性能与画质测试",
  pipeline_selection: "流程选择", provider_selection: "生成服务选择",
  renderer_family_selection: "合成方式选择", render_runtime_selection: "渲染引擎选择",
  composition_mode: "合成模式", playbook_selection: "视觉风格选择",
  fallback_decision: "替代方案", budget_tradeoff: "预算取舍", downgrade_approval: "降级确认",
  music_source: "配乐来源", motion_commitment: "运动效果要求", concept_selection: "创意方案选择",
  voice_selection: "配音选择", capability_extension: "功能扩展", playbook_override: "风格调整",
  visual_accuracy_check: "画面准确性检查", approval_policy: "审核规则",
  image: "图片", video: "视频", audio: "音频", narration: "旁白", music: "配乐", sfx: "音效",
  diagram: "图解", subtitle: "字幕", font: "字体", lut: "调色预设", code_snippet: "代码片段",
  "3d_asset": "三维素材", "3d_world": "三维场景", text_card: "文字卡片", broll: "补充镜头",
  overlay: "叠加元素", stat_card: "数据卡片", talking_head: "出镜讲解", screen_recording: "录屏",
  character_scene: "角色场景", transition: "转场",
  platform: "目标平台", duration: "时长", tone: "语气", style: "风格", runtime: "渲染引擎",
  pipeline: "制作流程", "estimated cost": "预计费用", concepts: "创意方案", sources: "参考来源",
  "data points": "数据要点", angles: "切入角度", sections: "段落", scenes: "镜头",
  types: "素材类型", "generation cost": "生成费用", cuts: "剪辑片段", outputs: "输出文件",
  destinations: "发布目标", pass: "通过", passed: "通过", valid: "有效", invalid: "无效",
  pass_with_warnings: "通过（有提醒）", needs_revision: "需要修改", revise: "需要修改",
  wide: "全景", medium: "中景", medium_close: "中近景", close_up: "特写",
  extreme_close_up: "大特写", extreme_wide: "大远景", over_shoulder: "过肩镜头",
  insert: "细节镜头", establishing: "场景建立镜头", static: "固定机位",
  pan_left: "向左摇镜", pan_right: "向右摇镜", tilt_up: "向上摇镜", tilt_down: "向下摇镜",
  dolly_in: "推近", dolly_out: "拉远", tracking_left: "向左跟拍", tracking_right: "向右跟拍",
  crane_up: "镜头升起", crane_down: "镜头下降", handheld: "手持", steadicam: "稳定器跟拍",
  whip_pan: "甩镜", orbital: "环绕", zoom_in: "变焦推近", zoom_out: "变焦拉远", rack_focus: "焦点切换",
  high_key: "高调光", low_key: "低调光", natural: "自然光", golden_hour: "黄金时刻",
  blue_hour: "蓝调时刻", tungsten_warm: "暖钨丝光", neon: "霓虹光", silhouette: "剪影",
  rim_lit: "轮廓光", volumetric: "体积光", overcast_soft: "阴天柔光",
  "clean-professional": "简洁专业", "premium-minimalist": "精致极简",
  "flat-motion-graphics": "扁平动态图形", "minimalist-diagram": "极简图解", "ink-sketch": "水墨手绘",
};

export function label(value) {
  const text = String(value ?? "");
  return LABELS[text] ?? text.replaceAll("_", " ");
}

export async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  return res.json();
}

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null) continue;
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const child of children.flat()) {
    if (child == null) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

export function fmtDuration(seconds) {
  const n = Number(seconds);
  if (seconds == null || !Number.isFinite(n)) return "";
  const s = Math.max(0, Math.round(n));
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

export function fmtMoney(v) {
  const n = Number(v);
  if (v == null || !Number.isFinite(n)) return "—";
  return `$${n.toFixed(2)}`;
}

export function fmtAgo(epochSeconds) {
  if (!epochSeconds) return "";
  const diff = Date.now() / 1000 - epochSeconds;
  if (diff < 90) return "刚刚";
  if (diff < 3600) return `${Math.round(diff / 60)} 分钟前`;
  if (diff < 86400) return `${Math.round(diff / 3600)} 小时前`;
  return `${Math.round(diff / 86400)} 天前`;
}

export function fmtClock(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  } catch {
    return "";
  }
}

export function mediaURL(projectId, relPath) {
  return `/media/${encodeURIComponent(projectId)}/${relPath.split("/").map(encodeURIComponent).join("/")}`;
}

// Downscaled cached JPEG for images (full media only in players/lightbox).
export function thumbURL(projectId, relPath, w = 640) {
  return `/thumb/${encodeURIComponent(projectId)}/${relPath.split("/").map(encodeURIComponent).join("/")}?w=${w}`;
}

// Subscribe to a server-sent change feed; call onChange (debounced) per burst.
export function subscribe(url, onChange) {
  let timer = null;
  const source = new EventSource(url);
  source.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data);
      if (data.type !== "change") return;
    } catch {
      return;
    }
    clearTimeout(timer);
    timer = setTimeout(onChange, 250);
  };
  source.onerror = () => { /* EventSource auto-reconnects */ };
  return source;
}

// Deterministic pseudo-waveform bars (seeded by a string).
export function waveBars(container, seedStr, count = 26, maxH = 14) {
  let seed = 0;
  for (const c of seedStr || "wave") seed = (seed * 31 + c.charCodeAt(0)) % 2147483647;
  seed = seed || 7;
  container.innerHTML = "";
  for (let i = 0; i < count; i++) {
    seed = (seed * 16807) % 2147483647;
    const h = 3 + ((seed % 100) / 100) * maxH * (0.55 + 0.45 * Math.sin(i / 5));
    const bar = document.createElement("i");
    bar.style.height = `${Math.max(3, h)}px`;
    container.append(bar);
  }
}

export const STAGE_ICONS = {
  completed: "✓",
  in_progress: "◉",
  awaiting_human: "◈",
  failed: "✕",
};
