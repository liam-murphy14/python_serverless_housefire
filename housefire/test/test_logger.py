import unittest
import os
import tempfile
import shutil
import logging
from housefire.logger import HousefireLoggerFactory

class TestHousefireLogger(unittest.TestCase):
    def setUp(self):
        self.log_dir = tempfile.mkdtemp()
        # It's important to reset the logging configuration between tests
        # to prevent handlers from accumulating.
        logging.shutdown()
        # Re-initialize the logging system after shutdown.
        for handler in logging.root.handlers:
            logging.root.removeHandler(handler)


    def tearDown(self):
        shutil.rmtree(self.log_dir)
        logging.shutdown()
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)


    def test_get_logger_aproduction(self):
        logger_factory = HousefireLoggerFactory(
            deploy_env="production", log_dir_path=self.log_dir
        )
        logger = logger_factory.get_logger("test_prod_logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "housefire.test_prod_logger")

        # The 'housefire' logger is the one configured with handlers.
        housefire_logger = logging.getLogger("housefire")
        self.assertTrue(
            all(
                isinstance(h, logging.FileHandler)
                for h in housefire_logger.handlers
            )
        )
        self.assertTrue(os.path.exists(os.path.join(self.log_dir, "housefire.log")))

    def test_get_logger_development(self):
        logger_factory = HousefireLoggerFactory(
            deploy_env="development", log_dir_path=self.log_dir
        )
        logger = logger_factory.get_logger("test_dev_logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "housefire.test_dev_logger")

        # The 'housefire' logger is the one configured with handlers.
        housefire_logger = logging.getLogger("housefire")
        self.assertTrue(
            any(
                isinstance(h, logging.StreamHandler)
                for h in housefire_logger.handlers
            )
        )
        self.assertTrue(os.path.exists(os.path.join(self.log_dir, "housefire.log")))

if __name__ == "__main__":
    unittest.main()
