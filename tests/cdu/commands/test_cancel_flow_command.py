import pytest
from rasa.cdu.commands.cancel_flow_command import CancelFlowCommand
from rasa.cdu.patterns.collect_information import (
    CollectInformationPatternFlowStackFrame,
)
from rasa.cdu.stack.dialogue_stack import DialogueStack
from rasa.cdu.stack.frames.flow_frame import UserFlowStackFrame
from rasa.shared.core.constants import DIALOGUE_STACK_SLOT
from rasa.shared.core.events import SlotSet
from rasa.shared.core.trackers import DialogueStateTracker
from tests.utilities import flows_from_yaml


def test_command_name():
    # names of commands should not change as they are part of persisted
    # trackers
    assert CancelFlowCommand.command() == "cancel flow"


def test_from_dict():
    assert CancelFlowCommand.from_dict({}) == CancelFlowCommand()


def test_run_command_on_tracker_without_flows():
    tracker = DialogueStateTracker.from_events("test", evts=[])
    command = CancelFlowCommand()

    assert command.run_command_on_tracker(tracker, [], tracker) == []


def test_run_command_on_tracker():
    all_flows = flows_from_yaml(
        """
        flows:
          foo:
            name: foo flow
            steps:
            - id: first_step
              action: action_listen
        """
    )

    tracker = DialogueStateTracker.from_events(
        "test",
        evts=[
            SlotSet(
                DIALOGUE_STACK_SLOT,
                [
                    {
                        "type": "flow",
                        "frame_type": "regular",
                        "flow_id": "foo",
                        "step_id": "first_step",
                        "frame_id": "some-frame-id",
                    }
                ],
            )
        ],
    )
    command = CancelFlowCommand()

    events = command.run_command_on_tracker(tracker, all_flows, tracker)
    assert len(events) == 1

    dialogue_stack_event = events[0]
    assert isinstance(dialogue_stack_event, SlotSet)
    assert dialogue_stack_event.key == DIALOGUE_STACK_SLOT

    dialogue_stack_dump = dialogue_stack_event.value
    # flow should still be on the stack and a cancel flow should have been added
    assert isinstance(dialogue_stack_dump, list) and len(dialogue_stack_dump) == 2

    assert dialogue_stack_dump[1]["type"] == "pattern_cancel_flow"
    assert dialogue_stack_dump[1]["flow_id"] == "pattern_cancel_flow"
    assert dialogue_stack_dump[1]["step_id"] == "__start__"
    assert dialogue_stack_dump[1]["canceled_name"] == "foo flow"
    assert dialogue_stack_dump[1]["canceled_frames"] == ["some-frame-id"]


def test_select_canceled_frames_cancels_patterns():
    stack = DialogueStack(
        frames=[
            UserFlowStackFrame(
                flow_id="foo", step_id="first_step", frame_id="some-frame-id"
            ),
            CollectInformationPatternFlowStackFrame(
                collect_information="bar", frame_id="some-other-id"
            ),
        ]
    )

    all_flows = flows_from_yaml(
        """
        flows:
          foo:
            name: foo flow
            steps:
            - id: first_step
              action: action_listen
        """
    )

    foo_flow = all_flows.flow_by_id("foo")
    assert foo_flow is not None

    canceled_frames = CancelFlowCommand.select_canceled_frames(stack, foo_flow)
    assert len(canceled_frames) == 2
    assert canceled_frames[0] == "some-other-id"
    assert canceled_frames[1] == "some-frame-id"


def test_select_canceled_frames_cancels_only_top_user_flow():
    stack = DialogueStack(
        frames=[
            UserFlowStackFrame(
                flow_id="bar", step_id="first_step", frame_id="some-bar-id"
            ),
            UserFlowStackFrame(
                flow_id="foo", step_id="first_step", frame_id="some-foo-id"
            ),
        ]
    )

    all_flows = flows_from_yaml(
        """
        flows:
          foo:
            name: foo flow
            steps:
            - id: first_step
              action: action_listen
          bar:
            name: bar flow
            steps:
            - id: first_step
              action: action_listen
        """
    )

    foo_flow = all_flows.flow_by_id("foo")
    assert foo_flow is not None

    canceled_frames = CancelFlowCommand.select_canceled_frames(stack, foo_flow)
    assert len(canceled_frames) == 1
    assert canceled_frames[0] == "some-foo-id"


def test_select_canceled_frames_empty_stack():
    stack = DialogueStack(frames=[])

    all_flows = flows_from_yaml(
        """
        flows:
          foo:
            name: foo flow
            steps:
            - id: first_step
              action: action_listen
        """
    )

    foo_flow = all_flows.flow_by_id("foo")
    assert foo_flow is not None

    with pytest.raises(ValueError):
        # this shouldn't actually, happen. if the stack is empty we shouldn't
        # try to cancel anything.
        CancelFlowCommand.select_canceled_frames(stack, foo_flow)


def test_select_canceled_frames_raises_if_frame_not_found():
    stack = DialogueStack(
        frames=[
            UserFlowStackFrame(
                flow_id="bar", step_id="first_step", frame_id="some-bar-id"
            ),
        ]
    )

    all_flows = flows_from_yaml(
        """
        flows:
          foo:
            name: foo flow
            steps:
            - id: first_step
              action: action_listen
        """
    )

    foo_flow = all_flows.flow_by_id("foo")
    assert foo_flow is not None

    with pytest.raises(ValueError):
        # can't cacenl if the current flow is not on the stack. in reality
        # this should never happen as the flow should always be on the stack
        # when this command is executed.
        CancelFlowCommand.select_canceled_frames(stack, foo_flow)
