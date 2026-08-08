"""
ComfyUI Huoshen Image Nodes — 接入 huoshenai.net 的 gpt-image-2 生图 API
OpenAI 兼容接口（/v1/images/generations），输出标准 IMAGE 张量，
可直接连接 MZSJ 视频生成节点的首帧/尾帧/参考图输入。
"""
import json
import os
import base64
import io
import time
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


class HuoshenImageGenerate:
    """调用 huoshenai.net gpt-image-2 生成图片"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "一只橘猫坐在窗台上看雨，电影感"}),
                "size": (["1024x1024", "1536x1024", "1024x1536", "auto"], {"default": "1024x1024"}),
            },
            "optional": {
                "filename_prefix": ("STRING", {"default": "huoshen"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "image_path")
    FUNCTION = "generate"
    CATEGORY = "mzsj-api"
    OUTPUT_NODE = True

    def generate(self, prompt, size, filename_prefix="huoshen"):
        cfg = _load_config().get("huoshen", {})
        api_key = cfg.get("api_key", "")
        base_url = cfg.get("base_url", "https://huoshenai.net").rstrip("/")
        model = cfg.get("model", "gpt-image-2")
        if not api_key:
            raise RuntimeError("缺少 huoshen API Key，请编辑 comfyui-huoshen-image/config.json")

        payload = {"model": model, "prompt": prompt, "n": 1}
        if size != "auto":
            payload["size"] = size

        try:
            req = urllib.request.Request(
                f"{base_url}/v1/images/generations",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                res = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"生图请求失败 HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")

        data = res.get("data", [])
        if not data:
            raise RuntimeError(f"API 未返回图片: {json.dumps(res, ensure_ascii=False)[:500]}")
        item = data[0]

        # 兼容 b64_json 与 url 两种返回
        if item.get("b64_json"):
            img_bytes = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            with urllib.request.urlopen(item["url"], timeout=120) as r:
                img_bytes = r.read()
        else:
            raise RuntimeError(f"响应中无图片数据: {json.dumps(item, ensure_ascii=False)[:300]}")

        import numpy as np
        import torch
        from PIL import Image

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        arr = np.asarray(img).astype("float32") / 255.0
        tensor = torch.from_numpy(arr)[None,]  # (1,H,W,3)

        # 保存到 output 目录，便于在输出面板查看
        out_dir = folder_paths.get_output_directory()
        filename = f"{filename_prefix}_{int(time.time())}.png"
        img.save(os.path.join(out_dir, filename))
        print(f"[HuoshenImage] 已保存: {os.path.join(out_dir, filename)}")
        return (tensor, os.path.join(out_dir, filename))


NODE_CLASS_MAPPINGS = {
    "HuoshenImageGenerate": HuoshenImageGenerate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HuoshenImageGenerate": "火神 生图 (gpt-image-2 API)",
}
