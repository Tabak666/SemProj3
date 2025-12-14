# tableAPI/apps.py
import os
import sys
import threading
from django.apps import AppConfig

if os.name == "posix":      # Linux / macOS
    DEVNULL = "/dev/null"
else:                       # Windows
    DEVNULL = "nul"

class TableapiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tableAPI"

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        if len(sys.argv) < 2 or sys.argv[1] != "runserver":
            return
            
        api_port = 8001
        desk_amount = 20
        log_level = "INFO"
        disable_log = True

        def _run_api():
            # Save original stdout/stderr before redirecting
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            try:
                if disable_log:
                    # Open DEVNULL once and keep it open for the duration
                    with open(DEVNULL, 'w') as output:
                        sys.stdout = output
                        sys.stderr = output
                        
                        from .simulator.api_main import start_api_server
                        start_api_server(
                            port=api_port,
                            desks=desk_amount,
                            log_level=log_level)
                else:
                    from .simulator.api_main import start_api_server
                    start_api_server(
                        port=api_port,
                        desks=desk_amount,
                        log_level=log_level)
            except Exception as e:
                import traceback
                # ✅ Make sure to restore stderr before printing errors
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                print("[TableAPI] API server crashed:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
            finally:
                # ✅ Always restore original streams
                sys.stdout = original_stdout
                sys.stderr = original_stderr

        thread = threading.Thread(target=_run_api, name="TableAPI-Server", daemon=True)
        thread.start()
        print(f"[TableAPI] API server thread started on port {api_port}")