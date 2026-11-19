#!/usr/bin/env python3
"""SFC 캠퍼스 찾기 — index.html 빌드 스크립트.

사용법:
    python3 build.py                 # 자료 기준일 = 오늘(KST)
    python3 build.py --date 2026.11.19

src/template.html 의 자리표시자(__DATA__ 등)를 src/data.json, src/assets/* 로 채워
저장소 루트의 index.html 을 만든다. index.html 은 직접 고치지 말고 항상 이 스크립트로 만든다.
"""
import argparse, base64, datetime, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
A = SRC / "assets"


def load_data():
    data = json.loads((SRC / "data.json").read_text(encoding="utf-8"))
    # 규칙: U는 가나다순
    data.sort(key=lambda g: g["u"])
    return data


def validate(data, template):
    problems = []
    pins = set(re.findall(r"'([^']+)':\[\d", template.split("const PINS", 1)[1].split("};", 1)[0]))
    for g in data:
        if g["u"] not in pins:
            problems.append(f"지도 핀 없음: {g['u']} (src/template.html 의 PINS 에 좌표 추가 필요)")
        schools = set(g.get("schools", []))
        for it in g["items"]:
            if it.get("def") and it["def"] not in schools:
                problems.append(f"{g['u']} / {it['n']}: def '{it['def']}' 가 schools 목록에 없음")
            if it.get("ig") and (it["ig"].startswith("@") or "/" in it["ig"]):
                problems.append(f"{g['u']} / {it['n']}: ig 는 아이디만 (@, URL 없이) — 현재 '{it['ig']}'")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="자료 기준일 (예: 2026.11.19). 생략하면 오늘(KST)")
    args = ap.parse_args()
    date = args.date or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y.%m.%d")

    t = (SRC / "template.html").read_text(encoding="utf-8")
    data = load_data()
    problems = validate(data, t)
    if problems:
        print("⚠️  확인 필요:\n  - " + "\n  - ".join(problems))

    svg = lambda f: (A / f).read_text(encoding="utf-8")
    m = "data:image/jpeg;base64," + base64.b64encode((A / "map.jpg").read_bytes()).decode()
    out = (t.replace("__MAP__", m)
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__QR__", (A / "qr.min.js").read_text(encoding="utf-8"))
            .replace("__DATE__", date)
            .replace("__SFC__", svg("sfc.svg"))
            .replace("__HAK__", svg("hakshin.svg"))
            .replace("__SFCW__", svg("student-for-christ.svg")))
    left = re.findall(r"__[A-Z]+__", out)
    if left:
        sys.exit(f"치환되지 않은 자리표시자: {set(left)}")
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    n = sum(len(g["items"]) for g in data)
    print(f"index.html 생성 완료 — U {len(data)}개, 캠퍼스 {n}곳, 기준일 {date}")


if __name__ == "__main__":
    main()
