# tests/unit/nala/athomic/config/test_dynaconf_env.py
import os
import pathlib
from pathlib import Path

from nala.athomic.config.providers.dynaconf_env import (
    get_path_from_env,
)


def test_get_path_from_env_var_exists(mocker):
    env_var = "MY_TEST_PATH"
    expected_path_str = "/absolute/test/path"
    resolved_path_obj = Path(expected_path_str)

    mocker.patch("os.getenv", return_value=expected_path_str)
    mocker.patch.object(pathlib.Path, "resolve", return_value=resolved_path_obj)

    result = get_path_from_env(env_var)

    assert result == resolved_path_obj
    os.getenv.assert_called_once_with(env_var)
    pathlib.Path.resolve.assert_called()


def test_get_path_from_env_var_missing_fallback_exists(mocker, tmp_path):
    env_var = "MY_TEST_PATH"
    fallback_rel = "fallback/dir"
    cwd_path = tmp_path
    fallback_abs_obj = (cwd_path / fallback_rel).resolve()

    mocker.patch("os.getenv", return_value=None)
    mocker.patch("pathlib.Path.cwd", return_value=cwd_path)
    mocker.patch.object(pathlib.Path, "resolve", return_value=fallback_abs_obj)

    result = get_path_from_env(env_var, default_relative_path=fallback_rel)

    assert result == fallback_abs_obj
    os.getenv.assert_called_once_with(env_var)
    pathlib.Path.cwd.assert_called()
    pathlib.Path.resolve.assert_called()
