from Foundation.GroupManager import GroupManager
from Foundation.TaskManager import TaskManager
from HOPA.Entities.Options.Options import Options as OptionsBase
from MARSDK.MarParamsManager import MarParamsManager
from MARSDK.MarUtils import MarUtils


class Options(OptionsBase):

    def _onActivate(self):
        super(Options, self)._onActivate()
        if GroupManager.hasObject("Options", "Movie2_chinese_urls") is False:
            return
        if MarUtils.isMartianIOS() is False:
            return

        chinese_urls_movie = GroupManager.getObject("Options", "Movie2_chinese_urls")
        chinese_urls_movie.setEnable(True)
        urls = {
            1: unicode(MarParamsManager.getData("url_1"), "utf-8"),
            2: unicode(MarParamsManager.getData("url_2"), "utf-8"),
            3: unicode(MarParamsManager.getData("url_3"), "utf-8"),
        }

        with TaskManager.createTaskChain(Name="Menu_Options_Chinese_URLs", Repeat=True) as tc:
            for (i, url), race in tc.addRaceTaskList(urls.items()):
                race.addTask("TaskMovie2SocketClick", SocketName="url_%s" % i, Movie2=chinese_urls_movie)
                race.addFunction(Mengine.openUrlInDefaultBrowser, url)

    def _onDeactivate(self):
        super(Options, self)._onDeactivate()

        if TaskManager.existTaskChain("Menu_Options_Chinese_URLs"):
            TaskManager.cancelTaskChain("Menu_Options_Chinese_URLs")
