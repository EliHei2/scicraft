"""Figure specification for compose_crops.py. Copy it beside your staged sources, rename the figures, and run
    python3 <skill>/scripts/compose_crops.py --spec spec.py --out figures/

Coordinates are in source units with the origin top-left: PDF points for .pdf, pixels for rasters. Read every
crop box and mask off a gridded preview (gridprev.py SRC OUT.png --step 25). Keep one comment per figure that
names the source (paper, figure number, version) so the caption's source line can be checked against it.

Rules the spec must keep (references/figures.md):
  - crop whole panels; never split a panel from the labels it shares with a neighbor (gene names, a key);
  - mask the source's own panel letters (masks=[...] or autoletters=True); compose sets new ones;
  - nothing is redrawn, re-plotted, re-labelled or rotated;
  - compose at the full measure and do not cap row height so far that text prints under 5.5 pt.
"""
import os

from compose_crops import Panel, Stack, compose, redacted, same_scale, fit_row  # noqa: F401

S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '[src]') + '/'   # staged sources, not committed
RASTER_DPI = 300   # print resolution of the raster source in its paper: px / (printed width in inches)


def fig_example():
    # [Paper], Fig. 2a and 2b (published version), plus Fig. 3 of the same paper.
    # Panel letters a and b are text in the vector source: autoletters finds and masks them.
    a = Panel(S + '[paper_fig2.pdf]', (25, 35, 215, 218), autoletters=True)
    b = Panel(S + '[paper_fig2.pdf]', (245, 35, 470, 218), autoletters=True)
    # The raster's letter is part of the image: mask it by hand from the grid.
    c = Panel(S + '[paper_fig3.png]', (0, 0, 800, 400), masks=[(4, 4, 24, 26)], dpi=RASTER_DPI)
    return compose('fig_example', [[a, b], [c]], letters=True,
                   note='[Paper] Fig. 2a,b and Fig. 3; letters re-set a, b, c')


FIGURES = {
    'fig_example': fig_example,
}
