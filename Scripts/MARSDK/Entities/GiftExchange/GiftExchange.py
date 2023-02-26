from HOPA.Entities.GiftExchange.GiftExchange import GiftExchange as GiftExchangeBase
from HOPA.Entities.GiftExchange.GiftExchange import _Log
from MARSDK.System.SystemMARSDK import SystemMARSDK

class GiftExchange(GiftExchangeBase):

    if SystemMARSDK.sdk_init is True:

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