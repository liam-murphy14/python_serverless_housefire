import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "sync_agents_md.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("sync_agents_md", SCRIPT_PATH)
sync_agents_md = importlib.util.module_from_spec(SCRIPT_SPEC)
assert SCRIPT_SPEC.loader is not None
SCRIPT_SPEC.loader.exec_module(sync_agents_md)


class TestSyncAgentsMd(unittest.TestCase):
    def test_render_inventory_uses_tracked_root_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("tracked\n", encoding="utf-8")
            (root / "pld_from_site.csv").write_text("untracked\n", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)

            original_root = sync_agents_md.ROOT
            try:
                sync_agents_md.ROOT = root
                inventory = sync_agents_md.render_inventory()
            finally:
                sync_agents_md.ROOT = original_root

            project_files = inventory.split("- Project/build files: ", 1)[1].split(
                "\n", 1
            )[0]
            self.assertIn("`README.md`", project_files)
            self.assertNotIn("`pld_from_site.csv`", project_files)


if __name__ == "__main__":
    unittest.main()
