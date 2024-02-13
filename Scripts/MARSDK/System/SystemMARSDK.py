from Foundation.System import System
from Foundation.DefaultManager import DefaultManager
from Foundation.GroupManager import GroupManager
from Foundation.PolicyManager import PolicyManager
from Foundation.Providers.AdvertisementProvider import AdvertisementProvider
from Foundation.Providers.PaymentProvider import PaymentProvider
from Foundation.Providers.AuthProvider import AuthProvider
from Foundation.SceneManager import SceneManager
from Foundation.Utils import SimpleLogger
from Foundation.MonetizationManager import MonetizationManager
from Foundation.Systems.SystemGDPR import ANDROID_PLUGIN_NAME as GDPR_ANDROID_PLUGIN_NAME
from HOPA.System.SystemMonetization import SystemMonetization
from MARSDK.MarParamsManager import MarParamsManager
from MARSDK.MarUtils import MarUtils
import json


_Log = SimpleLogger("SystemMARSDK")
APPLE_SDK_NAME = "AppleMARSDK"
ANDROID_SDK_NAME = "MengineMAR"

ADVERT_TYPE = "Rewarded"


class SystemMARSDK(System):
    sdk_init_event = Event("onMarSDKInitEvent")
    sdk_init = False
    current_sdk = None

    login_event = Event("onMarSDKLoginEvent")
    login_status = False
    login_details = None

    clipboard = None
    _last_purchase_data = None
    _last_advert = None     # (AdType, AdUnitName)

    def __init__(self):
        super(SystemMARSDK, self).__init__()
        self.isConfirmedUserAgreement = False

    def _onInitialize(self):
        if Mengine.isAvailablePlugin(APPLE_SDK_NAME) is True or Mengine.isAvailablePlugin(ANDROID_SDK_NAME) is True:
            if MarUtils.isMartianTouchpadDevice() is False:
                Trace.log("System", 0,
                          "Found important ERROR: available marsdk plugin, but config is wrong!!!!\n"
                          "Please check, next params:\n"
                          "- must be touchpad device (or use -touchpad)\n"
                          "- game locale must be 'zh' (check Configs.json 'Locale' section or use -locale:zh)\n"
                          "- publisher must be 'Martian' (check Configs.json 'Params' section, param 'Publisher')")
                return

        if MarUtils.isMartianTouchpadDevice():
            self._setupPolicies()
            self.addObserver(Notificator.onSelectAccount, SystemMARSDK._onSelectAccount)

        # INITIALIZE MARSDK HERE:
        if MarUtils.isMartianAndroid() and Mengine.isAvailablePlugin(ANDROID_SDK_NAME):
            self.__tryAndroidMarSDK()
        elif MarUtils.isMartianIOS():
            # for Premium version we don't use marsdk plugin:
            if Mengine.isAvailablePlugin(APPLE_SDK_NAME) is False:
                return

            self.__tryIOSMarSDK()
        else:
            if Utils.getCurrentPublisher() == "Martian":
                _Log("no MARSDK initialize call: please check game settings or marsdk plugin", err=True, force=True)

    def _onRun(self):
        if Mengine.getConfigBool("Martian", "RequireAcceptUserAgreements", False) is True:
            if self.isConfirmedUserAgreement is False:
                self.runUserAgreementBlocker()
        return True

    def __tryIOSMarSDK(self):
        if SystemMARSDK.isSDKInited() is True:
            return True

        Trace.msg(" TRY IOS SDK {} ".format(APPLE_SDK_NAME).center(51, "-"))

        try:
            self.addObserver(Notificator.onGameStoreSentRewards, SystemMARSDK._cbGotRewards)
            callbacks = {
                "onUserLogin": SystemMARSDK._cbAppleLogin,
                "onUserLogout": SystemMARSDK._cbLogout,
                "onPayPaid": SystemMARSDK._cbApplePayResult,
                "onPlatformInit": SystemMARSDK._cbAppleInit,
                "onRealName": SystemMARSDK._cbAppleRealName,
                "onPropComplete": SystemMARSDK._cbPropComplete,
                "onPropError": SystemMARSDK._cbPropError,
                "onPurchasedNonConsumable": SystemMARSDK._cbPurchasedNonConsumable,
                # advertisement cbs
                "onAdRewardedDidFailed": SystemMARSDK._cbAppleAdRewardedDidFailed,
                "onAdRewardedDidLoaded": SystemMARSDK._cbAppleAdRewardedDidLoaded,
                "onAdRewardedDidShow": SystemMARSDK._cbAppleAdRewardedDidShow,
                "onAdRewardedDidClicked": SystemMARSDK._cbAppleAdRewardedDidClicked,
                "onAdRewardedDidClosed": SystemMARSDK._cbAppleAdRewardedDidClosed,
                "onAdRewardedDidSkipped": SystemMARSDK._cbAppleAdRewardedDidSkipped,
                "onAdRewardedDidFinished": SystemMARSDK._cbAppleAdRewardedDidFinished,
            }
            Mengine.appleMARSDKSetProvider(callbacks)

            SystemMARSDK._addDebugger("IOS")
            SystemMARSDK.current_sdk = APPLE_SDK_NAME
        except Exception:
            traceback.print_exc()

        if SystemMARSDK.isSDKInited() is True:
            Trace.msg("MarSDK init successful: TRUE")
        else:
            Trace.msg("MarSDK not inited, wait for init success...")
        Trace.msg(" IOS MarSDK prepare status: {} ".format(SystemMARSDK.hasActiveSDK()).center(51, "-"))

    def __tryAndroidMarSDK(self):
        if SystemMARSDK.isSDKInited() is True:
            return True

        Trace.msg(" TRY ANDROID SDK {} ".format(ANDROID_SDK_NAME).center(51, "-"))

        try:
            self.addObserver(Notificator.onGameStoreSentRewards, SystemMARSDK._cbGotRewards)

            Mengine.waitSemaphore("onMarSDKInitSuccess", SystemMARSDK._cbInitSuccess)
            Mengine.waitSemaphore("onMarSDKInitFail", SystemMARSDK._cbInitFail)

            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKLoginSuccess", SystemMARSDK._cbAndroidLoginSuccess)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKLoginFail", SystemMARSDK._cbAndroidLoginFail)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKLoginTimeout", SystemMARSDK._cbLoginTimeout)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKSwitchAccount", SystemMARSDK._cbSwitchAccount)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKLogout", SystemMARSDK._cbLogout)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKPaySuccess", SystemMARSDK._cbPaySuccess)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKPayFail", SystemMARSDK._cbPayFail)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKPayError", SystemMARSDK._cbPayError)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKRedeemResult", SystemMARSDK._cbRedeemResultSuccess)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKRedeemError", SystemMARSDK._cbRedeemResultError)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKSaveClipboard", SystemMARSDK._cbGetFromClipboard)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKAdVideoCallback", SystemMARSDK._cbVideoAdCallback)

            SystemMARSDK._addDebugger("Android")
            SystemMARSDK.current_sdk = ANDROID_SDK_NAME
        except Exception:
            traceback.print_exc()

        if SystemMARSDK.isSDKInited() is True:
            Trace.msg("MarSDK init successful: TRUE")
        else:
            Trace.msg("MarSDK not inited, wait for init success...")
        Trace.msg(" MarSDK prepare status: {} ".format(SystemMARSDK.hasActiveSDK()).center(51, "-"))

    @staticmethod
    def hasActiveSDK():
        return SystemMARSDK.current_sdk is not None

    @staticmethod
    def getActiveSDKName():
        return SystemMARSDK.current_sdk

    @staticmethod
    def isSDKInited():
        return SystemMARSDK.sdk_init is True

    @classmethod
    def _setupPolicies(cls):
        DefaultManager.addDefault("UseDefaultGDPRProvider", False)
        DefaultManager.addDefault("EnergyIndicatorWhitelist", "Store,InGameMenu")

        PolicyManager.setPolicy("Authorize", "PolicyAuthMarSDK")   # deprecated
        AuthProvider.setProvider("MARSDK", {
            "login": SystemMARSDK.login,
            "logout": SystemMARSDK.logout,
            "isLoggedIn": SystemMARSDK.isLogged,
            "switchAccount": SystemMARSDK.switchAccount
        })

        PaymentProvider.setProvider("MARSDK", dict(pay=SystemMARSDK.pay))
        AdvertisementProvider.setProvider("MARSDK", {
            "ShowRewardedAdvert": lambda ad_name: SystemMARSDK.showAd("Rewarded", ad_name),
            "CanOfferRewardedAdvert": lambda ad_name: SystemMARSDK.canOfferAd("Rewarded", ad_name),
            "IsRewardedAdvertAvailable": lambda ad_name: SystemMARSDK.isAdvertAvailable("Rewarded", ad_name),
            "IsInterstitialAdvertAvailable": lambda ad_name: False,
        })

    def _onStop(self):
        pass

    def _onFinalize(self):
        SystemMARSDK._remDebugger()

    ###################################################
    # Methods for working with Gift Exchange (promo codes)
    ###################################################

    @staticmethod
    def redeemCode(code):
        _Log("redeemCode: {!r}".format(code))
        Mengine.androidMethod(ANDROID_SDK_NAME, "redeemCode", code)
        return True

    @staticmethod
    def getFromClipboard():
        status = Mengine.androidBooleanMethod(ANDROID_SDK_NAME, "pasteCode")
        _Log("try to get from clipboard status = {}".format(status))

    @staticmethod
    def _cbGetFromClipboard(hasPrimaryClip, text):
        _Log("onGetFromClipboard (hasPrimaryClip={}): {!r}".format(hasPrimaryClip, text))
        SystemMARSDK.clipboard = text

    @staticmethod
    def _cbRedeemResultSuccess(propNumber, propType, msg):
        _Log("onRedeemResult: propNumber={}, propType={}, msg={}".format(propNumber, propType, msg))
        if propType in ["golds", "energy", "guide"] and propNumber > 0:
            _Log("onRedeemResult - SUCCESS: {}, {}, {}".format(propNumber, propType, msg))
            Notification.notify(Notificator.onGiftExchangeRedeemResult, propType, propNumber)
        elif propType == "unlock":
            _Log("onRedeemResult - SUCCESS: {}, {}".format(propType, msg))
            Notification.notify(Notificator.onGiftExchangeRedeemResult, "MysteryChapter", None)
        else:
            _Log("onRedeemResult - FAIL: {}, {}, {}".format(propNumber, propType, msg), force=True, err=True)
            Notification.notify(Notificator.onGiftExchangeRedeemResult, None, None)

    @staticmethod
    def _cbRedeemResultError(msg, exception_text):
        _Log("onRedeemResult - ERROR ({}): {}".format(msg, exception_text), err=True, force=True)
        Notification.notify(Notificator.onGiftExchangeRedeemResult, None, None)

    ###################################################
    # Methods for working with Payment
    ###################################################

    @staticmethod
    def pay(productID):
        if MarUtils.isMartianTouchpadDevice() is False:
            return

        prod_params = MonetizationManager.getProductInfo(productID)

        if prod_params is None:
            _Log("[MarSDK] pay error: product {} not found".format(productID), err=True, force=True)
            return

        productDesc = prod_params.descr
        productName = prod_params.name
        price = prod_params.price

        balance = SystemMonetization.getBalance()
        if SystemMARSDK.isSDKInited() is False:
            _Log("[MarSDK not inited] pay: %s %s %s %s %s" % (balance, productID, productName, productDesc, price))
            SystemMARSDK._cbPaySuccess(productID, "dev_order_{}".format(Mengine.getTime()))
        else:
            _Log("[MarSDK] pay: %s %s %s %s %s" % (balance, productID, productName, productDesc, price))

            payment_data = dict(
                productId=productID, price=price,
                productName=productName, productDesc=productDesc,
                buyNum=1, coinNum=balance,
                # REQUIRED DATA without documentation:
                ratio=0, payNotifyUrl="", orderID="", extension="", channelOrderID="", state=0
            )
            json_payment_data = json.dumps(payment_data)

            try:
                SystemMARSDK._pay_json(json_payment_data)
            except ValueError as e:
                Trace.log("System", 0, "MarSDK pay error: {}".format(e))

    @staticmethod
    def _pay_json(json_payment_data):
        _Log("[MarSDK] json payment data: {}".format(json_payment_data))

        if SystemMARSDK.getActiveSDKName() == ANDROID_SDK_NAME:
            if Mengine.androidBooleanMethod(ANDROID_SDK_NAME, "pay", json_payment_data) is False:
                raise ValueError("sdk pay method returns false")
        elif SystemMARSDK.getActiveSDKName() == APPLE_SDK_NAME:
            Mengine.appleMARSDKSubmitPaymentData(json_payment_data)
        else:
            Trace.log("System", 0, "[MarSDK] pay error: no active sdk (prepared={}, inited={})".format(
                SystemMARSDK.hasActiveSDK(), SystemMARSDK.isSDKInited()))

    @staticmethod
    def requestNonConsumablePurchased():
        if SystemMARSDK.hasActiveSDK() is False:
            _Log("requestNonConsumablePurchased No active sdk", err=True)
            return False

        _Log("Request NonConsumable Purchased...")
        if SystemMARSDK.getActiveSDKName() == APPLE_SDK_NAME:
            Mengine.appleMARSDKRequestNonConsumablePurchased()
            return True

        _Log("Current sdk ({}) hasn't this feature - request fail".format(SystemMARSDK.getActiveSDKName()), err=True)
        return False

    @staticmethod
    def _cbPurchasedNonConsumable(purchased_ids):
        _Log("[cb] Purchased NonConsumable: {}".format(purchased_ids))
        for product_id in purchased_ids:
            if SystemMonetization.isProductPurchased(product_id) is True:
                continue
            Notification.notify(Notificator.onDelayPurchased, product_id)

    @staticmethod
    def _cbPropComplete(orderID):
        _Log("[Prop cb] order {} complete done".format(orderID))
        SystemMARSDK._last_purchase_data = None

    @staticmethod
    def _cbPropError(orderID):
        _Log("[Prop cb] order {} complete fail".format(orderID), err=True, force=True)

    @staticmethod
    def _cbApplePayResult(details):
        """
            EXAMPLE
        {'orderId': '1587795813961199616', 'ryzfType': 'ApplePay',
        'hbAmount': '18', 'productName': '48\xe4\xb8\xaa\xe9\x87\x91\xe5\xb8\x81',
        'hbType': 'CNY', 'productID': 'com.martian.PAP_prompt_18'},
        """
        _Log("[AppleMARSDK] onApplePayResult: {}".format(details))
        SystemMARSDK._cbPaySuccess(details["productID"], details["orderId"])

    @staticmethod
    def _cbPaySuccess(productID, orderID):
        """ when payment finished successful """
        SystemMARSDK._last_purchase_data = dict(productID=productID, orderID=orderID)
        Notification.notify(Notificator.onPaySuccess, productID)
        _Log("pay success %s (order = %s)" % (productID, orderID))

    @staticmethod
    def _cbPayFail(productID):
        """ when payment failed """
        Notification.notify(Notificator.onPayFailed, productID)
        _Log("pay fail %s" % productID, err=True, force=True)

    @staticmethod
    def _cbPayError(code, msg, exception_text):
        """ something happen when we call `pay` """
        _Log("pay error [{}] {}: {}".format(code, msg, exception_text), err=True, force=True)

    @staticmethod
    def _cbGotRewards(productID, rewards):
        """ Player got rewards after purchase something """
        if SystemMARSDK._last_purchase_data is None:
            return False
        if SystemMARSDK.isSDKInited() is False:
            return False

        last_product_id = SystemMARSDK._last_purchase_data["productID"]

        if productID == last_product_id:
            last_order_id = SystemMARSDK._last_purchase_data["orderID"]

            if SystemMARSDK.getActiveSDKName() == APPLE_SDK_NAME:
                Mengine.appleMARSDKPropComplete(last_order_id)
            elif SystemMARSDK.getActiveSDKName() == ANDROID_SDK_NAME:
                Mengine.androidMethod(ANDROID_SDK_NAME, "setPropDeliveredComplete", last_order_id)

        return False

    ###################################################
    # Methods for working with Advertisements
    ###################################################

    @staticmethod
    def isAdvertAvailable(AdType=ADVERT_TYPE, AdUnitName=None):
        return True

    @staticmethod
    def canOfferAd(AdType=ADVERT_TYPE, AdUnitName=None):
        return True

    @staticmethod
    def showAd(AdType=ADVERT_TYPE, AdUnitName=None):
        if AdType != ADVERT_TYPE:
            Trace.log("System", 1, "MarSDK has only Rewarded ads, but given {!r}".format(AdType))
            return False

        if MarUtils.isMartianTouchpadDevice() is False:
            return False

        SystemMARSDK._setLastAdvert(AdType, AdUnitName)

        if SystemMARSDK.isSDKInited() is False:
            _Log("[MarSDK not inited] show ad {}:{}, simulate that you watched it".format(AdType, AdUnitName))
            SystemMARSDK._cbVideoAdCallback("1")
        else:
            _Log("show ad {}:{}".format(AdType, AdUnitName))
            if Mengine.isAvailablePlugin(ANDROID_SDK_NAME):
                Mengine.androidBooleanMethod(ANDROID_SDK_NAME, "showAd")
            elif Mengine.isAvailablePlugin(APPLE_SDK_NAME):
                Mengine.appleMARSDKShowRewardVideoAd("", 0)
        return True

    @staticmethod
    def _cbVideoAdCallback(msg, watch_ad_time=None):
        """ callback after view advert, code is CODE_AD_VIDEO_CALLBACK """
        if SystemMARSDK.hasLastAdvert() is False:
            _Log("[showAd cb] ERROR: no last advert, but got ad view callback!! ({})".format(msg), err=True, force=True)
            return

        ad_type, ad_name = SystemMARSDK.getLastAdvert()
        _Log("[showAd cb] [{}:{}] result={} ({}) ".format(ad_type, ad_name, msg, watch_ad_time), force=True)

        if msg == "1":
            Notification.notify(Notificator.onAdvertDisplayed, ad_type, ad_name)
            if ad_type == "Rewarded":
                Notification.notify(Notificator.onAdvertRewarded, ad_name, 'gold', None)
            Notification.notify(Notificator.onAdvertHidden, ad_type, ad_name)
        if msg == "0":
            Notification.notify(Notificator.onAdvertDisplayFailed, ad_type, ad_name)

    @staticmethod
    def __getTodayDate():
        time = Mengine.getLocalDateStruct()
        today_date = "{}/{}/{}".format(time.day, time.month, time.year)
        return today_date

    @staticmethod
    def _setLastAdvert(AdType, AdUnitName):
        SystemMARSDK._last_advert = (AdType, AdUnitName)

    @staticmethod
    def getLastAdvert():
        return SystemMARSDK._last_advert

    @staticmethod
    def hasLastAdvert():
        return SystemMARSDK._last_advert is not None

    # apple sdk

    @staticmethod
    def _cbAppleAdRewardedDidFailed():
        Notification.notify(Notificator.onAdvertLoadFail, *SystemMARSDK.getLastAdvert())
        _Log("[AppleMarSDK cb] Failed - Rewarded video ad loading fail", err=True, force=True)

    @staticmethod
    def _cbAppleAdRewardedDidLoaded():
        for ad_name in MonetizationManager.getAdvertNames(ADVERT_TYPE):
            Notification.notify(Notificator.onAdvertLoadSuccess, ADVERT_TYPE, ad_name)

    @staticmethod
    def _cbAppleAdRewardedDidShow():
        Notification.notify(Notificator.onAdvertDisplayed, *SystemMARSDK.getLastAdvert())

    @staticmethod
    def _cbAppleAdRewardedDidClicked():
        Notification.notify(Notificator.onAdvertClicked, *SystemMARSDK.getLastAdvert())

    @staticmethod
    def _cbAppleAdRewardedDidClosed():
        ad_type, ad_name = SystemMARSDK.getLastAdvert()
        Notification.notify(Notificator.onAdvertHidden, ad_type, ad_name)
        _Log("[AppleMarSDK cb] ({}:{}) close ad".format(ad_type, ad_name))

    @staticmethod
    def _cbAppleAdRewardedDidSkipped():
        ad_type, ad_name = SystemMARSDK.getLastAdvert()
        Notification.notify(Notificator.onAdvertSkipped, ad_type, ad_name)
        Notification.notify(Notificator.onAdvertHidden, ad_type, ad_name)
        _Log("[AppleMarSDK cb] ({}:{}) skip ad".format(ad_type, ad_name))

    @staticmethod
    def _cbAppleAdRewardedDidFinished(reward_type, amount):
        ad_type, ad_name = SystemMARSDK.getLastAdvert()
        if ad_type != "Rewarded":
            _Log("[AppleMarSDK cb] last ad is not rewarded video, but got rewarded finish cb"
                 " ({}:{})".format(ad_type, ad_name), err=True, force=True)
            return
        Notification.notify(Notificator.onAdvertRewarded, ad_name, 'gold', None)
        _Log("[AppleMarSDK cb] the video play is done, props need to be sent to user: {!r} {!r}".format(reward_type, amount))

    ###################################################
    # Other
    ###################################################

    @staticmethod
    def getNetworkTime():
        """ returns timestamp in seconds from China (baidu or zky) """
        if Mengine.isAvailablePlugin(ANDROID_SDK_NAME):
            time = Mengine.androidLongMethod(ANDROID_SDK_NAME, "getNetworkTime") / 1000
        elif Mengine.isAvailablePlugin(APPLE_SDK_NAME):
            # Get the server timestamp (Baidu time, return 0 if there is no network,
            # return millisecond timestamp if there is network || 1684310674000)
            time = Mengine.appleMARSDKGetInternetDate() / 1000
            _Log("getNetworkTime = {}".format(time))
        else:
            time = Mengine.getTime()
        return time

    @staticmethod
    def _moveCoinIndicator():
        new_local_position = MarParamsManager.getDataOS("coin_local_position", False)
        if new_local_position is False:
            return
        new_local_position = [float(pos) for pos in new_local_position.split(", ")]

        groups_names = ["Hint", "SkipPuzzle"]
        for group_name in groups_names:
            group = GroupManager.getGroup(group_name)
            if group.hasObject("Movie2_Coin") is False:
                continue
            coin = group.getObject("Movie2_Coin")

            coin.setPosition(new_local_position)

    def runUserAgreementBlocker(self):
        if self.existTaskChain("MartianUserAgreementBlocker") is True:
            return

        from Foundation.SystemManager import SystemManager
        SystemGlobal1 = SystemManager.getSystem("SystemGlobal1")

        def _confirm():
            self.isConfirmedUserAgreement = True

        def _cb(isSkip):
            if self.isConfirmedUserAgreement is False:
                self.runUserAgreementBlocker()

        with self.createTaskChain(Name="MartianUserAgreementBlocker", Cb=_cb) as tc:
            def _scopeFirstEnterCheck(source):
                demon_profile = GroupManager.getObject("Profile", "Demon_Profile")
                account_id = demon_profile.getParam("Current")
                if account_id is None:
                    source.addEvent(SystemGlobal1.MENU_LOAD_DONE_EVENT)

            if SceneManager.getCurrentSceneName() != "Menu":
                tc.addListener(Notificator.onSceneInit, Filter=lambda scene_name: scene_name == "Menu")
            tc.addScope(_scopeFirstEnterCheck)

            with tc.addIfTask(lambda: self.isConfirmedUserAgreement) as (true, false):
                with false.addRaceTask(2) as (tc_alias, tc_reset):
                    tc_alias.addTask("AliasConfirmUserAgreement", ConfirmUserAgreement=_confirm)

                    # scene may be restarted
                    tc_reset.addListener(Notificator.onSceneDeactivate, Filter=lambda scene_name: scene_name == "Menu")
                    tc_reset.addListener(Notificator.onSceneActivate, Filter=lambda scene_name: scene_name == "Menu")

    ###################################################
    # MarSDK callbacks and status checkers
    ###################################################

    @staticmethod
    def _cbInitSuccess(*_, **__):
        _Log("MarSDK init cb: SUCCESS")
        SystemMARSDK.sdk_init = True
        SystemMARSDK.sdk_init_event(True)

    @staticmethod
    def _cbInitFail(*_, **__):
        _Log("MarSDK init cb: !!!!!!!! FAIL !!!!!!!!", err=True, force=True)
        SystemMARSDK.sdk_init = False
        SystemMARSDK.sdk_init_event(False)

    @staticmethod
    def _cbAppleInit(*args):
        _Log("[AppleMARSDK cb] platform init: args={}".format(args))
        SystemMARSDK._cbInitSuccess(args)
        SystemMARSDK.requestNonConsumablePurchased()

    @staticmethod
    def _cbAppleRealName(*args):
        _Log("[AppleMARSDK cb] onAppleRealName: {}".format(args))

    @staticmethod
    def _cbAppleLogin(login_details):
        """
            EXAMPLE
        {'userId': '68922033ep202211021587784750876221440',
        'isSuc': 'true',
        'channelId': '68922033',
        'nickName': '\xe4\xb8\x9c\xe5\xae\xab\xe7\xbf\xa0\xe9\xad\x82',
        'token': 'marsdk_server-f919c9f0607af1412ee7b4ee01d37b37'}
        """
        _Log("[AppleMARSDK cb] onAppleLogin: {}".format(login_details))

        if login_details.get("isSuc", True) is False:
            SystemMARSDK._cbLoginFail()
            return

        if Mengine.isAvailablePlugin("AppleGeneralDataProtectionRegulation") is True:
            Mengine.appleSetGDPRPass(True)

        SystemMARSDK.login_details = login_details
        SystemMARSDK._cbLoginSuccess()

    @staticmethod
    def _cbAndroidLoginSuccess(gameType, isFreeFlag):
        extra_data_status = SystemMARSDK.submitLoginExtraData()
        _Log("extra login data status = {}".format(extra_data_status))

        if gameType in [1, 3] and isFreeFlag is False:
            # acquire ads control information
            Mengine.androidMethod(ANDROID_SDK_NAME, "reqAdControlInfo")

            if Mengine.isAvailablePlugin(GDPR_ANDROID_PLUGIN_NAME) is True:
                Mengine.androidMethod(GDPR_ANDROID_PLUGIN_NAME, "setGDPRPass", True)

        SystemMARSDK._cbLoginSuccess(gameType, isFreeFlag)

    @staticmethod
    def _cbAndroidLoginFail(gameType):
        if gameType == 1:
            Mengine.androidMethod(ANDROID_SDK_NAME, "visitorLogin")

        SystemMARSDK._cbLoginFail(gameType)

    @staticmethod
    def _cbLoginSuccess(*args):
        """ when user logged in """
        _Log("MarSDK login cb: SUCCESS: args={}".format(args))

        SystemMARSDK.login_event(True)
        SystemMARSDK.login_status = True
        Notification.notify(Notificator.onUserLoggedIn)
        SystemMARSDK.__updateDebuggerLoginDetails()

    @staticmethod
    def _cbLoginFail(*args):
        """ when user fail on login """
        _Log("MarSDK login cb: FAIL: args={}".format(args), err=True)

        SystemMARSDK.login_event(False)
        SystemMARSDK.__updateDebuggerLoginDetails()

    @staticmethod
    def _cbLoginTimeout():
        _Log("MarSDK login timeout")

    @staticmethod
    def _cbSwitchAccount(*args):
        _Log("MarSDK switch account cb: args={}".format(args))
        SystemMARSDK.__updateDebuggerLoginDetails()

    @staticmethod
    def _cbLogout(*args):
        _Log("MarSDK logout cb: args={}".format(args))
        SystemMARSDK.login_status = False
        SystemMARSDK.login_details = None
        SystemMARSDK.__updateDebuggerLoginDetails()
        Notification.notify(Notificator.onUserLoggedOut)
        SystemMARSDK.login()

    @staticmethod
    def isLogged():
        return SystemMARSDK.login_status is True

    ###################################################
    # Auth methods
    ###################################################

    @staticmethod
    def submitLoginExtraData():
        """ should be called after login success """
        if SystemMARSDK.isSDKInited() is False:
            return False

        if SystemMARSDK.getActiveSDKName() == APPLE_SDK_NAME:
            pass    # todo if exists or remove ios part
        elif SystemMARSDK.getActiveSDKName() == ANDROID_SDK_NAME:
            extra_data = dict(
                dataType=3,  # TYPE_ENTER_GAME
                roleID="100", roleName="player", roleLevel="10",
                serverID=10, serverName="server_10"
            )
            _Log("submit extra user data after login: {}".format(extra_data))

            json_extra_data = json.dumps(extra_data)
            status = Mengine.androidBooleanMethod(ANDROID_SDK_NAME, "submitExtraData", json_extra_data)

            return status

        return False

    @staticmethod
    def login():
        if Mengine.isAvailablePlugin(ANDROID_SDK_NAME) is True:
            Mengine.androidMethod(ANDROID_SDK_NAME, "login")
            return True

        if Mengine.isAvailablePlugin(APPLE_SDK_NAME) is False:
            if MarUtils.getDebugOption() == "ios":
                _Log("[AppleMARSDK not active] simulate login success")
                SystemMARSDK._cbLoginSuccess()
                return True

            _Log("[AppleMARSDK] login aborted - plugin not active", err=True, force=True)
            return False

        _Log("[AppleMARSDK] try login...", force=True)
        if Mengine.appleMARSDKLogin() is False:
            Trace.log("System", 0, "AppleMarSDK: login returns False")

        return True

    @staticmethod
    def logout():
        if Mengine.isAvailablePlugin(ANDROID_SDK_NAME) is True:
            _Log("logout not exists")
            return False

        if Mengine.isAvailablePlugin(APPLE_SDK_NAME) is False:
            if MarUtils.getDebugOption() == "ios":
                _Log("[AppleMARSDK not active] simulate logout")
                SystemMARSDK._cbLogout()
                return True

            _Log("[AppleMARSDK] logout aborted - plugin not active", err=True, force=True)
            return False

        _Log("[AppleMARSDK] try logout...", force=True)
        Mengine.appleMARSDKLogout()
        return True

    @staticmethod
    def switchAccount():
        if Mengine.isAvailablePlugin(ANDROID_SDK_NAME) is True:
            _Log("switchAccount not exists")
            return False

        if Mengine.isAvailablePlugin(APPLE_SDK_NAME) is False:
            if MarUtils.getDebugOption() == "ios":
                _Log("[AppleMARSDK not active] simulate switch account")
                SystemMARSDK.logout()
                SystemMARSDK.login()
                return True

            _Log("[AppleMARSDK] switch account aborted - plugin not active", err=True, force=True)
            return False

        if SystemMARSDK.login_status is False:
            _Log("[AppleMARSDK] you are not logged in to do switch account... but i'll try", force=True)  # return True

        _Log("[AppleMARSDK] try switch account...", force=True)
        Mengine.appleMARSDKLogout()
        return True

    ###################################################
    # Methods for working with player data
    ###################################################

    def _onLoad(self, dict_save):
        self.isConfirmedUserAgreement = dict_save.get("user_agreement_confirm", False)
        self._onLoadSave()

    def _onSave(self):
        self._onLoadSave()
        dict_save = {"user_agreement_confirm": self.isConfirmedUserAgreement}
        return dict_save

    def _onLoadSave(self):
        if MarUtils.isMartianTouchpadDevice() is False:
            return
        if Utils.getCurrentBusinessModel() == "Free":
            self._moveCoinIndicator()

    @staticmethod
    def _onSelectAccount(accountID):
        hint_time = MarParamsManager.getData("use_hint", "Time", default=5) * 1000.0
        skip_time = MarParamsManager.getData("skip_puzzle", "Time", default=10) * 1000.0

        Mengine.changeCurrentAccountSetting("DifficultyCustomHintTime", unicode(hint_time))
        Mengine.changeCurrentAccountSetting("DifficultyCustomSkipTime", unicode(skip_time))

        difficulties = {
            "SPARKLES_ON_ACTIVE_AREAS": "DifficultyCustomSparklesOnActiveAreas",
            "TUTORIAL_AVAILABLE": "DifficultyCustomTutorial",
            "PLUS_ITEM_INDICATED": "DifficultyCustomPlusItemIndicated",
            "CHANGE_ICON_ON_ACTIVE_AREAS": "DifficultyCustomChangeIconOnActiveAreas",
            "INDICATORS_ON_MAP": "DifficultyCustomIndicatorsOnMap",
            "SPARKLES_ON_HO": "DifficultyCustomSparklesOnHOPuzzles",
        }

        for key, param in difficulties.items():
            value = MarParamsManager.getData(key)
            if value is None:
                continue
            Mengine.changeCurrentAccountSetting(param, unicode(bool(value)))

        _Log("set MarSDK difficulty params ({})".format(accountID))
        return False

    # --- DevDebugger --------------------------------------------------------------------------------------------------

    @staticmethod
    def __updateDebuggerLoginDetails(widget=None):
        if Mengine.isAvailablePlugin("DevToDebug") is False:
            return

        if widget is None:
            if Mengine.hasDevToDebugTab("MarSDK") is False:
                return

            tab = Mengine.getDevToDebugTab("MarSDK")
            widget = tab.findWidget("descr")
            if widget is None:
                return

        descr = "login status: {}\n".format(SystemMARSDK.login_status)
        descr += "login details: {}".format(SystemMARSDK.login_details)

        widget.setText(descr)

    @staticmethod
    def _addDebugger(platform):
        if Mengine.isAvailablePlugin("DevToDebug") is False:
            return
        if Mengine.hasDevToDebugTab("MarSDK") is True:
            return

        tab = Mengine.addDevToDebugTab("MarSDK")
        widgets = []

        w_title = Mengine.createDevToDebugWidgetText("title")
        w_title.setText("## MarSDK {}".format(platform))
        widgets.append(w_title)

        w_descr = Mengine.createDevToDebugWidgetText("descr")
        SystemMARSDK.__updateDebuggerLoginDetails(w_descr)
        widgets.append(w_descr)

        # login buttons

        w_login = Mengine.createDevToDebugWidgetButton("login")
        w_login.setTitle("Login")
        w_login.setClickEvent(SystemMARSDK.login)
        widgets.append(w_login)

        w_logout = Mengine.createDevToDebugWidgetButton("logout")
        w_logout.setTitle("Logout")
        w_logout.setClickEvent(SystemMARSDK.logout)
        widgets.append(w_logout)

        w_switch_account = Mengine.createDevToDebugWidgetButton("switch_account")
        w_switch_account.setTitle("Switch account")
        w_switch_account.setClickEvent(SystemMARSDK.switchAccount)
        widgets.append(w_switch_account)

        # other

        for ad_name in MonetizationManager.getAdvertNames("Rewarded"):
            w_ad = Mengine.createDevToDebugWidgetButton("show_ad_{}".format(ad_name))
            w_ad.setTitle("Show Ad {!r}".format(ad_name))
            w_ad.setClickEvent(SystemMARSDK.showAd, "Rewarded", ad_name)
            widgets.append(w_ad)

        w_payments = SystemMARSDK._createDebuggerPayWidgets()
        widgets.extend(w_payments)

        # specific widgets

        if platform == "Android":
            _widgets = SystemMARSDK.__getAndroidWidgets()
            widgets.extend(_widgets)
        elif platform == "IOS":
            _widgets = SystemMARSDK.__getIOSWidgets()
            widgets.extend(_widgets)

        for widget in widgets:
            tab.addWidget(widget)

    @staticmethod
    def __getIOSWidgets():
        widgets = []

        # buttons

        w_request_purchased = Mengine.createDevToDebugWidgetButton("request_purchased")
        w_request_purchased.setTitle("Request NonConsumable Purchased")
        w_request_purchased.setClickEvent(SystemMARSDK.requestNonConsumablePurchased)
        widgets.append(w_request_purchased)

        # command lines

        w_prop_complete = Mengine.createDevToDebugWidgetCommandLine("prop_complete")
        w_prop_complete.setTitle("Complete order")
        w_prop_complete.setPlaceholder("<order_id>")
        w_prop_complete.setCommandEvent(lambda order_id: Mengine.appleMARSDKPropComplete(str(order_id)))
        widgets.append(w_prop_complete)

        return widgets

    @staticmethod
    def __getAndroidWidgets():
        widgets = []

        # command lines

        w_redeem_code = Mengine.createDevToDebugWidgetCommandLine("redeem_code")
        w_redeem_code.setTitle("Redeem gift code")
        w_redeem_code.setPlaceholder("Syntax: <code>")
        w_redeem_code.setCommandEvent(SystemMARSDK.redeemCode)
        widgets.append(w_redeem_code)

        # buttons

        w_clipboard = Mengine.createDevToDebugWidgetButton("clipboard")
        w_clipboard.setTitle("Get from Clipboard")
        w_clipboard.setClickEvent(SystemMARSDK.getFromClipboard)
        widgets.append(w_clipboard)

        w_time = Mengine.createDevToDebugWidgetButton("net_time")
        w_time.setTitle("Get Network Time")
        w_time.setClickEvent(SystemMARSDK.getNetworkTime)
        widgets.append(w_time)

        return widgets

    @staticmethod
    def _remDebugger():
        if Mengine.isAvailablePlugin("DevToDebug") is False:
            return

        if Mengine.hasDevToDebugTab("MarSDK"):
            Mengine.removeDevToDebugTab("MarSDK")

    # utils

    @staticmethod
    def _createDebuggerPayWidgets():
        w_id = Mengine.createDevToDebugWidgetCommandLine("payment_with_id")
        w_id.setTitle("Payment (with product_id)")
        w_id.setPlaceholder("Syntax: <product_id>")
        w_id.setCommandEvent(SystemMARSDK.pay)

        def _pay_with_json(json_str):
            try:
                SystemMARSDK._pay_json(json_str)
            except Exception as e:
                _Log("[DevToDebug] ERROR in pay: {}".format(e), err=True)

        w_json = Mengine.createDevToDebugWidgetCommandLine("payment_with_json")
        w_json.setTitle("Payment (with json)")
        w_json.setPlaceholder("Syntax: <json payment details>")
        w_json.setCommandEvent(_pay_with_json)

        return w_id, w_json
