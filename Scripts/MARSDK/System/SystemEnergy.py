from HOPA.System.SystemEnergy import SystemEnergy as SystemEnergyBase
from MARSDK.System.SystemMARSDK import SystemMARSDK
from MARSDK.MarUtils import MarUtils


class SystemEnergy(SystemEnergyBase):

    if MarUtils.isMartianAndroid() is True:
        def _getTimestamp(self):
            return SystemMARSDK.getNetworkTime()
