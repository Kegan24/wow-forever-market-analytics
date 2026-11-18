import tempfile
import unittest
from pathlib import Path
from storage import initialize, save_snapshot, load_history

class StorageTests(unittest.TestCase):
    def test_deduplicate_and_reject_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Path(directory)/'test.sqlite3'
            row={'Material':'Iron Ore','Item ID':2772,'Copper/unit':1234,'Observed at':'2026-11-18T12:00:00Z','Quantity listed':100}
            self.assertTrue(save_snapshot('forever.normal.horde.us',row,db))
            self.assertFalse(save_snapshot('forever.normal.horde.us',row,db))
            self.assertFalse(save_snapshot('forever.normal.horde.us',{**row,'Copper/unit':-1},db))
            history=load_history('forever.normal.horde.us',2772,db)
            self.assertEqual(len(history),1)
            self.assertEqual(history[0]['min_buyout_copper'],1234)

if __name__=='__main__':unittest.main()
