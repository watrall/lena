'use client';

import Link from 'next/link';
import { useRouter } from 'next/router';

import type { ActiveCourse } from '../../lib/course';

const links = [
  { href: '/', label: 'Chat' },
  { href: '/faq', label: 'FAQ' },
  { href: '/insights', label: 'Insights' },
];

interface HeaderProps {
  activeCourse: ActiveCourse | null;
  onSwitchCourse: () => void;
}

export default function Header({ activeCourse, onSwitchCourse }: HeaderProps) {
  const { pathname } = useRouter();

  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-8">
        <div className="flex flex-col gap-1">
          <div className="flex flex-col gap-0.5 leading-tight">
            <span className="text-lg font-semibold tracking-tight text-slate-900">LENA</span>
            <span className="text-sm font-medium text-slate-600">
              Learning Engagement &amp; Navigation Assistant
            </span>
            <span className="text-xs text-slate-500">Pilot - no authentication, demo data</span>
          </div>
          <nav className="flex items-center gap-2 text-sm font-medium text-slate-600">
            {links.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative rounded-md px-3 py-2 transition hover:text-slate-900 ${
                    isActive ? 'text-slate-900' : ''
                  }`}
                >
                  <span>{link.label}</span>
                  {isActive && (
                    <span className="pointer-events-none absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-slate-900" aria-hidden />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-600 shadow-sm md:justify-end">
          <div className="flex flex-col">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Active course
            </span>
            <span className="text-sm font-semibold text-slate-800">
              {activeCourse ? activeCourse.name : 'Select a course to begin'}
            </span>
            {activeCourse?.code && (
              <span className="text-xs text-slate-500">
                {activeCourse.code}
                {activeCourse.term ? ` · ${activeCourse.term}` : ''}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onSwitchCourse}
            className="rounded-full bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-200"
          >
            {activeCourse ? 'Switch course' : 'Choose course'}
          </button>
        </div>
      </div>
    </header>
  );
}
