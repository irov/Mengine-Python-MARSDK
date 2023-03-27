from Foundation.GroupManager import GroupManager
from HOPA.System.SystemNavigation import SystemNavigation as SystemNavigationBase


class SystemNavigation(SystemNavigationBase):

    def _onRun(self):
        super(SystemNavigation, self)._onRun()

        if _ANDROID is True and Mengine.getLocale() == "zh":
            navDemon = GroupManager.getObject("Navigation", "Demon_Navigation")
            if navDemon.hasObject("Movie2Button_NavShowTransitions"):
                navigation_button = navDemon.getObject("Movie2Button_NavShowTransitions")
                navigation_button.setEnable(False)

        return True
