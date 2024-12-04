from locust import run_single_user, FastHttpUser, between, LoadTestShape

# import common.configservice as config
from common.configservice import config
import importlib
import os
import tempfile


if config.features.PROJECTLIST.boolean:
    mod1 = importlib.import_module(config.features.PROJECTLIST.modFile)
    class1 = getattr(mod1, config.features.PROJECTLIST.userClass)


if config.features.AGENTLIST.boolean:
    mod2 = importlib.import_module(config.features.AGENTLIST.modFile)
    class2 = getattr(mod2, config.features.AGENTLIST.userClass)


if config.features.BETAMANAGEUSER.boolean:
    mod3 = importlib.import_module(config.features.BETAMANAGEUSER.modFile)
    class3 = getattr(mod3, config.features.BETAMANAGEUSER.userClass)


if config.features.BETAMANAGEVIOLATION.boolean:
    mod4 = importlib.import_module(config.features.BETAMANAGEVIOLATION.modFile)
    class4 = getattr(mod4, config.features.BETAMANAGEVIOLATION.userClass)


if config.features.ONBOARDEDAGENT.boolean:
    mod5 = importlib.import_module(config.features.ONBOARDEDAGENT.modFile)
    class5 = getattr(mod5, config.features.ONBOARDEDAGENT.userClass)


if config.features.USERMANAGEMENT.boolean:
    mod6 = importlib.import_module(config.features.USERMANAGEMENT.modFile)
    class6 = getattr(mod6, config.features.USERMANAGEMENT.userClass)

if config.features.VIOLATIONMANAGEMENT.boolean:
    mod7 = importlib.import_module(config.features.VIOLATIONMANAGEMENT.modFile)
    class7 = getattr(mod7, config.features.VIOLATIONMANAGEMENT.userClass)
#collection of classes


class StagesShape(LoadTestShape):
    global stagename
    stages = [
        #{"duration": 120, "users": 2400, "spawn_rate": 20, "name": "ramp"},
	    #{"duration": 420, "users": 2400, "spawn_rate": 20, "name": "2x"},   
	    #{"duration": 600, "users": 6000, "spawn_rate": 20, "name": "ramp"},
        {"duration": 330, "users": 25, "spawn_rate": 3, "name": "3x"}   
    ]
    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                stagename = stage["name"]
                print(stagename)
                self.update_stage_name(stagename)
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
        return None


    def update_stage_name(self, stagename):
        from os.path import exists
        file_exists = exists(os.path.join(tempfile.gettempdir(), 'perf-test', stagename + '.stage'))
        if not file_exists:
            folder = os.listdir(os.path.join(tempfile.gettempdir(), 'perf-test'))
            for item in folder:
                if item.endswith(".stage"):
                    os.remove(os.path.join(tempfile.gettempdir(), 'perf-test' , item))

            f = open(os.path.join(tempfile.gettempdir(), 'perf-test', stagename + '.stage'), "w")
            f.close


# if launched directly, e.g. "python3 TestCollection.py", not "locust -f TestCollection.py"
if __name__ == "__main__":
    run_single_user(LoadTestShape)


