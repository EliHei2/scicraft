# Motion and the static twin

Movement belongs on a slide when it is the argument: the audience watches the claim happen. The author asked for
animations "optimized for engagement and clarity", liked the ones that showed real data moving, and rejected the
ones that tried to explain a mechanism with invented drawings.

## Contents
1. Clips that earned their place
2. Rules for every clip
3. Making a clip
4. Encoding
5. Recording a figure from a website
6. Fade-ins that start by themselves
7. The static twin
8. The size budget

## 1. Clips that earned their place

| Clip | What moves | Length | Ends |
|---|---|---|---|
| Title loop | a slow drift over the showcase data, dimmed under the text | 12 to 16 s | loops |
| Zoom through scales | one camera move from the whole sample to single measurements; the scale ladder and bar update | 12 to 17 s | loops, or rests zoomed in |
| Divider | a vertical divider sweeps back and forth across one field of view: expert annotation on one side, the method's output on the other | 16 s, sinusoidal | loops |
| Fly to the embedding | points leave the tissue and land in the embedding picture, which then turns; the divider can then cross both | 20 s | rests |
| Search | a selection is ringed, the similarity lights up as the view widens to the whole sample, then the view flies into matches | 7 to 14 s per selection | loops |
| Lines one at a time | each method's line appears in turn; the work's own stays on top | 20 s | rests on all lines |
| The website's method figure | recorded as it is, labels made readable | its own length, sped up if slow | rests |

**Two linked views in one clip.** One clip per slide still holds when the slide shows two views that move together
(the divider over the input and the same points in the embedding). Render both from one `frame(t)`, or lock two
existing clips frame to frame with `compose_clips.py LEFT.mp4 RIGHT.mp4 OUT.mp4`, which re-times the second to the
first so both loop together.

**The divider clip from two renders.** When the two readings already exist as clips or stills of the same view,
`divider_clip.py LEFT RIGHT OUT.mp4 --labels "<left words>" "<right words>" --period 16 --ground 141416` makes the
divider clip: a vertical divider sweeps sinusoidally (0.5 + 0.24 x sin(2 pi t / 16) of the width), a thin ink line
with a round handle marks the boundary, and each side carries its label on a plate. The first frame has the divider
in the middle, so the poster and the still for the PDF show both readings. Both inputs must share one camera path;
otherwise the divider joins two different places. The original slider clip was made this way from two zoom clips of
one camera move.

A clip that explains a mechanism with a newly invented drawing was rejected twice ("use our previous vid"). If the
project has an animation the author likes, use that one.

## 2. Rules for every clip

- It starts with the slide and needs no click. It loops, or plays once and rests on its last frame (`loop=False`);
  the last frame of a resting clip is its poster and must be worth looking at for half a minute.
- One clip per slide, no sound, no visible controls.
- Labels inside the clip follow the type rules: white, on plates where they cross data, at least 28 px at the size
  the clip is shown. Their words are the author's and count toward the slide's 25 (`words=`).
- Ease camera moves in and out (a smoothstep); hold the first and last view for a second.
- **The first frame is a full, meaningful picture.** No fade in from the ground at t = 0: Keynote and QuickLook use
  the first frame as the poster, and a faded one shows an empty rectangle. In the original project every clip was
  re-rendered for this.
- Keep one camera path for clips that will be compared or split by a divider.
- Pixel size at least the size shown on a 1920 x 1080 slide; a square clip in the column layout is 1080 x 1080.
- Changing a clip the author liked: change labels, colors or size. Keep the picture.

## 3. Making a clip

Render frames with numpy and PIL (or the project's own plotting code) and encode them. The frame loop should take
`t` in seconds and return an RGB array, so single frames can be rendered as stills for the PDF from the same code:

```python
def frame(t):            # -> (H, W, 3) uint8
    ...
stills = {name: frame(t) for name, t in (('whole', 0.0), ('cells', 9.5))}
```

Put every string a clip draws in one module or JSON file, so the words can be checked (`words.md`, section 5).
Write the poster (the frame the deck shows before play, and the still for the PDF) to `media/posters/<clip>.png`;
`deck.py` cuts it from the clip when it is missing.

Render long clips in the background and wait for them. **Never build the deck while a clip is being written**: the
deck embeds the unfinished file and the clip is broken in a way only a decode check finds.

## 4. Encoding

PowerPoint and Keynote on every platform play H.264 in yuv420p with an even pixel size. Anything else (4:4:4,
10 bit, HEVC without the right tag, odd sizes) plays on the machine that made it and shows a still elsewhere.

With PyAV (`pip install av`):

```python
import av
from fractions import Fraction
co = av.open('clip.mp4', 'w', format='mp4', options={'movflags': '+faststart'})
st = co.add_stream('libx264', rate=30)
st.width, st.height, st.pix_fmt = W, H, 'yuv420p'                 # W and H even
cc = st.codec_context
cc.colorspace, cc.color_primaries, cc.color_trc, cc.color_range = 1, 1, 1, 1      # BT.709, limited range
st.options = {'crf': '20', 'preset': 'slow'}
for i in range(n):
    f = av.VideoFrame.from_ndarray(frame(i / 30), format='rgb24').reformat(format='yuv420p', dst_colorspace='ITU709', dst_color_range='MPEG')
    f.pts, f.time_base = i, Fraction(1, 30)
    for p in st.encode(f):
        co.mux(p)
for p in st.encode():
    co.mux(p)
co.close()
```

- CRF 18 to 22 for tissue and points; flat diagrams compress to a few hundred kbit/s at CRF 17.
- Without PyAV, OpenCV's `VideoWriter` with the `avc1` code writes H.264 on a Mac (check `isOpened()`); an `ffmpeg`
  binary works too. `clip_sheet.py` shows what each file really is.
- 24 or 30 frames a second; more does not help and costs size.
- A GIF of the same quality is several times larger than the H.264 clip and limited to 256 colors: keep the clips.

## 5. Recording a figure from a website

Interactive canvas figures of a project site can be recorded frame by frame, exactly on their own timeline, with
puppeteer driving a local copy of the site (no screen capture, no real-time playback):

- Serve a copy of the site locally. Patch the copy, never the site: colors (for example the expert's annotation
  colors instead of the figure's own), quiet gray labels to the deck's ink, thicker arrows, formulas removed.
- For each frame set the figure's time, render, and save `canvas.toDataURL('image/png')`. Run the timeline forward
  to the frame so that step-dependent state is right. `record_canvas.js URL OUT_DIR --selector canvas --set-time
  "<code using t>" --fps 30 --seconds N` does this with puppeteer and writes `NNNNN.png`; it resumes after the last
  frame written. `--set-time` is the figure's own way of setting its clock (in the original site, setting the
  stage's time and calling its render). Needs Node 18 or later, `puppeteer-core` and a Chrome binary.
- Composite the transparent frames on the deck's ground, crop to the drawing, and encode. Speed a slow figure up by
  picking frames (1.6x), and add two seconds of rest on the finished drawing.
- After patching colors, check the labels inside light boxes: a patch that turns all ink light makes them vanish.
- After re-theming a recorded figure (dark to white or back), measure what was lost: binarize the strokes of each
  frame in both versions, count strokes present in the original and missing in the new one, and look at the crops
  with the most losses. Thin strokes vanished this way in the original project.
- A canvas may cap its own pixel ratio, so asking for twice the size can give less than that. Check the size of the
  frame you got before using it for a still.
- A headless recording under heavy machine load times out: record one figure at a time and resume from the last
  written frame.

## 6. Fade-ins that start by themselves

For a slide that should assemble (the zoom-ins arriving after the whole view, the arguments of the future slide):
`s.auto(at_ms, *shapes)` fades shapes in at a time after the slide opens. Nothing waits for a click, so the speaker
can move on whenever they want. Use click builds (`s.step`) only if the author asks; the audit reports them.

## 7. The static twin

The same builder writes a second file with `--static`, in which every clip is replaced by a still. It becomes the
PDF: what the author reads on a phone, what is uploaded where movies are not accepted, the fallback in the hall.

The two files may differ slide by slide, because they are good at different things:

| In the deck | In the PDF |
|---|---|
| zoom through scales | the whole view with zoom-in panels, or a row of the stages with their names |
| moving divider | the divider in the middle of a field of view where structures cross it |
| search clip | the whole view with selection and numbered matches, and their zoom-ins |
| lines one at a time | the finished chart, or the heat map of ranks |
| website method animation | the paper's figure, recolored |
| points flying to the embedding | the tissue and the embedding side by side with a key |

Branch on `D.static` in the builder for these slides. Give each static slide the stills it needs
(`still='name.png'` on a clip, or its own pictures) and check that the still alone makes the slide's point: the
last frame of a clip is often not the frame that shows the claim.

Render the PDF from the twin: `preview_slides.py` at 3840 px, then `make_pdf.py` with a size limit.

## 8. The size budget

Decks are uploaded to conference systems and mailed. Ask for the limit early (50 MB is common).

1. `check_pptx.py DECK 50` lists every media part by size.
2. Unless the deck may be shown from Keynote (then skip to 3), lighten what is not looked at: the poster frames of
   clips (`Deck(poster_quality=65)`); large opaque stills as JPEG.
3. Budget the clips: give each a share by how much of the talk it carries, and fit the largest ones with
   `fit_clip.py IN OUT MB` (same pixels, lower bitrate). Write the fitted copy outside `media/` and move it to
   `media/fit/` when it is finished; the builder uses a fitted copy only if it is newer than the clip.
4. Do not refit a clip that was already encoded to a target size at a fixed quality: the second pass can come out
   larger. Fit from the master (the high-quality first encode) instead.
5. Before swapping a re-encoded clip in, compare it with the master: a signal-to-noise figure over the frames and a
   side-by-side crop at full size. Done this way, a deck went from 220 MB to 142 MB with no visible loss.
6. Run at most two encodes or recordings at once on a laptop, whoever asks for more (`process.md` section 7).
7. Never lower pixel sizes below what the slide shows. "Smaller with no loss" means bitrate and posters.
8. Say the final sizes in the report.

**An open question about lighter posters.** Step 2 makes poster frames lighter (`poster_quality=65`). In the
original project the author once opened the deck in Keynote and saw "super low quality static images" and clips
that did not move; the cause was never found. If a program shows a clip as its poster (a failed import, a clip
that does not start, Keynote's import), the lighter poster is what the room sees. So when the deck may be shown
from Keynote, or the slideshow has not been run in the presenting program, keep posters at full quality
(`Deck(poster_quality=92)` or higher) and lighten them last, and say in the report which you chose. See
`traps.md`, Keynote.
