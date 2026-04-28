import tempfile
import unittest
from pathlib import Path

from core.task_status import TaskState, TaskStatus
from core.task_store import TaskStatusStore


class TaskStatusTests(unittest.TestCase):
    def test_task_status_transition_updates_state(self) -> None:
        status = TaskStatus(task_id="bootstrap")

        status.transition(TaskState.RUNNING, "starting")

        self.assertIs(status.state, TaskState.RUNNING)
        self.assertEqual(status.message, "starting")

    def test_task_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TaskStatusStore(Path(temp_dir))
            status = TaskStatus(task_id="bootstrap")
            status.transition(TaskState.COMPLETED, "done")

            store.save(status)
            loaded = store.load()

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.task_id, "bootstrap")
        self.assertIs(loaded.state, TaskState.COMPLETED)
        self.assertEqual(loaded.message, "done")
