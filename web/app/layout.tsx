import type { Metadata } from "next";
import "./style.css";

export const metadata: Metadata = {
  title: "LastCopy · Stage 1",
  description: "ODK evidence contracts and integration diagnostics. Development skeleton.",
  robots: {index: false, follow: false}
};
export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body><a className="skip" href="#main">Skip to content</a>{children}</body></html>;
}
