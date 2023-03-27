from Foundation.DemonManager import DemonManager
from Foundation.GroupManager import GroupManager
from Foundation.PolicyManager import PolicyManager
from Foundation.Utils import isCollectorEdition
from HOPA.BonusManager import BonusManager
from HOPA.System.SystemBonus import SystemBonus as SystemBonusBase
from MARSDK.MarParamsManager import MarParamsManager
from MARSDK.MarUtils import MarUtils


class SystemBonus(SystemBonusBase):

    def _onParams(self, params):
        super(SystemBonus, self)._onParams(params)
        self.logo_movie = None
        self.__disableSomeMoviesOnMobileState__ = False
        self.tc = None

    def _onRun(self):
        super(SystemBonus, self)._onRun()

        if isCollectorEdition() is False:
            return True

        if GroupManager.hasObject("Bonus", "Movie2_Logo"):
            self.logo_movie = GroupManager.getObject("Bonus", "Movie2_Logo")

        self.addObserver(Notificator.onTransitionEnd, self._cbTransitionEnd)

        return True

    def _scopeTransition(self, source, scene_to):
        if scene_to == "Guide":
            source.addBlock()
            return
        source.addNotify(Notificator.onBonusSceneTransition, scene_to)

    def __cbSetTransitionStatus(self, scene_from=None, scene_to=None, zoom_name=None):
        if scene_to is None or scene_to != 'Bonus':
            if self.existTaskChain("BonusOpenGuidesPaid") is True:
                self.removeTaskChain("BonusOpenGuidesPaid")
                self.tc = None
            return False

        # guides
        PolicyGuideOpen = PolicyManager.getPolicy("GuideOpen", "PolicyGuideOpenDefault")
        self.tc = self.createTaskChain(Name="BonusOpenGuidesPaid", Repeat=True)
        with self.tc as tc:
            tc.addTask(PolicyGuideOpen, GroupName="Bonus", Movie2ButtonName="Movie2Button_Guide")

        self.__disableSomeMoviesOnMobile()

        states = BonusManager.getStates()
        for state in states.values():
            demon = DemonManager.getDemon(state.demon_name)
            if self.__disableSomeMoviesOnMobileState__ is True:
                # special behavior
                status = False
                if state.state_id is "BonusVideo":
                    self.current_state = state.state_id
                    status = True
                demon.setEnable(status)
            else:
                # default behavior
                if state.status is True:
                    self.current_state = state.state_id
                demon.setEnable(state.status)

        return False

    def __disableSomeMoviesOnMobile(self):
        if Mengine.hasTouchpad() is True:
            to_disable = ["Movie2Button_BonusPapers", "Movie2Button_BonusMusic", ]

            for title in to_disable:
                if GroupManager.hasObject("Bonus", title):
                    movie = GroupManager.getObject("Bonus", title)
                    if movie.getParam("Enable") is True:
                        movie.setEnable(False)

            self.__disableSomeMoviesOnMobileState__ = True
            return True
        return False

    def _cbTransitionEnd(self, scene_from, scene_to, group_name):
        if scene_to is None or scene_to != 'Bonus':
            return False

        self.__disableWrongLogo()
        return False

    def __disableWrongLogo(self):
        if self.logo_movie is None:
            if _DEVELOPMENT:
                Trace.msg("[!] SystemBonus.__disableWrongLogo: movie 'Movie2_Logo' with logo not found, fix it :(")
            return

        disableLayers = self.logo_movie.getParam("DisableLayers")

        to_disable = ["Sprite_Logo_ZH.png"]
        if MarUtils.isMartianTouchpadDevice():
            to_disable = ["Sprite_Logo"]

            CE_label = MarParamsManager.getData("disable_CE")
            if CE_label is not None and bool(int(CE_label)) is True:
                to_disable.append("Sprite_CE.png")

        for layer in to_disable:
            if layer in disableLayers:
                continue
            if self.logo_movie.entity.movie.hasMovieLayers(layer) is False:
                continue
            self.logo_movie.appendParam("DisableLayers", layer)
