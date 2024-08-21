import pytest
from main import get_env  # Replace with the actual module name if different

def test_get_env_sandbox(monkeypatch):
    # Mock the environment variable to simulate a sandbox URL
    monkeypatch.setenv('GITHUB_SERVER_URL', 'https://sandbox.example.com/repo')
    
    # Call the function and check if it returns 'sandbox'
    assert get_env() == 'sandbox'

def test_get_env_local(monkeypatch):
    # Mock the environment variable to simulate a localhost URL
    monkeypatch.setenv('GITHUB_SERVER_URL', 'http://localhost:8000/repo')
    
    # Call the function and check if it returns 'local'
    assert get_env() == 'local'

def test_get_env_staging(monkeypatch):
    # Mock the environment variable to simulate a staging URL
    monkeypatch.setenv('GITHUB_SERVER_URL', 'https://staging.example.com/repo')
    
    # Call the function and check if it returns 'staging'
    assert get_env() == 'staging'

def test_get_env_production(monkeypatch):
    # Mock the environment variable to simulate a production URL
    monkeypatch.setenv('GITHUB_SERVER_URL', 'https://production.example.com/repo')
    
    # Call the function and check if it returns 'production' (default case)
    assert get_env() == 'production'

def test_get_env_empty_url(monkeypatch):
    # Mock the environment variable to simulate an empty URL (or not set)
    monkeypatch.setenv('GITHUB_SERVER_URL', '')
    
    # Call the function and check if it returns 'production' (default case)
    assert get_env() == 'production'

def test_get_env_unexpected_url(monkeypatch):
    # Mock the environment variable to simulate an unexpected URL
    monkeypatch.setenv('GITHUB_SERVER_URL', 'https://unknown.example.com/repo')
    
    # Call the function and check if it returns 'production' (default case)
    assert get_env() == 'production'

import pytest
from main import get_env  # Replace with the actual module name if different

@pytest.mark.parametrize("git_url, expected_env", [
    ("https://sandbox.example.com/repo", "sandbox"),
    ("http://localhost:8000/repo", "local"),
    ("https://staging.example.com/repo", "staging"),
    ("https://production.example.com/repo", "production"),
    ("https://unknown.example.com/repo", "production"),  # Default case
])
def test_get_env(monkeypatch, git_url, expected_env):
    # Use monkeypatch to set the GITHUB_SERVER_URL environment variable
    monkeypatch.setenv('GITHUB_SERVER_URL', git_url)
    
    # Call the function and assert the expected environment is returned
    assert get_env() == expected_env


