from Foundation.GroupManager import GroupManager
from Foundation.Utils import getCurrentBusinessModel
from HOPA.Entities.Toolbar.Toolbar import Toolbar as ToolbarBase
from MARSDK.MarUtils import MarUtils

class Toolbar(ToolbarBase):
    def _onPreparation(self):
        if GroupManager.hasObject("Toolbar", "Movie2_Slot") is False:
            return

        menu = GroupManager.getObject("Toolbar", "Movie2Button_Menu")
        slot_movie = GroupManager.getObject("Toolbar", "Movie2_Slot")

        if MarUtils.isMartianIOS() and getCurrentBusinessModel() == "Free":
            slot = slot_movie.getMovieSlot("leftBiggerSize")
        else:
            slot = slot_movie.getMovieSlot("default")
        slot.addChild(menu.getEntityNode())

    def _onDeactivate(self):
        if GroupManager.hasObject("Toolbar", "Movie2_Slot") is False:
            return

        menu = GroupManager.getObject("Toolbar", "Movie2Button_Menu")
        menu.returnToParent()