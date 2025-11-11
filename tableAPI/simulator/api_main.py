import argparse
import ssl
import random
import logging
from http.server import HTTPServer
from .users import UserType
from .desk_manager import DeskManager
from .simple_rest_server import SimpleRESTServer

logger = logging.getLogger("main")

def setup_logging(log_level):
    """Configure logging based on the log level."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info(f"Logging initialized at {log_level} level.")

def generate_desk_id():
    return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

def generate_desk_name():
    return f"DESK {random.randint(1000, 9999)}"

def run(server_class=HTTPServer, handler_class=SimpleRESTServer, port=8000, use_https=False, cert_file=None, key_file=None, desks=2, speed=60):
    logger.info(f"Initializing DeskManager with simulation speed: {speed}")
    desk_manager = DeskManager(speed)

    logger.info("Adding default desks...")
    desk_manager.add_desk("cd:fb:1a:53:fb:e6", "DESK 4486", "Desk-O-Matic Co.", UserType.ACTIVE)
    desk_manager.add_desk("ee:62:5b:b8:73:1d", "DESK 6743", "Desk-O-Matic Co.", UserType.STANDING)

    if len(desk_manager.get_desk_ids()) < desks:
        logger.info(f"Adding {desks - len(desk_manager.get_desk_ids())} additional desks.")
        for i in range(desks - len(desk_manager.get_desk_ids())):
            desk_manager.add_desk(generate_desk_id(), generate_desk_name(), "Desk-O-Matic Co.", UserType.ACTIVE)

    desk_manager.start_updates()

    def handler(*args, **kwargs):
        handler_class(desk_manager, *args, **kwargs)

    server_address = ("localhost", port)
    SimpleRESTServer.initialize_api_keys()
    httpd = server_class(server_address, handler)

    if use_https:
        if not cert_file or not key_file:
            logger.error("Both certificate and key files must be provided for HTTPS.")
            raise ValueError("Both certificate and key files must be provided for HTTPS.")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=cert_file, keyfile=key_file)

        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        protocol = "HTTPS"
    else:
        protocol = "HTTP"

    logger.info(f"Starting {protocol} server on port {port}...")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        desk_manager.stop_updates()  # Stop the desk updates
        logger.info("Server stopped.")

"""
    To execute the script as HTTPS, use the following command:
        python main.py --port 8443 --https --certfile cert.pem --keyfile key.pem

    To execute the script as HTTP, use the following command:
        python main.py --port 8000
"""


def start_api_server(port = 8001,https=False, certfile=None, keyfile=None, desks=10, speed=1.0, log_level="INFO"):


    setup_logging(log_level)

    logger.info("Starting server with the following configuration:")
    logger.info(f"Port: {port}")
    logger.info(f"HTTPS: {'Enabled' if https else 'Disabled'}")
    if https:
        logger.info(f"Certificate file: {certfile}")
        logger.info(f"Key file: {keyfile}")
    logger.info(f"Number of desks: {desks}")
    logger.info(f"Simulation speed: {speed}")
    logger.info(f"Logging level: {log_level}")

    run(
        port=port,
        use_https=https,
        cert_file=certfile,
        key_file=keyfile,
        desks=desks,
        speed=speed
    )
