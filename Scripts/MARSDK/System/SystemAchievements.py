from Foundation.Notificator import Notificator
from Foundation.Providers.AchievementsProvider import AchievementsProvider
from Foundation.Utils import getCurrentPublisher, getCurrentBusinessModel
from HOPA.System.SystemAchievements import SystemAchievements as SystemAchievementsBase
from MARSDK.MarUtils import MarUtils


class SystemAchievements(SystemAchievementsBase):

    s_mar_achieve_ids = {
        "BatAll": {
            "Free": "Bat_All_F2P",
            "Premium": "Bat_All"
        },
        "DiaryAll": {
            "Free": "Diary_All_F2P",
            "Premium": "Diary_All"
        }
    }

    # observers

    def __onCollectiblesComplete(self, business_model):   # Catch all the bats
        if MarUtils.isMartianIOS():
            AchieveId = self.s_mar_achieve_ids["BatAll"].get(business_model)

            if AchieveId is None:
                Trace.log("System", 0, "__onCollectiblesComplete: business model is None!!!!!")
                return True

            AchievementsProvider.unlockAchievement(AchieveId)

        elif getCurrentPublisher() == "TellTale" and _ANDROID:
            AchievementsProvider.unlockAchievement("CgkI3q2FnaUHEAIQHg")

        return True

    def __onJournalAllPagesFound(self, business_model):   # Complete all logs
        if MarUtils.isMartianIOS():
            AchieveId = self.s_mar_achieve_ids["DiaryAll"].get(business_model)

            if AchieveId is None:
                Trace.log("System", 0, "__onJournalAllPagesFound: business model is None!!!!!")
                return True

            AchievementsProvider.unlockAchievement(AchieveId)
        return True

    # system things

    def _onRun(self):
        super(SystemAchievements, self)._onRun()
        current_business_model = getCurrentBusinessModel()

        self.addObserver(Notificator.onCollectiblesComplete, self.__onCollectiblesComplete, current_business_model)
        self.addObserver(Notificator.onJournalAllPagesFound, self.__onJournalAllPagesFound, current_business_model)

        return True
