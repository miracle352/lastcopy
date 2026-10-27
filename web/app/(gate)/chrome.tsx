export const REPO = 'https://github.com/miracle352/lastcopy';

const P: Record<string, string> = {
  tablet: 'M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zM11 18h2',
  check: 'M5 12.5l4.2 4.2L19 7',
  checkc: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM8.5 12.3l2.4 2.4 4.6-5',
  circle: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z',
  upload: 'M12 16V4M7 9l5-5 5 5M5 20h14',
  download: 'M12 4v12M7 11l5 5 5-5M5 20h14',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM20 20l-4-4',
  shield: 'M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3zM9 12l2 2 4-4',
  eyeoff: 'M3 3l18 18M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.1A9.7 9.7 0 0 1 12 5c5 0 8.5 4.5 9.5 7-.4 1-1.2 2.3-2.4 3.5M6.2 6.2C4.4 7.5 3.1 9.4 2.5 12c1 2.5 4.5 7 9.5 7 1.6 0 3.1-.4 4.4-1.1',
  layers: 'M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5',
  alert: 'M12 4l9 16H3l9-16zM12 10v4M12 17h.01',
  scale: 'M12 4v16M5 8h14M5 8l-3 6a3 3 0 0 0 6 0L5 8zM19 8l-3 6a3 3 0 0 0 6 0l-3-6zM8 20h8',
  git: 'M6 3v12M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM18 9c0 6-12 3-12 9',
  cpu: 'M8 8h8v8H8zM4 10h2M4 14h2M18 10h2M18 14h2M10 4v2M14 4v2M10 18v2M14 18v2',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0',
  table: 'M4 5h16v14H4zM4 10h16M10 10v9',
  chart: 'M4 20V10M10 20V4M16 20v-7M22 20H2',
  clock: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3 2',
  list: 'M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01',
  lock: 'M6 11h12v9H6zM8 11V8a4 4 0 0 1 8 0v3',
  arrow: 'M5 12h14M13 6l6 6-6 6',
  ext: 'M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5',
};

export function Icon({name, size = 18}: {name: keyof typeof P | string; size?: number}) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={P[name] || P.circle}/></svg>;
}

export function Mark() {
  return <svg className="mk" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <rect x="5" y="2.5" width="14" height="19" rx="3" fill="currentColor" opacity=".16"/>
    <rect x="5" y="2.5" width="14" height="19" rx="3" stroke="currentColor" strokeWidth="1.6"/>
    <path d="M8.6 12.2l2.3 2.3 4.5-4.8" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>;
}
