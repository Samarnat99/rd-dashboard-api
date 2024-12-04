from locust import run_single_user, FastHttpUser, between, LoadTestShape
import os

os.environ['stage_name'] = "default_LOAD"

class StagesShape(LoadTestShape):
    stages = [
        {"duration": 600, "users": 500, "spawn_rate": 5, "name": "1x"},
        {"duration": 1200, "users": 1500, "spawn_rate": 5, "name": "3x"},
        {"duration": 1600, "users": 1000, "spawn_rate": 5, "name": "2x"}
        ]
    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                os.environ['stage_name'] = stage["name"]
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
        return None
