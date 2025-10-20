// Header.tsx – shared navigation shell and course picker placeholder for every page.
import Link from 'next/link';
import { useRouter } from 'next/router';

const links = [
  { href: '/', label: 'Chat' },
  { href: '/faq', label: 'FAQ' },
  { href: '/insights', label: 'Insights' },
];

export default function Header() {
  const { pathname } = useRouter();

  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-6 px-4 py-4 md:px-8">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            LENA Pilot
          </span>
          <nav className="flex items-center gap-3 text-sm font-medium text-slate-600">
            {links.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-md px-3 py-1 transition ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-100 px-4 py-2 text-sm text-slate-600 shadow-sm">
          <span className="font-medium text-slate-500">Course</span>
          <span className="rounded-full bg-white px-3 py-1 text-slate-700 shadow-inner">
            Select course
          </span>
        </div>
      </div>
    </header>
  );
}
