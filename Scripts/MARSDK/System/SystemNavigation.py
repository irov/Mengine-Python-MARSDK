from HOPA.System.SystemNavigation import SystemNavigation as SystemNavigationBase


class SystemNavigation(SystemNavigationBase):

    def _onRun(self):
        super(SystemNavigation, self)._onRun()

        if _ANDROID is True and Mengine.getLocale() == "zh":
            navigation_button = self.getNavTransitionButton()
            if navigation_button is not None:
                navigation_button.setEnable(False)

        return True
