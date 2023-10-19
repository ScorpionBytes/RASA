import pytest

from rasa.dialogue_understanding.commands import (
    CancelFlowCommand,
    CorrectSlotsCommand,
    FreeFormAnswerCommand,
    SetSlotCommand,
    StartFlowCommand,
)
from rasa.dialogue_understanding.processor.command_processor import (
    _get_commands_from_tracker,
    contains_command,
    find_updated_flows,
    validate_state_of_commands,
)
from rasa.shared.core.events import SlotSet, UserUttered
from rasa.shared.core.flows.flow import FlowsList
from rasa.shared.core.trackers import DialogueStateTracker


@pytest.mark.parametrize(
    "commands, command_type, expected_result",
    [
        ([SetSlotCommand("slot_name", "slot_value")], SetSlotCommand, True),
        ([StartFlowCommand("flow_name")], StartFlowCommand, True),
        (
            [StartFlowCommand("flow_name"), SetSlotCommand("slot_name", "slot_value")],
            StartFlowCommand,
            True,
        ),
        ([SetSlotCommand("slot_name", "slot_value")], StartFlowCommand, False),
    ],
)
def test_contains_command(commands, command_type, expected_result):
    """Test if commands contains a command of a given type."""
    # When
    result = contains_command(commands, command_type)
    # Then
    assert result == expected_result


def test_get_commands_from_tracker(tracker: DialogueStateTracker):
    """Test if commands are correctly extracted from tracker."""
    # When
    commands = _get_commands_from_tracker(tracker)
    # Then
    assert isinstance(commands[0], StartFlowCommand)
    assert commands[0].command() == "start flow"
    assert commands[0].flow == "foo"


@pytest.mark.parametrize(
    "commands",
    [
        [CancelFlowCommand()],
        [StartFlowCommand("flow_name")],
        [SetSlotCommand("slot_name", "slot_value")],
        [StartFlowCommand("flow_name"), SetSlotCommand("slot_name", "slot_value")],
        [FreeFormAnswerCommand(), SetSlotCommand("slot_name", "slot_value")],
        [
            FreeFormAnswerCommand(),
            FreeFormAnswerCommand(),
            StartFlowCommand("flow_name"),
        ],
        [CorrectSlotsCommand([])],
        [CorrectSlotsCommand([]), StartFlowCommand("flow_name")],
    ],
)
def test_validate_state_of_commands(commands):
    """Test if commands are correctly validated."""
    # Then
    validate_state_of_commands(commands)
    # No exception should be raised


@pytest.mark.parametrize(
    "commands",
    [
        [CancelFlowCommand(), CancelFlowCommand()],
        [StartFlowCommand("flow_name"), FreeFormAnswerCommand()],
        [CorrectSlotsCommand([]), CorrectSlotsCommand([])],
    ],
)
def test_validate_state_of_commands_raises_exception(commands):
    """Test if commands are correctly validated."""
    # Then
    with pytest.raises(AssertionError):
        validate_state_of_commands(commands)


def test_find_updated_flows(tracker: DialogueStateTracker, all_flows: FlowsList):
    """Test if updated flows are correctly found."""
    # When
    updated_flows = find_updated_flows(tracker, all_flows)
    # Then
    assert updated_flows == {"foo"}
