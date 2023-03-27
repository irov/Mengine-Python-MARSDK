from Foundation.Task.TaskAlias import TaskAlias
from MARSDK.MarUtils import MarUtils
from MARSDK.System.SystemMARSDK import SystemMARSDK


class PolicyAuthMarSDK(TaskAlias):

    def scopeCallLogin(self, source):
        source.addFunction(SystemMARSDK.login)

    def scopeWaitLogin(self, source):
        source.addEvent(SystemMARSDK.login_event, Filter=lambda status: status is True)
        source.addPrint("<SystemMARSDK> auth done!")

    def _scopeAuthProcessing(self, source):
        if SystemMARSDK.isSDKInited() is False:
            source.addPrint("<SystemMARSDK> wait sdk init...")
            source.addEvent(SystemMARSDK.sdk_init_event, Filter=lambda status: status is True)

        with source.addIfTask(SystemMARSDK.isLogged) as (true, false):
            true.addPrint("<SystemMARSDK> already logged in :)")

            false.addPrint("<SystemMARSDK> wait auth...")
            with false.addParallelTask(2) as (response, request):
                response.addScope(self.scopeWaitLogin)
                request.addScope(self.scopeCallLogin)

    def _onGenerate(self, source):
        if SystemMARSDK.hasActiveSDK() is True:
            source.addScope(self._scopeAuthProcessing)
        elif MarUtils.isMartianTouchpadDevice() and _DEVELOPMENT is True:
            source.addPrint("<SystemMARSDK> [MarSDK not inited] dummy auth moment...")
        else:
            Trace.msg_err("<SystemMARSDK> auth error: no active sdk !!!")
            source.addDummy()
