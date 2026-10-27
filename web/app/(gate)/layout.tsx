import type {Metadata} from 'next';
import './gate.css';
import {Mark,REPO} from './chrome';
import Reveal from './reveal';

export const metadata: Metadata = {
  title: 'LastCopy · Wipe a tablet only after its last copy is safe',
  description: 'Per-tablet wipe clearance for ODK field teams: safe to wipe, recover first, or hold. Proven byte-for-byte by code, investigated by agents, explained in plain language.',
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
          <a href="/#how">How it works</a><a href="/#answers">Answers</a><a href="/#hood">Technology</a><a href="/#live">Live run</a><a href="/#roadmap">Roadmap</a><a href="/#faq">FAQ</a>
        </nav>
        <a className="btn ghost sm navcta" href="/demo">Replay</a>
      </div></header>
      {children}
      <footer className="foot"><div className="wrap">
        <div><a className="brand" href="/"><Mark size={20}/>LastCopy</a><p>Per-tablet wipe clearance for ODK field teams. Built for the Open Agent Hackathon 2026 with Zetaris, Meterless and NVIDIA Nemotron.</p></div>
        <div><h4>Product</h4><nav aria-label="Product"><a href="/demo">Investigation replay</a><a href="/#gate">Try the gate</a><a href="/#how">How it works</a></nav></div>
        <div><h4>Technology</h4><nav aria-label="Technology"><a href="/#hood">Agents &amp; code</a><a href="/#live">Live connected run</a><a href={`${REPO}#readme`}>README</a></nav></div>
        <div><h4>Project</h4><nav aria-label="Project"><a href={REPO}>Source on GitHub</a><a href="/#roadmap">Roadmap</a><a href="/#faq">FAQ</a></nav></div>
      </div></footer>
      <Reveal/>
    </body>
  </html>;
}
