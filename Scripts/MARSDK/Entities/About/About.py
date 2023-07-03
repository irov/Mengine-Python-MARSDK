from HOPA.Entities.About.About import About as AboutBase
from MARSDK.MarParamsManager import MarParamsManager


class About(AboutBase):
    def _getURLByName(self, name):
        url_value = MarParamsManager.getData(name)
        if url_value is None:
            return None
        url = unicode(url_value, "utf-8")
        return url
