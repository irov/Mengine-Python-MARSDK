def onInitialize():
    Trace.msg("MARSDK.onInitialize")

    from Foundation.TaskManager import TaskManager

    tasks = []

    TaskManager.importTasks("MARSDK.Task", tasks)

    aliases = [
        "AliasConfirmUserAgreement"
    ]

    TaskManager.importTasks("MARSDK.Alias", aliases)

    policies = [
        "PolicyAuthMarSDK"
    ]

    TaskManager.importTasks("MARSDK.Policy", policies)

    from Foundation.ObjectManager import ObjectManager

    from Foundation.Notificator import Notificator

    notifiers = []

    Notificator.addIdentities(notifiers)

    from Foundation.EntityManager import EntityManager

    Types = [
        {"name": "Options", "override": True},
        {"name": "SkipPuzzle", "override": True},
        {"name": "Credits", "override": True},
        {"name": "GiftExchange", "override": True},
        {"name": "Toolbar", "override": True},
        {"name": "About", "override": True}
    ]

    EntityManager.importEntities("MARSDK.Entities", Types)
    ObjectManager.importObjects("MARSDK.Object", Types)

    from Foundation.SessionManager import SessionManager
    from GameSession import GameSession
    SessionManager.setSessionType(GameSession)

    return True


def onFinalize():
    pass
