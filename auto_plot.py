#!/usr/bin/env python3

import argparse
from subprocess import Popen
import time


def plot(chia_args) -> Popen:
    args = ["chia", "plots", "create"] + chia_args
    return Popen(args)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--total_plots", type=int,
            help="Total number of plots to generate")
    parser.add_argument("--concurrent_plots", type=int,
            help="Max plots to generate concurrently")
    parser.add_argument("--stagger_minutes", type=float,
            help="Number of minutes to wait before starting a new "
            "plotting job after a previous job ends")
    return parser


def remove_finished_processes(plot_processes) -> None:
    still_running = list()
    successes = 0
    failures = 0
    for process in plot_processes:
        return_code = process.poll()
        if return_code is None:
            still_running.append(process)
        else:
            # A plotting process finished. Determine success or failure.
            if return_code == 0:
                print("Plotting succeeded on pid {}".format(return_code))
                successes += 1
            else:
                print("Plotting failed on pid {} with return code {}".format(
                    process.pid, return_code
                ))
                failures += 1
    plot_processes[:] = still_running
    return successes, failures


def staggered_plotter(
        stagger_args,
        chia_args,
        poll_rate_seconds:float = 60.0,
        ):
    if stagger_args.concurrent_plots < 1:
        print("concurrent_plots must be greater than 0, was {}".format(
            stagger_args.concurrent_plots
        ))
        return 0, 0
    total_successes = 0
    total_failures = 0
    plot_processes = list()
    for current_plot in range(stagger_args.total_plots):
        plot_processes.append(plot(chia_args))
        print("Starting plot {} of {} with pid {}".format(
            current_plot + 1,
            stagger_args.total_plots,
            plot_processes[-1].pid,
        ))
        minutes_already_slept = 0.0
        while len(plot_processes) >= stagger_args.concurrent_plots:
            successes, failures = remove_finished_processes(plot_processes)
            total_successes += successes
            total_failures += failures
            time.sleep(poll_rate_seconds)
            minutes_already_slept += poll_rate_seconds / 60.0
        minutes = (stagger_args.stagger_minutes - minutes_already_slept)
        time.sleep(minutes * 60)
    while len(plot_processes) > 0:
        successes, failures = remove_finished_processes(plot_processes)
        total_successes += successes
        total_failures += failures
        time.sleep(poll_rate_seconds)
    return total_successes, total_failures


if __name__ == "__main__":
    parser = create_parser()
    stagger_args, chia_args = parser.parse_known_args()
    successes, failures = staggered_plotter(stagger_args, chia_args)
    print("Successfully plotted {} new plots. Failed {}.".format(
        successes, failures
    ))
