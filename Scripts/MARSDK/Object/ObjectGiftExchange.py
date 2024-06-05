from Foundation.Object.DemonObject import DemonObject
from Foundation.TaskManager import TaskManager

FLOW_TC_NAME = "GiftExchange_Flow"


class ObjectGiftExchange(DemonObject):

    def runTaskChain(self, button, fade_value, fade_time, fade_group="FadeUI"):
        if TaskManager.existTaskChain(FLOW_TC_NAME) is True:
            Trace.log("Object", 0, "GiftExchange: {!r} already exist".format(FLOW_TC_NAME))
            return

        with TaskManager.createTaskChain(Name=FLOW_TC_NAME, Global=True, Repeat=True) as tc:
            tc.addTask("TaskMovie2ButtonClick", Movie2Button=button)

            with tc.addParallelTask(2) as (tc_fade, tc_layer):
                tc_fade.addTask('AliasFadeIn', FadeGroupName=fade_group, To=fade_value, Time=fade_time)
                tc_layer.addTask("TaskSceneLayerGroupEnable", LayerName="GiftExchange", Value=True)

            with tc.addRepeatTask() as (repeat, until):
                repeat.addScope(self.entity.scopeOpenPlate)
                repeat.addScope(self.entity.scopeRun)

                until.addScope(self.entity.scopeClickQuit)
                until.addScope(self.entity.scopeClosePlate)

            with tc.addParallelTask(2) as (tc_fade, tc_layer):
                tc_fade.addTask("AliasFadeOut", FadeGroupName=fade_group, From=fade_value, Time=fade_time)
                tc_layer.addTask("TaskSceneLayerGroupEnable", LayerName="GiftExchange", Value=False)

    def cancelTaskChain(self):
        if TaskManager.existTaskChain(FLOW_TC_NAME) is True:
            TaskManager.cancelTaskChain(FLOW_TC_NAME)
