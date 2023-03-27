from Foundation.DemonManager import DemonManager
from Foundation.Task.TaskAlias import TaskAlias
from MARSDK.MarParamsManager import MarParamsManager


class AliasConfirmUserAgreement(TaskAlias):
    def _onParams(self, params):
        # function that setup prev bool to True in main module
        self.ConfirmUserAgreement = params["ConfirmUserAgreement"]
        self.DialogWindow = DemonManager.getDemon("DialogWindow")

    def _showUserAgreement(self):
        urls = {
            "url_left": unicode(MarParamsManager.getData("url_1"), "utf-8"),
            "url_right": unicode(MarParamsManager.getData("url_2"), "utf-8"),
            "url_center": unicode(MarParamsManager.getData("url_3"), "utf-8"),
        }

        self.DialogWindow.runPreset("ChineseUserAgreement", content_style="urls", urls=urls)

    def _onGenerate(self, source):
        source.addTask("TaskSceneLayerGroupEnable", LayerName="DialogWindow", Value=True)

        source.addFunction(self._showUserAgreement)
        with source.addRaceTask(2) as (confirm, cancel):
            confirm.addListener(Notificator.onDialogWindowConfirm)
            confirm.addFunction(self.ConfirmUserAgreement)

            cancel.addListener(Notificator.onDialogWindowCancel)
            cancel.addTask("TaskQuitApplication")

        source.addEvent(self.DialogWindow.EVENT_WINDOW_DISAPPEAR)
        source.addTask("TaskSceneLayerGroupEnable", LayerName="DialogWindow", Value=False)
