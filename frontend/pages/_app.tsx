// _app.tsx – wires global layout, metadata, and Tailwind for the LENA frontend.
import type { AppProps } from 'next/app';
import Head from 'next/head';

import Header from '../components/Layout/Header';
import '../styles/globals.css';

export default function LENAApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>LENA Pilot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <div className="flex min-h-screen flex-col bg-slate-50">
        <Header />
        <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 pb-16 pt-8 md:px-8">
          <Component {...pageProps} />
        </main>
      </div>
    </>
  );
}
