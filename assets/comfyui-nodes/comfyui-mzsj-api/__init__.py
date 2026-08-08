"""
ComfyUI MZSJ API Nodes — 纯 API 视频生成节点包
不加载任何本地模型，通过 mzsjai.com 调用 MiniMax H3 视频模型，
通过 DeepSeek v4-flash 做提示词增强。
"""
import json
import os
import time
import base64
import io
import urllib.request
import urllib.error

import folder_paths

NODE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(NODE_DIR, "config.json")


def _load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _http_json(url, method="GET", headers=None, data=None, timeout=120):
    req = urllib.request.Request(url, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, body, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _image_to_data_url(image_tensor):
    """ComfyUI IMAGE tensor (1,H,W,C) float32 -> PNG data URL"""
    try:
        import numpy as np
        from PIL import Image
        arr = (image_tensor[0].cpu().numpy() * 255).clip(0, 255).astype("uint8")
        img = Image.fromarray(arr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        raise RuntimeError(f"图片编码失败: {e}")


SUCCESS_STATUSES = {"succeeded", "success", "completed", "finished", "done"}
FAIL_STATUSES = {"failed", "error", "cancelled", "canceled", "timeout"}


def _unwrap_task(res):
    """平台轮询响应为 {code, message, data:{...}}，解包出任务体"""
    if isinstance(res, dict) and isinstance(res.get("data"), dict) and "status" not in res and "status" in res["data"]:
        return res["data"]
    return res


class DeepSeekPromptEnhance:
    """用 DeepSeek v4-flash 增强视频提示词"""

    DEFAULT_SYSTEM = (
        "你是专业的视频生成提示词工程师。把用户的简短描述扩写成一段高质量的视频生成提示词："
        "包含主体、动作、场景、光影、镜头运动与画面质感（电影感）。"
        "只输出提示词本身，不要解释，不要引号，不超过200字。"
    )

    @classmethod
    def INPUT_TYPES(cls):
        cfg = _load_config().get("deepseek", {})
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "海上日出，电影感慢镜头"}),
                "system_prompt": ("STRING", {"multiline": True, "default": cls.DEFAULT_SYSTEM}),
                "model": (["deepseek-v4-flash", "deepseek-v4-pro"], {"default": "deepseek-v4-flash"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1}),
            },
            "optional": {},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("enhanced_prompt",)
    FUNCTION = "enhance"
    CATEGORY = "mzsj-api"
    OUTPUT_NODE = False

    def enhance(self, prompt, system_prompt, model, temperature):
        cfg = _load_config().get("deepseek", {})
        api_key = cfg.get("api_key", "")
        base_url = cfg.get("base_url", "https://api.deepseek.com")
        if not api_key:
            raise RuntimeError("缺少 DeepSeek API Key，请编辑 comfyui-mzsj-api/config.json")
        data = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            res = _http_json(
                f"{base_url}/chat/completions",
                method="POST",
                headers={"Authorization": f"Bearer {api_key}"},
                data=data,
                timeout=60,
            )
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"DeepSeek 调用失败 HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")
        text = res["choices"][0]["message"]["content"].strip()
        print(f"[DeepSeekEnhance] {text[:80]}...")
        return (text,)


class MzsjVideoGenerate:
    """调用 mzsjai.com 的 MiniMax H3 视频生成 API（提交+轮询+下载）"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "海上日出，电影感慢镜头"}),
                "model": (
                    [
                        "minimax/minimax-h3-fl2va",
                        "minimax/minimax-h3-ref2va",
                    ],
                    {"default": "minimax/minimax-h3-fl2va"},
                ),
                "resolution": (["720p", "1080p"], {"default": "720p"}),
                "duration": ("INT", {"default": 5, "min": 2, "max": 15, "step": 1}),
            },
            "optional": {
                "first_frame": ("IMAGE",),
                "last_frame": ("IMAGE",),
                "reference_image": ("IMAGE",),
                "extra_json": ("STRING", {"multiline": True, "default": "{}"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_filename", "video_fullpath")
    FUNCTION = "generate"
    CATEGORY = "mzsj-api"
    OUTPUT_NODE = True

    def generate(self, prompt, model, resolution, duration,
                 first_frame=None, last_frame=None, reference_image=None,
                 extra_json="{}"):
        cfg = _load_config().get("mzsj", {})
        api_key = cfg.get("api_key", "")
        base_url = cfg.get("base_url", "https://mzsjai.com").rstrip("/")
        poll_timeout = int(cfg.get("poll_timeout_seconds", 1200))
        if not api_key:
            raise RuntimeError("缺少 mzsjai API Key，请编辑 comfyui-mzsj-api/config.json")

        payload = {
            "model": model,
            "prompt": prompt,
            "resolution": resolution,
            "duration": duration,
        }
        # 图生视频素材（字段名若与平台不符，可用 extra_json 覆盖）
        if first_frame is not None:
            payload["first_frame_image"] = _image_to_data_url(first_frame)
        if last_frame is not None:
            payload["last_frame_image"] = _image_to_data_url(last_frame)
        if reference_image is not None:
            payload["reference_images"] = [_image_to_data_url(reference_image)]
        try:
            payload.update(json.loads(extra_json or "{}"))
        except json.JSONDecodeError:
            raise RuntimeError("extra_json 不是合法 JSON")

        headers = {"Authorization": f"Bearer {api_key}"}

        # 1) 提交任务（提交响应为扁平结构，无需解包）
        try:
            task = _http_json(
                f"{base_url}/v1/video/generations",
                method="POST", headers=headers, data=payload, timeout=120,
            )
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"任务提交失败 HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")
        task_id = task.get("id") or task.get("task_id")
        if not task_id:
            raise RuntimeError(f"API 未返回任务 ID: {json.dumps(task, ensure_ascii=False)[:500]}")
        print(f"[MzsjVideo] 任务已提交: {task_id}")

        # 2) 轮询状态（平台返回大写状态如 IN_PROGRESS，统一转小写比较）
        start = time.time()
        status = str(task.get("status", "queued")).lower()
        while True:
            if status in SUCCESS_STATUSES:
                break
            if status in FAIL_STATUSES:
                raise RuntimeError(f"任务失败: {json.dumps(task, ensure_ascii=False)[:500]}")
            if time.time() - start > poll_timeout:
                raise RuntimeError(f"任务轮询超时（{poll_timeout}s），task_id={task_id}")
            time.sleep(int(cfg.get("poll_interval_seconds", 8)))
            try:
                task = _unwrap_task(_http_json(
                    f"{base_url}/v1/video/generations/{task_id}",
                    headers=headers, timeout=60,
                ))
            except urllib.error.HTTPError as e:
                raise RuntimeError(f"查询任务失败 HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")
            status = str(task.get("status", "processing")).lower()
            print(f"[MzsjVideo] {task_id} -> {status}")

        # 3) 下载视频到 output 目录（优先 result_url，其次常见字段）
        video_url = task.get("result_url") or task.get("video_url") or task.get("url")
        if not video_url:
            for key in ("output", "result", "data", "video"):
                v = task.get(key)
                if isinstance(v, dict):
                    video_url = v.get("result_url") or v.get("video_url") or v.get("url")
                    if video_url:
                        break
                elif isinstance(v, str) and v.startswith("http"):
                    video_url = v
                    break
        if isinstance(video_url, str) and not video_url.startswith("http"):
            video_url = base_url + video_url
        if not video_url:
            raise RuntimeError(f"未找到视频地址: {json.dumps(task, ensure_ascii=False)[:800]}")

        out_dir = os.path.join(folder_paths.get_output_directory(), "mzsj")
        os.makedirs(out_dir, exist_ok=True)
        filename = f"mzsj_{task_id}.mp4"
        full_path = os.path.join(out_dir, filename)
        req = urllib.request.Request(video_url, headers=headers)
        with urllib.request.urlopen(req, timeout=300) as resp, open(full_path, "wb") as f:
            f.write(resp.read())
        print(f"[MzsjVideo] 已保存: {full_path}")
        return (filename, full_path)


NODE_CLASS_MAPPINGS = {
    "DeepSeekPromptEnhance": DeepSeekPromptEnhance,
    "MzsjVideoGenerate": MzsjVideoGenerate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DeepSeekPromptEnhance": "DeepSeek 提示词增强 (v4-flash)",
    "MzsjVideoGenerate": "MZSJ 视频生成 (MiniMax H3 API)",
}
