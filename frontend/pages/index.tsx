// index.tsx – placeholder landing card until the chat experience is wired up.
import type { NextPage } from 'next';

const HomePage: NextPage = () => (
  <section className="rounded-3xl bg-white px-6 py-10 shadow-sm ring-1 ring-slate-100 md:px-10">
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold text-slate-900 md:text-3xl">
        Welcome to the LENA pilot
      </h1>
      <p className="text-base text-slate-600 md:text-lg">
        This frontend is getting ready for a full chat, FAQ, and insights experience. Once a
        course is connected you&apos;ll be able to ask questions, review sourced answers, and
        escalate tricky topics to instructors.
      </p>
      <p className="rounded-2xl bg-slate-900/5 px-4 py-3 text-sm text-slate-600 md:w-max">
        Tip: the header course pill is just a placeholder for now. We hook it up in the next
        milestone.
      </p>
    </div>
  </section>
);

export default HomePage;
