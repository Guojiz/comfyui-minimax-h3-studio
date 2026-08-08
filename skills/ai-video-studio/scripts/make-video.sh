#!/bin/bash
# make-video — 一句话出片（DeepSeek 扩写 → gpt-image-2 生图 → MiniMax H3 视频）
# 用法: ./make-video.sh "雨夜霓虹街道，赛博朋克" [--duration 5] [--resolution 720p] [--size 1536x1024] [--no-open] [--dry-run]
# 配套: ./init-project.sh 初始化项目；./run-workflow.py 通用提交/轮询 API 工作流
set -euo pipefail

SERVER="${COMFY_SERVER:-http://127.0.0.1:8188}"
# 默认使用 Skill 自带模板，单独安装 Skill 时也可运行；可用 COMFY_WORKFLOW_TPL 覆盖。
WORKFLOW_TPL="${COMFY_WORKFLOW_TPL:-$(cd "$(dirname "$0")/.." && pwd)/assets/workflow_api_mzsj_video.json}"
PY="${COMFY_PYTHON:-$HOME/ComfyUI-Installs/ComfyUI/standalone-env/bin/python3.13}"
[ -x "$PY" ] || PY=python3
OUTPUT_DIR="${COMFY_OUTPUT_DIR:-$HOME/ComfyUI-Installs/ComfyUI/ComfyUI/output}"

PROMPT=""
DURATION=5
RESOLUTION="720p"
SIZE="1536x1024"
OPEN=1
DRY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --duration) DURATION="$2"; shift 2;;
    --resolution) RESOLUTION="$2"; shift 2;;
    --size) SIZE="$2"; shift 2;;
    --no-open) OPEN=0; shift;;
    --dry-run) DRY=1; shift;;
    *) PROMPT="$1"; shift;;
  esac
done

[ -z "$PROMPT" ] && echo "用法: make-video.sh \"你的视频描述\" [选项]" && exit 1

# 生成临时工作流（注入参数）；macOS mktemp 要求 X 在模板末尾，扩展名对 python 解析无影响
TMP=$(mktemp /tmp/make-video-XXXXXX)
trap 'rm -f "$TMP"' EXIT
"$PY" - "$WORKFLOW_TPL" "$TMP" "$PROMPT" "$DURATION" "$RESOLUTION" "$SIZE" <<'EOF'
import json, sys
tpl, out, prompt, dur, res, size = sys.argv[1:7]
wf = json.load(open(tpl))
wf["1"]["inputs"]["prompt"] = prompt
wf["2"]["inputs"]["size"] = size
wf["3"]["inputs"]["duration"] = int(dur)
wf["3"]["inputs"]["resolution"] = res
json.dump(wf, open(out, "w"), ensure_ascii=False)
EOF

if [ "$DRY" = 1 ]; then echo "dry-run: 校验通过，未启动服务、未提交"; cat "$TMP"; exit 0; fi

# 健康检查；仅真实提交时执行。服务未运行则自动后台拉起并等待就绪（最长 120 秒）。
COMFY_ROOT="${COMFY_ROOT:-$HOME/ComfyUI-Installs/ComfyUI/ComfyUI}"
if ! curl -s -m 5 "$SERVER/object_info" | grep -q "MzsjVideoGenerate"; then
  echo "⚠️ ComfyUI 未运行，正在自动拉起..."
  PORT="${SERVER##*:}"
  nohup "$COMFY_ROOT/.venv/bin/python3" -s "$COMFY_ROOT/main.py" \
    --enable-manager \
    --extra-model-paths-config "$HOME/Library/Application Support/Comfy Desktop/shared_model_paths.yaml" \
    --input-directory "$HOME/ComfyUI-Shared/input" \
    --output-directory "$HOME/ComfyUI-Shared/output" \
    --port "$PORT" >> "$HOME/Library/Logs/comfyui-headless.log" 2>&1 &
  READY=0
  for _ in $(seq 1 60); do
    sleep 2
    if curl -s -m 3 "$SERVER/object_info" | grep -q "MzsjVideoGenerate"; then READY=1; break; fi
  done
  [ "$READY" = 1 ] || { echo "❌ 自动拉起超时，查看 $HOME/Library/Logs/comfyui-headless.log"; exit 2; }
  echo "✅ ComfyUI 已就绪"
fi

echo "🚀 提交任务：$PROMPT"
"$PY" - "$SERVER" "$TMP" "$OUTPUT_DIR" "$OPEN" <<'EOF'
import json, sys, time, urllib.request, subprocess, glob, os
server, wf_path, out_dir, do_open = sys.argv[1:5]
wf = json.load(open(wf_path))
before_imgs = set(glob.glob(f"{out_dir}/huoshen_*.png"))
before_vids = set(glob.glob(f"{out_dir}/mzsj/*.mp4"))

req = urllib.request.Request(f"{server}/prompt",
    data=json.dumps({"prompt": wf}).encode(),
    headers={"Content-Type": "application/json"})
pid = json.loads(urllib.request.urlopen(req, timeout=30).read())["prompt_id"]
print(f"任务 ID: {pid}")

start = time.time()
while time.time() - start < 900:
    time.sleep(8)
    h = json.loads(urllib.request.urlopen(f"{server}/history/{pid}", timeout=10).read())
    if pid not in h:
        print(f"⏳ {int(time.time()-start)}s ...")
        continue
    st = h[pid].get("status", {})
    if st.get("status_str") == "error":
        for m in st.get("messages", []):
            if m[0] == "execution_error":
                print("❌", m[1].get("node_type"), str(m[1].get("exception_message"))[:300])
        sys.exit(3)
    if st.get("completed"):
        new_imgs = sorted(set(glob.glob(f"{out_dir}/huoshen_*.png")) - before_imgs)
        new_vids = sorted(set(glob.glob(f"{out_dir}/mzsj/*.mp4")) - before_vids)
        for f in new_imgs + new_vids:
            print("✅", f)
        if do_open == "1":
            for f in new_imgs + new_vids:
                subprocess.run(["open", f])
        sys.exit(0)
print("❌ 超时")
sys.exit(4)
EOF
