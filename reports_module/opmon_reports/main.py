from .reports_arguments import OpmonReportsArguments
from .reports_main import report_main
from .notifications_main import notify_main


def main():
    args = OpmonReportsArguments()

    actions = {
        'report': (report_main, [args]),  # generate report(s) and add notifications to queue in mongo
        'notify': (notify_main, [args]),  # send pending e-mail notifications
    }

    action = actions[args.action]
    action[0](*action[1])


if __name__ == '__main__':
    main()
