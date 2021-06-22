#!/usr/bin/env python3

import time
from unittest.mock import patch
import unittest

import auto_plot

class FakePopen:
    def __init__(self, return_code, sleep_on_poll=0):
        self.pid = 0
        self.return_code = return_code
        self.sleep_on_poll = sleep_on_poll

    def poll(self) -> int:
        code = self.return_code[0]
        if len(self.return_code) > 1:
            del self.return_code[0]
            time.sleep(self.sleep_on_poll)
        return code

class RemoveFinishedProcessesTest(unittest.TestCase):
    def test_no_processes(self) -> None:
        procs = list()
        auto_plot.remove_finished_processes(procs)
        self.assertEqual(len(procs), 0)

    def test_one_process_succeeded(self) -> None:
        procs = [FakePopen([0])]
        auto_plot.remove_finished_processes(procs)
        self.assertEqual(len(procs), 0)

    def test_one_process_failed(self) -> None:
        procs = [FakePopen([1])]
        auto_plot.remove_finished_processes(procs)
        self.assertEqual(len(procs), 0)

    def test_two_processes_finished(self) -> None:
        procs = [FakePopen([0]), FakePopen([1])]
        auto_plot.remove_finished_processes(procs)
        self.assertEqual(len(procs), 0)

    def test_one_process_running(self) -> None:
        procs = [FakePopen([None])]
        auto_plot.remove_finished_processes(procs)
        self.assertEqual(len(procs), 1)

    def test_one_process_running_one_finished(self) -> None:
        procs = [FakePopen([None]), FakePopen([1])]
        auto_plot.remove_finished_processes(procs)
        self.assertEqual(len(procs), 1)


class StaggeredPlotterTest(unittest.TestCase):
    @patch("auto_plot.plot")
    def test_zero_concurrent_plots(self, mock_plot) -> None:
        mock_plot.return_value = FakePopen([0])
        parser = auto_plot.create_parser()
        stagger_args = parser.parse_args([
            "--concurrent_plots=0",
            "--total_plots=1",
            "--stagger_minutes=0",
        ])
        successes, failures = auto_plot.staggered_plotter(
            stagger_args, [], poll_rate_seconds = 0
        )
        self.assertEqual(successes, 0)
        self.assertEqual(failures, 0)

    @patch("auto_plot.plot")
    def test_one_concurrent_plot(self, mock_plot) -> None:
        mock_plot.return_value = FakePopen([None, None, 0])
        parser = auto_plot.create_parser()
        stagger_args = parser.parse_args([
            "--concurrent_plots=1",
            "--total_plots=1",
            "--stagger_minutes=0",
        ])
        successes, failures = auto_plot.staggered_plotter(
            stagger_args, [], poll_rate_seconds = 0
        )
        self.assertEqual(successes, 1)
        self.assertEqual(failures, 0)

    @patch("auto_plot.plot")
    def test_two_plots_one_concurrent(self, mock_plot) -> None:
        mock_plot.return_value = FakePopen([None, None, 0])
        parser = auto_plot.create_parser()
        stagger_args = parser.parse_args([
            "--concurrent_plots=1",
            "--total_plots=2",
            "--stagger_minutes=0",
        ])
        successes, failures = auto_plot.staggered_plotter(
            stagger_args, [], poll_rate_seconds = 0
        )
        self.assertEqual(successes, 2)
        self.assertEqual(failures, 0)

    @patch("auto_plot.plot")
    def test_two_plots_two_concurrent(self, mock_plot) -> None:
        mock_plot.return_value = FakePopen([None, None, 0])
        parser = auto_plot.create_parser()
        stagger_args = parser.parse_args([
            "--concurrent_plots=2",
            "--total_plots=2",
            "--stagger_minutes=0",
        ])
        successes, failures = auto_plot.staggered_plotter(
            stagger_args, [], poll_rate_seconds = 0
        )
        self.assertEqual(successes, 2)
        self.assertEqual(failures, 0)

    @patch("auto_plot.plot")
    def test_ten_plots_two_concurrent(self, mock_plot) -> None:
        mock_plot.return_value = FakePopen([None, None, 0])
        parser = auto_plot.create_parser()
        stagger_args = parser.parse_args([
            "--concurrent_plots=2",
            "--total_plots=10",
            "--stagger_minutes=0",
        ])
        successes, failures = auto_plot.staggered_plotter(
            stagger_args, [], poll_rate_seconds = 0
        )
        self.assertEqual(successes, 10)
        self.assertEqual(failures, 0)

    @patch("auto_plot.plot")
    def test_two_plots_ten_concurrent(self, mock_plot) -> None:
        mock_plot.return_value = FakePopen([None, None, 0])
        parser = auto_plot.create_parser()
        stagger_args = parser.parse_args([
            "--concurrent_plots=10",
            "--total_plots=2",
            "--stagger_minutes=0",
        ])
        successes, failures = auto_plot.staggered_plotter(
            stagger_args, [], poll_rate_seconds = 0
        )
        self.assertEqual(successes, 2)
        self.assertEqual(failures, 0)

    @patch("auto_plot.plot")
    def test_negative_sleep(self, mock_plot) -> None:
        mock_plot.side_effect = [ FakePopen([None]*5 + [0], 0.5) ] * 9
        parser = auto_plot.create_parser()
        stagger_args = parser.parse_args([
            "--concurrent_plots=3",
            "--total_plots=9",
            "--stagger_minutes=-10",
        ])
        successes, failures = auto_plot.staggered_plotter(
            stagger_args, [], poll_rate_seconds = 0
        )
        self.assertEqual(successes, 9)
        self.assertEqual(failures, 0)


if __name__ == "__main__":
    unittest.main()
