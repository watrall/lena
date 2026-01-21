'use client';

import { useEffect } from 'react';

import type { NextPage } from 'next';
import { useRouter } from 'next/router';

const InsightsPage: NextPage = () => {
  const router = useRouter();
  useEffect(() => {
    router.replace('/instructors');
  }, [router]);

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-700 shadow-sm">
      Redirecting to <span className="font-semibold">Instructors</span>…
    </section>
  );
};

export default InsightsPage;
