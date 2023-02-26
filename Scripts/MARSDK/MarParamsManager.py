from Foundation.DatabaseManager import DatabaseManager
from Foundation.Manager import Manager

class MarParamsManager(Manager):
    s_data = {}

    @staticmethod
    def loadParams(module, name):
        records = DatabaseManager.getDatabaseRecords(module, name)

        for i, record in enumerate(records):
            data = {}
            for key in record.keys():
                data[key] = record.get(key, None)

            if data.get("ID") is None:
                Trace.log("Manager", 0, "MarParamsManager loaded data with empty ID (record {})!: {}".format(i, data))
                continue

            MarParamsManager.s_data[data["ID"]] = data

        return True

    @staticmethod
    def getData(id, key=None, default=None):
        """ if key is None - returns val from column 'Value'. None if nothing found (id or key) """
        data = MarParamsManager.s_data.get(id, None)

        if data is not None:
            if key is None:
                data = data.get("Value", None)
            else:
                data = data.get(key, None)

        if data is None and default is not None:
            return default

        return data

    @staticmethod
    def getAllData():
        return MarParamsManager.s_data