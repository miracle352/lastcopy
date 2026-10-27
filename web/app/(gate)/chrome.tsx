export const REPO = 'https://github.com/miracle352/lastcopy';

export function Mark({size = 22}: {size?: number}) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <rect x="5" y="2.5" width="14" height="19" rx="2.5" stroke="currentColor" strokeWidth="1.6"/>
    <path d="M8.5 12.2l2.4 2.4 4.6-4.9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M10.5 18.5h3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
  </svg>;
}

