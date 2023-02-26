from Foundation.Notificator import Notificator
from Foundation.PolicyManager import PolicyManager
from Foundation.TaskManager import TaskManager
from Foundation.Utils import getCurrentPublisher
from HOPA.System.SystemAchievements import SystemAchievements as SystemAchievementsBase
from MARSDK.MarUtils import MarUtils
from Notification import Notification

class SystemAchievements(SystemAchievementsBase):

    # observers

    def __onCollectiblesComplete(self):  ### Catch all the bats
        policy_progress = PolicyManager.getPolicy("ExternalAchieveProgress", "PolicyDummy")
        if MarUtils.isMartianIOS():
            TaskManager.runAlias(policy_progress, None, AchieveId="Bat_All", Complete=True)
        elif getCurrentPublisher() == "TellTale" and _ANDROID:
            Notification.notify(Notificator.onAchievementExternalUnlocked, "CgkI3q2FnaUHEAIQHg")

        return True

    def __onJournalAllPagesFound(self):  ### Complete all logs
        policy_progress = PolicyManager.getPolicy("ExternalAchieveProgress", "PolicyDummy")
        if MarUtils.isMartianIOS():
            TaskManager.runAlias(policy_progress, None, AchieveId="Diary_All", Complete=True)
        return True

    # system things

    def _onRun(self):
        super(SystemAchievements, self)._onRun()

        self.addObserver(Notificator.onCollectiblesComplete, self.__onCollectiblesComplete)
        self.addObserver(Notificator.onJournalAllPagesFound, self.__onJournalAllPagesFound)

        return True