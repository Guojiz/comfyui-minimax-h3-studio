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
import re

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
TASK_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _validate_task_id(task_id):
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise RuntimeError(f"provider 返回的任务 ID 不合法: {task_id!r}")
    return task_id


def _allowed_download_hosts(cfg, base_url):
    hosts = {urllib.parse.urlsplit(base_url).netloc}
    for extra in (cfg.get("allowed_download_hosts") or []):
        hosts.add(str(extra).strip())
    return {host for host in hosts if host}


def _download_video(video_url, headers, out_path, max_bytes):
    req = urllib.request.Request(video_url, headers=headers)
    with urllib.request.urlopen(req, timeout=300) as resp, open(out_path, "wb") as f:
        total = 0
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f"视频下载超过大小上限（{max_bytes} 字节）")
            f.write(chunk)


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
                "size": ("STRING", {"default": "768x448"}),
                "first_frame_url": ("STRING", {"default": ""}),
                "last_frame_url": ("STRING", {"default": ""}),
                "reference_image_urls": ("STRING", {"multiline": True, "default": ""}),
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

    def generate(self, prompt, model, resolution, duration, size="768x448",
                 first_frame_url="", last_frame_url="", reference_image_urls="",
                 first_frame=None, last_frame=None, reference_image=None,
                 extra_json="{}"):
        cfg = _load_config().get("mzsj", {})
        api_key = cfg.get("api_key", "")
        base_url = cfg.get("base_url", "https://mzsjai.com").rstrip("/")
        poll_timeout = int(cfg.get("poll_timeout_seconds", 1200))
        if not api_key:
            raise RuntimeError("缺少 mzsjai API Key，请编辑 comfyui-mzsj-api/config.json")

        api_mode = str(cfg.get("api_mode", "videos")).lower()
        image_urls = [url.strip() for url in (first_frame_url, last_frame_url) if url.strip()]
        image_urls.extend(line.strip() for line in reference_image_urls.splitlines() if line.strip())
        if api_mode == "videos":
            if any(value is not None for value in (first_frame, last_frame, reference_image)):
                raise RuntimeError(
                    "当前 /v1/videos 网关要求 HTTPS 图片地址；请使用 first_frame_url、"
                    "last_frame_url 或 reference_image_urls。不要把本地 IMAGE/data URL 直接提交。"
                )
            bad_urls = [url for url in image_urls if not url.startswith("https://")]
            if bad_urls:
                raise RuntimeError("参考图片必须是 HTTPS 地址")
            payload = {
                "model": model,
                "prompt": prompt,
                "seconds": duration,
                "size": size or ("1280x720" if resolution == "1080p" else "768x448"),
            }
            if image_urls:
                payload["images"] = image_urls
            submit_path = "/v1/videos"
        else:
            payload = {
                "model": model,
                "prompt": prompt,
                "resolution": resolution,
                "duration": duration,
            }
            if first_frame is not None:
                payload["first_frame_image"] = _image_to_data_url(first_frame)
            if last_frame is not None:
                payload["last_frame_image"] = _image_to_data_url(last_frame)
            if reference_image is not None:
                payload["reference_images"] = [_image_to_data_url(reference_image)]
            if image_urls:
                payload["images"] = image_urls
            submit_path = "/v1/video/generations"
        try:
            payload.update(json.loads(extra_json or "{}"))
        except json.JSONDecodeError:
            raise RuntimeError("extra_json 不是合法 JSON")

        headers = {"Authorization": f"Bearer {api_key}"}

        # 1) 提交任务（提交响应为扁平结构，无需解包）
        try:
            task = _http_json(
                f"{base_url}{submit_path}",
                method="POST", headers=headers, data=payload, timeout=120,
            )
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"任务提交失败 HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")
        task_id = _validate_task_id(task.get("id") or task.get("task_id"))
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
                    f"{base_url}{submit_path}/{urllib.parse.quote(task_id, safe='')}",
                    headers=headers, timeout=60,
                ))
            except urllib.error.HTTPError as e:
                raise RuntimeError(f"查询任务失败 HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")
            status = str(task.get("status", "processing")).lower()
            print(f"[MzsjVideo] {task_id} -> {status}")

        # 3) 下载视频到 output 目录（优先 result_url，其次常见字段）
        video_url = task.get("content_url") or task.get("result_url") or task.get("video_url") or task.get("url")
        if not video_url and isinstance(task.get("metadata"), dict):
            video_url = task["metadata"].get("url")
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
            if api_mode == "videos":
                video_url = f"{base_url}{submit_path}/{task_id}/content"
            else:
                raise RuntimeError(f"未找到视频地址: {json.dumps(task, ensure_ascii=False)[:800]}")

        out_dir = os.path.join(folder_paths.get_output_directory(), "mzsj")
        os.makedirs(out_dir, exist_ok=True)
        filename = f"mzsj_{task_id}.mp4"
        full_path = os.path.join(out_dir, filename)
        allowed_hosts = _allowed_download_hosts(cfg, base_url)
        download_host = urllib.parse.urlsplit(video_url).netloc
        if download_host not in allowed_hosts:
            raise RuntimeError(
                f"拒绝下载非白名单主机 {download_host} 的视频；"
                "请在 config.json 的 allowed_download_hosts 中显式声明"
            )
        download_headers = (
            headers if download_host == urllib.parse.urlsplit(base_url).netloc else {}
        )
        max_bytes = int(cfg.get("max_download_bytes", 4 * 1024 * 1024 * 1024))
        _download_video(video_url, download_headers, full_path, max_bytes)
        print(f"[MzsjVideo] 已保存: {full_path}")
        return {
            "ui": {"video_paths": [full_path], "video_filenames": [filename]},
            "result": (filename, full_path),
        }


NODE_CLASS_MAPPINGS = {
    "DeepSeekPromptEnhance": DeepSeekPromptEnhance,
    "MzsjVideoGenerate": MzsjVideoGenerate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DeepSeekPromptEnhance": "DeepSeek 提示词增强 (v4-flash)",
    "MzsjVideoGenerate": "MZSJ 视频生成 (MiniMax H3 API)",
}
