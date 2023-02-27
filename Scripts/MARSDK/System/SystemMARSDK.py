from Event import Event
from Foundation.DefaultManager import DefaultManager
from Foundation.GroupManager import GroupManager
from Foundation.PolicyManager import PolicyManager
from Foundation.Providers.AdvertisementProvider import AdvertisementProvider
from Foundation.SceneManager import SceneManager
from Foundation.System import System
from Foundation.Systems.SystemAppleServices import SystemAppleServices
from Foundation.Utils import SimpleLogger
from Foundation.Utils import getCurrentBusinessModel
from HOPA.System.SystemMonetization import SystemMonetization
from MARSDK.MarParamsManager import MarParamsManager
from MARSDK.MarUtils import MarUtils
from Notification import Notification
import json


_Log = SimpleLogger("SystemMARSDK")
APPLE_SDK_NAME = "AppleMARSDK"
ANDROID_SDK_NAME = "MarSDK"


class SystemMARSDK(System):
    sdk_init_event = Event("onMarSDKInitEvent")
    sdk_init = False
    current_sdk = None

    login_event = Event("onMarSDKLoginEvent")
    login_status = False
    login_details = None

    clipboard = None
    _last_purchase_data = None

    def __init__(self):
        super(SystemMARSDK, self).__init__()
        self.isConfirmedUserAgreement = False

    def _onInitialize(self):
        if MarUtils.isMartianTouchpadDevice():
            self._setupPolicies()
            self.addObserver(Notificator.onSelectAccount, SystemMARSDK._onSelectAccount)

        if MarUtils.isMartianAndroid() and Mengine.isAvailablePlugin(ANDROID_SDK_NAME):
            self.__tryAndroidMarSDK()

        elif MarUtils.isMartianIOS():
            SystemAppleServices.setGameCenterConnectProvider()

            if Mengine.isAvailablePlugin(APPLE_SDK_NAME) is False:
                return

            self.__tryIOSMarSDK()

    def _onRun(self):
        if Mengine.getConfigBool("Martian", "RequireAcceptUserAgreements", False) is True:
            if self.isConfirmedUserAgreement is False:
                self.runUserAgreementBlocker()
        return True

    def __tryIOSMarSDK(self):
        if SystemMARSDK.sdk_init is True:
            return True

        # ( _cbUserLogin, _cbUserLogout, _cbPayPaid, _args )
        Trace.msg(" TRY IOS SDK {} INIT ".format(APPLE_SDK_NAME).center(51, "-"))

        try:
            callbacks = {
                "onUserLogin": SystemMARSDK._cbAppleLogin,
                "onUserLogout": SystemMARSDK._cbLogout,
                "onPayPaid": SystemMARSDK._cbApplePayResult,
                "onPlatformInit": SystemMARSDK._cbAppleInit,
                "onRealName": SystemMARSDK._cbAppleRealName,
                "onPropComplete": SystemMARSDK._cbPropComplete,
                "onPropError": SystemMARSDK._cbPropError,
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
            self.addObserver(Notificator.onGameStoreSentRewards, SystemMARSDK._cbGotRewards)

            SystemMARSDK._addDebugger("IOS")
            SystemMARSDK.current_sdk = APPLE_SDK_NAME
        except Exception:
            traceback.print_exc()

        Trace.msg(" IOS MarSDK init status: {} ".format(SystemMARSDK.hasActiveSDK()).center(51, "-"))

    @staticmethod
    def __tryAndroidMarSDK():
        if SystemMARSDK.sdk_init is True:
            return True

        Trace.msg(" TRY ANDROID SDK {} INIT ".format(ANDROID_SDK_NAME).center(51, "-"))

        try:
            Mengine.waitAndroidSemaphore("onMarSDKInitSuccess", SystemMARSDK._cbInitSuccess)
            Mengine.waitAndroidSemaphore("onMarSDKInitFail", SystemMARSDK._cbInitFail)

            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKLoginSuccess", SystemMARSDK._cbLoginSuccess)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKLoginFail", SystemMARSDK._cbLoginFail)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKSwitchAccount", SystemMARSDK._cbSwitchAccount)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKLogout", SystemMARSDK._cbLogout)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKPaySuccess", SystemMARSDK._cbPaySuccess)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKPayFail", SystemMARSDK._cbPayFail)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKRedeemResult", SystemMARSDK._cbRedeemResult)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKSaveClipboard", SystemMARSDK._cbGetFromClipboard)
            Mengine.setAndroidCallback(ANDROID_SDK_NAME, "onMarSDKAdVideoCallback", SystemMARSDK._cbVideoAdCallback)

            SystemMARSDK._addDebugger("Android")
            SystemMARSDK.current_sdk = ANDROID_SDK_NAME
        except Exception:
            traceback.print_exc()

        Trace.msg(" MarSDK init status: {} ".format(SystemMARSDK.hasActiveSDK()).center(51, "-"))

    @staticmethod
    def hasActiveSDK():
        return SystemMARSDK.current_sdk is not None

    @staticmethod
    def isSDKInited():
        return SystemMARSDK.sdk_init is True

    @classmethod
    def _setupPolicies(cls):
        DefaultManager.addDefault("UseDefaultGDPRProvider", False)
        PolicyManager.setPolicy("Purchase", "PolicyPurchaseMarSDK")
        PolicyManager.setPolicy("Authorize", "PolicyAuthMarSDK")
        AdvertisementProvider.setProvider("MARSDK", {
            "ShowRewardedAdvert": SystemMARSDK.showAd,
            "CanOfferRewardedAdvert": SystemMARSDK.canOfferAd,
            "IsRewardedAdvertAvailable": SystemMARSDK.isAdvertAvailable,
        })

    def _onStop(self):
        if MarUtils.isMartianIOS():
            SystemAppleServices.removeGameCenterConnectProvider()

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
        Mengine.androidMethod(ANDROID_SDK_NAME, "pasteCode")

    @staticmethod
    def _cbGetFromClipboard(text):
        _Log("onGetFromClipboard: {!r}".format(text))
        SystemMARSDK.clipboard = text

    @staticmethod
    def _cbRedeemResult(result, propNumber, propType, msg):
        _Log("onRedeemResult: result={}, propNumber={}, propType={}, msg={}".format(result, propNumber, propType, msg))
        if result == 0:
            if propType in ["golds", "energy"] and propNumber > 0:  # add gold
                Notification.notify(Notificator.onGiftExchangeRedeemResult, propType, propNumber)
                _Log("onRedeemResult - SUCCESS: {}, {}, {}".format(propNumber, propType, msg))
            elif propType == "unlock":
                Notification.notify(Notificator.onGiftExchangeRedeemResult, "MysteryChapter", None)
                _Log("onRedeemResult - SUCCESS: {}, {}".format(propType, msg))
            else:
                Notification.notify(Notificator.onGiftExchangeRedeemResult, None, None)
                _Log("onRedeemResult - FAIL: {}, {}, {}".format(propNumber, propType, msg), err=True)
        else:
            Notification.notify(Notificator.onGiftExchangeRedeemResult, None, None)
            _Log("onRedeemResult - FAIL with result {}".format(result), err=True, force=True)

    ###################################################
    # Methods for working with Payment
    ###################################################

    @staticmethod
    def pay(productID, productName, productDesc, price):
        if not MarUtils.isMartianTouchpadDevice():
            return

        balance = SystemMonetization.getBalance()
        if SystemMARSDK.sdk_init is False:
            _Log("[MarSDK not inited] pay: %s %s %s %s %s" % (balance, productID, productName, productDesc, price))
            SystemMARSDK._cbPaySuccess(productID)
        else:
            _Log("[MarSDK] pay: %s %s %s %s %s" % (balance, productID, productName, productDesc, price))
            if Mengine.isAvailablePlugin(ANDROID_SDK_NAME):
                Mengine.androidMethod(ANDROID_SDK_NAME, "pay", balance, productID, productName, productDesc, price)
            elif Mengine.isAvailablePlugin(APPLE_SDK_NAME):
                SystemMARSDK.__submitPaymentData(balance, productID, productName, productDesc, price)

    @staticmethod
    def __submitPaymentData(balance, productID, productName, productDesc, price):
        if Mengine.isAvailablePlugin(APPLE_SDK_NAME) is False:
            return SystemMARSDK.pay(productID, productName, productDesc, price)

        payment_data = dict(
            productId=productID, price=price,
            productName=productName, productDesc=productDesc,
            buyNum=1, coinNum=balance
        )

        _Log("[AppleMARSDK] SubmitPaymentData: payment_data={}".format(payment_data))

        json_payment_data = json.dumps(payment_data)
        Mengine.appleMARSDKSubmitPaymentData(json_payment_data)

    @staticmethod
    def _cbPropComplete(orderID):
        _Log("[AppleMARSDK cb] order complete: {}".format(orderID))
        SystemMARSDK._last_purchase_data = None

    @staticmethod
    def _cbPropError(orderID):
        _Log("[AppleMARSDK cb] order error: {}".format(orderID), err=True, force=True)

    @staticmethod
    def _cbApplePayResult(details):
        """
            EXAMPLE
        {'orderId': '1587795813961199616', 'ryzfType': 'ApplePay',
        'hbAmount': '18', 'productName': '48\xe4\xb8\xaa\xe9\x87\x91\xe5\xb8\x81',
        'hbType': 'CNY', 'productID': 'com.martian.PAP_prompt_18'},
        """
        _Log("[AppleMARSDK] onApplePayResult: {}".format(details))
        SystemMARSDK._last_purchase_data = details
        SystemMARSDK._cbPaySuccess(details["productID"])

    @staticmethod
    def _cbPaySuccess(productID):
        """ onPaySuccess java callback """
        Notification.notify(Notificator.onPaySuccess, productID)
        _Log("pay success %s" % productID)

    @staticmethod
    def _cbPayFail(productID):
        """ onPayFail java callback """
        Notification.notify(Notificator.onPayFailed, productID)
        _Log("pay fail %s" % productID, err=True, force=True)

    @staticmethod
    def _cbGotRewards(productID, rewards):
        if SystemMARSDK._last_purchase_data is None:
            return False

        last_product_id = SystemMARSDK._last_purchase_data["productID"]

        if productID == last_product_id:
            last_order_id = SystemMARSDK._last_purchase_data["orderId"]
            Mengine.appleMARSDKPropComplete(last_order_id)

        return False

    ###################################################
    # Methods for working with Advertisements
    ###################################################

    @staticmethod
    def isAdvertAvailable():
        return True

    @staticmethod
    def canOfferAd():
        return True

    @staticmethod
    def showAd():
        if not MarUtils.isMartianTouchpadDevice():
            return False

        if SystemMARSDK.sdk_init is False:
            _Log("[MarSDK not inited] show ad, simulate that you watched it")
            SystemMARSDK._cbVideoAdCallback("1")
        else:
            _Log("show ad", force=True)
            if Mengine.isAvailablePlugin(ANDROID_SDK_NAME):
                Mengine.androidMethod(ANDROID_SDK_NAME, "showAd")
            elif Mengine.isAvailablePlugin(APPLE_SDK_NAME):
                Mengine.appleMARSDKShowRewardVideoAd("", 0)
        return True

    @staticmethod
    def _cbVideoAdCallback(msg, watch_ad_time=None):
        """ onResult java callback if result code is CODE_AD_VIDEO_CALLBACK """
        _Log("[showAd cb] result={} ({})".format(msg, watch_ad_time), force=True)
        if msg == "1":
            Notification.notify(Notificator.onAdvertDisplayed, "Rewarded")
            Notification.notify(Notificator.onAdvertRewarded, 'gold', None)
            Notification.notify(Notificator.onAdvertHidden, "Rewarded")
        if msg == "0":
            Notification.notify(Notificator.onAdvertDisplayFailed, "Rewarded")

    @staticmethod
    def __getTodayDate():
        time = Mengine.getLocalDateStruct()
        today_date = "{}/{}/{}".format(time.day, time.month, time.year)
        return today_date

    # apple sdk

    @staticmethod
    def _cbAppleAdRewardedDidFailed():
        Notification.notify(Notificator.onAdvertLoadFail, "Rewarded")
        _Log("[AppleMarSDK cb] Failed - Rewarded video ad loading fail", err=True, force=True)

    @staticmethod
    def _cbAppleAdRewardedDidLoaded():
        Notification.notify(Notificator.onAdvertLoadSuccess, "Rewarded")

    @staticmethod
    def _cbAppleAdRewardedDidShow():
        Notification.notify(Notificator.onAdvertDisplayed, "Rewarded")

    @staticmethod
    def _cbAppleAdRewardedDidClicked():
        Notification.notify(Notificator.onAdvertClicked, "Rewarded")

    @staticmethod
    def _cbAppleAdRewardedDidClosed():
        Notification.notify(Notificator.onAdvertHidden, "Rewarded")
        _Log("[AppleMarSDK cb] close ad")

    @staticmethod
    def _cbAppleAdRewardedDidSkipped():
        Notification.notify(Notificator.onAdvertHidden, "Rewarded")
        _Log("[AppleMarSDK cb] skip ad")

    @staticmethod
    def _cbAppleAdRewardedDidFinished(reward_type, amount):
        Notification.notify(Notificator.onAdvertRewarded, 'gold', None)
        _Log("[AppleMarSDK cb] the video play is done, props need to be sent to user: {!r} {!r}".format(reward_type, amount))

    ###################################################
    # Other
    ###################################################

    @staticmethod
    def _moveCoinIndicator():
        if MarUtils.isMartianIOS() is False:
            return

        groups_names = ["Hint", "SkipPuzzle"]
        for group_name in groups_names:
            group = GroupManager.getGroup(group_name)
            if group.hasObject("Movie2_Coin") is False:
                continue
            coin = group.getObject("Movie2_Coin")

            coin.setPosition((-80.0, 10.0, 0.0))

    def runUserAgreementBlocker(self):
        if self.existTaskChain("MartianUserAgreementBlocker") is True:
            return

        from GOAP4.System.SystemGlobal1 import MENU_LOAD_DONE_EVENT

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
                    source.addEvent(MENU_LOAD_DONE_EVENT)

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
    def _cbInitSuccess(*args):
        _Log("MarSDK init cb: SUCCESS: args={}".format(args))
        SystemMARSDK.sdk_init = True
        SystemMARSDK.sdk_init_event(True)

    @staticmethod
    def _cbInitFail(*args):
        _Log("MarSDK init cb: !!!!!!!! FAIL !!!!!!!!: args={}".format(args), err=True)
        SystemMARSDK.sdk_init = False
        SystemMARSDK.sdk_init_event(False)

    @staticmethod
    def _cbAppleInit(*args):
        _Log("[AppleMARSDK cb] platform init: args={}".format(args))
        SystemMARSDK._cbInitSuccess(args)

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

        SystemMARSDK.login_details = login_details
        SystemMARSDK._cbLoginSuccess()

    @staticmethod
    def _cbLoginSuccess(*args):
        _Log("MarSDK login cb: SUCCESS: args={}".format(args))
        SystemMARSDK.login_event(True)
        SystemMARSDK.login_status = True
        SystemMARSDK.__updateDebuggerLoginDetails()

    @staticmethod
    def _cbLoginFail(*args):
        _Log("MarSDK login cb: FAIL: args={}".format(args), err=True)
        SystemMARSDK.login_event(False)
        SystemMARSDK.__updateDebuggerLoginDetails()

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

    @staticmethod
    def isLogged():
        return SystemMARSDK.login_status is True

    ###################################################
    # Auth methods
    ###################################################

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
                SystemMARSDK._cbLogout()
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
        if getCurrentBusinessModel() == "Free":
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

        w_ad = Mengine.createDevToDebugWidgetButton("show_ad")
        w_ad.setTitle("Show Ad")
        w_ad.setClickEvent(SystemMARSDK.showAd)
        widgets.append(w_ad)

        w_pay = SystemMARSDK._createDebuggerPayWidget()
        widgets.append(w_pay)

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

        return widgets

    @staticmethod
    def _remDebugger():
        if Mengine.isAvailablePlugin("DevToDebug") is False:
            return

        if Mengine.hasDevToDebugTab("MarSDK"):
            Mengine.removeDevToDebugTab("MarSDK")

    # utils

    @staticmethod
    def _createDebuggerPayWidget():
        def _pay(text):
            """ input text allow 4 words separated by space:
                    productID, productName, productDesc, price
            """
            params = text.split(" ")
            if len(params) != 4:
                _Log("Wrong params len: add productID, productName, productDesc, price separated by space", err=True)
                return
            args = [int(arg) if arg.isdigit() else arg for arg in params]
            SystemMARSDK.pay(*args)

        widget = Mengine.createDevToDebugWidgetCommandLine("payment")
        widget.setTitle("Payment")
        widget.setPlaceholder("Syntax: <id> <name> <descr> <price>")
        widget.setCommandEvent(_pay)

        return widget