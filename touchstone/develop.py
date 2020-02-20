import re

from pyfiglet import figlet_format

from touchstone import common
from touchstone.bootstrap import Bootstrap


def execute():
    common.prep_run()
    bootstrap = Bootstrap(is_dev_mode=True)
    print(figlet_format('Touchstone', font='larry3d'))

    try:
        mock_run_contexts = bootstrap.mocks.start()
        bootstrap.mocks.print_available_mocks()

        __print_help()
        while True:
            command = input('TS > ')
            if command == 'help':
                __print_help()
            elif command == 'run':
                bootstrap.mocks.services_became_available()
                tests_did_pass = bootstrap.services.run_all_tests()
                if tests_did_pass:
                    print('All Touchstone tests passed successfully!')
                else:
                    print('One or more Touchstone tests failed.')
            elif re.search('run \\S* \\S* \\S*', command):
                command = command.lower()
                parts = command.split(' ')
                bootstrap.mocks.services_became_available()
                bootstrap.services.run_test(parts[1], parts[2], parts[3])
            elif command == 'services start':
                try:
                    bootstrap.services.start(mock_run_contexts)
                    bootstrap.mocks.services_became_available()
                except KeyboardInterrupt:
                    bootstrap.services.stop()
            elif command == 'services stop':
                bootstrap.services.stop()
            elif command == 'mocks print':
                bootstrap.mocks.print_available_mocks()
            elif command == 'mocks reset':
                bootstrap.mocks.reset()
            elif command == 'exit':
                bootstrap.services.stop()
                bootstrap.mocks.stop()
                bootstrap.runner.exit_touchstone(True)
            elif command == '':
                pass
            else:
                print(f'Unknown Touchstone command "{command}"')
    except (Exception, KeyboardInterrupt) as e:
        print('\nTouchstone was interrupted. Cleaning up...')
        bootstrap.runner.cleanup()
        raise e


def __print_help():
    print('\nDevelopment mode:\n'
          'help - Prints this message.\n'
          'run - Runs all Touchstone tests.\n'
          'run {service} {test file name} {test name} - Run a single test. Leaves mocks in the tested state.\n'
          'services start - Starts all services under test.\n'
          'services stop - Stops all services under test.\n'
          'mocks print - Prints mock UI URLs.\n'
          'mocks reset - Resets all mocks to their default state.\n'
          'exit - Exit Touchstone.\n')