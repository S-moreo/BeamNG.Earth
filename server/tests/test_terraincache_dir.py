"""terraincache.cache_dir: the game's terrain texture cache folder whatever its case (issue #1330: on Linux + Proton the
game read temp/art/terrainMaterialCache while the server prefilled temp/art/terrainmaterialcache)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import terraincache  # noqa: E402


class CacheDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.user = self.tmp.name
        self.art = os.path.join(self.user, "temp", "art")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nothing_yet_lower_case_as_before(self):
        self.assertEqual(terraincache.cache_dir(self.user), os.path.join(self.art, "terrainmaterialcache"))
        os.makedirs(self.art)
        self.assertEqual(terraincache.cache_dir(self.user), os.path.join(self.art, "terrainmaterialcache"))

    def test_the_games_folder(self):
        os.makedirs(os.path.join(self.art, "terrainMaterialCache"))
        self.assertEqual(os.path.basename(terraincache.cache_dir(self.user)), "terrainMaterialCache")

    def test_any_other_spelling_found(self):
        os.makedirs(os.path.join(self.art, "TerrainMaterialCACHE"))
        self.assertEqual(os.path.basename(terraincache.cache_dir(self.user)), "TerrainMaterialCACHE")

    def test_a_file_of_that_name_is_no_folder(self):
        os.makedirs(self.art)
        Path(self.art, "TERRAINMATERIALCACHE").write_bytes(b"")
        self.assertEqual(terraincache.cache_dir(self.user), os.path.join(self.art, "terrainmaterialcache"))

    def test_both_the_engines_spelling_wins(self):
        os.makedirs(os.path.join(self.art, "terrainmaterialcache"))
        os.makedirs(os.path.join(self.art, "terrainMaterialCache"), exist_ok=True)
        if len(os.listdir(self.art)) < 2:
            self.skipTest("a case-insensitive file system: one folder")
        self.assertEqual(os.path.basename(terraincache.cache_dir(self.user)), "terrainMaterialCache")


if __name__ == "__main__":
    unittest.main()
