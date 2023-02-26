from Foundation.Utils import getCurrentPlatform, getCurrentPublisher

class MarUtils(object):

    ###################################################
    # Methods for check player device
    ###################################################

    @staticmethod
    def getDebugOption():
        """ Returns context for -martian (use -martian:ios or -martian:android) """
        if Mengine.hasOption("martian") is False:
            return None
        if Mengine.hasTouchpad() is False:
            Trace.msg_err("<MarUtils> looks like you want to debug MarSDK features"
                          ", but you forget option -touchpad - fix it and try again!")
            return None

        option = Mengine.getOptionValue("martian").lower()
        if option not in ["ios", "android"]:
            Trace.msg_err("<MarUtils> wrong context {!r}. Use -martian:ios or -martian:android!".format(option))
            return None
        return option

    @staticmethod
    def isMartianTouchpadDevice():
        b_locale = Mengine.getLocale() == "zh"
        b_touchpad = Mengine.hasTouchpad() is True
        b_publisher = getCurrentPublisher() == "Martian"
        return all([b_locale, b_touchpad, b_publisher])

    @staticmethod
    def isMartianAndroid():
        b_locale = Mengine.getLocale() == "zh"
        b_android = True in [_ANDROID, getCurrentPlatform().lower() == "android"]
        b_publisher = getCurrentPublisher() == "Martian"
        return all([b_locale, b_android, b_publisher])

    @staticmethod
    def isMartianIOS():
        b_locale = Mengine.getLocale() == "zh"
        b_ios = True in [_IOS, getCurrentPlatform().lower() == "ios"]
        b_publisher = getCurrentPublisher() == "Martian"
        return all([b_locale, b_ios, b_publisher])