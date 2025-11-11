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

        if os.environ.get("RUN_MAIN") != "true":
            return

        if len(sys.argv) < 2 or sys.argv[1] != "runserver":
            return
            
        # parser = argparse.ArgumentParser(add_help=False)

        
        # parser.add_argument("--api_port", type=int, default=8001)
        # parser.add_argument("--https", action="store_true")
        # parser.add_argument("--certfile", type=str)
        # parser.add_argument("--keyfile", type=str)
        # parser.add_argument("--desks", type=int, default=2)
        # parser.add_argument("--speed", type=int, default=60)
        # parser.add_argument("--log-level", type=str, default="INFO")


        # try:
        #     runserver_idx = sys.argv.index("runserver")
        #     api_args = sys.argv[runserver_idx + 1 :]
        # except ValueError:
        #     api_args = []

        # args, _ = parser.parse_known_args(api_args)
        

        api_port= 8001
        desk_amount = 20

        def _run_api():
            try:
                from .simulator.api_main import start_api_server
                start_api_server(
                    port=api_port,
                    desks=desk_amount)
            except Exception as e:
                import traceback
                print("[TableAPI] API server crashed:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

        thread = threading.Thread(target=_run_api, name="TableAPI-Server", daemon=True)
        thread.start()
        print(f"[TableAPI] API server thread started on port {api_port}")