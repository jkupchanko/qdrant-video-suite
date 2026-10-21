"""What each line of the opening says and when its key words land, in edit time. Style-agnostic: every
style reads the same cues and decides its own picture for them. A future script-driven version of this is
generated from the script's camera calls; this one is written by hand for the Bulk Uploads opening."""
def cues(p):
    c = {}
    c["hook_t0"], c["hook_t1"] = p.L(0), p.end(0); c["large"] = p.cue(0, "large"); c["just"] = p.cue(0, "just"); c["store"] = p.cue(0, "store")
    c["list_t0"], c["list_t1"] = p.L(1), p.end(1); c["payloads"] = p.cue(1, "payload"); c["indexes"] = p.cue(1, "index"); c["much"] = p.cue(1, "much"); c["background"] = p.cue(1, "background")
    c["cfg_t0"], c["cfg_t1"] = p.L(2), p.end(2); c["single"] = p.cue(2, "single"); c["works"] = p.cue(2, "works"); c["all"] = p.cue(2, "all")
    c["plan_t0"], c["plan_t1"] = p.L(3), p.end(3); c["options"] = p.cue(3, "option"); c["best"] = p.cue(3, "best")
    c["ds_t0"], c["ds_t1"] = p.L(4), p.end(4); c["dense"] = p.cue(4, "dense"); c["sparse"] = p.cue(4, "sparse")
    c["hnsw_t0"], c["hnsw_t1"] = p.L(5), p.end(5); c["hnsw"] = p.cue(5, "h")
    c["sp_t0"], c["sp_t1"] = p.L(6), p.end(6); c["sparse2"] = p.cue(6, "sparse"); c["indexing"] = p.cue(6, "index")
    c["mp_t0"], c["mp_t1"] = p.L(7), p.end(7); c["memory"] = p.cue(7, "memory"); c["perf"] = p.cue(7, "perf"); c["bulk"] = p.cue(7, "bulk")
    c["ch_t0"], c["ch_t1"] = p.L(8), p.end(8); c["first"] = p.cue(8, "first"); c["ch_face_end"] = 36.10      # the look-away 36.45-37.01 sits in this line's tail; 0.35 s early so a dip or push has faded the face before it
    c["o1_t0"], c["o1_t1"] = p.L(9), p.end(9); c["storing"] = p.cue(9, "storing"); c["disk"] = p.cue(9, "disk")
    return c

# the transcript's mishearings, corrected for anything that prints the spoken words
SPOKEN_FIX = {"quadrant": "Qdrant", "does": "doesn't", "factors": "vectors", "h": "HNSW", "sw": ""}
def spoken(p, i):
    """[(word, edit time)] for piece i with the transcript's mishearings corrected; words mapped to '' are dropped"""
    out = []
    for w in p.words:
        if p.pieces[i][1] - 0.05 <= w["s"] <= p.pieces[i][2]:
            raw = w["w"].strip(); key = raw.strip(" ,.?!").lower(); fixed = SPOKEN_FIX.get(key, raw)
            if fixed == "": continue
            if fixed != raw and raw[-1:] in ",.?!": fixed += raw[-1]
            out.append((fixed, p.L(i) + w["s"] - p.pieces[i][1]))
    return out
