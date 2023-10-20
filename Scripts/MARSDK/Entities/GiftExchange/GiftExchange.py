from HOPA.Entities.GiftExchange.GiftExchange import GiftExchange as GiftExchangeBase
from HOPA.Entities.GiftExchange.GiftExchange import _Log
from MARSDK.System.SystemMARSDK import SystemMARSDK
from MARSDK.MarUtils import MarUtils


class GiftExchange(GiftExchangeBase):
    if SystemMARSDK.isSDKInited():
        def _getFromClipboard(self):
            SystemMARSDK.getFromClipboard()
            clipboard = SystemMARSDK.clipboard
            return clipboard

        def _sendRequest(self):
            code = self._getInputCode()

            msg = "-- wait for respond, redeem code {!r}".format(code)
            try:
                code = str(code)  # I'm not really sure anymore is it right
            except UnicodeEncodeError as e:
                code = str()
                msg += ", but except error - {}, so code is ''".format(e)

            _Log(msg)
            SystemMARSDK.redeemCode(code)

    elif MarUtils.isMartianAndroid() and _DEVELOPMENT is True:
        def _sendRequest(self):
            code = self._getInputCode()

            if code == "timeout":
                return

            type_of_rewards = ["unlock", "golds", "energy", "guide"]
            _Log("DUMMY Redeem code {!r}...".format(code))

            if code not in type_of_rewards:
                _Log("DUMMY unknown reward code {!r}".format(code), err=True)
                SystemMARSDK._cbRedeemResultSuccess(0, code, "0")
                return

            reward_size = 1 + Mengine.rand(50)
            SystemMARSDK._cbRedeemResultSuccess(reward_size, code, "1")
