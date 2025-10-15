import unittest

from pitaeegsensorapi4lsl.main import main


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_main(self) -> None:
        main()
        self.assertTrue(True)
