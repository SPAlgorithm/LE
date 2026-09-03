#!/usr/bin/env python3
"""Word-timed captions for every narration file of a video.

    python3 captions.py <video_dir>

Reads <video_dir>/scenes.json and audio/sNN.mp3, writes captions.json:
{"NN": [{"start", "end", "text"}, ...]} with times relative to the clip.
Uses faster-whisper (base) with word timestamps; falls back to spreading
the authored text evenly over the measured duration if Whisper fails.
"""
import json, os, re, subprocess, sys

MAX_WORDS = 7
MAX_CHARS = 42


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return float(out)


def chunk_words(words):
    """words: [(start, end, text)] -> caption chunks."""
    chunks, cur = [], []
    def flush():
        if cur:
            chunks.append({"start": cur[0][0], "end": cur[-1][1], "text": " ".join(w[2] for w in cur)})
    for w in words:
        text_len = sum(len(x[2]) + 1 for x in cur) + len(w[2])
        if cur and (len(cur) >= MAX_WORDS or text_len > MAX_CHARS or w[0] - cur[-1][1] > 0.9):
            flush(); cur = []
        cur.append(w)
        if re.search(r"[.!?]$", w[2]) and len(cur) >= 3:
            flush(); cur = []
    flush()
    # an orphaned one- or two-word tail joins the previous caption
    if len(chunks) >= 2 and len(chunks[-1]["text"].split()) <= 2 \
            and len((chunks[-2]["text"] + " " + chunks[-1]["text"])) <= MAX_CHARS + 12:
        tail = chunks.pop()
        chunks[-1]["text"] += " " + tail["text"]
        chunks[-1]["end"] = tail["end"]
    # captions should not overlap and should hold at least 0.8 s
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1]["start"] if i + 1 < len(chunks) else c["end"] + 1.0
        c["end"] = max(c["start"] + 0.8, min(c["end"] + 0.35, nxt - 0.05))
    return chunks


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def align_to_script(words, text):
    """Keep Whisper's timings but take every word's spelling from the
    authored script, so names like Ladhe's are never mis-transcribed."""
    import difflib
    script = text.split()
    a = [norm(w[2]) for w in words]
    b = [norm(w) for w in script]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out.append((words[i1 + k][0], words[i1 + k][1], script[j1 + k]))
        elif tag == "replace":
            t0, t1 = words[i1][0], words[i2 - 1][1]
            n = j2 - j1
            for k in range(n):
                out.append((t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n, script[j1 + k]))
        elif tag == "insert":
            prev_end = out[-1][1] if out else (words[i1][0] - 0.3 * (j2 - j1) if i1 < len(words) else 0.0)
            next_start = words[i1][0] if i1 < len(words) else prev_end + 0.3 * (j2 - j1)
            n = j2 - j1
            for k in range(n):
                out.append((prev_end + (next_start - prev_end) * k / n,
                            prev_end + (next_start - prev_end) * (k + 1) / n, script[j1 + k]))
        # "delete": Whisper heard extra words; drop them
    return out


def fallback(text, dur):
    words = text.split()
    per = dur / max(1, len(words))
    timed = [(i * per, (i + 1) * per, w) for i, w in enumerate(words)]
    return chunk_words(timed)


def main(vdir):
    scenes = json.load(open(os.path.join(vdir, "scenes.json")))
    model = None
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
    except Exception as e:                    # noqa: BLE001
        print("whisper unavailable, using even spread:", e)
    out = {}
    existing = {}
    try:
        existing = json.load(open(os.path.join(vdir, "captions.json")))
    except Exception:
        pass
    for s in scenes:
        key = "%02d" % s["n"]
        if key in existing:
            out[key] = existing[key]
            continue
        path = os.path.join(vdir, "audio", "s%s.mp3" % key)
        dur = duration(path)
        caps = None
        if model is not None:
            try:
                segments, _ = model.transcribe(path, word_timestamps=True, language="en",
                                               initial_prompt=s["text"][:200])
                words = []
                for seg in segments:
                    for w in seg.words or []:
                        words.append((w.start, w.end, w.word.strip()))
                if len(words) >= 0.6 * len(s["text"].split()):
                    caps = chunk_words(align_to_script(words, s["text"]))
            except Exception as e:            # noqa: BLE001
                print("whisper failed on", key, e)
        if caps is None:
            caps = fallback(s["text"], dur)
        out[key] = caps
        print(key, "%.1fs" % dur, len(caps), "captions")
    json.dump(out, open(os.path.join(vdir, "captions.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
