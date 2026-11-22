"""Saved-map lookup with an empty UID after restart; synthetic files only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dreame_local" / "app"))
from device import Device


class SavedMapIdTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def device(self, uid="", did="synthetic-device"):
        return Device(did, uid, "synthetic-model", "eu", AsyncMock(), data_dir=self.root)

    def save_list(self, uid, did="synthetic-device", map_id=24):
        path = self.root / "uploads" / "ali_dreame" / uid / did / "9"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"curr_id": map_id, "mapstr": []}))

    def test_missing_uid_uses_unique_same_device_cache(self):
        self.save_list("synthetic-account")
        self.assertEqual(self.device().saved_map_id(), 24)

    def test_missing_uid_never_selects_other_device(self):
        self.save_list("synthetic-account", did="different-device")
        self.assertIsNone(self.device().saved_map_id())

    def test_missing_uid_rejects_ambiguous_accounts(self):
        self.save_list("synthetic-account-a", map_id=24)
        self.save_list("synthetic-account-b", map_id=25)
        self.assertIsNone(self.device().saved_map_id())

    def test_known_uid_never_falls_back_to_other_account(self):
        self.save_list("different-account")
        self.assertIsNone(self.device(uid="known-account").saved_map_id())

    def test_known_uid_reads_own_cache(self):
        self.save_list("known-account", map_id=7)
        self.assertEqual(self.device(uid="known-account").saved_map_id(), 7)


if __name__ == "__main__":
    unittest.main()
