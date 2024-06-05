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
        def shouldAcceptPrice():
            return True

        def _getPossibleGiftExchangeRewards(self, reward_amount):
            rewards = super(SystemMonetization, self)._getPossibleGiftExchangeRewards(reward_amount)
            rewards["MysteryChapter"] = rewards.pop("chapter")  # rename key `chapter` to `MysteryChapter`
            return rewards
