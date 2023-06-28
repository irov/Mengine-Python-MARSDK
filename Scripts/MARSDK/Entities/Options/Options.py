from Foundation.GroupManager import GroupManager
from Foundation.TaskManager import TaskManager
from HOPA.Entities.Options.Options import Options as OptionsBase
from MARSDK.MarParamsManager import MarParamsManager
from MARSDK.MarUtils import MarUtils


class Options(OptionsBase):

    def _onActivate(self):
        super(Options, self)._onActivate()
        self.clickMartianURLs()
        self.clickMartianAbout()

    def clickMartianURLs(self):
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

        with TaskManager.createTaskChain(Name="Menu_Options_Martian_URLs", Repeat=True) as tc:
            for (i, url), race in tc.addRaceTaskList(urls.items()):
                race.addTask("TaskMovie2SocketClick", SocketName="url_%s" % i, Movie2=chinese_urls_movie)
                race.addFunction(Mengine.openUrlInDefaultBrowser, url)

    def clickMartianAbout(self):
        if GroupManager.hasObject("Options", "Movie2Button_About") is False:
            return
        if MarUtils.isMartianIOS() is False:
            return

        btn_about = GroupManager.getObject("Options", "Movie2Button_About")
        btn_about.setParam("Enable", True)

        with TaskManager.createTaskChain(Name="Menu_Options_Martian_About", Repeat=True) as tc:
            tc.addTask("TaskMovie2ButtonClick", Movie2Button=btn_about)
            tc.addScope(self.SceneEffect, "Options", "Movie2_Close")
            tc.addTask("TaskSceneLayerGroupEnable", LayerName="About", Value=True)
            tc.addScope(self.SceneEffect, "About", "Movie2_Open")
            tc.addTask("TaskSceneLayerGroupEnable", LayerName="Options", Value=False)

    def _onDeactivate(self):
        super(Options, self)._onDeactivate()

        if TaskManager.existTaskChain("Menu_Options_Martian_URLs"):
            TaskManager.cancelTaskChain("Menu_Options_Martian_URLs")

        if TaskManager.existTaskChain("Menu_Options_Martian_About"):
            TaskManager.cancelTaskChain("Menu_Options_Martian_About")
