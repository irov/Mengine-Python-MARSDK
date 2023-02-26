from HOPA.Entities.SkipPuzzle.SkipPuzzle import SkipPuzzle as SkipPuzzleBase
from MARSDK.MarParamsManager import MarParamsManager
from MARSDK.MarUtils import MarUtils

class SkipPuzzle(SkipPuzzleBase):

    def __getLoadSkipTime(self):
        if MarUtils.isMartianTouchpadDevice():
            return MarParamsManager.getData("skip_puzzle", "Time") * 1000.0
        if self.ForceReload is not None:
            return self.ForceReload
        return Mengine.getCurrentAccountSettingFloat("DifficultyCustomSkipTime")