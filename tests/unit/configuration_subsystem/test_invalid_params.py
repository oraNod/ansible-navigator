"""Tests using invalid parameters."""

import tempfile

from typing import Any

import pytest

from ansible_navigator.configuration_subsystem import NavigatorConfiguration
from ansible_navigator.configuration_subsystem import SettingsEntry
from ansible_navigator.utils.definitions import LogMessage
from ansible_navigator.utils.functions import ExitMessage

from .conftest import GenerateConfigCallable
from .utils import id_for_name


def which(*_args: Any, **_kwargs: dict[str, Any]) -> str:
    """Return the path to the container engine.

    :param _args: args
    :param _kwargs: kwargs
    :returns: path to container engine
    """
    return "/path/to/container_engine"


def test_generate_argparse_error(generate_config: GenerateConfigCallable) -> None:
    """Ensure exit_messages generated by argparse are caught.

    :param generate_config: Fixture to generate a config
    """
    params = "Sentinel"
    response = generate_config(params=params.split())
    assert len(response.exit_messages) == 3
    exit_msg = "invalid choice: 'Sentinel'"
    assert exit_msg in response.exit_messages[2].message


def test_inventory_no_inventory(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure exit_messages generated for an inventory without an inventory specified.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """
    monkeypatch.setattr("shutil.which", which)
    response = generate_config(params=["inventory"])
    exit_msg = "An inventory is required when using the inventory subcommand"
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


def test_ee_false_no_ansible(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure an error is created if EE is false and ansible not present.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """

    def check_for_ansible(
        *_args: Any, **_kwargs: dict[str, Any]
    ) -> tuple[list[LogMessage], list[ExitMessage]]:
        """Return the path to the container engine.

        :param _args: args
        :param _kwargs: kwargs
        :returns: no ansible
        """
        return ([], [ExitMessage(message="no_ansible")])

    monkeypatch.setattr(
        "ansible_navigator.configuration_subsystem.navigator_post_processor.check_for_ansible",
        check_for_ansible,
    )
    response = generate_config(params=["--ee", "false"])
    assert "no_ansible" in [exit_msg.message for exit_msg in response.exit_messages]


def test_no_container_engine(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure an error is created if EE is false and ansible not present.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """

    def local_which(*_args: Any, **_kwargs: dict[str, Any]) -> None:
        """Return the path to the container engine.

        :param _args: args
        :param _kwargs: kwargs
        :returns: no container engine
        """
        return None

    monkeypatch.setattr("shutil.which", local_which)
    response = generate_config()
    expected = "No container engine could be found"
    assert any(
        expected in exit_msg.message for exit_msg in response.exit_messages
    ), response.exit_messages


def test_fail_log_file_dir(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure an error is created if log file cannot be created.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """

    def makedirs(*args: Any, **kwargs: dict[str, Any]) -> None:
        """Raise OSError.

        :param args: args
        :param kwargs: kwargs
        :raises OSError: Indicate the creation of directories failed
        """
        raise OSError

    monkeypatch.setattr("os.makedirs", makedirs)
    monkeypatch.setattr("shutil.which", which)

    response = generate_config()
    exit_msg = "Failed to create log file"
    assert exit_msg in " ".join([exit_msg.message for exit_msg in response.exit_messages])


def test_doc_no_plugin_name(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure an error is created doc is used without plugin_name.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """
    monkeypatch.setattr("shutil.which", which)
    response = generate_config(params=["doc"])
    exit_msg = "A plugin name or other parameter is required when using the doc subcommand"
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


def test_replay_no_artifact(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure an error is created replay is used without playbook artifact.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """
    monkeypatch.setattr("shutil.which", which)
    response = generate_config(params=["replay"])
    exit_msg = "An playbook artifact file is required when using the replay subcommand"
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


def test_replay_missing_artifact(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure an error is created load is used with a missing playbook artifact.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """
    monkeypatch.setattr("shutil.which", which)
    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file_name = temp_file.name
    response = generate_config(params=["replay", temp_file_name])
    exit_msg = "The specified playbook artifact could not be found:"
    assert exit_msg in " ".join([exit_msg.message for exit_msg in response.exit_messages])


def test_badly_formatted_env_var(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure exit_messages generated for badly formatted ``--senv``.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """
    monkeypatch.setattr("shutil.which", which)
    params = "run site.yml --senv TK1:TV1"
    response = generate_config(params=params.split())
    exit_msg = "The following set-environment-variable entry could not be parsed: TK1:TV1"
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


def test_not_a_bool(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
) -> None:
    """Ensure exit_messages generated for wrong type of value.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    """
    monkeypatch.setattr("shutil.which", which)
    response = generate_config(settings_file_name="ansible-navigator_not_bool.yml")
    exit_msg = "In 'ansible-navigator.execution-environment.enabled': 5 is not of type 'boolean'."
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


choices = [entry for entry in NavigatorConfiguration.entries if entry.choices]


@pytest.mark.parametrize("entry", choices, ids=id_for_name)
def test_poor_choices(
    monkeypatch: pytest.MonkeyPatch,
    generate_config: GenerateConfigCallable,
    entry: SettingsEntry,
) -> None:
    """Ensure exit_messages generated for poor choices.

    :param monkeypatch: Fixture for patching
    :param generate_config: Fixture to generate a config
    :param entry: SettingsEntry
    """
    monkeypatch.setattr("shutil.which", which)

    def test(subcommand: Any, param: Any, look_for: str) -> None:
        if subcommand is None:
            response = generate_config(params=[param, "Sentinel"])
        else:
            response = generate_config(params=[subcommand, param, "Sentinel"])
        assert any(
            look_for in exit_msg.message for exit_msg in response.exit_messages
        ), response.exit_messages

    subcommand = entry.subcommands[0] if isinstance(entry.subcommands, list) else None

    if entry.cli_parameters and entry.cli_parameters.action == "store_true":
        pass
    elif entry.cli_parameters:
        look_for = "must be one"
        # ansible-navigator choice error
        test(subcommand, entry.cli_parameters.short, look_for)
        test(
            subcommand,
            entry.cli_parameters.long_override or f"--{entry.name_dashed}",
            look_for,
        )
    else:
        # argparse choice error
        test(subcommand, "", "choose from")
