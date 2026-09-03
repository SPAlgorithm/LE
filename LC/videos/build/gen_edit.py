#!/usr/bin/env python3
"""Generate edit.jsx for higgsedit from scenes.json + durations.json + captions.json.

    python3 gen_edit.py <video_dir>

video_dir holds: scenes.json (list of {n,title,visual,text}), durations.json
({"NN": seconds}), captions.json ({"NN": [{start,end,text}]}), audio/sNN.mp3,
media/heroNN.png.  Writes <video_dir>/edit.jsx.
"""
import json, os, re, sys

PAD = 0.8                      # silence after each narration line
CAP_MAX = 6.0                  # seconds a caption may stay


def js(s):
    return json.dumps(s, ensure_ascii=False)


def parse_visual(v):
    kind, _, payload = v.partition(":")
    kind = kind.strip()
    payload = payload.strip()
    if kind == "hero":
        m = re.match(r"(\d+)", payload)
        return {"kind": "hero", "n": int(m.group(1))}
    if kind in ("equations", "rulecard", "stats", "exceptions", "bars",
                "ladder", "terminal", "titlecard"):
        return {"kind": kind, "items": [x.strip() for x in payload.split("|")]}
    if kind == "question":
        return {"kind": "question", "text": payload}
    if kind == "numberline":
        return {"kind": "numberline", "n": int(payload or 30)}
    if kind == "sequence":
        return {"kind": "sequence", "items": ["11", "101", "191", "821", "1481", "1871", "2081", "3251", "3461", "5651"]}
    if kind == "mod30":
        return {"kind": "equations", "items": ["p = 11 (mod 30)", "p, p+2, p+6, p+8", "last digits  1  3  7  9"]}
    if kind == "mod30gap":
        return {"kind": "equations", "items": ["gap = 22 (mod 30)", "11 + 11 = 22", "13001 = 9439 + 3461 + 101"]}
    return {"kind": "titlecard", "items": [payload or v]}


JS_LIB = r'''
let T0 = 0;
const W = 1920, H = 1080, M = 120;
const BG = "#0B0F1A", PANEL = "#131A2B", PANEL2 = "#1B2437", TXT = "#F5F5F0", GOLD = "#FFD166",
      TEAL = "#4FD1C5", MUTED = "#9AA3B5", CORAL = "#FF6B6B", INK = "#0A0C12";
const SANS = "Inter", MONO = "JetBrains Mono";
const ICON = (name, o) => (typeof globalThis.__icon === "function" ? globalThis.__icon(name, o) : <rect x={0} y={0} width={o.size} height={o.size} fill={o.color} radius={o.size / 2} />);
const fit = (d, span) => Math.max(0.05, Math.min(d, span * 0.9));
const isPrime = (n) => { if (n < 2) return false; for (let i = 2; i * i <= n; i++) if (n % i === 0) return false; return true; };

function fadeIn(dur, delay = 0) {
  return [{ property: "opacity", from: 0, to: 1, at: delay, duration: fit(0.5, dur - delay), easing: "house" }];
}
function rise(dur, delay = 0) {
  return [
    { property: "opacity", from: 0, to: 1, at: delay, duration: fit(0.45, dur - delay), easing: "house" },
    { property: "offsetY", from: 30, to: 0, at: delay, duration: fit(0.6, dur - delay), easing: "house" },
  ];
}
function kicker(title, dur) {
  return (
    <row x={M} y={64} gap={16} align="center" animate={fadeIn(dur)}>
      <rect x={0} y={0} width={14} height={14} fill={GOLD} radius={7} />
      <text fontFamily={SANS} fontSize={28} fontWeight={700} letterSpacing={3} color={MUTED}>{title.toUpperCase()}</text>
    </row>
  );
}
function captionNodes(caps, dur) {
  const out = [];
  for (const c of caps) {
    const at = Math.max(0, Math.min(c.start, dur - 0.3));
    const d = Math.max(0.3, Math.min(c.end, dur) - at);
    out.push(
      <column x={M} y={930} width={W - 2 * M} align="center" at={T0 + at} duration={d}>
        <column fill="rgba(5,7,12,0.78)" radius={14} padding={[10, 26, 12, 26]}>
          <text fontFamily={SANS} fontSize={44} fontWeight={700} color={TXT} align="center" width={W - 2 * M - 52}>{c.text}</text>
        </column>
      </column>
    );
  }
  return out;
}
function heroScene(h, dur) {
  return [
    <group width={W} height={H} x={0} y={0} origin="center"
           animate={[{ property: "scale", from: 1.0, to: 1.07, duration: fit(dur, dur), easing: "linear" }]}>
      <media file={h} x={0} y={0} width={W} height={H} fit="cover" />
    </group>,
    <rect x={0} y={780} width={W} height={300}
          fill={{ kind: "linear", angle: 180, stops: [{ offset: 0, color: "rgba(11,15,26,0)" }, { offset: 1, color: "rgba(11,15,26,0.85)" }] }} />,
  ];
}
function eqSize(lines) {
  const n = Math.max(...lines.map((s) => s.length));
  const byLen = n <= 24 ? 104 : n <= 34 ? 84 : n <= 46 ? 66 : n <= 60 ? 52 : 42;
  return Math.min(byLen, Math.floor(620 / (1.9 * lines.length)));
}
function equationsScene(lines, dur) {
  const size = eqSize(lines);
  const step = Math.min(1.2, (dur * 0.5) / Math.max(1, lines.length));
  return [
    <column x={M} y={lines.length > 4 ? 150 : lines.length > 2 ? 230 : 300} width={W - 2 * M} gap={Math.round(size * 0.5)}>
      {lines.map((s, i) => (
        <text fontFamily={MONO} fontSize={size} fontWeight={700} color={i === 0 ? GOLD : TXT} width={W - 2 * M}
              at={T0 + i * step} duration={dur - i * step}
              motion={{ by: "word", from: { y: 26, opacity: 0 }, overlap: 0.7, easing: "house", duration: fit(0.9, dur - i * step) }}>{s}</text>
      ))}
    </column>,
  ];
}
function ruleScene(lines, dur) {
  const step = Math.min(1.4, (dur * 0.5) / lines.length);
  return [
    <column x={M} y={230} width={W - 2 * M} gap={34} padding={56} fill={PANEL} radius={32} animate={fadeIn(dur)}>
      {lines.map((s, i) => (
        <row gap={28} align="center" at={T0 + i * step} duration={dur - i * step} animate={rise(dur - i * step)}>
          {ICON("circle-check", { size: 56, color: GOLD })}
          <text fontFamily={SANS} fontSize={50} fontWeight={700} color={TXT} width={W - 2 * M - 250}>{s}</text>
        </row>
      ))}
    </column>,
  ];
}
function titleScene(items, dur) {
  const [title, sub] = items;
  return [
    <column x={M} y={330} width={W - 2 * M} gap={40} align="center">
      <text fontFamily={SANS} fontSize={title.length > 28 ? 96 : 132} fontWeight={700} color={GOLD} align="center" width={W - 2 * M}
            motion={{ by: "word", from: { y: 40, opacity: 0 }, overlap: 0.6, easing: "house", duration: fit(1.2, dur) }}>{title}</text>
      {sub ? <text fontFamily={SANS} fontSize={54} color={MUTED} align="center" width={W - 2 * M} at={T0 + 0.8} duration={dur - 0.8} animate={fadeIn(dur - 0.8)}>{sub}</text> : null}
    </column>,
  ];
}
function statsScene(items, dur) {
  const pairs = [];
  for (let i = 0; i + 1 < items.length; i += 2) pairs.push([items[i], items[i + 1]]);
  const tileW = Math.floor((W - 2 * M - 40 * (pairs.length - 1)) / pairs.length);
  const step = Math.min(1.0, (dur * 0.4) / pairs.length);
  return [
    <row x={M} y={330} gap={40}>
      {pairs.map(([label, value], i) => (
        <column width={tileW} gap={18} padding={44} fill={PANEL} radius={28} align="center" at={T0 + i * step} duration={dur - i * step} animate={rise(dur - i * step)}>
          <text fontFamily={MONO} fontSize={value.length > 12 ? 60 : 84} fontWeight={700} color={GOLD} align="center" width={tileW - 88}>{value}</text>
          <text fontFamily={SANS} fontSize={34} color={MUTED} align="center" width={tileW - 88}>{label}</text>
        </column>
      ))}
    </row>,
  ];
}
function exceptionsScene(items, dur) {
  const step = Math.min(0.8, (dur * 0.5) / items.length);
  const tileW = Math.floor((W - 2 * M - 24 * (items.length - 1)) / items.length);
  return [
    <text x={M} y={260} width={W - 2 * M} fontFamily={SANS} fontSize={56} fontWeight={700} color={TXT} align="center" animate={fadeIn(dur)}>The ten gaps that need a royal value</text>,
    <row x={M} y={420} gap={24}>
      {items.map((s, i) => (
        <column width={tileW} padding={[36, 8, 36, 8]} fill={PANEL2} radius={22} align="center" at={T0 + i * step} duration={dur - i * step} animate={rise(dur - i * step)}>
          <text fontFamily={MONO} fontSize={60} fontWeight={700} color={CORAL} align="center" width={tileW - 16}>{s}</text>
        </column>
      ))}
    </row>,
  ];
}
function barsScene(items, dur) {
  const vals = items.map(Number);
  const n = vals.length, gap = 36, barW = Math.floor((W - 2 * M - gap * (n - 1)) / n), maxH = 480, base = 800;
  const step = Math.min(0.6, (dur * 0.5) / n);
  const nodes = [
    <text x={M} y={200} width={W - 2 * M} fontFamily={SANS} fontSize={52} fontWeight={700} color={TXT} align="center" animate={fadeIn(dur)}>Share of gaps that are a sum of just two earlier members, per block of quads</text>,
  ];
  vals.forEach((v, i) => {
    const h = Math.round(maxH * v / 30);
    const x = M + i * (barW + gap);
    nodes.push(<rect x={x} y={base - h} width={barW} height={h} fill={TEAL} radius={10} at={T0 + i * step} duration={dur - i * step} animate={rise(dur - i * step)} />);
    nodes.push(<text x={x} y={base - h - 64} width={barW} fontFamily={MONO} fontSize={48} fontWeight={700} color={GOLD} align="center" at={T0 + i * step + 0.2} duration={dur - i * step - 0.2} animate={fadeIn(dur - i * step - 0.2)}>{v + "%"}</text>);
    nodes.push(<text x={x} y={base + 20} width={barW} fontFamily={SANS} fontSize={30} color={MUTED} align="center" at={T0 + i * step} duration={dur - i * step}>{"block " + (i + 1)}</text>);
  });
  return nodes;
}
function ladderScene(items, dur) {
  const n = items.length, step = Math.min(1.0, (dur * 0.6) / n), rowH = Math.min(120, Math.floor(700 / n));
  const nodes = [];
  items.forEach((v, i) => {
    const y = 820 - i * rowH;
    const delay = i * step;
    nodes.push(<rect x={560} y={y} width={800} height={14} fill={GOLD} radius={7} at={T0 + delay} duration={dur - delay} animate={rise(dur - delay)} />);
    nodes.push(<text x={1400} y={y - 30} width={400} fontFamily={MONO} fontSize={64} fontWeight={700} color={TXT} at={T0 + delay} duration={dur - delay} animate={rise(dur - delay)}>{v}</text>);
  });
  nodes.push(<rect x={540} y={820 - (n - 1) * rowH - 40} width={12} height={(n - 1) * rowH + 80} fill={TEAL} radius={6} animate={fadeIn(dur)} />);
  nodes.push(<rect x={1368} y={820 - (n - 1) * rowH - 40} width={12} height={(n - 1) * rowH + 80} fill={TEAL} radius={6} animate={fadeIn(dur)} />);
  nodes.push(<text x={M} y={150} width={W - 2 * M} fontFamily={SANS} fontSize={52} fontWeight={700} color={TXT} align="center" animate={fadeIn(dur)}>Every integer up to this rung can be built</text>);
  return nodes;
}
function questionScene(text, dur) {
  return [
    <row x={M} y={330} width={W - 2 * M} gap={48} align="center" padding={64} fill={PANEL} radius={32} animate={fadeIn(dur)}>
      {ICON("circle-help", { size: 140, color: GOLD })}
      <text fontFamily={SANS} fontSize={64} fontWeight={700} color={TXT} width={W - 2 * M - 128 - 190}
            motion={{ by: "word", from: { y: 24, opacity: 0 }, overlap: 0.7, easing: "house", duration: fit(1.2, dur) }}>{text}</text>
    </row>,
  ];
}
function terminalScene(lines, dur) {
  const step = Math.min(1.1, (dur * 0.6) / lines.length);
  const size = Math.max(...lines.map((s) => s.length)) > 44 ? 40 : 48;
  return [
    <column x={M} y={220} width={W - 2 * M} gap={22} padding={48} fill={INK} radius={24} animate={fadeIn(dur)}>
      <row gap={14}>
        <rect x={0} y={0} width={20} height={20} fill={CORAL} radius={10} />
        <rect x={0} y={0} width={20} height={20} fill={GOLD} radius={10} />
        <rect x={0} y={0} width={20} height={20} fill={TEAL} radius={10} />
      </row>
      {lines.map((s, i) => (
        <text fontFamily={MONO} fontSize={size} color={s.startsWith("python") ? TEAL : TXT} width={W - 2 * M - 96} at={T0 + i * step} duration={dur - i * step} animate={fadeIn(dur - i * step)}>{(s.startsWith("python") ? "$ " : "  ") + s}</text>
      ))}
    </column>,
  ];
}
function numberlineScene(n, dur) {
  const nodes = [];
  const cellW = Math.floor((W - 2 * M) / n);
  const step = Math.min(0.25, (dur * 0.5) / n);
  nodes.push(<rect x={M} y={560} width={W - 2 * M} height={8} fill={MUTED} radius={4} animate={fadeIn(dur)} />);
  for (let i = 1; i <= n; i++) {
    const x = M + (i - 1) * cellW, p = isPrime(i), delay = i * step;
    nodes.push(<rect x={x + cellW / 2 - 3} y={p ? 520 : 540} width={6} height={p ? 48 : 28} fill={p ? GOLD : MUTED} radius={3} at={T0 + delay} duration={dur - delay} animate={fadeIn(dur - delay)} />);
    nodes.push(<text x={x} y={p ? 420 : 600} width={cellW} fontFamily={MONO} fontSize={p ? 52 : 34} fontWeight={p ? 700 : 400} color={p ? GOLD : MUTED} align="center" at={T0 + delay} duration={dur - delay} animate={rise(dur - delay)}>{String(i)}</text>);
  }
  nodes.push(<text x={M} y={200} width={W - 2 * M} fontFamily={SANS} fontSize={56} fontWeight={700} color={TXT} align="center" animate={fadeIn(dur)}>The primes up to thirty</text>);
  return nodes;
}
function sequenceScene(items, dur) {
  const step = Math.min(1.0, (dur * 0.6) / items.length);
  const tileW = Math.floor((W - 2 * M - 20 * 4) / 5);
  const rows = [items.slice(0, 5), items.slice(5)];
  return [
    <text x={M} y={200} width={W - 2 * M} fontFamily={SANS} fontSize={56} fontWeight={700} color={TXT} align="center" animate={fadeIn(dur)}>First members of the prime quadruplets</text>,
    <column x={M} y={360} gap={24}>
      {rows.map((r, ri) => (
        <row gap={20}>
          {r.map((s, i) => (
            <column width={tileW} padding={[34, 8, 34, 8]} fill={PANEL} radius={24} align="center" at={T0 + (ri * 5 + i) * step} duration={dur - (ri * 5 + i) * step} animate={rise(dur - (ri * 5 + i) * step)}>
              <text fontFamily={MONO} fontSize={64} fontWeight={700} color={GOLD} align="center" width={tileW - 16}>{s}</text>
            </column>
          ))}
        </row>
      ))}
    </column>,
  ];
}
function buildScene(sc, dur, heroes) {
  const v = sc.visual;
  let body;
  switch (v.kind) {
    case "hero": body = heroScene(heroes[v.n], dur); break;
    case "equations": body = equationsScene(v.items, dur); break;
    case "rulecard": body = ruleScene(v.items, dur); break;
    case "titlecard": body = titleScene(v.items, dur); break;
    case "stats": body = statsScene(v.items, dur); break;
    case "exceptions": body = exceptionsScene(v.items, dur); break;
    case "bars": body = barsScene(v.items, dur); break;
    case "ladder": body = ladderScene(v.items, dur); break;
    case "question": body = questionScene(v.text, dur); break;
    case "terminal": body = terminalScene(v.items, dur); break;
    case "numberline": body = numberlineScene(v.n, dur); break;
    case "sequence": body = sequenceScene(v.items, dur); break;
    default: body = titleScene([sc.title], dur);
  }
  const nodes = [];
  if (v.kind !== "hero") nodes.push(<rect x={0} y={0} width={W} height={H} fill={{ kind: "radial", stops: [{ offset: 0, color: "#141B2E" }, { offset: 1, color: BG }] }} />);
  nodes.push(...body);
  if (v.kind !== "hero") nodes.push(kicker(sc.title, dur));
  nodes.push(...captionNodes(sc.captions, dur));
  return nodes;
}
'''


def main(vdir):
    scenes = json.load(open(os.path.join(vdir, "scenes.json")))
    durations = json.load(open(os.path.join(vdir, "durations.json")))
    captions = json.load(open(os.path.join(vdir, "captions.json")))
    heroes = sorted({parse_visual(s["visual"])["n"] for s in scenes if s["visual"].startswith("hero:")})
    data = []
    total = 0.0
    for s in scenes:
        key = "%02d" % s["n"]
        audio = float(durations[key])
        dur = round(audio + PAD, 3)
        caps = []
        for c in captions.get(key, []):
            caps.append({"start": round(c["start"], 2), "end": round(min(c["end"], c["start"] + CAP_MAX), 2), "text": c["text"]})
        data.append({"n": s["n"], "title": s["title"], "visual": parse_visual(s["visual"]),
                     "audio": "audio/s%s.mp3" % key, "audioDur": audio, "dur": dur, "captions": caps})
        total += dur
    out = []
    out.append("// generated by gen_edit.py — do not edit by hand\n")
    out.append(JS_LIB)
    out.append("\nconst SCENES = " + js(data) + ";\n")
    out.append("const HERO_IDS = " + js(heroes) + ";\n")
    out.append(r'''
export default async (ctx) => {
  const { project } = ctx;
  globalThis.__icon = ctx.icon;
  console.log("CTX_KEYS", Object.keys(ctx).join(","));
  const p = await project({ dir: "proj", size: "1920x1080", fps: 30, background: BG });
  const heroes = {};
  for (const n of HERO_IDS) heroes[n] = await p.add("media/hero" + String(n).padStart(2, "0") + ".png");
  const total = SCENES.reduce((a, s) => a + s.dur, 0);
  p.compose(
    <rect x={0} y={0} width={W} height={H} fill={BG} />,
    { at: 0, dur: total, name: "bg" },
  );
  let at = 0;
  for (const sc of SCENES) {
    const a = await p.add(sc.audio);
    p.cut(a, { at, from: 0, dur: sc.audioDur });
    T0 = at;
    p.compose(buildScene(sc, sc.dur, heroes), { at, dur: sc.dur, name: "scene" + String(sc.n).padStart(2, "0") });
    at += sc.dur;
  }
  p.compose(
    <rect x={0} y={0} width={W} height={6} fill={GOLD}
          animate={[{ property: "scaleX", from: 0, to: 1, duration: total * 0.999, easing: "linear" }]} />,
    { at: 0, dur: total, name: "progress" },
  );
  console.log("TOTAL_SECONDS", total.toFixed(2), "SCENES", SCENES.length);
  if (process.env.PROOF) {
    const ts = process.env.PROOF.split(",").map(Number);
    for (let i = 0; i < ts.length; i++) await p.frame(ts[i], "renders/proof_" + i + ".png");
  }
  if (process.env.RENDER) await p.render("renders/final.mp4");
};
''')
    with open(os.path.join(vdir, "edit.jsx"), "w") as fh:
        fh.write("".join(out))
    print("edit.jsx written: %d scenes, %.1f s total, heroes %s" % (len(data), total, heroes))


if __name__ == "__main__":
    main(sys.argv[1])
