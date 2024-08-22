import subprocess
import sys
import os
import yaml
import logging

log_level = os.getenv('LOG_LEVEL') if os.getenv('LOG_LEVEL') else '20'
logging.basicConfig(level=int(log_level), format='%(asctime)s :: %(levelname)s :: %(message)s')
workspace = os.getenv('GITHUB_WORKSPACE')
lcov_html_report_path = f"{workspace}/coverage/lcov-report"

def main():
    operation = sys.argv[1]
    config_map = yaml.safe_load(sys.argv[2])
    if operation == 'set-vars':
        set_vars(config_map)
    elif operation == 'generate-report':
        generate_test_reports(config_map)

def generate_test_reports(build_var_map):
    args_test = build_var_map.get('args_test')
    if args_test:
        logging.info(f'Generating test report using {args_test}')
        try:
            subprocess.run(f'export LOG_LEVEL=ERROR && {args_test}', shell=True, check=True, timeout=3600)
        except subprocess.CalledProcessError as e:
            logging.error(f"Test report generation failed: {e}")
        except subprocess.TimeoutExpired as e:
            logging.error(f"Test report generation timed out: {e}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError) as e:
            logging.error(e)

    build_group = build_var_map.get('build_group')
    lcov_report_path = build_group.get('js-lcov-report-path')
    cobertura = build_group.get('cobertura')
    cobertura_report_path = None
    if cobertura is not None:
        subprocess.run(f'python -m pycobertura show --format html --output coverage/cobertura-coverage.html coverage/cobertura-coverage.xml', shell=True)
        cobertura_report_path = f"{workspace}/coverage/cobertura-coverage.html"

    try:
        html_report_dir = build_group.get('html-reports').get('pipeline-coverage-report').get('report-dir')
    except AttributeError as e:
        html_report_dir = None
        logging.error(f"No HTML report found: {e}")

    if lcov_report_path:
        logging.info(f"Lcov report path {lcov_report_path}")
        os.system(f"echo 'lcov-report-path={lcov_report_path}' >> $GITHUB_OUTPUT")
        logging.info(f"Lcov HTML report path {lcov_html_report_path}")
        os.system(f"echo 'lcov-html-report-path={lcov_html_report_path}' >> $GITHUB_OUTPUT")

    if cobertura_report_path:
        logging.info(f"Cobertura report path {cobertura_report_path}")
        os.system(f"echo 'cobertura-report-path={cobertura_report_path}' >> $GITHUB_OUTPUT")

    if html_report_dir:
        try:
            html_report_path = subprocess.check_output(f"find {workspace} -depth 1 -type d -name {html_report_dir}", shell=True, text=True).strip()
            if html_report_path:
                logging.info(f"HTML report path {html_report_path}")
                os.system(f"echo 'html-report-path={html_report_path}' >> $GITHUB_OUTPUT")
        except Exception as e:
            logging.info(f"Test execution did not produce any HTML reports: {e}")

def set_vars(config_map):
    runtime_version = config_map.get('runtime_version')
    if runtime_version:
        os.system(f"echo 'runtime-version={runtime_version}' >> $GITHUB_OUTPUT")
    os.system(f"echo 'args-build={config_map['args_build']}' >> $GITHUB_OUTPUT")
    os.system(f"echo 'args-test={config_map['args_test']}' >> $GITHUB_OUTPUT")
    os.system(f"echo 'test-flag-enabled={config_map['test_flag_enabled']}' >> $GITHUB_OUTPUT")

main()
