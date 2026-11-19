# Traps

Each of these cost time once. Grouped by where they bite.

## PowerPoint

- **A deck replaced on disk while PowerPoint has it open** shows "the picture can't be displayed" for media it had
  not loaded yet, and clips that do not move. Build each delivery under a name that is not open, and tell the
  author to close the old file. A lock file `~$Name.pptx` beside the deck means it is open.
- **Media controls** (the bar with the time line) appear over clips in a show unless `showMediaCtrls` is off in
  `presProps.xml`. `Deck.save()` writes that.
- **Autoplay** needs timing XML per slide that calls `playFrom(0.0)` on the clip after the slide begins; a clip
  placed with python-pptx alone waits for a click. `Slide.done()` writes it; the audit checks every clip.
- **PowerPoint opened by a script** stops on a "Grant File Access" dialog on a Mac. Open the deck with
  `open -a "Microsoft PowerPoint"` first, then read it back by script; say so first, it opens on the author's
  screen.
- Pictures PowerPoint cannot show: CMYK or 16-bit images, interlaced PNGs, JPEG data under a `.png` name.
  `check_pptx.py` finds them.
- A typeface missing on the showing computer is replaced silently and lines re-break. Deliver the Arial copy for
  any hall machine.

## Keynote

- **Keynote refuses a .pptx whose speaker notes were written by python-pptx.** Keep notes in files
  (`notes_in_file=False`, the default) and set them in Keynote by script if needed.
- A refused or blocked import leaves a small modal alert that scripts cannot see or dismiss; later opens then hang.
  The author has to close it, or Keynote must be restarted.
- Autoplay and fade-ins written as PowerPoint timing survived the import once, in one conversion; looping must be
  set again (`repetition method`). Check the imported file by eye. Two days later the author reported the
  opposite (next item), so treat survival as unproven.
- **Open trap, never diagnosed:** opening the .pptx in Keynote, the author saw "super low quality static images"
  and clips that did not move, and the dynamic deck seemed not to move either. No cause was found. It puts in
  doubt the claim above, the use of lighter poster frames as the first way to save size (`motion.md` section 8:
  a clip that does not play shows its poster), and any report that says the deck "works in Keynote" without
  someone having run it there. If the author presents from Keynote: keep posters at full quality, convert with
  `to_keynote.applescript` and read back the exported images, and have the author run the .key well before the
  talk.
- Inside an AppleScript `tell application "Keynote"`, reading a file stalls on a sandbox prompt; read with
  `do shell script "cat ..."`.
- Opening any file in Keynote or PowerPoint puts it on the author's screen. Never open a half-built deck there.

**Converting to .key by script** (`scripts/to_keynote.applescript`; it worked once, then failed for two days because
Keynote was left stuck):

1. Check that the author is not working in Keynote. Launching it reopened three of the author's saved decks; say so
   in the report if it happens.
2. Launch clean: `open -a Keynote --args -ApplePersistenceIgnoreState YES`.
3. Warm up: open a minimal one-slide .pptx first and wait until `count of documents` > 0; the first open after a
   launch often hangs.
4. Open the real deck and poll `name of every document` until it appears; the reference `open` returns is not
   usable for decks with several movies. The script does this, sets notes read by `do shell script "cat ..."`,
   loops the movies, saves the .key and exports images and an all-stages PDF.
5. Read back: count the build stages in the PDF against the deck, look at the exported images, check that the
   movies kept autoplay.
6. Give every osascript call a time limit: `perl -e 'alarm 300; exec @ARGV' osascript ...`.
7. When a run stalls: list on-screen windows (JXA with CoreGraphics needs no accessibility rights), capture only the
   alert window (`screencapture -x -o -l <window id>`) and read it. Then bisect with `scripts/keynote_try.sh`: one
   test deck per feature (movies, fade-ins, notes, text-frame settings), then the deck without movies, each movie
   alone, two, three and six together. In the original project every piece opened on its own: the stall came from
   Keynote's state.
8. Keep the last good .key aside (`qa/previous.key`) and restore it if a new run fails.
9. **Never force-quit Keynote while the author may have documents open.** A scripted quit was refused by the agent
   harness as destructive, and the author got no .key for two days. Give them one line to run instead ("open the
   .pptx in Keynote and save it as .key"), and say in the report that the .key was not delivered.

## Previews

- `qlmanage -t` (QuickLook) renders a one-slide copy of the deck to PNG without opening an application. It can
  hang; `preview_slides.py` uses a timeout, retries, and its own temporary folders, and never kills other
  QuickLook processes.
- QuickLook shows a clip as its poster frame. A missing poster shows as an empty rectangle.
- QuickLook's text rendering is close to PowerPoint's but not identical: a line that fits by a pixel can wrap.
  Leave boxes a little wider than the measured text (the library does).
- Full-deck previews at 3840 px take a second or two per slide; use 1600 px while working.
- Without QuickLook, `preview_slides.py --backend libreoffice` converts the whole deck with LibreOffice. A
  LibreOffice window already open makes a headless conversion fail silently, so the script runs it in a private
  profile in its own temporary folder. LibreOffice replaces missing fonts and can break lines where PowerPoint
  does not: judge layout from it, and judge line breaks only on the showing computer or in QuickLook. This
  backend was tested here with a stand-in converter only (Suggested, not yet tested in real work).

## Clips

- **A deck built while a clip is encoding embeds a broken clip.** Wait for renders. The audit decodes the first and
  last frame of every embedded clip.
- H.264 in yuv444p, 10 bit, or HEVC plays only on some machines and shows as a still elsewhere. Encode yuv420p.
- Odd pixel sizes fail in some players: crop to even numbers.
- A "white" background encoded to video comes back as 253 and shows as a faint box on a white slide. Clamp
  near-white to 255 before encoding, or use the deck's ground color.
- Re-encoding a clip that was already encoded to a target size, at a fixed CRF, can produce a larger file. Fit
  from the master.
- A stale fitted copy (older than its source) silently wins if the builder prefers `media/fit/`. `deck.py` compares
  times and warns.
- OpenCV writes H.264 only where the platform has an encoder (`VideoWriter(...).isOpened()`); PyAV carries its own.

## Images

- PIL needs `ImageFile.MAXBLOCK` raised to save large optimized JPEGs ("Suspension not allowed here", "broken data
  stream when writing image file"). `deck.py` sets it.
- Drawing on an RGBA layer with `ImageDraw` overwrites alpha: draw translucent shapes on their own layer and
  composite.
- JPEG with chroma subsampling smears colored points: use `subsampling=0` at quality 88 and above.
- A panel of points colored by thousands of categories is noise at any resolution.

## Recording from a website

- Record from a patched local copy, one figure at a time. Under heavy load the browser times out
  (`Runtime.callFunctionOn timed out`); resume from the last frame written (`record_canvas.js` does, and writes
  each frame under a temporary name first, so a killed run leaves no half-written frame).
- A color patch applied to shared code can turn labels inside light boxes invisible. Look at one frame before
  recording nine hundred.
- The canvas may cap its pixel ratio; measure the frame.
- The local test server may be single-threaded: one headless browser at a time.

## Shell and environment

- zsh does not split an unquoted variable into words: `for pair in "a 1" "b 2"; do set -- $pair` passes one
  argument, and `P="env PYTHONNOUSERSITE=1 python3"; $P script.py` fails. Write the commands out, use an array, or
  `export` the variable and keep `$P` a single path.
- zsh expands a word that starts with `=` as the path of a command: `echo ==A1` is an error. Quote such strings.
- A foreground `sleep` may be blocked in agent shells; wait on a condition in a background command instead.
- Check free disk space before long renders, and the battery before an hour of encoding on a laptop.
- Install nothing into the system Python without asking; note which interpreter has which package (PyAV is often
  only in a project's virtual environment).

## People and the web

- Institute pages, figshare, publisher and vendor pages often refuse scripted downloads. Do not disguise the
  client. An honest, descriptive client name (what the download is and why) worked on a media commons site where a
  generic or browser-like one was refused; otherwise ask the author for the file.
- A vendor page that answers HTTP 429 to a fact-checker is not a reason to cite from memory: find another primary
  record (a filing, the press release, the data repository) or mark the fact as not opened.
- Photographs: confirm the person by the name on the source page. Two people in one institute can share a first
  name.
- A QR code to a gated or unpublished page leads the room to a login. Publishing a page is the author's decision:
  run the site's own leak scan, tell them exactly what becomes public, and do it only on their word.
