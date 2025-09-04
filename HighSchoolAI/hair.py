#!/usr/bin/env python3
import re
import sys
import json
from collections import defaultdict

HEADER_RE = re.compile(r'^[A-Za-z0-9_]+$')       # stanza name line, e.g. raven_stanza_5
TOKEN_RE  = re.compile(r'[A-Za-z]+')             # letters only; punctuation removed

def parse_marked_text(text: str):
    """Split file into (stanza_name, stanza_text) pairs."""
    stanzas = []
    current_name = None
    buf = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if HEADER_RE.match(line):
            # flush previous stanza
            if current_name is not None and buf:
                stanzas.append((current_name, ' '.join(buf)))
            current_name = line
            buf = []
        else:
            buf.append(line)

    if current_name is not None and buf:
        stanzas.append((current_name, ' '.join(buf)))

    return stanzas

def follower_table(words):
    followers = defaultdict(set)
    for i in range(len(words) - 1):
        followers[words[i]].add(words[i+1])
    return {w: sorted(f) for w, f in followers.items()}

def hairiness_metrics(followers):
    if not followers:
        return {
            "average_branching": 0.0,
            "max_branching": 0,
            "branching_words": 0,
            "branching_fraction": 0.0
        }
    counts = [len(v) for v in followers.values()]
    avg = sum(counts) / len(counts)
    mx  = max(counts)
    branching_words = sum(1 for c in counts if c > 1)
    branching_fraction = branching_words / len(counts)
    result = {
        "average_branching": round(avg, 4),
        "max_branching": mx,
        "branching_words": branching_words,
        "branching_fraction": round(branching_fraction, 4)
    }
    print(str(result))
    return result

def analyze_marked_file(filename: str):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    results = {}
    for name, stanza_text in parse_marked_text(text):
        words = [w.lower() for w in TOKEN_RE.findall(stanza_text)]
        followers = follower_table(words)
        print(name)
        results[name] = {
            "hairiness": hairiness_metrics(followers),
            "followers": followers
        }
    return results

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <marked_text_file>", file=sys.stderr)
        sys.exit(1)
    filename = sys.argv[1]
    results = analyze_marked_file(filename)
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
