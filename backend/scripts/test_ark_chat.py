import argparse
import json
import os
import sys
import time


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV_FILE = os.path.join(ROOT_DIR, ".env")

os.chdir(ROOT_DIR)

if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.services.ark_ai import (  # noqa: E402
    build_search_chat_prompt,
    call_ark_chat,
    extract_item_search_filters,
    extract_quick_publish_fields,
)


CHAT_SYSTEM_PROMPT = (
    "你是校园失物招领系统的 AI 助手。"
    "请用简洁、自然的中文回答，优先围绕失物招领场景提供帮助。"
)


def timed_call(label: str, fn, *args, **kwargs):
    started = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - started
    print(f"[{label}] 耗时 {elapsed:.2f}s")
    return result


def read_multiline_block() -> str | None:
    print("\n进入多行输入模式。")
    print("输入内容后，单独输入 /send 发送，/cancel 取消，/exit 退出。")
    lines: list[str] = []
    while True:
        line = input("... ")
        command = line.strip().lower()
        if command == "/exit":
            return None
        if command == "/cancel":
            return ""
        if command == "/send":
            return "\n".join(lines).strip()
        lines.append(line)


def run_chat_mode(multiline: bool = False) -> None:
    if multiline:
        print("进入 chat 测试模式（多行）。")
    else:
        print("进入 chat 测试模式，输入 exit 或 quit 退出，输入 /multi 切换多行。")

    while True:
        if multiline:
            user_input = read_multiline_block()
            if user_input is None:
                print("已结束对话。")
                return
            if not user_input:
                continue
        else:
            user_input = input("\n你: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("已结束对话。")
                return
            if user_input.lower() == "/multi":
                multiline = True
                continue

        try:
            reply = timed_call(
                "chat",
                call_ark_chat,
                [
                    {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.2,
                max_tokens=512,
            )
            print(f"AI: {reply}")
        except Exception as exc:
            print(f"AI 调用失败: {exc}")


def run_extract_mode(text: str) -> None:
    result = timed_call("extract", extract_item_search_filters, text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def run_quick_publish_mode(text: str, item_type: str | None) -> None:
    result = timed_call("quick-publish", extract_quick_publish_fields, text, item_type)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def run_prompt_mode(text: str) -> None:
    messages = build_search_chat_prompt(text)
    for message in messages:
        print(f"[{message['role']}]")
        print(message["content"])
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="测试 chat 风格的方舟调用与字段适配。")
    parser.add_argument(
        "--mode",
        choices=["chat", "extract", "quick", "prompt"],
        default="chat",
        help="chat=直接对话，extract=用 chat 风格提取字段，quick=快速发布字段提取，prompt=查看提取提示词",
    )
    parser.add_argument("--text", help="extract / quick / prompt 模式下要测试的文本")
    parser.add_argument("--type", choices=["lost", "found"], help="quick 模式可选")
    parser.add_argument("--multi", action="store_true", help="chat 模式启用多行输入")
    args = parser.parse_args()

    if args.mode == "chat":
        run_chat_mode(multiline=args.multi)
        return

    if not args.text:
        raise SystemExit("extract / quick / prompt 模式需要提供 --text")

    if args.mode == "extract":
        run_extract_mode(args.text)
        return

    if args.mode == "quick":
        run_quick_publish_mode(args.text, args.type)
        return

    run_prompt_mode(args.text)


if __name__ == "__main__":
    main()
