#!/bin/bash

# - bind on 8000 port
# - sapwn 2 worker process
# - set request timeout as 20 seconds, process not responding for 20 seconds
#   will be restarted automatically.
gunicorn --bind 0.0.0.0:$DOCKER_PORT --timeout=20 --workers=2 --log-config log_config --log-level debug --capture-output server:api
