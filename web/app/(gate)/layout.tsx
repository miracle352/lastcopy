import type {Metadata} from 'next';
import './gate.css';
import {Mark, REPO} from './chrome';
import Motion from './motion';

export const metadata: Metadata = {
  metadataBase: new URL('https://lastcopy-five.vercel.app'),
  twitter: {card: 'summary_large_image'},
  title: 'LastCopy · Know which field tablets are safe to wipe',
  description: 'One answer per field tablet: safe to wipe, recover first, or hold. Proven byte-for-byte by code, investigated by agents, explained in plain language.',
  robots: {index: true, follow: true},
};

export default function GateLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en">
    <head>
      <link rel="preload" href="/fonts/fraunces-var-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/>
      <link rel="preload" href="/fonts/figtree-var-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/>
    </head>
    <body>
      <a className="skip" href="#main">Skip to content</a>
      <header className="nav"><div className="wrap">
        <a className="brand" href="/" aria-label="LastCopy home"><Mark/>LastCopy</a>
        <nav aria-label="Main">
          <a href="/#how">How it works</a><a href="/#answers">Decisions</a><a href="/#blind">Blind tests</a><a href="/#hood">Technology</a><a href="/#roadmap">Roadmap</a><a href="/#faq">FAQ</a>
        </nav>
        <a className="btn primary sm" href="/demo">Open the replay</a>
      </div></header>
      {children}
      <Motion/>
      <footer className="foot"><div className="wrap">
        <div><a className="brand" href="/"><Mark/>LastCopy</a><p>Wipe clearance for offline field-data tablets. Built for the Open Agent Hackathon 2026 on Zetaris, Meterless and NVIDIA Nemotron.</p></div>
        <div><h4>Product</h4><ul><li><a href="/demo">Investigation replay</a></li><li><a href="/#gate">Try the gate</a></li><li><a href="/#answers">The three decisions</a></li></ul></div>
        <div><h4>Technology</h4><ul><li><a href="/#hood">Agents &amp; verifier</a></li><li><a href="/#live">Live connected run</a></li><li><a href="/technical">Technical notes</a></li></ul></div>
        <div><h4>Project</h4><ul><li><a href={REPO}>Source &amp; README</a></li><li><a href="/#roadmap">Roadmap</a></li><li><a href="/privacy">Privacy</a></li></ul></div>
      </div></footer>
    </body>
  </html>;
}
