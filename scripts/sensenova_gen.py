#!/usr/bin/env python3
"""SenseNova 文生图 CLI（sensenova-u1.5-lite）。

默认：无水印、最高画质、PNG、b64_json 直接落盘。
每次生成产出图片 + 同编号 .txt 元数据（完整参数 + prompt + usage）。
纯标准库，开箱即用。

用法：
  python sensenova_gen.py gen -p "prompt" --aspect 16:9 --slug name
  python sensenova_gen.py batch items.json --outdir Render/概念图
  python sensenova_gen.py models
  python sensenova_gen.py size-check [--size WxH]
"""
import argparse
import base64
import json
import os
import struct
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_URL = "https://token.sensenova.cn/v1/images/generations"
MODELS_URL = "https://token.sensenova.cn/v1/models"
DEFAULT_MODEL = "sensenova-u1.5-lite"

# 常见比例 -> 高画质尺寸（均为 32 倍数、512-4096、宽高比 ≤3，已实测通过）
ASPECT_SIZES = {
    "1:1":  (3072, 3072),
    "16:9": (4096, 2304),
    "9:16": (2304, 4096),
    "4:3":  (4096, 3072),
    "3:4":  (3072, 4096),
    "3:2":  (3840, 2560),
    "2:3":  (2560, 3840),
    "21:9": (4096, 1760),
}


# ── 工具函数 ────────────────────────────────────────────────

def load_key():
    k = os.environ.get("SENSENOVA_API_KEY")
    if k and k.strip():
        return k.strip()
    f = Path.home() / ".config" / "sensenova" / "api_key"
    if f.exists():
        k = f.read_text(encoding="utf-8").strip()
        if k:
            return k
    sys.exit("ERROR: 未找到 API key。设置环境变量 SENSENOVA_API_KEY，"
             "或把 key 写入 ~/.config/sensenova/api_key（单行）。")


def validate_size(w, h):
    """真实规则：WIDTHxHEIGHT，宽高 32 倍数，512-4096，宽高比 ≤3。"""
    if not (isinstance(w, int) and isinstance(h, int)):
        return False
    if not (512 <= w <= 4096 and 512 <= h <= 4096):
        return False
    if w % 32 or h % 32:
        return False
    if max(w, h) / min(w, h) > 3:
        return False
    return True


def parse_size(size_arg, aspect_arg):
    if aspect_arg:
        if aspect_arg not in ASPECT_SIZES:
            sys.exit(f"未知比例 {aspect_arg}；可选：{', '.join(ASPECT_SIZES)}")
        w, h = ASPECT_SIZES[aspect_arg]
    elif size_arg:
        try:
            w, h = map(int, size_arg.lower().split("x"))
        except ValueError:
            sys.exit(f"尺寸格式错误 {size_arg}，应为 WxH 如 2048x2048")
    else:
        w, h = ASPECT_SIZES["1:1"]
    if not validate_size(w, h):
        sys.exit(f"尺寸非法 {w}x{h}：宽高须为 32 倍数、512-4096、宽高比 ≤3")
    return f"{w}x{h}", w, h


def next_number(outdir):
    """扫描 outdir 中 NNNN-* 文件，返回下一个编号。"""
    nums = []
    for p in outdir.iterdir():
        if p.is_file() and p.stem[:4].isdigit():
            nums.append(int(p.stem[:4]))
    return (max(nums) + 1) if nums else 1


def png_dims(img_bytes):
    if img_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", img_bytes[16:24])
        return f"{w}x{h}"
    return None


def write_metadata(txt_path, meta):
    """写同编号 .txt：键值对 + prompt 全文。"""
    lines = ["# SenseNova 生成元数据"]
    for k, v in meta.items():
        if k == "prompt":
            continue
        lines.append(f"{k}: {v}")
    lines.append("")
    lines.append("=== PROMPT ===")
    lines.append(meta["prompt"])
    if meta.get("negative_prompt"):
        lines.append("")
        lines.append("=== NEGATIVE PROMPT ===")
        lines.append(meta["negative_prompt"])
    txt_path.write_text("\n".join(lines), encoding="utf-8")


def call_api(key, payload, timeout=300):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        raw = urllib.request.urlopen(req, timeout=timeout).read()
        return json.loads(raw)
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:500]
        sys.exit(f"API HTTP {e.code}: {msg}")
    except Exception as e:
        sys.exit(f"API 错误: {type(e).__name__}: {e}")


def extract_image_bytes(data):
    d0 = data["data"][0]
    b64 = d0.get("b64_json") or d0.get("b64")
    if b64:
        return base64.b64decode(b64)
    url = d0.get("url")
    if url:
        print(f"[fallback] b64 缺失，下载 URL: {url[:80]}...")
        return urllib.request.urlopen(url, timeout=120).read()
    sys.exit("响应中无 b64_json 也无 url")


def build_payload(args, prompt, size_str):
    payload = {
        "model": args.model,
        "prompt": prompt,
        "n": 1,
        "size": size_str,
        "watermark": False,
        "response_format": "b64_json",
        "output_format": args.format,
    }
    if getattr(args, "negative", None):
        payload["negative_prompt"] = args.negative
    if getattr(args, "seed", None) is not None:
        payload["seed"] = args.seed
    if getattr(args, "style", None):
        payload["style"] = args.style
    if getattr(args, "quality", None):
        payload["quality"] = args.quality
    if getattr(args, "temperature", None) is not None:
        payload["temperature"] = args.temperature
    return payload


# ── 子命令 ──────────────────────────────────────────────────

def cmd_gen(args):
    key = load_key()
    size_str, w, h = parse_size(args.size, args.aspect)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    prompt = args.prompt
    if not prompt:
        prompt = sys.stdin.read().strip()
    if not prompt:
        sys.exit("无 prompt：用 -p 传入或通过 stdin")

    seed = args.seed if args.seed is not None else (int(time.time() * 1000) % (2**31))
    payload = build_payload(args, prompt, size_str)

    print(f"[gen] model={args.model} size={size_str} fmt={args.format} watermark=false seed={seed}")
    print(f"[gen] prompt ({len(prompt)} chars): {prompt[:120]}{'...' if len(prompt)>120 else ''}")

    t0 = time.time()
    data = call_api(key, payload)
    dt = time.time() - t0
    img = extract_image_bytes(data)
    dims = png_dims(img)

    num = next_number(outdir)
    slug = (args.slug or "image").replace(" ", "-")[:40]
    base = f"{num:04d}-{slug}"
    img_path = outdir / f"{base}.{args.format}"
    txt_path = outdir / f"{base}.txt"
    img_path.write_bytes(img)

    usage = data.get("usage", {})
    meta = {
        "file": img_path.name,
        "model": args.model,
        "size_requested": size_str,
        "size_response": data.get("size", ""),
        "image_dimensions": dims or "?",
        "aspect": args.aspect or "custom",
        "output_format": data.get("output_format", args.format),
        "watermark": "false",
        "seed": seed,
        "style": args.style or "",
        "quality": args.quality or "",
        "temperature": args.temperature if args.temperature is not None else "",
        "negative_prompt": args.negative or "",
        "prompt": prompt,
        "created_ts": data.get("created", ""),
        "usage_input_tokens": usage.get("input_tokens", ""),
        "usage_output_tokens": usage.get("output_tokens", ""),
        "usage_total_tokens": usage.get("total_tokens", ""),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "elapsed_s": f"{dt:.1f}",
        "bytes": len(img),
    }
    write_metadata(txt_path, meta)

    print(f"[ok] {img_path} ({len(img)} bytes, {dims})")
    print(f"[ok] {txt_path} (元数据)")
    print(f"[ok] tokens: in={usage.get('input_tokens')} out={usage.get('output_tokens')} "
          f"total={usage.get('total_tokens')} | {dt:.1f}s")


def cmd_batch(args):
    key = load_key()
    items = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if not isinstance(items, list):
        sys.exit("批量文件须为 JSON 数组")
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    ok = skip = fail = 0
    for i, it in enumerate(items, 1):
        fid = it.get("id", f"{i:04d}")
        name = it.get("name", "item")
        prompt = it.get("prompt")
        if not prompt:
            print(f"[{i}/{len(items)}] {fid} SKIP: 无 prompt"); skip += 1; continue

        size_str, w, h = parse_size(it.get("size"), it.get("aspect", "1:1"))
        safe_name = str(name).replace("/", "-").replace(" ", "-")[:40]
        img_path = outdir / f"{fid}-{safe_name}.png"
        txt_path = outdir / f"{fid}-{safe_name}.txt"

        # 断点续传：已存在且 >10KB 跳过
        if img_path.exists() and img_path.stat().st_size > 10000:
            print(f"[{i}/{len(items)}] {fid} skip (exists, {img_path.stat().st_size}B)"); skip += 1; continue

        payload = {
            "model": args.model, "prompt": prompt, "n": 1, "size": size_str,
            "watermark": False, "response_format": "b64_json", "output_format": "png",
        }
        if it.get("negative"):
            payload["negative_prompt"] = it["negative"]
        if it.get("seed") is not None:
            payload["seed"] = it["seed"]

        print(f"[{i}/{len(items)}] {fid} gen size={size_str}...")
        try:
            t0 = time.time()
            data = call_api(key, payload)
            dt = time.time() - t0
            img = extract_image_bytes(data)
            img_path.write_bytes(img)
            dims = png_dims(img)
            usage = data.get("usage", {})
            meta = {
                "file": img_path.name, "model": args.model,
                "size_requested": size_str, "size_response": data.get("size", ""),
                "image_dimensions": dims or "?", "aspect": it.get("aspect", "custom"),
                "output_format": data.get("output_format", "png"),
                "watermark": "false", "seed": it.get("seed", ""),
                "negative_prompt": it.get("negative", ""), "prompt": prompt,
                "created_ts": data.get("created", ""),
                "usage_total_tokens": usage.get("total_tokens", ""),
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
                "elapsed_s": f"{dt:.1f}", "bytes": len(img),
            }
            write_metadata(txt_path, meta)
            print(f"[{i}/{len(items)}] {fid} ok ({len(img)}B, {dims}) {dt:.1f}s")
            ok += 1
            time.sleep(args.sleep)
        except SystemExit as e:
            print(f"[{i}/{len(items)}] {fid} FAIL: {e}"); fail += 1
            time.sleep(args.sleep * 2)

    print(f"\n完成: ok={ok} skip={skip} fail={fail} total={len(items)}")


def cmd_models(args):
    key = load_key()
    req = urllib.request.Request(MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=40).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"models HTTP {e.code}: {e.read().decode()[:300]}")
    ids = [d.get("id") for d in data.get("data", [])]
    img = [i for i in ids if any(k in i.lower() for k in ("u1", "image", "nova", "diffus"))]
    print("图像模型:", img if img else "(未识别到图像模型)")
    print("全部模型:", ids)


def cmd_size_check(args):
    print("比例预设：")
    for a, (w, h) in ASPECT_SIZES.items():
        print(f"  {a:6s} -> {w}x{h}  {'OK' if validate_size(w, h) else 'INVALID'}")
    if args.size:
        try:
            w, h = map(int, args.size.lower().split("x"))
        except ValueError:
            print(f"custom {args.size}: 格式错误（WxH）"); return
        ok = validate_size(w, h)
        print(f"\ncustom {w}x{h}: {'OK' if ok else 'INVALID'}")
        if not ok:
            print("  规则：宽高均为 32 倍数、512-4096、宽高比 ≤3")


# ── argparse ────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="SenseNova 文生图 CLI（u1.5-lite，默认无水印最高画质）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="单张生成")
    g.add_argument("-p", "--prompt", help="prompt（不传则读 stdin）")
    g.add_argument("--negative", help="负向提示词")
    g.add_argument("--aspect", choices=list(ASPECT_SIZES), help="比例预设")
    g.add_argument("--size", help="自定义尺寸 WxH（覆盖 --aspect）")
    g.add_argument("--seed", type=int, help="随机种子（复现用）")
    g.add_argument("--style", help="风格选项（如 vivid/natural，视 API 支持）")
    g.add_argument("--quality", help="质量选项（如 standard/hd，视 API 支持）")
    g.add_argument("--temperature", type=float, help="采样温度 0.0-1.0")
    g.add_argument("--format", choices=["png", "jpeg"], default="png", help="输出格式（默认 png）")
    g.add_argument("--slug", help="文件名slug（如 cyberpunk-city）")
    g.add_argument("--outdir", default="Render", help="输出目录")
    g.add_argument("--model", default=DEFAULT_MODEL, help="模型 ID")
    g.set_defaults(func=cmd_gen)

    b = sub.add_parser("batch", help="批量生成（JSON 文件）")
    b.add_argument("file", help="JSON 路径，数组：[{id,name,prompt,aspect?,negative?,seed?}]")
    b.add_argument("--outdir", default="Render", help="输出目录")
    b.add_argument("--sleep", type=float, default=3.0, help="成功后间隔秒（默认 3）")
    b.add_argument("--model", default=DEFAULT_MODEL, help="模型 ID")
    b.set_defaults(func=cmd_batch)

    m = sub.add_parser("models", help="查询当前可用模型")
    m.set_defaults(func=cmd_models)

    sc = sub.add_parser("size-check", help="校验尺寸规则")
    sc.add_argument("--size", help="自定义尺寸 WxH")
    sc.set_defaults(func=cmd_size_check)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
