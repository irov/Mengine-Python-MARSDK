from HOPA.System.SystemEnergy import SystemEnergy as SystemEnergyBase
from MARSDK.System.SystemMARSDK import SystemMARSDK


class SystemEnergy(SystemEnergyBase):

    def _getTimestamp(self):
        if SystemMARSDK.hasActiveSDK():
            return SystemMARSDK.getNetworkTime()
        return super(SystemEnergy, self)._getTimestamp()
