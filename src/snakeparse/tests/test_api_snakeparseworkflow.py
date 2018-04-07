import unittest
from pathlib import Path
from snakeparse.api import SnakeParseWorkflow, SnakeParseException
import tempfile
import os


class SnakeParseWorkflowTest(unittest.TestCase):

    def setUp(self) -> None:
        # create a snakefile
        with tempfile.NamedTemporaryFile('w', suffix='.smk', delete=False) as fh:
            pass
        self.snakefile = Path(fh.name)

        # create a missing path
        self.missing_path = Path('/path/does/not/exist')

    def tearDown(self) -> None:
        os.unlink(str(self.snakefile))

    def test_missing_snakefile(self) -> None:
        self.assertTrue(not self.missing_path.exists())
        with self.assertRaises(SnakeParseException):
            SnakeParseWorkflow(
                name = 'name',
                snakefile = self.missing_path
            )

    def test_valid_workflow(self) -> None:
        workflow = SnakeParseWorkflow(
            name = 'name',
            snakefile = self.snakefile,
            group = 'group',
            description = 'description'
        )
        self.assertEqual(workflow.name, 'name')
        self.assertEqual(workflow.snakefile, self.snakefile)
        self.assertEqual(workflow.group, 'group')
        self.assertEqual(workflow.description, 'description')


if __name__ == '__main__':
    unittest.main()
