from HOPA.System.SystemHint import SystemHint as SystemHintBase
from MARSDK.MarParamsManager import MarParamsManager
from MARSDK.MarUtils import MarUtils

class SystemHint(SystemHintBase):

    def getTotalReloadingTime(self):
        if MarUtils.isMartianAndroid():
            HintReloadTime = MarParamsManager.getData("use_hint", "Time") * 1000.0
            if HintReloadTime is None:
                if _DEVELOPMENT is True:
                    Trace.msg("<SystemHint> can't load reload time from from MarParamsManager 'use_hint', s_data={}".format(MarParamsManager.s_data))
                HintReloadTime = Mengine.getCurrentAccountSettingFloat("DifficultyCustomHintTime")
        else:
            HintReloadTime = Mengine.getCurrentAccountSettingFloat("DifficultyCustomHintTime")

        if self.HintGroup.hasObject("Movie2_Reload") is False:
            return HintReloadTime

        Movie_Reload = self.HintGroup.getObject("Movie2_Reload")
        Movie_ReloadDuration = Movie_Reload.getDuration()

        Movie_Reload.setSpeedFactor(Movie_ReloadDuration / HintReloadTime)

        return HintReloadTime