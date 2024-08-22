import pytest
import subprocess
from main import generate_test_reports, set_vars

# Test case 1: Test when args_test is present and subprocess runs successfully
def test_generate_test_reports_success(monkeypatch):
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

    # Mocking subprocess.run and logging.info using monkeypatch
    def mock_run(command, shell, check, timeout):
        if 'npm test' in command:
            return subprocess.CompletedProcess(args=command, returncode=0)
        elif 'pycobertura' in command:
            return subprocess.CompletedProcess(args=command, returncode  = 0)
        elif 'find' in command:
            return subprocess.CompletedProcess(args=command, returncode=0, stdout='/fake/workspace/coverage-report-dir')

    def mock_info(message):
        pass  # Do nothing for logging.info

    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr('main.logging.info', mock_info)
    monkeypatch.setattr('main.workspace', '/fake/workspace')

    generate_test_reports(build_var_map)

    # Assertions to check if subprocess.run was called with expected commands
    mock_run.assert_any_call('export LOG_LEVEL=ERROR && npm test', shell=True, check=True, timeout=3600)
    mock_run.assert_any_call(
        'python -m pycobertura show --format html --output coverage/cobertura-coverage.html coverage/cobertura-coverage.xml',
        shell=True
    )
    mock_run.assert_any_call(
        ['find /fake/workspace -depth 1 -type d -name coverage-report-dir'],
        stdout=-1, timeout=None, check=True, shell=True, text=True
    )

# Test case 5: Test when the HTML report directory is missing or incorrect
def test_generate_test_reports_no_html_report(monkeypatch):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            # The 'html-reports' key is None to simulate the AttributeError
            'html-reports': None
        }
    }

    def mock_run(command, shell, check, timeout):
        return subprocess.CompletedProcess(args=command, returncode=0)

    def mock_error(message):
        raise AttributeError("No HTML report found")

    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr('main.logging.error', mock_error)
    monkeypatch.setattr('main.workspace', '/fake/workspace')

    with pytest.raises(AttributeError, match="No HTML report found"):
        generate_test_reports(build_var_map)

# Test case 2: Test when the subprocess fails
def test_generate_test_reports_subprocess_failure(monkeypatch, caplog):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {}
    }

    def mock_run(command, shell, check, timeout):
        raise subprocess.CalledProcessError(1, 'npm test')

    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr('main.workspace', '/fake/workspace')

    generate_test_reports(build_var_map)

    assert any("Command 'npm test' returned non-zero exit status 1." in record.message for record in caplog.records)

# Test case 3: Test when the subprocess times out
def test_generate_test_reports_timeout(monkeypatch, caplog):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {}
    }

    def mock_run(command, shell, check, timeout):
        raise subprocess.TimeoutExpired(cmd='npm test', timeout=3600)

    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr('main.workspace', '/fake/workspace')

    generate_test_reports(build_var_map)

    assert any("Command 'npm test' timed out after 3600 seconds" in record.message for record in caplog.records)

# Test case 4: Test when a runtime error occur during subprocess execution
def test_generate_test_reports_runtime_error(monkeypatch, caplog):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {}
    }

    def mock_run(command, shell, check, timeout):
        raise RuntimeError("Runtime error occurred")

    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr('main.workspace', '/fake/workspace')

    generate_test_reports(build_var_map)

    assert any("Runtime error occurred" in record.message for record in caplog.records)

# Test case 4: Test for cobertura report generation
def test_generate_test_reports_cobertura(monkeypatch):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            'cobertura': True
        }
    }

    def mock_run(command, shell, check, timeout):
        return subprocess.CompletedProcess(args=command, returncode=0)

    def mock_info(message):
        pass  # Do nothing for logging.info

    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr('main.logging.info', mock_info)
    monkeypatch.setattr('main.workspace', '/fake/workspace')

    generate_test_reports(build_var_map)

    mock_run.assert_any_call(
        'python -m pycobertura show --format html --output coverage/cobertura-coverage.html coverage/cobertura-coverage.xml',
        shell=True
    )
    assert mock_info.call_count > 1  # Check that logging was called for the Cobertura report

# Test case 6: Test when lcov report path is available
def test_generate_test_reports_lcov_path(monkeypatch):
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            'js-lcov-report-path': '/path/to/lcov-report'
        }
    }

    def mock_system(command):
        return 0  # Simulate a successful command

    def mock_info(message):
        pass  # Do nothing for logging.info

    monkeypatch.setattr('main.os.system', mock_system)
    monkeypatch.setattr('main.logging.info', mock_info)
    monkeypatch.setattr('main.workspace', '/fake/workspace')

    generate_test_reports(build_var_map)

    mock_info.assert_any_call('Lcov report path /path/to/lcov-report')
    mock_system.assert_any_call("echo 'lcov-report-path=/path/to/lcov-report' >> $GITHUB_OUTPUT")

# Test case 7: Test when no args_test is provided
def test_generate_test_reports_no_args_test(monkeypatch):
    build_var_map = {
        'build_group': {}
    }

    def mock_info(message):
        pass  # Do nothing for logging.info

    monkeypatch.setattr('main.logging.info', mock_info)

    generate_test_reports(build_var_map)

    mock_info.assert_not_called()

# Test case 1: Test with all values present in config_map
def test_set_vars_all_values_present(monkeypatch):
    config_map = {
        'runtime_version': '14.17.0',
        'args_build': 'npm run build',
        'args_test': 'npm test',
        'test_flag_enabled': 'true'
    }

    def mock_system(command):
        return 0  # Simulate a successful command

    monkeypatch.setattr('main.os.system', mock_system)

    set_vars(config_map)

    mock_system.assert_any_call("echo 'runtime-version=14.17.0' >> $GITHUB_OUTPUT")
    mock_system.assert_any_call("echo 'args-build=npm run build' >> $GITHUB_OUTPUT")
    mock_system.assert_any_call("echo 'args-test=npm test' >> $GITHUB_OUTPUT")
    mock_system.assert_any_call("echo 'test-flag-enabled=true' >> $GITHUB_OUTPUT")

    assert mock_system.call_count == 4

# Test case 2: Test without runtime_version
def test_set_vars_without_runtime_version(monkeypatch):
    config_map = {
        'args_build': 'npm run build',
        'args_test': 'npm test',
        'test_flag_enabled': 'false'
    }

    def mock_system(command):
        return 0  # Simulate a successful command

    monkeypatch.setattr('main.os.system', mock_system)

    set_vars(config_map)

    mock_system.assert_any_call("echo 'args-build=npm run build' >> $GITHUB_OUTPUT")
    mock_system.assert_any_call("echo 'args-test=npm test' >> $GITHUB_OUTPUT")
    mock_system.assert_any_call("echo 'test-flag-enabled=false' >> $GITHUB_OUTPUT")

    assert mock_system.call_count == 3

# Test case 3: Test with empty config_map (should fail)
def test_set_vars_empty_config_map(monkeypatch):
    config_map = {}

    def mock_system(command):
        return 0  # Simulate a successful command

    monkeypatch.setattr('main.os.system', mock_system)

    with pytest.raises(KeyError):
        set_vars(config_map)

    mock_system.assert_not_called()
