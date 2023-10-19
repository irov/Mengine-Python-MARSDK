from HOPA.MonetizationManager import MonetizationManager
from HOPA.System.SystemMonetization import SystemMonetization as SystemMonetizationBase
from HOPA.System.SystemMonetization import _Log
from MARSDK.MarUtils import MarUtils


class SystemMonetization(SystemMonetizationBase):
    if MarUtils.isMartianTouchpadDevice():
        def _setupParams(self):
            super(SystemMonetization, self)._setupParams()
            MonetizationManager.addCurrencyCode("MAR", "ID_CURRENCY_YUAN_CHAR")
            MonetizationManager.setCurrentCurrencyCode("MAR")

    if MarUtils.isMartianAndroid() is True:
        @staticmethod
        def _onGiftExchangeRedeemResult(reward_type, reward_amount):
            _Log("onGiftExchangeRedeemResult - {} {}".format(reward_type, reward_amount))

            if reward_type is None:
                return False

            def _callPaySuccess(prod_id):
                Notification.notify(Notificator.onPaySuccess, prod_id)

            rewards = {
                "golds": [SystemMonetization.addGold, reward_amount],
                "energy": [SystemMonetization.addEnergy, reward_amount],
                "MysteryChapter": [SystemMonetization.unlockChapter, "Bonus"],
            }

            guide_product_id = MonetizationManager.getGeneralSetting("GuidesProductID")
            if MonetizationManager.hasProductInfo(guide_product_id):
                guide_product = MonetizationManager.getProductInfo(guide_product_id)
                rewards["guide"] = [_callPaySuccess, guide_product.id]

            if reward_type not in rewards:
                Trace.log("System", 0, "SystemMonetization (MarSDK) reward_type {!r} is unknown".format(reward_type))
                return False

            send_reward, arg = rewards[reward_type]
            send_reward(arg)

            return False

        @staticmethod
        def shouldAcceptPrice():
            return True
