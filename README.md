# qa-tools 

qa-tools is a set of Python scripts to compare test build report from qa-reports with a full list of expected test to identify any missing tests. 

## Dependencies
* [Requests](https://docs.python-requests.org/en/latest/)
* [tabulate](https://pypi.org/project/tabulate/) 


## Usage

```python
python squad_print_build_results.py \
--squad-url https://qa-reports.foundries.io \
--source-project-slug lmp-ci-testing \
--source-project-build 101

python compare_builds2.py \
--board-full-list imx6ullevk-full \
--build-number imx6ullevk-101
```

Run squad_print_build_results.py with parameters to select build to generate build test run list. 
Then run compare_builds2.py with board + build number to compare with full list and print out missing tests. 
