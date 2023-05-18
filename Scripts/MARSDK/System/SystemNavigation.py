from HOPA.System.SystemNavigation import SystemNavigation as SystemNavigationBase
from MARSDK.MarUtils import MarUtils


class SystemNavigation(SystemNavigationBase):

    def _onRun(self):
        super(SystemNavigation, self)._onRun()

        if MarUtils.isMartianTouchpadDevice():
            navigation_button = self.getNavTransitionButton()
            if navigation_button is not None:
                navigation_button.setEnable(False)

        return True
