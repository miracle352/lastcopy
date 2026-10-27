'use client';
import {useEffect} from 'react';

/** Progressive enhancement: content is visible without JS; with JS, sections fade up once. */
export default function Reveal() {
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return;
    const items = [...document.querySelectorAll<HTMLElement>('[data-r]')].filter(el => el.getBoundingClientRect().top > innerHeight);
    items.forEach(el => el.classList.add('reveal'));
    const io = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), {rootMargin: '0px 0px -8% 0px'});
    items.forEach(el => io.observe(el));
    return () => io.disconnect();
  }, []);
  return null;
}
