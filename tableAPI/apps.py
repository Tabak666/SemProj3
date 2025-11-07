# tableAPI/apps.py
import os
import sys
import threading
import argparse
from django.apps import AppConfig


class TableapiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tableAPI"

    def ready(self):
        # -------------------------------------------------
        # 1. Run only in the *real* runserver process
        # -------------------------------------------------
        if os.environ.get("RUN_MAIN") != "true":
            return

        # -------------------------------------------------
        # 2. Run only when the command is `runserver`
        # -------------------------------------------------
        if len(sys.argv) < 2 or sys.argv[1] != "runserver":
            return

        # -------------------------------------------------
        # 3. Parse the arguments that come *after* `runserver`
        # -------------------------------------------------
        parser = argparse.ArgumentParser(add_help=False)

        # Match the arguments your `start_api_server` expects
        parser.add_argument("--api_port", type=int, default=8001)
        parser.add_argument("--https", action="store_true")
        parser.add_argument("--certfile", type=str)
        parser.add_argument("--keyfile", type=str)
        parser.add_argument("--desks", type=int, default=2)
        parser.add_argument("--speed", type=int, default=60)
        parser.add_argument("--log-level", type=str, default="INFO")

        # Everything after `runserver`
        try:
            runserver_idx = sys.argv.index("runserver")
            api_args = sys.argv[runserver_idx + 1 :]
        except ValueError:
            api_args = []

        args, _ = parser.parse_known_args(api_args)

        # -------------------------------------------------
        # 4. Start the API server in a **daemon thread**
        # -------------------------------------------------
        def _run_api():
            try:
                from .simulator.api_main import start_api_server
                start_api_server(
                    port=args.api_port,
                    https=args.https,
                    certfile=args.certfile,
                    keyfile=args.keyfile,
                    desks=args.desks,
                    speed=args.speed,
                    log_level=args.log_level,
                )
            except Exception as e:
                # Print to stderr so Django console still shows the error
                import traceback
                print("[TableAPI] API server crashed:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

        thread = threading.Thread(target=_run_api, name="TableAPI-Server", daemon=True)
        thread.start()
        print(f"[TableAPI] API server thread started on port {args.api_port}")