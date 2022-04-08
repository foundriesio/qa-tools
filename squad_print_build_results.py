#!/usr/bin/env python3
import argparse
import requests
from tabulate import tabulate

import logging


def get_objects(endpoint_url, expect_one=False, parameters={}):
    """
    gets list of objects from endpoint_url
    optional parameters allow for filtering
    expect_count
    """
    obj_r = requests.get(endpoint_url, parameters)
    if obj_r.status_code == 200:
        objs = obj_r.json()
        if "count" in objs.keys():
            if expect_one and objs["count"] == 1:
                return objs["results"][0]
            else:
                ret_obj = []
                while True:
                    for obj in objs["results"]:
                        ret_obj.append(obj)
                    if objs["next"] is None:
                        break
                    else:
                        obj_r = requests.get(objs["next"])
                        if obj_r.status_code == 200:
                            objs = obj_r.json()
                return ret_obj
        else:
            return objs


def get_testrun_results(squad_url, build, environment):
    testruns_url = squad_url + "/api/testruns/"
    params = {"environment": environment["id"], "build": build["id"]}
    testruns = get_objects(testruns_url, False, params)
    results = {}
    for testrun in testruns["results"]:
        if testrun["tests_file"]:
            _results_resp = requests.get(testrun["tests_file"])
            _results = _results_resp.json()
            results.update(_results)
    return results


def main():
    logger = logging.getLogger()
    logFormatter = logging.Formatter("%(message)s")
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    logger.setLevel(logging.INFO)
    parser = argparse.ArgumentParser(description="Pull qa-reports data")
    parser.add_argument(
        "--source-project-slug",
        dest="source_project_slug",
        required=True,
        help="slug of the base project, from which to pull data",
    )
    parser.add_argument(
        "--source-project-build",
        dest="source_project_build",
        required=True,
        help="Build version of the source project",
    )
    parser.add_argument(
        "--squad-url",
        dest="squad_url",
        required=True,
        help="URL of SQUAD instance in form https://example.com",
    )
    parser.add_argument(
        "--save-file",
        dest="save_file",
        default=None,
        help="Path to the file to save the results to",
    )

    args = parser.parse_args()
    params = {"slug": args.source_project_slug}
    base_url = args.squad_url + "/api/projects/"
    builds_url = args.squad_url + "/api/builds/"
    envs_url = args.squad_url + "/api/environments/"

    project = get_objects(base_url, True, params)
    project_envs = get_objects(envs_url, False, {"project": project["id"]})
    build = get_objects(
        builds_url,
        True,
        {"project": project["id"], "version": args.source_project_build},
    )

    if args.save_file:
        fileHandler = logging.FileHandler(f"{args.save_file}.log")
        fileHandler.setFormatter(logFormatter)
        logger.addHandler(fileHandler)
    for env in project_envs:
        source_results = get_testrun_results(args.squad_url, build, env)
        logger.info("Processing: " + env["slug"])
        try:
            with open(env["slug"] + "-full", "r") as ref_file:
                ref_list = set(map(str.strip, ref_file))

                build_results = []
                failed_tests = []
                skipped_tests = []
                missing_tests = set()
                for name, result in source_results.items():
                    build_results.append(name)
                    if not result or result["result"] == "fail":
                        failed_tests.append([name])
                    if not result or result["result"] == "skip":
                        skipped_tests.append([name])
                missing_tests = ref_list.symmetric_difference(set(build_results))

                if failed_tests or missing_tests or skipped_tests:
                    logger.info("Issues with: " + env["slug"])
                if skipped_tests:
                    logger.info("Skipped tests:")
                    logger.info(tabulate(sorted(skipped_tests)))
                if failed_tests:
                    logger.info("Failed tests:")
                    logger.info(tabulate(sorted(failed_tests)))
                if missing_tests:
                    logger.info("Missing tests:")
                    logger.info(tabulate(map(lambda x: [x], sorted(missing_tests))))
        except FileNotFoundError:
            logger.warning("No reference for: " + env["slug"])


if __name__ == "__main__":
    main()
