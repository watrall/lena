import { useEffect, useState } from 'react';

import type { AppProps } from 'next/app';
import Head from 'next/head';
import { useRouter } from 'next/router';

import CoursePickerModal from '../components/CoursePickerModal';
import Header from '../components/Layout/Header';
import '../styles/globals.css';
import type { ActiveCourse } from '../lib/course';
import { getActiveCourse, subscribeToCourse } from '../lib/course';

export default function LENAApp({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [activeCourse, setActiveCourse] = useState<ActiveCourse | null>(() => getActiveCourse());
  const [courseModalOpen, setCourseModalOpen] = useState(() => !getActiveCourse());

  useEffect(() => {
    const unsubscribe = subscribeToCourse((course) => {
      setActiveCourse(course);
      setCourseModalOpen((current) => (course ? false : true));
    });
    return unsubscribe;
  }, []);

  const allowNoCourse = router.pathname.startsWith('/instructors');
  const forceSelection = !allowNoCourse && !activeCourse;

  const handleCloseModal = () => {
    if (!forceSelection) {
      setCourseModalOpen(false);
    }
  };

  return (
    <>
      <Head>
        <title>LENA Pilot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <div className="flex min-h-screen flex-col bg-slate-50">
        <Header activeCourse={activeCourse} onSwitchCourse={() => setCourseModalOpen(true)} />
        <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 pb-16 pt-8 md:px-8">
          <Component {...pageProps} activeCourse={activeCourse} />
        </main>
      </div>
      <CoursePickerModal
        open={courseModalOpen}
        forceSelection={forceSelection}
        activeCourseId={activeCourse?.id}
        onClose={handleCloseModal}
      />
    </>
  );
}
