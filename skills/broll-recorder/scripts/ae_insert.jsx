// ae_insert.jsx: drop a recorded B-roll clip into an After Effects comp in one of the house styles.
// Edit the CONFIG block, then run it (File > Scripts > Run Script File), or let an agent run it. ES3 only.
var CONFIG = {
  COMP: "",                       // comp name; "" = the comp open in the viewer
  CLIP: "C:/path/to/clip.mp4",    // from broll.py (manifest.clip)
  T_IN: 4.3, T_OUT: 7.7,          // comp seconds
  STYLE: "fullscreen-pip",        // fullscreen-pip | fullscreen | evidence-card
  PIP_LAYER: "John",              // name of the presenter layer to duplicate as the PiP ("" = no PiP)
  PIP_CORNER: "bottom-right",     // bottom-right | top-right | bottom-left | top-left
  PIP_WIDTH: 435,                 // px
  PIP_CROP: [588, 372, 640, 360], // face crop in the presenter layer's own pixels: cx, cy, w, h
  PIP_BORDER: [1, 1, 1],          // rgb 0..1
  CAPTION: "",                    // "" = no caption pill
  CAPTION_FONT: "MonaSans-Medium",
  CAPTION_SIZE: 38,
  SLIDE_IN: true,                 // slide from the right on entry
  PUSH: 1.05,                     // end scale of the slow push (1 = none)
  CARD_SCALE: 50, CARD_POS: [470, 330], CARD_ROT: -6,   // evidence-card only
  WHOOSH: ""                      // path to a whoosh file, "" = none
};

(function (C) {
  function P(l, n) { return l.property("ADBE Transform Group").property(n); }
  function roundRect(x, y, w, h, r) {
    var k = 0.5523 * r, s = new Shape();
    s.vertices = [[x + r, y], [x + w - r, y], [x + w, y + r], [x + w, y + h - r], [x + w - r, y + h], [x + r, y + h], [x, y + h - r], [x, y + r]];
    s.inTangents = [[-k, 0], [0, 0], [0, -k], [0, 0], [k, 0], [0, 0], [0, k], [0, 0]];
    s.outTangents = [[0, 0], [k, 0], [0, 0], [0, k], [0, 0], [-k, 0], [0, 0], [0, -k]];
    s.closed = true; return s;
  }
  function shadow(l, op, dist, soft) {
    var ds = l.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");
    ds.property("ADBE Drop Shadow-0002").setValue(op); ds.property("ADBE Drop Shadow-0003").setValue(135);
    ds.property("ADBE Drop Shadow-0004").setValue(dist); ds.property("ADBE Drop Shadow-0005").setValue(soft);
  }
  function chain(keys, extra) {
    var parts = [];
    for (var i = 0; i < keys.length; i++) parts.push("[" + keys[i][0] + "," + (keys[i][1] instanceof Array ? "[" + keys[i][1].join(",") + "]" : keys[i][1]) + "]");
    return "var k = [" + parts.join(",") + "]; var p = k[0][1]; for (var i = 0; i < k.length - 1; i++) p = ease(time, k[i][0], k[i + 1][0], p, k[i + 1][1]); " + (extra || "p");
  }
  var comp = C.COMP ? null : app.project.activeItem;
  if (C.COMP) for (var i = 1; i <= app.project.numItems; i++) if (app.project.item(i).name === C.COMP && app.project.item(i) instanceof CompItem) comp = app.project.item(i);
  if (!(comp instanceof CompItem)) { alert("Open the target comp (or set CONFIG.COMP)."); return; }
  app.beginUndoGroup("insert B-roll");
  var W = comp.width, H = comp.height, tIn = C.T_IN, tOut = C.T_OUT;
  var item = app.project.importFile(new ImportOptions(new File(C.CLIP)));
  var clip = comp.layers.add(item);
  clip.name = "B-roll " + item.name;
  clip.startTime = tIn; clip.inPoint = tIn; clip.outPoint = tOut; clip.motionBlur = true;

  if (C.STYLE === "evidence-card") {
    clip.property("ADBE Mask Parade").addProperty("ADBE Mask Atom").property("ADBE Mask Shape").setValue(roundRect(0, 0, item.width, item.height, 24));
    P(clip, "ADBE Scale").setValue([C.CARD_SCALE, C.CARD_SCALE, 100]);
    P(clip, "ADBE Rotate Z").setValue(C.CARD_ROT);
    P(clip, "ADBE Position").expression = chain([[tIn, [-item.width * C.CARD_SCALE / 200, -item.height * C.CARD_SCALE / 200]], [tIn + 0.5, C.CARD_POS]], "p + [0, 6 * Math.sin(time * 1.1)]");
    P(clip, "ADBE Opacity").expression = "ease(time, " + tIn + ", " + (tIn + 0.2) + ", 0, 100)";
    shadow(clip, 190, 26, 60);
  } else {
    var sc = Math.max(W / item.width, H / item.height) * 100;
    P(clip, "ADBE Scale").expression = "var s = " + sc + " * linear(time, " + tIn + ", " + tOut + ", 1.0, " + C.PUSH + "); [s, s]";
    if (C.SLIDE_IN) P(clip, "ADBE Position").expression = chain([[tIn, [W * 1.5, H / 2]], [tIn + 0.32, [W / 2, H / 2]]]);
    else P(clip, "ADBE Opacity").expression = chain([[tIn, 0], [tIn + 0.2, 100]]);
  }

  if (C.STYLE === "fullscreen-pip" && C.PIP_LAYER) {
    var src = null;
    for (var j = 1; j <= comp.numLayers; j++) if (comp.layer(j).name === C.PIP_LAYER) src = comp.layer(j);
    if (src) {
      var pip = src.duplicate();
      pip.name = "PiP " + C.PIP_LAYER;
      pip.moveBefore(clip);
      pip.audioEnabled = false;
      pip.inPoint = tIn; pip.outPoint = tOut;
      var cx = C.PIP_CROP[0], cy = C.PIP_CROP[1], cw = C.PIP_CROP[2], ch = C.PIP_CROP[3];
      var masks = pip.property("ADBE Mask Parade");
      while (masks.numProperties > 0) masks.property(1).remove();
      masks.addProperty("ADBE Mask Atom").property("ADBE Mask Shape").setValue(roundRect(cx - cw / 2, cy - ch / 2, cw, ch, 36));
      P(pip, "ADBE Anchor Point").setValue([cx, cy]);
      var ps = C.PIP_WIDTH / cw * 100;
      P(pip, "ADBE Scale").setValue([ps, ps, 100]);
      P(pip, "ADBE Scale").expression = null; P(pip, "ADBE Position").expression = null; P(pip, "ADBE Rotate Z").expression = null; P(pip, "ADBE Opacity").expression = null;
      var m = 40, pw = cw * ps / 100, ph = ch * ps / 100;
      var pos = { "bottom-right": [W - m - pw / 2, H - m - ph / 2], "top-right": [W - m - pw / 2, m + ph / 2], "bottom-left": [m + pw / 2, H - m - ph / 2], "top-left": [m + pw / 2, m + ph / 2] }[C.PIP_CORNER];
      P(pip, "ADBE Position").setValue(pos);
      P(pip, "ADBE Scale").expression = "var a = ease(time, " + (tIn + 0.15) + ", " + (tIn + 0.45) + ", 0, 1); var o = 1 + 0.12 * Math.sin(Math.min(1, Math.max(0, (time - " + (tIn + 0.15) + ") / 0.3)) * Math.PI); var s = value[0] * a * o; [s, s]";
      shadow(pip, 200, 20, 50);
      var edge = comp.layers.addShape(); edge.name = "PiP edge";
      var g = edge.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
      var r = g.property("ADBE Vectors Group").addProperty("ADBE Vector Shape - Rect");
      r.property("ADBE Vector Rect Size").setValue([pw + 8, ph + 8]); r.property("ADBE Vector Rect Roundness").setValue(36 * ps / 100 + 4);
      var st = g.property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Stroke");
      st.property("ADBE Vector Stroke Color").setValue(C.PIP_BORDER); st.property("ADBE Vector Stroke Width").setValue(4);
      P(edge, "ADBE Position").setValue(pos);
      P(edge, "ADBE Scale").expression = "thisComp.layer('" + pip.name + "').scale / " + ps + " * 100";
      edge.inPoint = tIn; edge.outPoint = tOut;
      edge.moveBefore(pip);
    }
  }

  if (C.CAPTION) {
    var t = comp.layers.addText(C.CAPTION);
    t.name = "caption";
    var doc = t.property("ADBE Text Properties").property("ADBE Text Document").value;
    doc.font = C.CAPTION_FONT; doc.fontSize = C.CAPTION_SIZE; doc.fillColor = [1, 1, 1]; doc.justification = ParagraphJustification.CENTER_JUSTIFY; doc.tracking = 0;
    t.property("ADBE Text Properties").property("ADBE Text Document").setValue(doc);
    P(t, "ADBE Position").setValue([W / 2, H - 80]);
    var bar = comp.layers.addShape(); bar.name = "caption bar";
    var bg = bar.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
    var br = bg.property("ADBE Vectors Group").addProperty("ADBE Vector Shape - Rect");
    br.property("ADBE Vector Rect Roundness").setValue(14);
    br.property("ADBE Vector Rect Size").expression = "[thisComp.layer('caption').sourceRectAtTime(time, false).width + 56, 64]";
    var fill = bg.property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
    fill.property("ADBE Vector Fill Color").setValue([0.03, 0.035, 0.06]);
    P(bar, "ADBE Position").setValue([W / 2, H - 93]);
    bar.moveAfter(t);
    var fade = chain([[tIn, 0], [tIn + 0.2, 100], [tOut - 0.15, 100], [tOut, 0]]);
    P(t, "ADBE Opacity").expression = fade; P(bar, "ADBE Opacity").expression = "(" + fade + ") * 0.82";
    t.inPoint = tIn; t.outPoint = tOut; bar.inPoint = tIn; bar.outPoint = tOut;
  }
  if (C.WHOOSH) {
    var wh = app.project.importFile(new ImportOptions(new File(C.WHOOSH)));
    var a = comp.layers.add(wh); a.name = "whoosh"; a.startTime = tIn - 0.12; a.outPoint = tIn + 0.55; a.audioLevels = [-16, -16];
  }
  app.endUndoGroup();
})(CONFIG);
