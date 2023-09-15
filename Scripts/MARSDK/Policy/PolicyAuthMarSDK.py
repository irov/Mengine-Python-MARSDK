from Foundation.Task.TaskAlias import TaskAlias
from MARSDK.MarUtils import MarUtils
from MARSDK.System.SystemMARSDK import SystemMARSDK


class PolicyAuthMarSDK(TaskAlias):

    def scopeCallLogin(self, source):
        source.addFunction(SystemMARSDK.login)

    def scopeWaitLogin(self, source):
        source.addEvent(SystemMARSDK.login_event, Filter=lambda status: status is True)
        source.addFunction(Trace.msg, "<SystemMARSDK> auth done!")

    def _scopeAuthProcessing(self, source):
        if SystemMARSDK.isSDKInited() is False:
            source.addFunction(Trace.msg, "<SystemMARSDK> wait sdk init...")
            source.addEvent(SystemMARSDK.sdk_init_event, Filter=lambda status: status is True)

        with source.addIfTask(SystemMARSDK.isLogged) as (true, false):
            true.addFunction(Trace.msg, "<SystemMARSDK> already logged in")

            false.addFunction(Trace.msg, "<SystemMARSDK> wait auth...")
            with false.addParallelTask(2) as (response, request):
                response.addScope(self.scopeWaitLogin)
                request.addScope(self.scopeCallLogin)

    def _scopeDummyAuth(self, source):
        with source.addIfTask(SystemMARSDK.isLogged) as (true, false):
            true.addFunction(Trace.msg, "<SystemMARSDK> [MarSDK not inited] dummy already logged in")

            false.addFunction(Trace.msg, "<SystemMARSDK> [MarSDK not inited] dummy login success")
            false.addFunction(SystemMARSDK._cbLoginSuccess)

    def _onGenerate(self, source):
        if SystemMARSDK.hasActiveSDK() is True:
            source.addScope(self._scopeAuthProcessing)
        elif MarUtils.isMartianTouchpadDevice() and _DEVELOPMENT is True:
            source.addScope(self._scopeDummyAuth)
        else:
            Trace.msg_err("<SystemMARSDK> auth error: no active sdk !!!")
            source.addDummy()
