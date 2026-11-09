"""
Builds a starter PowerPoint poster for SCiP 2026 (48 x 36 in, same size as the 2025 poster)
from the figures in figures/. Everything is a normal PowerPoint object, so move, resize
or restyle freely; swap a PNG for its SVG sibling in PowerPoint if you want editable art.

  python build_poster.py        ->  poster_scip_2026.pptx
"""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"

GREEN, GOLD, INK, SUB, CARD = "12645A", "D6B870", "1C1B1A", "52514E", "FFFFFF"
BLUE, ORANGE = "2A78D6", "EB6834"
FONT = "Arial"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(48), Inches(36)
slide = prs.slides.add_slide(prs.slide_layouts[6])


def rgb(h):
    return RGBColor.from_string(h)


def rect(x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(2)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def text(x, y, w, h, paras, size=34, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=8):
    """paras: list of strings or (string, dict(size=, bold=, color=)) tuples."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.1)
    first = True
    for p in paras:
        t, o = (p, {}) if isinstance(p, str) else p
        para = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        para.alignment = align
        para.space_after = Pt(o.get("space", space))
        r = para.add_run()
        r.text = t
        r.font.name = FONT
        r.font.size = Pt(o.get("size", size))
        r.font.bold = o.get("bold", bold)
        r.font.color.rgb = rgb(o.get("color", color))
    return tb


def picture(name, x, y, w=None, h=None):
    """Place a figure keeping its aspect ratio inside the w x h box (left/top aligned)."""
    path = FIG / f"{name}.png"
    iw, ih = Image.open(path).size
    ar = iw / ih
    if w and h:
        if w / h > ar:
            w = h * ar
        else:
            h = w / ar
    elif h:
        w = h * ar
    else:
        h = w / ar
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    return w, h


def heading(x, y, w, title, sub=None):
    paras = [(title, dict(size=44, bold=True, color=GREEN, space=0))]
    if sub:
        paras.append((sub, dict(size=30, color=SUB, space=0)))
    text(x, y, w, 1.9 if sub else 1.2, paras)


# ---------------------------------------------------------------- frame + title
rect(0, 0, 48, 36, GREEN)
rect(0.8, 0.8, 46.4, 34.4, CARD)
rect(0.8, 0.8, 46.4, 5.4, GOLD)
text(2.5, 1.0, 43, 3.4, [("CAN LANGUAGE MODELS WRITE FEATURE NORMS LIKE PEOPLE DO?",
                          dict(size=88, bold=True, color=INK, space=0))], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(2.5, 4.3, 43, 1.6, [("Erin M. Buchanan  [add co-authors]",
                          dict(size=40, color=INK, space=0)),
                         ("Harrisburg University of Science and Technology",
                          dict(size=34, color=INK, space=0))], align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- left column (text)
LX, LW = 1.6, 12.0
y = 6.7
heading(LX, y, LW, "THE QUESTION")
text(LX, y + 1.3, LW, 6.4, [
    "Feature norms (people list what a word means) are slow and expensive to collect.",
    "Can open language models write them? We gave two models the same instructions people had, "
    "and treated each model run as one virtual participant (20 per word).",
    "We compared the lists with human norms for 200 words, each listed by 30 or more people.",
], size=31)

y = 16.0
heading(LX, y, LW, "WHAT WE FOUND")
text(LX, y + 1.3, LW, 9.2, [
    ("Llama 3.1 (8B) recovers 86% of the features people list most. A sample of 20 people recovers 89%.", dict(bold=True)),
    "A much smaller model (Qwen 2.5, 1.5B) recovers 78-79%.",
    "But count only each model's first 5 words (what a person writes) and Llama drops to 61%.",
    "Showing the model real examples helps little (about +2 points).",
    "Concrete words are a little easier (about +3.5 points per SD); word frequency and length do not matter.",
], size=31)

y = 27.0
heading(LX, y, LW, "LIMITS")
text(LX, y + 1.3, LW, 6.6, [
    "Models write about 27 words per run, people about 5.",
    "The models were not checked for having seen these norms.",
    "Two models, 200 test words, one temperature (0.7).",
], size=28)

# ---------------------------------------------------------------- right area (figures)
RX, RW = 14.4, 32.4

# row A: how it works (native boxes so the text is large)
y = 6.7
heading(RX, y, RW, "HOW IT WORKS", "Models do the same task as people; both lists go through the same cleaning")
STEPS = [
    ("1  The task", "Same instructions people had: list the properties of the word (alone, or with 8 real human lists)"),
    ("2  20 virtual people", "Each model answers 20 times; every run is one participant"),
    ("3  Cleaned like people", "Spelling, numbers, stop words; related words merged (gambling = gamble)"),
    ("4  Feature norms", "Percent of runs that listed each feature, for each of 200 test words"),
    ("5  Compared with people", "Share of the human top-10 features the model also lists; ceiling = 20 real people"),
]
bw, gap, by, bh = 5.8, 0.85, y + 2.1, 4.5
for i, (t, body) in enumerate(STEPS):
    bx = RX + i * (bw + gap)
    box = rect(bx, by, bw, bh, "F4F3EF", line=(SUB if i in (0, 4) else BLUE), shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    box.adjustments[0] = 0.06
    text(bx + 0.1, by + 0.15, bw - 0.2, 1.2, [(t, dict(size=30, bold=True, color=INK, space=0))])
    text(bx + 0.1, by + 1.45, bw - 0.2, bh - 1.5, [(body, dict(size=24, color=SUB, space=0))])
    if i < 4:
        ar = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(bx + bw + 0.1), Inches(by + bh / 2 - 0.3), Inches(gap - 0.2), Inches(0.6))
        ar.fill.solid(); ar.fill.fore_color.rgb = rgb(SUB); ar.line.fill.background()
text(RX, by + bh + 0.1, RW, 0.9, [("Example, one model run for \u201cchair\u201d:  \u201chas four legs, used for sitting, made of wood\u201d   \u2192   four \u00b7 leg \u00b7 sit \u00b7 wood",
                                  dict(size=28, color=INK, space=0))], align=PP_ALIGN.CENTER)

# row B: headline result + threshold
y = 14.4
heading(RX, y, RW, "THE HEADLINE", "Llama 3.1 comes close to what 20 people produce; a repeat-only bar flips it")
wB, hB = picture("fig2_coverage", RX, y + 2.0, w=18.6, h=7.1)
picture("fig6_threshold", RX + wB + 0.5, y + 1.0, w=RW - wB - 0.5, h=9.2)
text(RX, y + 2.0 + hB + 0.1, wB, 1.2,
     ["Models beat 20 people at 4 of 20 runs because they repeat words; people spread over many different ones."], size=22, color=SUB)

# row C: what helps + example
y = 25.2
heading(RX, y, RW, "WHAT HELPS, AND WHAT IT LOOKS LIKE")
wC, hC = picture("fig4_predictors", RX, y + 1.5, w=15.4, h=6.6)
text(RX, y + 1.6 + hC, wC, 1.4, ["Coverage rises a little with concreteness; word frequency and length do not matter."], size=22, color=SUB)
picture("fig5_examples", RX + wC + 0.6, y + 1.4, w=RW - wC - 0.6, h=8.0)

# ---------------------------------------------------------------- QR / links (placeholder)
rect(LX, 33.0, 4.0, 1.9, "EFEEEA", line=SUB)
text(LX, 33.0, 4.0, 1.9, [("QR code", dict(size=26, color=SUB, space=0))], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(LX + 4.2, 33.0, LW - 4.2, 1.9, [("Pipeline, data and results: github.com/SemanticPriming/subs2strudel (llm_feature_norms/)",
                                      dict(size=22, color=SUB, space=0))], anchor=MSO_ANCHOR.MIDDLE)

out = HERE / "poster_scip_2026.pptx"
prs.save(out)
print("wrote", out)
