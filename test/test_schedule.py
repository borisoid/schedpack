import unittest

import arrow

from schedpack import ManualSchedule
from .utils import (
    NeverStartingPeriodicActivity,
    SchoolClass,
    c1,
    c2,
    c3,
    cron,
    even_week,
    odd_week,
    impossible_condition,
)


class TestFilledScheduleWithExtraConditions(unittest.TestCase):
    def setUp(self):
        self.schedule = ManualSchedule([
            SchoolClass('mon,thu c2', cron('mon,thu', c2)),  # mixed

            SchoolClass('mon c1 ew', cron('mon', c1), extra_conditions=[even_week]),
            SchoolClass('mon c3', cron('mon', c3)),

            SchoolClass('tue c1', cron('tue', c1)),
            SchoolClass('tue c2', cron('tue', c2)),
            SchoolClass('tue c3', cron('tue', c3)),

            SchoolClass('wed c1 ow', cron('wed', c1), extra_conditions=[odd_week]),
            SchoolClass('wed c1 ew', cron('wed', c1), extra_conditions=[even_week]),
            SchoolClass('wed c2', cron('wed', c2)),
            SchoolClass('wed c3', cron('wed', c3)),

            SchoolClass('thu c1 ow', cron('thu', c1), extra_conditions=[odd_week]),  
            SchoolClass('thu c1 ew', cron('thu', c1), extra_conditions=[even_week]),                  
            SchoolClass('thu c3', cron('thu', c3)),

            SchoolClass('fri c1', cron('fri', c1)),
            SchoolClass('fri c2', cron('fri', c2)),
            SchoolClass('fry c3', cron('fri', c3)),

            SchoolClass('sat c2', cron('sat', c2)),
            SchoolClass('sat c3', cron('sat', c3)),

            SchoolClass('sun c11', cron('sun', c1)),  # simultaneous
            SchoolClass('sun c12', cron('sun', c1)),
            SchoolClass('sun c2', cron('sun', c2)),
        ])

    # jul 2021 calendar
    # [[ 0,  0,  0,  1,  2,  3,  4],
    #  [ 5,  6,  7,  8,  9, 10, 11],
    #  [12, 13, 14, 15, 16, 17, 18],
    #  [19, 20, 21, 22, 23, 24, 25],
    #  [26, 27, 28, 29, 30, 31,  0]]

    def test_schedule_get_next__when_no_current_and_extra_conditions(self):
        moment = arrow.get('2021-07-01T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'thu c1 ow')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-01T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-01T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_next__when_start_equals_moment(self):
        moment = arrow.get('2021-07-02T08:00:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'fri c2')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-02T09:50:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-02T11:25:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_next__when_no_current_and_many_activities(self):
        moment = arrow.get('2021-07-04T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(len(activities), 2)
        self.assertEqual(activities[0].payload, 'sun c11')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-04T09:35:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(activities[1].payload, 'sun c12')
        self.assertEqual(
            activities[1].start,
            arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[1].end,
            arrow.get('2021-07-04T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_next__when_start_equals_moment_and_many_activities(self):
        moment = arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'sun c2')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-04T09:50:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-04T11:25:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_next__when_moment_equals_end(self):
        moment = arrow.get('2021-07-02T09:35:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'fri c2')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-02T09:50:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-02T11:25:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current__when_no_current(self):
        moment = arrow.get('2021-07-01T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current(moment)

        self.assertEqual(len(activities), 0)

    def test_schedule_get_current__when_start_equals_moment_and_extra_conditions(self):
        moment = arrow.get('2021-07-01T08:00:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'thu c1 ow')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-01T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-01T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current__when_moment_equals_end(self):
        moment = arrow.get('2021-07-02T09:35:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current(moment)

        self.assertEqual(len(activities), 0)

    def test_schedule_get_current__when_there_is_current_and_many_activities(self):
        moment = arrow.get('2021-07-04T08:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current(moment)

        self.assertEqual(len(activities), 2)
        self.assertEqual(activities[0].payload, 'sun c11')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-04T09:35:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(activities[1].payload, 'sun c12')
        self.assertEqual(
            activities[1].start,
            arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[1].end,
            arrow.get('2021-07-04T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current_or_next__when_no_current_and_extra_conditions(self):
        moment = arrow.get('2021-07-01T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current_or_next(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'thu c1 ow')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-01T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-01T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current_or_next__when_there_is_current_and_extra_conditions(self):
        moment = arrow.get('2021-07-01T08:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current_or_next(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'thu c1 ow')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-01T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-01T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current_or_next__when_no_current_and_return_is_current(self):
        moment = arrow.get('2021-07-01T07:30:00', tzinfo='Europe/Moscow').datetime

        activities, is_current = self.schedule.get_current_or_next(
            moment, return_is_current=True
        )

        self.assertFalse(is_current)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'thu c1 ow')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-01T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-01T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current_or_next__when_there_is_current_and_return_is_current(self):
        moment = arrow.get('2021-07-01T08:30:00', tzinfo='Europe/Moscow').datetime

        activities, is_current = self.schedule.get_current_or_next(
            moment, return_is_current=True
        )

        self.assertTrue(is_current)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'thu c1 ow')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-01T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-01T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current_or_next__when_current_and_return_is_current_and_many_activities(self):
        moment = arrow.get('2021-07-04T08:30:00', tzinfo='Europe/Moscow').datetime

        activities, is_current = self.schedule.get_current_or_next(
            moment, return_is_current=True
        )

        self.assertTrue(is_current)
        self.assertEqual(len(activities), 2)
        self.assertEqual(activities[0].payload, 'sun c11')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-04T09:35:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(activities[1].payload, 'sun c12')
        self.assertEqual(
            activities[1].start,
            arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[1].end,
            arrow.get('2021-07-04T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current_or_next__when_no_current_and_return_is_current_and_many_activities(self):
        moment = arrow.get('2021-07-04T07:30:00', tzinfo='Europe/Moscow').datetime

        activities, is_current = self.schedule.get_current_or_next(
            moment, return_is_current=True
        )

        self.assertFalse(is_current)
        self.assertEqual(len(activities), 2)
        self.assertEqual(activities[0].payload, 'sun c11')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-04T09:35:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(activities[1].payload, 'sun c12')
        self.assertEqual(
            activities[1].start,
            arrow.get('2021-07-04T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[1].end,
            arrow.get('2021-07-04T09:35:00', tzinfo='Europe/Moscow').datetime
        )


class TestEmptySchedule(unittest.TestCase):
    def setUp(self):
        self.schedule = ManualSchedule([])

    def test_schedule_get_current__when_empty(self):
        moment = arrow.get('2021-07-04T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current(moment)

        self.assertEqual(activities, ())

    def test_schedule_get_next__when_empty(self):
        moment = arrow.get('2021-07-04T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(activities, ())

    def test_schedule_get_current_or_next__when_empty(self):
        moment = arrow.get('2021-07-04T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current_or_next(moment)

        self.assertEqual(activities, ())

    def test_schedule_get_current_or_next__when_empty_and_return_is_current(self):
        moment = arrow.get('2021-07-04T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current_or_next(moment, return_is_current=True)

        self.assertEqual(activities, ((), None))


class TestScheduleWithImpossibleExtraConditions(unittest.TestCase):
    def setUp(self):
        self.schedule = ManualSchedule([
            SchoolClass('thu c1', cron('thu', c1), extra_conditions=[impossible_condition]),
            SchoolClass('thu c2', cron('thu', c2)),                
            SchoolClass('thu c3', cron('thu', c3)),

            SchoolClass('fri c11', cron('fri', c1), extra_conditions=[impossible_condition]),
            SchoolClass('fri c12', cron('fri', c1)),
            SchoolClass('fri c2', cron('fri', c2)),
            SchoolClass('fry c3', cron('fri', c3)),

            SchoolClass('sat c2', cron('sat', c2)),
            SchoolClass('sat c3', cron('sat', c3)),
        ])

    def test_schedule_get_current__when_current_has_impossible_extra_condition(self):
        moment = arrow.get('2021-07-01T08:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current(moment)

        self.assertEqual(activities, ())

    def test_schedule_get_current__when_many_current_and_one_has_impossible_extra_condition(self):
        moment = arrow.get('2021-07-02T08:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'fri c12')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-02T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-02T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_next__when_has_impossible_extra_condition(self):
        moment = arrow.get('2021-07-01T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'thu c2')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-01T09:50:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-01T11:25:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_next__when_many_next_and_one_has_impossible_extra_condition(self):
        moment = arrow.get('2021-07-02T07:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'fri c12')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-02T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-02T09:35:00', tzinfo='Europe/Moscow').datetime
        )

    def test_schedule_get_current_or_next__when_has_impossible_extra_condition(self):
        moment = arrow.get('2021-07-02T08:30:00', tzinfo='Europe/Moscow').datetime

        activities, is_current = self.schedule.get_current_or_next(
            moment, return_is_current=True
        )

        self.assertTrue(is_current)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].payload, 'fri c12')
        self.assertEqual(
            activities[0].start,
            arrow.get('2021-07-02T08:00:00', tzinfo='Europe/Moscow').datetime
        )
        self.assertEqual(
            activities[0].end,
            arrow.get('2021-07-02T09:35:00', tzinfo='Europe/Moscow').datetime
        )


class TestScheduleWithNeverStartingActivities(unittest.TestCase):
    def setUp(self):
        self.schedule = ManualSchedule([
            NeverStartingPeriodicActivity('never 1'),
            NeverStartingPeriodicActivity('never 2'),
        ])

    def test_schedule_get_current__when_no_activities_ever_start(self):
        moment = arrow.get('2021-07-01T08:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_current(moment)

        self.assertEqual(activities, ())

    def test_schedule_get_next__when_no_activities_ever_start(self):
        moment = arrow.get('2021-07-01T08:30:00', tzinfo='Europe/Moscow').datetime

        activities = self.schedule.get_next(moment)

        self.assertEqual(activities, ())

    def test_schedule_get_current_or_next__when_no_activities_ever_start(self):
        moment = arrow.get('2021-07-01T08:30:00', tzinfo='Europe/Moscow').datetime

        activities, is_current = self.schedule.get_current_or_next(
            moment, return_is_current=True
        )

        self.assertEqual(activities, ())
        self.assertIsNone(is_current)


if __name__ == '__main__':
    unittest.main()
