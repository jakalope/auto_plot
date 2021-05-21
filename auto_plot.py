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
    for index, process in enumerate(plot_processes):
        return_code = process.poll()
        if return_code is not None:
            # A plotting process finished.
            # Determine success or failure.
            if return_code == 0:
                print("Plotting succeeded on pid {}".format(return_code))
            else:
                print("Plotting failed on pid {} with return code {}".format(
                    return_code, process.pid
                ))
            # Remove it from the list.
            del plot_processes[index]


def staggered_plotter(args, chia_args) -> None:
    if args.concurrent_plots < 1:
        print("concurrent_plots must be greater than 0")
        return
    plot_processes = list()
    for current_plot in range(args.total_plots):
        plot_processes.append(plot(chia_args))
        print("Starting plot {} of {} with pid {}".format(
            current_plot + 1,
            args.total_plots,
            plot_processes[-1].pid,
        ))
        minutes_already_slept = 0
        while len(plot_processes) >= args.concurrent_plots:
            remove_finished_processes(plot_processes)
            time.sleep(60)  # Wait one minute between polling.
            minutes_already_slept += 1
        time.sleep((args.stagger_minutes - minutes_already_slept) * 60)


if __name__ == "__main__":
    parser = create_parser()
    args, chia_args = parser.parse_known_args()
    staggered_plotter(args, chia_args)
