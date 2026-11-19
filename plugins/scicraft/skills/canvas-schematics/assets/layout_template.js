/* Layout contract: EDIT per figure. Logical px at 10 px/mm, so W = print width in mm x 10
 * (1830 px = 183 mm double column, 890 px = 89 mm single column). Set H from the
 * reference's aspect ratio when there is one. S is the device scale (3 gives 30 px/mm,
 * about 760 dpi). PACKS lists the primitive packs the preview harness loads.
 *
 * A region fn draws in local [0,0]..[w,h]. The master draws each panel letter and its
 * left-aligned title on one baseline in the band above the rect (titleY).
 * Titles are noun phrases of at most four words, or a bare symbol. No periods. */
(function () {
  const CANVAS = { W: 1830, H: 1040, S: 3 };
  const PACKS = ['arch'];          // 'arch', 'bio' or both
  const TY = 60;                   // title baseline band

  const REGIONS = {
    a: { x: 40,   y: 92, w: 880, h: 900, fn: 'drawRegion_a', letter: 'a', title: '[Panel a title]', titleY: TY },
    b: { x: 956,  y: 92, w: 380, h: 900, fn: 'drawRegion_b', letter: 'b', title: '[Panel b title]', titleY: TY },
    c: { x: 1372, y: 92, w: 418, h: 900, fn: 'drawRegion_c', letter: 'c', title: '[Panel c title]', titleY: TY },
  };

  const STRUCT = {
    titleY: TY,
    // inter-panel spine arrows {x0, y0, x1, y1, color}; one flow direction
    flow: [
      { x0: 924,  y0: 542, x1: 952,  y1: 542 },
      { x0: 1340, y0: 542, x1: 1368, y1: 542 },
    ],
  };

  window.LAYOUT = { CANVAS, PACKS, REGIONS, STRUCT };
})();
