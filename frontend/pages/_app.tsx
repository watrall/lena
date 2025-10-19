'use client';

import type { AppProps } from 'next/app';
import Head from 'next/head';

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
          Pilot Mode — No login. Sample data only.
        </header>
        <main className="app-content">
          <Component {...pageProps} />
        </main>
      </div>
    </>
  );
}
