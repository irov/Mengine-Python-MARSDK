from HOPA.Entities.Credits.Credits import Credits as CreditsBase
from MARSDK.MarParamsManager import MarParamsManager
from MARSDK.MarUtils import MarUtils

class Credits(CreditsBase):

    def __init__(self):
        super(Credits, self).__init__()
        self.logo_movie = None

    def _onPreparation(self):
        super(Credits, self)._onPreparation()

        if self.object.hasObject("Movie2_Credits"):
            self.logo_movie = self.object.getObject("Movie2_Credits")
        self.__disableLogo()

    def __disableLogo(self):
        if self.logo_movie is None:
            if _DEVELOPMENT:
                Trace.msg("[!] Credits.__disableLogo: movie 'Movie2_Credits' with logo not found, fix it :(")
            return

        disableLayers = self.logo_movie.getParam("DisableLayers")

        to_disable = ["Martian_Logo.png"]
        if MarUtils.isMartianTouchpadDevice():
            to_disable = ["Default_Logo.png"]

            CE_label = MarParamsManager.getData("disable_CE")
            if CE_label is not None and bool(int(CE_label)) is True:
                to_disable.append("ce_label")

        for layer in to_disable:
            if layer in disableLayers:
                continue
            self.logo_movie.appendParam("DisableLayers", layer)