'use client';
import {useEffect} from 'react';

// Scroll choreography for the landing page. Everything is progressive:
// without JS (or with reduced motion) the page renders fully, statically.
const GROUPS = '.head, .g2, .g3, .g4, .hood, .card.glance, .card.equation, .fig, .tbl tbody, .ilist, .final, .faq, .road';
const ITEMS = ':scope > *';

export default function Motion() {
  useEffect(() => {
    const root = document.documentElement;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    root.classList.add('mo');

    // progress bar + nav state
    const bar = document.createElement('div');
    bar.className = 'mo-bar';
    document.body.appendChild(bar);
    const nav = document.querySelector('.nav');
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const h = root.scrollHeight - innerHeight;
        bar.style.transform = `scaleX(${h > 0 ? scrollY / h : 0})`;
        nav?.classList.toggle('scrolled', scrollY > 12);
        // gentle parallax on the hero figure
        const fig = document.querySelector<HTMLElement>('.hero .diagram');
        if (fig && scrollY < innerHeight) fig.style.transform = `translateY(${scrollY * -0.06}px)`;
        ticking = false;
      });
    };
    addEventListener('scroll', onScroll, {passive: true});
    onScroll();

    // tag reveal targets
    const targets: Element[] = [];
    document.querySelectorAll('main section:not(.hero)').forEach(sec => {
      sec.querySelectorAll(GROUPS).forEach(g => {
        const kids = Array.from(g.querySelectorAll(ITEMS));
        const list = kids.length > 1 && !g.matches('.head') ? kids : [g];
        list.forEach((el, i) => {
          if (el.classList.contains('rv')) return;
          el.classList.add('rv');
          (el as HTMLElement).style.setProperty('--i', String(Math.min(i, 8)));
          targets.push(el);
        });
      });
      // headings inside sections slide words in
      sec.querySelectorAll('h2').forEach(h => {
        if (h.closest('#gate')) return;
        if (h.dataset.split) return;
        h.dataset.split = '1';
        const words = (h.textContent || '').split(' ');
        h.setAttribute('aria-label', h.textContent || '');
        h.innerHTML = words.map((w, i) => `<span class="w" aria-hidden="true" style="--w:${i}"><span>${w.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</span></span>`).join(' ');
      });
    });

    // number count-up for mono figures like "500 / 500" or "1,980"
    const countUp = (el: HTMLElement) => {
      if (el.dataset.counted) return;
      el.dataset.counted = '1';
      const original = el.textContent || '';
      const nums = original.match(/\d[\d,]*/g);
      if (!nums) return;
      const values = nums.map(n => Number(n.replace(/,/g, '')));
      const t0 = performance.now(), dur = 1100;
      const frame = (t: number) => {
        const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
        let k = 0;
        el.textContent = original.replace(/\d[\d,]*/g, () => {
          const v = Math.round(values[k++] * e);
          return v.toLocaleString('en');
        });
        if (p < 1) requestAnimationFrame(frame); else el.textContent = original;
      };
      requestAnimationFrame(frame);
    };

    const io = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (!en.isIntersecting) return;
        const el = en.target as HTMLElement;
        el.classList.add('in');
        el.closest('section')?.classList.add('in');
        el.querySelectorAll<HTMLElement>('td.mono, .hero-stats b').forEach(countUp);
        io.unobserve(el);
      });
    }, {rootMargin: '0px 0px -12% 0px', threshold: 0.12});
    targets.forEach(t => io.observe(t));
    document.querySelectorAll('main section h2').forEach(h => io.observe(h));

    return () => { removeEventListener('scroll', onScroll); io.disconnect(); bar.remove(); };
  }, []);
  return null;
}
