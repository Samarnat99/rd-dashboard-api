from locust import run_single_user, FastHttpUser, between, LoadTestShape
import os

os.environ["ENV_NAME"] = "rd-perf01"


# import common.configservice as config
from common.configservice import config
import importlib
import tempfile


if config.features.PROJECTLIST.boolean:
    mod1 = importlib.import_module(config.features.PROJECTLIST.modFile)
    class1 = getattr(mod1, config.features.PROJECTLIST.userClass)



#collection of classes


class StagesShape(LoadTestShape):
    global stagename
    stages = [
        #{"duration": 120, "users": 2400, "spawn_rate": 20, "name": "ramp"},
	    #{"duration": 420, "users": 2400, "spawn_rate": 20, "name": "2x"},   
	    #{"duration": 600, "users": 6000, "spawn_rate": 20, "name": "ramp"},
        {"duration": 1800, "users": 50, "spawn_rate": 1, "name": "3x"}   
    ]
    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                stagename = stage["name"]
                print(stagename)
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
        return None


    # def update_stage_name(self, stagename):
    #     from os.path import exists
    #     file_exists = exists(os.path.join(tempfile.gettempdir(), 'perf-test', stagename + '.stage'))
    #     if not file_exists:
    #         folder = os.listdir(os.path.join(tempfile.gettempdir(), 'perf-test'))
    #         for item in folder:
    #             if item.endswith(".stage"):
    #                 os.remove(os.path.join(tempfile.gettempdir(), 'perf-test' , item))

    #         f = open(os.path.join(tempfile.gettempdir(), 'perf-test', stagename + '.stage'), "w")
    #         f.close


# if launched directly, e.g. "python3 TestCollection.py", not "locust -f TestCollection.py"
if __name__ == "__main__":
    run_single_user(LoadTestShape)