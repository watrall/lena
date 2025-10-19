'use client';

import type { AppProps } from 'next/app';
import Head from 'next/head';
import Link from 'next/link';

import '../styles/globals.css';

export default function LENAApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>LENA Pilot Chat</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <div className="app-shell">
        <header className="banner">
          <div className="banner-inner">
            <span className="banner-tagline">Pilot Mode — No login. Sample data only.</span>
            <nav className="banner-nav">
              <Link href="/">Chat</Link>
              <Link href="/faq">FAQ</Link>
              <Link href="/insights">Insights</Link>
            </nav>
          </div>
        </header>
        <main className="app-content">
          <Component {...pageProps} />
        </main>
      </div>
    </>
  );
}
