import logging.config
import os
import sys

from tribler_core.dependencies import check_for_missing_dependencies
from tribler_core.utilities.osutils import get_root_state_directory

import tribler_gui

if __name__ == "__main__":
    # Get root state directory (e.g. from environment variable or from system default)
    root_state_dir = get_root_state_directory()

    # Check whether we need to start the core or the user interface
    # Set up logging
    tribler_gui.load_logger_config(root_state_dir)

    # Check for missing both(GUI, Core) dependencies
    check_for_missing_dependencies(scope='both')

    # Do imports only after dependencies check
    from tribler_core.check_os import check_and_enable_code_tracing, check_environment, check_free_space, \
        enable_fault_handler, error_and_exit, should_kill_other_tribler_instances
    from tribler_core.exceptions import TriblerException

    try:
        # Enable tracer using commandline args: --trace-debug or --trace-exceptions
        trace_logger = check_and_enable_code_tracing('gui', root_state_dir)

        enable_fault_handler(root_state_dir)

        # Exit if we cant read/write files, etc.
        check_environment()

        should_kill_other_tribler_instances()

        check_free_space()

        from tribler_gui.tribler_app import TriblerApplication
        from tribler_gui.tribler_window import TriblerWindow

        app_name = os.environ.get('TRIBLER_APP_NAME', 'triblerapp')
        app = TriblerApplication(app_name, sys.argv)
        app.installTranslator(app.translator)

        if app.is_running():
            for arg in sys.argv[1:]:
                if os.path.exists(arg) and arg.endswith(".torrent"):
                    app.send_message(f"file:{arg}")
                elif arg.startswith('magnet'):
                    app.send_message(arg)
            sys.exit(1)

        window = TriblerWindow()
        window.setWindowTitle("Tribler")
        app.set_activation_window(window)
        app.parse_sys_args(sys.argv)
        sys.exit(app.exec_())

    except ImportError as ie:
        logging.exception(ie)
        error_and_exit("Import Error", f"Import error: {ie}")

    except TriblerException as te:
        logging.exception(te)
        error_and_exit("Tribler Exception", f"{te}")

    except SystemExit:
        logging.info("Shutting down Tribler")
        if trace_logger:
            trace_logger.close()
        # Flush all the logs to make sure it is written to file before it exits
        for handler in logging.getLogger().handlers:
            handler.flush()
        raise
