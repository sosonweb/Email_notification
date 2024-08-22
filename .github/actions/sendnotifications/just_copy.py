import pytest
import subprocess
from unittest import mock
import logging
from main import generate_test_reports
from main import set_vars

# Test case 1: Test when args_test is present and subprocess runs successfully
@mock.patch('main.subprocess.run', return_value=mock.Mock())
@mock.patch('main.logging.info')
def test_generate_test_reports_success(mock_logging_info, mock_subprocess_run):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            'js-lcov-report-path': '/path/to/lcov-report',
            'cobertura': True,
            'html-reports': {
                'pipeline-coverage-report': {
                    'report-dir': 'coverage-report-dir'
                }
            }
        }
    }

    with mock.patch('main.workspace', '/fake/workspace'):
        generate_test_reports(build_var_map)
    
    mock_logging_info.assert_any_call('Generating test report using npm test')

    # Check if subprocess.run was called with the npm test command
    mock_subprocess_run.assert_any_call('export LOG_LEVEL=ERROR && npm test', shell=True, check=True, timeout=3600)

    # Check if subprocess.run was called with the Cobertura command
    mock_subprocess_run.assert_any_call(
        'python -m pycobertura show --format html --output coverage/cobertura-coverage.html coverage/cobertura-coverage.xml',
        shell=True
    )

    # Check if subprocess.run was called with the find command
    mock_subprocess_run.assert_any_call(
        'find /fake/workspace -depth 1 -type d -name coverage-report-dir',
        stdout=-1, timeout=None, check=True, shell=True, text=True
    )


# Test case 5: Test when the HTML report directory is missing or incorrect
@mock.patch('main.subprocess.run', return_value=mock.Mock())  # Prevent the npm test from failing
@mock.patch('main.logging.error')
def test_generate_test_reports_no_html_report(mock_logging_error, mock_subprocess_run):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            # 'html-reports' key is None to simulate the AttributeError
            'html-reports': None  
        }
    }

    with mock.patch('main.workspace', '/fake/workspace'):
        generate_test_reports(build_var_map)

    # Validate that the "No HTML report found" error message is logged
    mock_logging_error.assert_any_call(mock.ANY)
    
    # Check the exact message
    error_message = str(mock_logging_error.call_args_list[0][0][0])
    assert "No HTML report found:" in error_message
    assert "'NoneType' object has no attribute 'get'" in error_message

# Test case 2: Test when subprocess.run raises a CalledProcessError
@mock.patch('main.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'npm test'))
@mock.patch('main.logging.error')
def test_generate_test_reports_subprocess_failure(mock_logging_error, mock_subprocess_run):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {}
    }

    with mock.patch('main.workspace', '/fake/workspace'):
        generate_test_reports(build_var_map)

    mock_logging_error.assert_any_call(
        "Test report generation failed: Command 'npm test' returned non-zero exit status 1."
    )

# Test case 3: Test when subprocess.run raises a TimeoutExpired
@mock.patch('main.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='npm test', timeout=3600))
@mock.patch('main.logging.error')
def test_generate_test_reports_timeout(mock_logging_error, mock_subprocess_run):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            # 'html-reports' key is None to simulate the AttributeError
            'html-reports': None
        }
    }

    with mock.patch('main.workspace', '/fake/workspace'):
        generate_test_reports(build_var_map)

    # Extract all log messages
    logged_messages = [call[0][0] for call in mock_logging_error.call_args_list]

    # Ensure the timeout error was logged
    assert "Test report generation timed out: Command 'npm test' timed out after 3600 seconds" in logged_messages, (
        f"Expected timeout error not found in logged messages: {logged_messages}"
    )


# Test case 4: Test for cobertura report generation
@mock.patch('main.subprocess.run', return_value=mock.Mock())
@mock.patch('main.logging.info')
def test_generate_test_reports_cobertura(mock_logging_info, mock_subprocess_run):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            'cobertura': True
        }
    }

    with mock.patch('main.workspace', '/fake/workspace'):
        generate_test_reports(build_var_map)

    mock_subprocess_run.assert_any_call(
        'python -m pycobertura show --format html --output coverage/cobertura-coverage.html coverage/cobertura-coverage.xml',
        shell=True
    )
    assert mock_logging_info.call_count > 1  # Check that logging was called for the Cobertura report


# Test case 6: Test when lcov report path is available
@mock.patch('main.os.system')
@mock.patch('main.logging.info')
def test_generate_test_reports_lcov_path(mock_logging_info, mock_os_system):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            'js-lcov-report-path': '/path/to/lcov-report'
        }
    }

    with mock.patch('main.workspace', '/fake/workspace'):
        generate_test_reports(build_var_map)

    mock_logging_info.assert_any_call('Lcov report path /path/to/lcov-report')
    mock_os_system.assert_any_call("echo 'lcov-report-path=/path/to/lcov-report' >> $GITHUB_OUTPUT")

# Test case 7: Test when no args_test is provided
@mock.patch('main.logging.info')
def test_generate_test_reports_no_args_test(mock_logging_info):
    build_var_map = {
        'build_group': {}
    }

    generate_test_reports(build_var_map)
    
    # Check that nothing is logged for "Generating test report"
    mock_logging_info.assert_not_called()

# Test case 1: Test with all values present in config_map
@mock.patch('main.os.system')
def test_set_vars_all_values_present(mock_os_system):
    config_map = {
        'runtime_version': '14.17.0',
        'args_build': 'npm run build',
        'args_test': 'npm test',
        'test_flag_enabled': 'true'
    }

    set_vars(config_map)

    # Check that all os.system calls were made with the correct parameters
    mock_os_system.assert_any_call("echo 'runtime-version=14.17.0' >> $GITHUB_OUTPUT")
    mock_os_system.assert_any_call("echo 'args-build=npm run build' >> $GITHUB_OUTPUT")
    mock_os_system.assert_any_call("echo 'args-test=npm test' >> $GITHUB_OUTPUT")
    mock_os_system.assert_any_call("echo 'test-flag-enabled=true' >> $GITHUB_OUTPUT")

    # Ensure that os.system was called exactly 4 times
    assert mock_os_system.call_count == 4

# Test case 2: Test without runtime_version
@mock.patch('main.os.system')
def test_set_vars_without_runtime_version(mock_os_system):
    config_map = {
        'args_build': 'npm run build',
        'args_test': 'npm test',
        'test_flag_enabled': 'false'
    }

    set_vars(config_map)

    # Check that os.system calls were made with the correct parameters
    # runtime_version is not included, so it should not be called for it
    mock_os_system.assert_any_call("echo 'args-build=npm run build' >> $GITHUB_OUTPUT")
    mock_os_system.assert_any_call("echo 'args-test=npm test' >> $GITHUB_OUTPUT")
    mock_os_system.assert_any_call("echo 'test-flag-enabled=false' >> $GITHUB_OUTPUT")

    # Ensure that os.system was called exactly 3 times
    assert mock_os_system.call_count == 3

# Test case 3: Test with empty config_map (should fail)
@mock.patch('main.os.system')
def test_set_vars_empty_config_map(mock_os_system):
    config_map = {}

    with pytest.raises(KeyError):
        set_vars(config_map)

    # Ensure that no os.system calls were made
    mock_os_system.assert_not_called()
