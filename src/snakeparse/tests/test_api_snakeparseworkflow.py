import unittest
from pathlib import Path
from snakeparse.api import SnakeParseConfig, SnakeParseWorkflow, SnakeParseException
import tempfile
import os

class SnakeParseWorkflowTest(unittest.TestCase):

    def setUp(self):
        # create a snakefile
        with tempfile.NamedTemporaryFile('w', suffix='.smk', delete=False) as fh:
            pass
        self.snakefile = Path(fh.name)

        # create a snakeparse file
        suffix = SnakeParseConfig.DEFAULT_SNAKEPARSE_EXTENSION
        self.snakeparse = Path(str(self.snakefile.with_suffix('')) + suffix)
        with self.snakeparse.open('w') as fh:
            pass

        # create a missing path
        self.missing_path = Path('/path/does/not/exist')

    def tearDown(self):
        os.unlink(str(self.snakefile))
        os.unlink(str(self.snakeparse))

    def test_missing_snakefile(self):
        self.assertTrue(not self.missing_path.exists())
        with self.assertRaises(SnakeParseException):
            SnakeParseWorkflow(
                name = 'name',
                snakefile = self.missing_path,
                snakeparse = self.snakeparse
            )

    def test_missing_snakeparse(self):
        self.assertTrue(not self.missing_path.exists())
        with self.assertRaises(SnakeParseException):
            SnakeParseWorkflow(
                name = 'name',
                snakefile = self.snakefile,
                snakeparse = self.missing_path
            )

    def test_valid_workflow(self):
        workflow = SnakeParseWorkflow(
            name = 'name',
            snakefile = self.snakefile,
            snakeparse = self.snakeparse,
            group = 'group',
            description = 'description'
        )
        self.assertEqual(workflow.name, 'name')
        self.assertEqual(workflow.snakefile, self.snakefile)
        self.assertEqual(workflow.snakeparse, self.snakeparse)
        self.assertEqual(workflow.group, 'group')
        self.assertEqual(workflow.description, 'description')


if __name__ == '__main__':
    unittest.main()
