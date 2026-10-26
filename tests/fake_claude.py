"""測試用的假 claude:依環境變數決定要怎麼回應,不會真的呼叫 Claude。"""

import json
import os
import sys
import time
from pathlib import Path

REVIEW = {
    "valid_photo": True,
    "invalid_description": "",
    "multiple_people": False,
    "clothing": {"status": "pass", "comment": "棉質。"},
    "shoes": {"status": "pass", "comment": "布鞋。"},
    "hair": {"status": "pass", "comment": "馬尾。"},
    "accessories": {"status": "pass", "comment": "沒有首飾。"},
    "mask": {"status": "pass", "comment": "沒戴口罩。"},
    "glasses": {"status": "pass", "comment": "沒戴眼鏡。"},
    "overall": "合格",
}


def main() -> None:
    # 真的 claude 輸出 UTF-8;Windows 的 Python 預設是 cp950,要明確指定
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    mode = os.environ["FAKE_CLAUDE_MODE"]

    counter = Path(os.environ["FAKE_CLAUDE_COUNTER"])
    with counter.open("a", encoding="utf-8") as handle:
        handle.write("call\n")
    calls = len(counter.read_text(encoding="utf-8").splitlines())

    cwd = Path.cwd()
    Path(os.environ["FAKE_CLAUDE_LOG"]).write_text(
        json.dumps(
            {"cwd": str(cwd), "files": sorted(p.name for p in cwd.iterdir()), "args": sys.argv[1:]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    if mode == "hang":
        time.sleep(30)
    elif mode == "always_fail" or (mode == "fail_then_ok" and calls == 1):
        print("claude 當掉了", file=sys.stderr)
        sys.exit(1)
    elif mode == "bad_json":
        print("這不是 JSON")
    elif mode == "is_error":
        print(json.dumps({"is_error": True, "result": "boom"}))
    elif mode == "prose_result":
        text = "好的,以下是結果:\n" + json.dumps(REVIEW, ensure_ascii=False) + "\n希望有幫助"
        print(json.dumps({"is_error": False, "result": text}, ensure_ascii=False))
    else:  # ok、fail_then_ok 的第二次
        envelope = {
            "is_error": False,
            "structured_output": REVIEW,
            "result": json.dumps(REVIEW, ensure_ascii=False),
            "permission_denials": [],
        }
        print(json.dumps(envelope, ensure_ascii=False))


if __name__ == "__main__":
    main()
