#!/bin/bash
# init-project — 初始化 AI Video Studio 媒体项目骨架
# 用法: init-project.sh [项目目录] [--name "项目标题"] [--git] [--dry-run]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 模板随 Skill 自带，单独安装到 .qoder/skills 或其他 Agent 平台时也可直接运行。
TPL_DIR="${PROJECT_TEMPLATE_DIR:-$SCRIPT_DIR/../assets/project-template}"

PROJECT_DIR=""
PROJECT_NAME=""
DO_GIT=0
DO_DRY=0

usage() {
  cat <<'EOF'
用法: init-project.sh [项目目录] [--name "项目标题"] [--git] [--dry-run]

创建 project.md、shots/index.md、source、brief-and-story、characters、scenes、styles、props、
references、storyboards、workflows、audio、final、runs 目录，以及适合媒体项目的 .gitignore。

选项:
  --name NAME   在新建的 project.md 中填入项目标题（默认取目录名）
  --git         目录不是 Git 仓库时执行 git init（默认不执行）
  --dry-run     只打印将要创建的内容，不写入任何文件
  -h, --help    显示帮助

环境变量:
  PROJECT_TEMPLATE_DIR  模板目录（默认脚本上三级 assets/project-template）

已有文件和目录永远不会被覆盖或删除。
EOF
}

log() { printf '%s\n' "$*"; }

run_or_dry() {
  if [ "$DO_DRY" = 1 ]; then
    log "dry-run: $*"
  else
    "$@"
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --name)
      if [ $# -lt 2 ]; then log "错误: --name 需要参数" >&2; exit 2; fi
      PROJECT_NAME="$2"
      shift 2
      ;;
    --git) DO_GIT=1; shift;;
    --dry-run) DO_DRY=1; shift;;
    -h|--help) usage; exit 0;;
    -*) log "错误: 未知选项 $1" >&2; usage >&2; exit 2;;
    *)
      if [ -n "$PROJECT_DIR" ]; then
        log "错误: 只能指定一个项目目录" >&2
        exit 2
      fi
      PROJECT_DIR="$1"
      shift
      ;;
  esac
done

PROJECT_DIR="${PROJECT_DIR:-project}"
PROJECT_NAME="${PROJECT_NAME:-$(basename "$PROJECT_DIR")}"

if [ ! -d "$TPL_DIR" ]; then
  log "错误: 找不到模板目录 $TPL_DIR" >&2
  exit 2
fi

DIRS="source brief-and-story characters scenes styles props references storyboards workflows shots audio final runs"

run_or_dry mkdir -p "$PROJECT_DIR"
for d in $DIRS; do
  run_or_dry mkdir -p "$PROJECT_DIR/$d"
done

CREATED_PROJECT_MD=0
if [ -e "$PROJECT_DIR/project.md" ]; then
  log "保留已有 project.md: $PROJECT_DIR/project.md"
else
  run_or_dry cp "$TPL_DIR/project.md" "$PROJECT_DIR/project.md"
  CREATED_PROJECT_MD=1
fi

if [ -e "$PROJECT_DIR/.gitignore" ]; then
  log "保留已有 .gitignore: $PROJECT_DIR/.gitignore"
else
  run_or_dry cp "$TPL_DIR/.gitignore" "$PROJECT_DIR/.gitignore"
fi

if [ -e "$PROJECT_DIR/shots/index.md" ]; then
  log "保留已有 shots/index.md: $PROJECT_DIR/shots/index.md"
else
  run_or_dry cp "$TPL_DIR/shots/index.md" "$PROJECT_DIR/shots/index.md"
fi

if [ "$CREATED_PROJECT_MD" = 1 ] && [ "$DO_DRY" = 0 ]; then
  TMP_MD="$(mktemp "${TMPDIR:-/tmp}/init-project.XXXXXX")"
  while IFS= read -r line; do
    line="${line//__PROJECT_NAME__/$PROJECT_NAME}"
    line="${line//__PROJECT_DIR__/$PROJECT_DIR}"
    printf '%s\n' "$line"
  done < "$TPL_DIR/project.md" > "$TMP_MD"
  mv "$TMP_MD" "$PROJECT_DIR/project.md"
fi

if [ "$DO_GIT" = 1 ]; then
  if [ -d "$PROJECT_DIR/.git" ]; then
    log "已是 Git 仓库: $PROJECT_DIR/.git"
  elif run_or_dry git init -b main "$PROJECT_DIR"; then
    :
  else
    run_or_dry git init "$PROJECT_DIR"
  fi
fi

log "项目骨架: $PROJECT_DIR"
for d in $DIRS; do
  log "  $d/"
done
log "文件: project.md, shots/index.md, .gitignore"
if [ "$DO_GIT" = 1 ]; then log "Git: 已初始化"; fi
if [ "$DO_DRY" = 1 ]; then log "（dry-run：未写入任何内容）"; fi
