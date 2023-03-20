#!/usr/bin/env python
import subprocess
import os
import sys
import time
import shutil
import argparse
import contextlib
import typing as t

PYTHON_PATH = sys.executable


def print_error(*s: str):
    print("\033[91m {}\033[00m".format(' '.join(s)))


def print_succes(*s: str):
    print("\033[92m {}\033[00m".format(' '.join(s)))


def print_info(*s: str):
    print("\033[93m {}\033[00m".format(' '.join(s)))


@contextlib.contextmanager
def create_distribution(dist_path: t.Optional[str]):
    if dist_path:
        cwd = os.getcwd()
        try:
            print_info(f'\nCreating addon distribution in \"{dist_path}\" ...')
            os.makedirs(dist_path, exist_ok=True)
            shutil.copytree(os.path.dirname(os.path.abspath(__file__)), dist_path, dirs_exist_ok=True)
            print(os.path.dirname(os.path.abspath(__file__)), dist_path)
            os.chdir(dist_path)

            yield None

            # remove junk
            for root, dirs, _ in os.walk(dist_path):
                for subdir in dirs:
                    if subdir.startswith('.') or subdir == '__pycache__':
                        shutil.rmtree(os.path.join(root, subdir), ignore_errors=True)

        finally:
            os.chdir(cwd)
            print_succes("\nSuccessfully created addon distribution.")
    else:
        yield None


def build_project(no_req: bool, dist_path: t.Optional[str]):
    start_time = time.time()

    print_info('\nBuilding UModelTools...')
    print(f'Python third-party modules: {"OFF" if no_req else "ON"}')

    try:
        from pip import main as pipmain
    except ImportError:
        try:
            from pip._internal import main as pipmain
        except ImportError:
            print_error("\npip is required to build this project.")
            sys.exit(1)

    with create_distribution(dist_path):
        # install required Python modules
        if not no_req:
            print_info('\nInstalling third-party Python modules...')

            def install_requirements(f):
                for line in f.readlines():
                    status = subprocess.call([PYTHON_PATH, '-m', 'pip', 'install', line, '-t',
                                             'umodel_tools/third_party', '--upgrade'])
                    if status:
                        print('\nError: failed installing module \"{}\". See pip error above.'.format(line))
                        sys.exit(1)

            with open('requirements.txt') as f:
                install_requirements(f)

        else:
            print_info("Warning: Third-party Python modules will not be installed. (--noreq option)")

    print_succes("UmodelTools building finished successfully.",
                 "Total build time: ", time.strftime("%M minutes %S seconds\a", time.gmtime(time.time() - start_time)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build UModelTools."
                                                 "\n"
                                                 "\nRequired dependencies are:"
                                                 "\n  pip (https://pip.pypa.io/en/stable/installation/)",
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--dist', type=str, help='create a distribution of WBS in specified directory')
    parser.add_argument('--noreq', action='store_true', help='do not pull python modules from PyPi')
    args = parser.parse_args()

    build_project(args.noreq, args.dist)
