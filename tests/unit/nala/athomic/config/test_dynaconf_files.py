from nala.athomic.config.providers.dynaconf_files import (
    resolve_settings_files,
)


def test_resolve_finds_one_valid_relative(tmp_path, monkeypatch):
    rel_path_str = "config/settings.valid.toml"
    abs_path = tmp_path / rel_path_str
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.touch()
    monkeypatch.chdir(tmp_path)
    input_str = rel_path_str
    result = resolve_settings_files(input_str)
    assert result == [abs_path.resolve()]


def test_resolve_finds_one_valid_absolute(tmp_path):
    abs_path = tmp_path / "absolute" / "settings.valid.yaml"
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.touch()
    input_str = str(abs_path)
    result = resolve_settings_files(input_str)
    assert result == [abs_path]


def test_resolve_skips_non_existent(tmp_path, monkeypatch):
    rel_path_str = "config/i_do_not_exist.json"
    monkeypatch.chdir(tmp_path)
    input_str = rel_path_str
    result = resolve_settings_files(input_str)
    assert result == []


def test_resolve_skips_directory(tmp_path, monkeypatch):
    rel_path_str = "i_am_a_directory"
    abs_path = tmp_path / rel_path_str
    abs_path.mkdir()
    monkeypatch.chdir(tmp_path)
    input_str = rel_path_str
    result = resolve_settings_files(input_str)
    assert result == []


def test_resolve_handles_mixed_list(tmp_path, monkeypatch):
    valid_rel_str = "conf/actual.toml"
    valid_abs_path = tmp_path / "data/absolute.yaml"
    invalid_rel_str = "conf/non_existent.json"
    directory_str = "i_am_a_dir"
    (tmp_path / valid_rel_str).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / valid_rel_str).touch()
    valid_abs_path.parent.mkdir(parents=True, exist_ok=True)
    valid_abs_path.touch()
    (tmp_path / directory_str).mkdir()
    monkeypatch.chdir(tmp_path)
    input_str = (
        f" {valid_rel_str} , {invalid_rel_str}, {str(valid_abs_path)}, {directory_str} "
    )
    expected_rel_resolved = (tmp_path / valid_rel_str).resolve()
    result = resolve_settings_files(input_str)
    assert len(result) == 2
    assert expected_rel_resolved in result
    assert valid_abs_path.resolve() in result


def test_resolve_settings_files_empty_input():
    assert resolve_settings_files("") == []
    assert resolve_settings_files(" , , ") == []
