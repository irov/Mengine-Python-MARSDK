from HOPA.System.SystemEnergy import SystemEnergy as SystemEnergyBase
from MARSDK.System.SystemMARSDK import SystemMARSDK


class SystemEnergy(SystemEnergyBase):

    @staticmethod
    def _getTimestamp():
        return SystemMARSDK.getNetworkTimeMs()
