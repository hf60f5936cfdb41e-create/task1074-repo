#!/usr/bin/env python3
"""
Unit and integration tests for src/main.py process subcommand.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from src.main import main, process_file, validate_item


class TestValidateItem:
    """Unit tests for validate_item function."""

    def test_valid_item(self):
        """Test that a valid item passes validation."""
        item = {"id": 1, "name": "test", "value": 10.5}
        # Should not raise
        validate_item(item)

    def test_valid_item_int_value(self):
        """Test that integer values are accepted."""
        item = {"id": 42, "name": "integer value", "value": 100}
        validate_item(item)

    def test_missing_id(self):
        """Test that missing 'id' field raises ValueError."""
        item = {"name": "test", "value": 10.5}
        with pytest.raises(ValueError, match="missing field 'id'"):
            validate_item(item)

    def test_missing_name(self):
        """Test that missing 'name' field raises ValueError."""
        item = {"id": 1, "value": 10.5}
        with pytest.raises(ValueError, match="missing field 'name'"):
            validate_item(item)

    def test_missing_value(self):
        """Test that missing 'value' field raises ValueError."""
        item = {"id": 1, "name": "test"}
        with pytest.raises(ValueError, match="missing field 'value'"):
            validate_item(item)

    def test_id_not_int(self):
        """Test that non-int 'id' raises ValueError."""
        item = {"id": "1", "name": "test", "value": 10.5}
        with pytest.raises(ValueError, match="field 'id' must be int"):
            validate_item(item)

    def test_id_float_not_allowed(self):
        """Test that float 'id' raises ValueError."""
        item = {"id": 1.5, "name": "test", "value": 10.5}
        with pytest.raises(ValueError, match="field 'id' must be int"):
            validate_item(item)

    def test_name_not_string(self):
        """Test that non-string 'name' raises ValueError."""
        item = {"id": 1, "name": 123, "value": 10.5}
        with pytest.raises(ValueError, match="field 'name' must be a non-empty string"):
            validate_item(item)

    def test_name_empty_string(self):
        """Test that empty 'name' raises ValueError."""
        item = {"id": 1, "name": "", "value": 10.5}
        with pytest.raises(ValueError, match="field 'name' must be a non-empty string"):
            validate_item(item)

    def test_name_whitespace_only(self):
        """Test that whitespace-only 'name' raises ValueError."""
        item = {"id": 1, "name": "   ", "value": 10.5}
        with pytest.raises(ValueError, match="field 'name' must be a non-empty string"):
            validate_item(item)

    def test_value_not_number(self):
        """Test that non-numeric 'value' raises ValueError."""
        item = {"id": 1, "name": "test", "value": "10.5"}
        with pytest.raises(ValueError, match="field 'value' must be a number"):
            validate_item(item)

    def test_item_not_dict(self):
        """Test that non-dict item raises ValueError."""
        with pytest.raises(ValueError, match="item must be an object"):
            validate_item("not a dict")

    def test_item_is_list(self):
        """Test that list item raises ValueError."""
        with pytest.raises(ValueError, match="item must be an object"):
            validate_item([1, 2, 3])


class TestProcessFile:
    """Unit tests for process_file function."""

    def test_valid_single_item(self):
        """Test processing a single valid item."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump([{"id": 1, "name": "test", "value": 10.0}], f)
            f.flush()
            result = process_file(f.name)

        assert result == {"count": 1, "total_value": 10.0, "avg_value": 10.0}
        Path(f.name).unlink()

    def test_valid_multiple_items(self):
        """Test processing multiple valid items."""
        data = [
            {"id": 1, "name": "first", "value": 10.0},
            {"id": 2, "name": "second", "value": 20.0},
            {"id": 3, "name": "third", "value": 30.0},
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            result = process_file(f.name)

        assert result == {"count": 3, "total_value": 60.0, "avg_value": 20.0}
        Path(f.name).unlink()

    def test_empty_list(self):
        """Test processing an empty list."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump([], f)
            f.flush()
            result = process_file(f.name)

        assert result == {"count": 0, "total_value": 0.0, "avg_value": 0.0}
        Path(f.name).unlink()

    def test_not_a_list(self):
        """Test that non-list JSON raises ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({"id": 1, "name": "test", "value": 10.0}, f)
            f.flush()
            with pytest.raises(ValueError, match="input JSON must be a list"):
                process_file(f.name)
        Path(f.name).unlink()

    def test_invalid_item_in_list(self):
        """Test that invalid item in list raises ValueError."""
        data = [
            {"id": 1, "name": "valid", "value": 10.0},
            {"id": 2, "name": "missing value"},  # missing 'value'
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            with pytest.raises(ValueError, match="missing field 'value'"):
                process_file(f.name)
        Path(f.name).unlink()

    def test_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            process_file("/nonexistent/path/file.json")

    def test_invalid_json(self):
        """Test that invalid JSON raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not valid json {")
            f.flush()
            with pytest.raises(json.JSONDecodeError):
                process_file(f.name)
        Path(f.name).unlink()


class TestMainFunction:
    """Unit tests for main() CLI function."""

    def test_main_valid_input(self, capsys):
        """Test main() with valid input returns 0 and prints summary."""
        data = [
            {"id": 1, "name": "a", "value": 5.0},
            {"id": 2, "name": "b", "value": 15.0},
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            exit_code = main(["process", "--input", f.name])

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert exit_code == 0
        assert output == {"count": 2, "total_value": 20.0, "avg_value": 10.0}
        Path(f.name).unlink()

    def test_main_invalid_input_returns_1(self, capsys):
        """Test main() with invalid input returns 1."""
        data = [{"id": "not int", "name": "test", "value": 10.0}]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            exit_code = main(["process", "--input", f.name])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "Error:" in captured.err
        Path(f.name).unlink()

    def test_main_missing_file_returns_1(self, capsys):
        """Test main() with missing file returns 1."""
        exit_code = main(["process", "--input", "/nonexistent/file.json"])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "Error:" in captured.err

    def test_main_short_option(self, capsys):
        """Test main() with short -i option."""
        data = [{"id": 1, "name": "test", "value": 100.0}]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            exit_code = main(["process", "-i", f.name])

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert exit_code == 0
        assert output == {"count": 1, "total_value": 100.0, "avg_value": 100.0}
        Path(f.name).unlink()


class TestCLIIntegration:
    """Integration tests that call the CLI as a subprocess."""

    def test_cli_valid_input(self):
        """Integration test: CLI processes valid input correctly."""
        data = [
            {"id": 1, "name": "item1", "value": 25.0},
            {"id": 2, "name": "item2", "value": 75.0},
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            result = subprocess.run(
                [sys.executable, "-m", "src.main", "process", "--input", f.name],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output == {"count": 2, "total_value": 100.0, "avg_value": 50.0}
        Path(f.name).unlink()

    def test_cli_invalid_input_exits_1(self):
        """Integration test: CLI exits with code 1 on invalid input."""
        data = [{"id": 1, "name": "test"}]  # missing 'value'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            result = subprocess.run(
                [sys.executable, "-m", "src.main", "process", "--input", f.name],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

        assert result.returncode == 1
        assert "Error:" in result.stderr
        Path(f.name).unlink()

    def test_cli_missing_input_argument(self):
        """Integration test: CLI errors when --input is missing."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "process"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode != 0

    def test_cli_empty_list(self):
        """Integration test: CLI handles empty list correctly."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump([], f)
            f.flush()
            result = subprocess.run(
                [sys.executable, "-m", "src.main", "process", "--input", f.name],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output == {"count": 0, "total_value": 0.0, "avg_value": 0.0}
        Path(f.name).unlink()
