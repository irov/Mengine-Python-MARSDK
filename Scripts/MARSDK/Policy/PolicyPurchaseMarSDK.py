from Foundation.Task.TaskAlias import TaskAlias
from MARSDK.MarUtils import MarUtils
from MARSDK.System.SystemMARSDK import SystemMARSDK

class PolicyPurchaseMarSDK(TaskAlias):

    def _onParams(self, params):
        self.Product = params["Product"]

    def pay(self):
        prod_params = self.Product

        prod_id = prod_params.id
        descr = prod_params.descr
        name = prod_params.name
        price = prod_params.price

        SystemMARSDK.pay(str(prod_id), name, descr, price)

    def hasAccess(self):
        return MarUtils.isMartianTouchpadDevice() is True

    def _onGenerate(self, source):
        if self.hasAccess() is True:
            source.addFunction(self.pay)
        else:
            source.addTask("PolicyPurchaseDummy", Product=self.Product)