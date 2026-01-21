'use client';

import type { NextPage } from 'next';

import InstructorsPage from '../components/instructors/InstructorsPage';
import type { ActiveCourse } from '../lib/course';

type Props = {
  activeCourse: ActiveCourse | null;
};

const Page: NextPage<Props> = ({ activeCourse }) => <InstructorsPage activeCourse={activeCourse} />;

export default Page;

