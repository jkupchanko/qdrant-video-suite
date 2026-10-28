#!/usr/bin/env python
"""selftest.py: prove the upload kit still catches what it is meant to, on faults planted in made-up files.

  python selftest.py [--out DIR]      -> SELF-TEST PASSED, or FAILED with what was missed (exit 1)

chapters   a script of five sections against a cut list: one section the cut leaves 6 s long -> it joins the next with
           both titles kept (a first rule dropped such a title and showed "Intro" over the Docker part); one section the
           cut never says -> no chapter; the rest start where the cut first says them, the first at 0:00
draft      the description leads with the intro's "you can" line, not its "I'll show you" line, and links the source
           page in its first two lines; a placeholder address in the script never reaches it
checks     a 110-character title, an emoji, chapters not starting at 0:00, two chapters 5 s apart, a placeholder address
           -> each caught; the draft above -> nothing to fix
"""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import chapters as CH, upload_kit as UK

SCRIPT = """<!-- Source page: https://qdrant.tech/documentation/quickstart/ -->

# Run Qdrant Anywhere

## Intro   0:00 to 0:20

In this video I'll show you every option.
You can run Qdrant locally, on your own servers, or in the cloud.

## Docker   0:20 to 0:40

Docker is the quickest way to start.
[B-ROLL: https://qdrant.tech/documentation/installation/ | Docker is the quickest way | section: Docker | 5s | name: docker]

## Kubernetes   0:40 to 0:50

Kubernetes runs it in production.

## Binary   0:50 to 1:00

The binary needs no container at all.

## Cloud   1:00 to 1:30

Qdrant Cloud manages it for you at https://YOUR-CLUSTER.cloud.qdrant.io:6333 once it is created.
"""
CUTLIST = """| edit time | source | push | script line | said | take |
|---|---|---|---|---|---|
| 0.00 | 1.00-4.00 | x1.00 | In this video I'll show you every option. | x | t |
| 4.00 | 5.00-9.00 | x1.00 | You can run Qdrant locally, on your own servers, or in the cloud. | x | t |
| 25.00 | 30.00-40.00 | x1.00 | Docker is the quickest way to start. | x | t |
| 40.00 | 50.00-56.00 | x1.00 | Kubernetes runs it in production. | x | t |
| 46.00 | 70.00-90.00 | x1.00 | Qdrant Cloud manages it for you at https://YOUR-CLUSTER.cloud.qdrant.io:6333 once it is created. | x | t |
"""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="upload_selftest"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    sp, cp = os.path.join(a.out, "script.md"), os.path.join(a.out, "cutlist.md")
    open(sp, "w", encoding="utf-8").write(SCRIPT); open(cp, "w", encoding="utf-8").write(CUTLIST)
    C = CH.chapters(sp, cp); names = [n for n, _ in C]; ok = True
    T, D, _ = UK.draft(sp, cp)
    first = " ".join(D.splitlines()[:2])
    for what, good in (("first chapter at 0:00", C and C[0] == ["Intro", 0.0]),
                       ("a 6 s section joins the next, both titles kept", "Kubernetes and Cloud" in names),
                       ("a section the cut never says has no chapter", not any("Binary" in n for n in names)),
                       ("Docker starts where the cut says it (0:25)", ["Docker", 25.0] in C),
                       ('the description leads with "you can", not "I\'ll show you"', first.startswith("You can run Qdrant") and "show you" not in first),
                       ("the source page linked in the first two lines", "https://qdrant.tech/documentation/quickstart/" in first),
                       ("no placeholder address in the description", "YOUR-CLUSTER" not in D)):
        print(f"  {'caught' if good else 'MISSED'}  {what}" + ("" if good else f"  -> {C} | {first[:80]}")); ok &= bool(good)
    bad_desc = "Learn Qdrant today.\n\nChapters\n0:05 Intro\n0:40 Docker\n0:45 Cloud\n\nhttps://YOUR-CLUSTER.cloud.qdrant.io:6333\n"
    F = UK.check("Get Started with Qdrant: " + "a very long title " * 5 + "\U0001F680", bad_desc)
    for what, needle, sev in (("title over 100 characters", "refuses over 100", "fix"), ("an emoji in the title", "emoji", "check"),
                              ("no link in the first two lines", "no link in the first", "check"), ("first chapter not at 0:00", "not at 0:00", "fix"),
                              ("two chapters 5 s apart", "under 10 s apart", "fix"), ("a placeholder address", "placeholder", "fix")):
        hit = any(s == sev and needle in m for s, m in F); print(f"  {'caught' if hit else 'MISSED'}  checks: {what}"); ok &= hit
    clean = [m for s, m in UK.check(T, D) if s == "fix"]
    for m in clean: print(f"  INVENTED  {m}")
    print("SELF-TEST PASSED" if ok and not clean else "SELF-TEST FAILED"); return 0 if ok and not clean else 1

if __name__ == "__main__":
    sys.exit(main())
