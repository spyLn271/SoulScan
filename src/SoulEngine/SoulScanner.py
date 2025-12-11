import redis
import json
import logging

####################################
from src.Config import config
from src.Config.GracefullShutDown import TerminateSignal, sigterm_handler
from src.SoulEngine.SmartRouter.OnlineSmartRouter import get_active_metadata, get_active_state
####################################