// A small engine for method figures: one canvas per figure, a timeline of steps whose captions come from the paper,
// chips to jump to a step, and pointer handling that leaves page scrolling alone. No dependencies besides ../tex.js
// (assets/tex.js of the skill), which draws TeX labels. Copy assets/tex.js to public/tex.js and assets/fx/ to public/fx/.
//
// Markup of one figure (the captions are whole sentences from the paper; without script they stay a readable list):
//   <figure class="fx" data-fx="name">
//     <h3>Title</h3>
//     <div class="fx-stage" role="img" aria-label="What the finished drawing shows."></div>
//     <ol class="fx-steps"><li><b>Step</b><span>Caption from the paper.</span></li> ...</ol>
//   </figure>
//   new Stage(figureElement, scene)
//
// A scene is an object
//   size(narrow) -> {W, H}          its design size, for a narrow (< 700 px) or a wide stage
//   durations                       seconds per step, one per <li> of .fx-steps
//   draw(ctx, s)                    one frame, in design units; a function of the timeline time s.t and of the pointer
//   poster?(starts) -> t            the frame to rest on before the first play (default: the last frame)
//   pointer?(type, x, y, e, stage)  'move' | 'down' | 'up' | 'leave' in design units; may return a CSS cursor
//   grabs?(x, y, stage)             true where a touch drag belongs to the figure (a sphere to turn, a region to draw);
//                                   elsewhere a vertical swipe scrolls the page
//   ambient?(s)                     true while the scene moves on its own although the timeline stands still
//   hint?(s), controls?(stage)      a line of help over the stage; the scene's own controls
//   skip?                           false to keep a click from skipping to the end
// The figure plays once when it comes into view, rests on a finished frame before and after, jumps on a chip, and
// honors reduced motion by showing finished frames. The loop runs only while something moves.
//
// Test hook: the figure element gets  el.__fig = { stage, seek(u) }, u from 0 to 1 over the whole timeline. This is
// what scripts/sweep.js calls:  SEEK='el.__fig && el.__fig.seek(t)' FIGS='figure.fx' node sweep.js
import { upgradeTex } from '../tex.js';
export { loadTex, tex, texBox, texSVG, upgradeTex } from '../tex.js';

export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const seg = (t, a, b) => clamp((t - a) / (b - a));                         // progress of t through [a, b]
export const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const easeOut = (t) => 1 - Math.pow(1 - t, 3);
export const back = (t) => 1 + 2.2 * Math.pow(t - 1, 3) + 1.2 * Math.pow(t - 1, 2);   // a small overshoot
export const sseg = (t, a, b) => ease(seg(t, a, b));
export const rgb = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
export const mix = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
export const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
export const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const SKIP = matchMedia('(pointer: coarse)').matches ? 'tap the figure to skip ahead' : 'click the figure to skip ahead';

// A small deterministic generator, so a figure looks the same on every visit.
export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ------------------------------------------------------------------------------------------------ text
// Live values (counts, names) are set in the page's mono face.
export function text(ctx, str, x, y, o = {}) {
  const a = o.alpha ?? 1;
  if (a <= 0.003) return 0;
  ctx.save();
  ctx.globalAlpha *= a;
  ctx.font = `${o.weight || 400} ${o.size || 12}px "IBM Plex Mono", ui-monospace, Menlo, monospace`;
  ctx.textAlign = o.align || 'left';
  ctx.textBaseline = o.baseline || 'alphabetic';
  if (o.halo) {
    ctx.lineWidth = 3.5;
    ctx.lineJoin = 'round';
    ctx.strokeStyle = o.halo;
    ctx.strokeText(str, x, y);
  }
  ctx.fillStyle = o.color || '#f4f4f5';
  ctx.fillText(str, x, y);
  const w = ctx.measureText(str).width;
  ctx.restore();
  return w;
}

// ------------------------------------------------------------------------------------------------ stage
export class Stage {
  constructor(root, scene) {
    this.root = root;
    this.scene = scene;
    this.box = root.querySelector('.fx-stage');
    this.canvas = document.createElement('canvas');
    // the description belongs to the drawing itself; the stage also holds controls, which stay reachable
    this.canvas.setAttribute('role', 'img');
    this.canvas.setAttribute('aria-label', this.box.getAttribute('aria-label') || '');
    this.box.removeAttribute('role');
    this.box.removeAttribute('aria-label');
    this.box.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
    this.dur = scene.durations;
    this.starts = [0];
    for (const d of this.dur) this.starts.push(this.starts[this.starts.length - 1] + d);
    this.T = this.starts[this.dur.length];
    this.t = 0;
    this.until = this.T;
    this.playing = false;
    this.seen = false;
    this.visible = false;
    this.clock = 0;
    this.step = -1;
    this.ptr = { x: -1, y: -1, inside: false, down: false };
    this.buildControls();
    this.bind();
    this.resize();
    // Before its first play a figure rests on a finished frame (its last, or the one its scene names) and already
    // answers the pointer: nobody scrolls past an empty canvas.
    this.t = REDUCED || !scene.poster ? this.T : scene.poster(this.starts);
    if (REDUCED) this.seen = true;
    this.syncStep();
    this.render(0);
    root.__fig = { stage: this, seek: (u) => this.seek(u) };
  }

  // Jump to the fraction u of the whole timeline and draw that frame (for tests and for a scrubber).
  seek(u) {
    this.seen = true;
    this.playing = false;
    this.t = clamp(u) * this.T;
    this.syncStep();
    this.render(0);
  }

  // ---- DOM: a play button, one chip per step, and the caption of the step in view
  buildControls() {
    const list = this.root.querySelector('.fx-steps');
    const items = [...list.children];
    if (items.length !== this.dur.length) throw new Error(`${this.root.dataset.fx}: ${items.length} captions for ${this.dur.length} steps`);
    const bar = document.createElement('div');
    bar.className = 'fx-bar';
    this.playBtn = document.createElement('button');
    this.playBtn.type = 'button';
    this.playBtn.className = 'fx-play';
    this.playBtn.addEventListener('click', () => {
      if (this.playing) this.pause();
      else if (this.t >= this.T - 1e-3) this.play(0, this.T);
      else this.play(this.t, this.T);
    });
    bar.appendChild(this.playBtn);
    const chips = document.createElement('div');
    chips.className = 'fx-chips';
    chips.setAttribute('role', 'group');
    chips.setAttribute('aria-label', 'Steps');
    this.chips = items.map((li, k) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'fx-chip';
      const title = li.querySelector(':scope > b');
      b.append(...[...title.childNodes].map((n) => n.cloneNode(true)));
      b.addEventListener('click', () => this.go(k));
      chips.appendChild(b);
      return b;
    });
    bar.appendChild(chips);
    this.cap = document.createElement('p');
    this.cap.className = 'fx-cap';
    this.cap.setAttribute('aria-live', 'polite');
    this.texts = items.map((li) => li.querySelector(':scope > span').innerHTML);
    this.top = document.createElement('div');
    this.top.className = 'fx-top';
    this.hintEl = document.createElement('div');
    this.hintEl.className = 'fx-hint';
    this.top.appendChild(this.hintEl);
    (this.box.closest('.scroll-x') || this.box).before(this.top);
    list.hidden = true;
    this.root.append(bar, this.cap);
    this.bar = bar;
    if (this.scene.controls) this.scene.controls(this);
    this.root.classList.add('fx-live');
  }

  bind() {
    const c = this.canvas;
    const at = (e) => {
      const r = c.getBoundingClientRect();
      this.ptr.x = (e.clientX - r.left) / this.k;
      this.ptr.y = (e.clientY - r.top) / this.k;
    };
    const send = (type, e) => {
      const cur = this.scene.pointer ? this.scene.pointer(type, this.ptr.x, this.ptr.y, e, this) : null;
      if (typeof cur === 'string') c.style.cursor = cur;
      this.wake();
    };
    // A touch that starts where the scene wants the drag is kept from scrolling the page (the canvas lets vertical
    // swipes through everywhere else).
    c.addEventListener('touchstart', (e) => {
      if (!this.scene.grabs || e.touches.length !== 1) return;
      const r = c.getBoundingClientRect(), t = e.touches[0];
      if (this.scene.grabs((t.clientX - r.left) / this.k, (t.clientY - r.top) / this.k, this)) e.preventDefault();
    }, { passive: false });
    c.addEventListener('pointermove', (e) => { at(e); this.ptr.inside = true; send('move', e); });
    c.addEventListener('pointerdown', (e) => {
      at(e);
      this.ptr.down = this.ptr.inside = true;
      this.tap = [e.clientX, e.clientY];
      try { c.setPointerCapture(e.pointerId); } catch { /* a synthetic event has no capture */ }
      send('down', e);
    });
    const up = (e) => {
      if (!this.ptr.down) return;
      at(e);
      this.ptr.down = false;
      const tapped = e.type === 'pointerup' && this.tap && Math.hypot(e.clientX - this.tap[0], e.clientY - this.tap[1]) < 8;
      this.tap = null;
      if (tapped) this.seen = true;                                  // a visitor already exploring is not interrupted by the first play
      if (tapped && this.playing && this.scene.skip !== false) { this.finish(); return; }
      send('up', e);
    };
    c.addEventListener('pointerup', up);
    c.addEventListener('pointercancel', up);
    // a finger that lifts leaves its selection in place; a mouse that leaves clears it
    c.addEventListener('pointerleave', (e) => { this.ptr.inside = false; if (e.pointerType !== 'touch') send('leave', e); });
    new ResizeObserver(() => { this.resize(); this.render(0); }).observe(this.box);
    new IntersectionObserver(([e]) => {
      this.visible = e.isIntersecting;
      if (this.visible) this.kick();
    }, { rootMargin: '80px' }).observe(this.box);
    if (!REDUCED) {
      const first = new IntersectionObserver(([e]) => {
        if (!e.isIntersecting) return;
        first.disconnect();
        if (!this.seen) this.begin();
      }, { threshold: 0.45 });
      first.observe(this.root);                                    // the whole figure: a stage wider than a phone still starts
    }
    document.fonts?.ready.then(() => this.render(0));
  }

  resize() {
    const cw = this.box.clientWidth || 1;
    this.narrow = cw < 700;
    const { W, H } = this.scene.size(this.narrow);
    this.W = W;
    this.H = H;
    this.k = cw / W;
    this.box.style.aspectRatio = `${W} / ${H}`;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const pw = Math.round(cw * dpr), ph = Math.round(cw * H / W * dpr);
    if (this.canvas.width !== pw || this.canvas.height !== ph) { this.canvas.width = pw; this.canvas.height = ph; }
    this.px = pw / W;                                             // device pixels per design unit
    const wrap = this.box.closest('.scroll-x');
    this.scrolls = !!wrap && wrap.scrollWidth > wrap.clientWidth + 1;
  }

  // ---- timeline
  play(from, until) {
    this.seen = true;
    this.t = from;
    this.until = until;
    this.playing = true;
    this.kick();
    this.syncStep();
  }

  pause() { this.playing = false; this.syncStep(); }

  // The first play: the finished frame fades, then the figure builds itself from the start.
  begin() {
    this.seen = true;
    this.canvas.style.opacity = 0;
    setTimeout(() => { this.canvas.style.opacity = 1; this.play(0, this.T); }, 300);
  }

  // Skip ahead to the finished figure, which answers the pointer.
  finish() {
    this.playing = false;
    this.t = this.T;
    this.syncStep();
    this.wake();
  }

  // Show step k: play it from its start, or with reduced motion show it complete.
  go(k) {
    this.seen = true;
    if (REDUCED) { this.t = this.starts[k + 1] - 1e-3; this.playing = false; this.syncStep(); this.render(0); return; }
    this.play(this.starts[k], this.starts[k + 1]);
  }

  stepAt(t) {
    let k = 0;
    while (k < this.dur.length - 1 && t >= this.starts[k + 1]) k++;
    return k;
  }

  syncStep() {
    const k = this.stepAt(this.t);
    if (k !== this.step) {
      this.step = k;
      this.chips.forEach((c, i) => { c.classList.toggle('on', i === k); c.setAttribute('aria-pressed', String(i === k)); });
      this.cap.innerHTML = this.texts[k];
      upgradeTex(this.cap);
    }
    const p = clamp((this.t - this.starts[k]) / this.dur[k]);
    this.chips.forEach((c, i) => c.style.setProperty('--p', i < k ? 1 : i === k ? p.toFixed(3) : 0));
    const state = this.playing ? 'pause' : this.t >= this.T - 1e-3 ? 'replay' : 'play';
    if (this.playBtn.dataset.state !== state) {
      this.playBtn.dataset.state = state;
      this.playBtn.setAttribute('aria-label', state === 'pause' ? 'Pause' : state === 'replay' ? 'Play again' : 'Play');
    }
  }

  // ---- frames: the loop runs while the figure is on screen and something moves
  wake(seconds = 1.5) {
    this.awake = Math.max(this.awake || 0, performance.now() + seconds * 1000);
    this.kick();
  }

  kick() {
    if (this.raf || !this.visible) return;
    if (REDUCED) { this.render(0); return; }
    this.last = performance.now();
    const tick = (now) => {
      this.raf = 0;
      const dt = Math.min(0.05, (now - this.last) / 1000);
      this.last = now;
      if (this.playing) {
        this.t += dt;
        if (this.t >= this.until) { this.t = this.until >= this.T ? this.T : this.until - 1e-3; this.playing = false; }
      }
      this.clock += dt;
      this.syncStep();
      this.render(dt);
      const moving = this.playing || now < (this.awake || 0) || (this.scene.ambient && this.scene.ambient(this.state));
      if (this.visible && moving) this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  render(dt) {
    const ctx = this.ctx, k = this.stepAt(this.t);
    ctx.setTransform(this.px, 0, 0, this.px, 0, 0);
    ctx.clearRect(0, 0, this.W, this.H);
    const s = {
      t: this.t, T: this.T, step: k, local: this.t - this.starts[k], starts: this.starts, dur: this.dur, clock: this.clock, dt,
      W: this.W, H: this.H, narrow: this.narrow, playing: this.playing, rest: !this.playing, done: this.t >= this.T - 1e-3,
      ptr: this.ptr, px: this.px, scrolls: this.scrolls,
    };
    this.state = s;
    this.scene.draw(ctx, s);
    const hint = this.playing && this.scene.skip !== false ? SKIP : this.scene.hint ? this.scene.hint(s) || '' : '';
    if (hint !== this.hintText) { this.hintText = hint; this.hintEl.textContent = hint; this.hintEl.classList.toggle('on', !!hint); }
  }
}
