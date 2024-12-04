import csv
import json
import logging
import os
from pathlib import Path
import random

import cattrs
from attrs import define
from typing import List

current_folder = os.path.dirname(__file__)
module_folder = os.path.join(Path(__file__).parents[1], 'Module')


@define
class Attrs:
    boolean: bool = False
    modFile: str = "FILE"
    userClass: str = "CLASS"
    weight: int = 1


@define
class Features:
    DEMO : Attrs = None
    
@define
class Endpoints:
    host: str = "http://127.0.0.1/MISSING-CONFIG"
    hostr: str = "http://127.0.0.1/MISSING-CONFIG"
    host2: str = "http://127.0.0.1/MISSING-CONFIG"
    host3: str = "http://127.0.0.1/MISSING-CONFIG"
    host4: str = "http://127.0.0.1/MISSING-CONFIG"
    authtoken: str = "http://127.0.0.1/MISSING-CONFIG"


@define
class Loops:
    #  Update Profile
    profile_RefreshToken: int = 1
    profile_GLSLocation: int = 1
    profile_ViewProfile: int = 1
    profile_UpdateProfile: int = 1


@define
class MarketParams:
    country: str = "MISSING_CONFIG"
    lang: str = "MISSING_CONFIG"


@define
class Config:
    env: str = None
    features: Features = None
    endpoints: Endpoints = None
    wait_time: list = [0]
    time_out: int = 10
    unique: bool = False

    markets: List[MarketParams] = None
    loops: Loops = None

    users_profile: list = None
    store_profile: list = None
    users_profile_unique: list = None
    store_profile_unique: list = None

    users_CCPAprofile: list = None
    users_CCPAprofile_unique: list = None


@define
class UserInfo:
    ## ---- Update Profile
    profileLogin: str = None
    profileStoreID: str = None
    profileLongitude: str = None
    profileLatitude: str = None

    def __init__(self, pro_login, pro_storeid, pro_lat, pro_lon):
        ## ---- Update Profile
        self.profileLogin = pro_login
        self.profileStoreID = pro_storeid
        self.profileLatitude = pro_lat
        self.profileLongitude = pro_lon


def get_user():
    if config.unique:
        user = get_unique_user()
    else:
        user = get_random_user()
    return user


def get_random_user():
    # --------- Update Profile

    pro_users = ' '.join(random.choice(config.users_profile))
    pro_login = pro_users.split(' ')[0]

    pro_storesDetails = ' '.join(random.choice(config.store_profile))
    pro_storeid = pro_storesDetails.split(' ')[0]
    pro_lat = pro_storesDetails.split(' ')[1]
    pro_lon = pro_storesDetails.split(' ')[2]

    user = UserInfo(pro_login, pro_storeid, pro_lat, pro_lon)
    return user


def get_unique_user():
    ##------- Update Profile

    if len(config.users_profile_unique) < 1:
        config.users_profile_unique = config.users_profile[:]
    if len(config.store_profile_unique) < 1:
        config.store_profile_unique = config.store_profile[:]

    # ---------------- Update Profile

    pro_Users = ' '.join(config.users_profile_unique.pop())
    pro_login = pro_Users.split(' ')[0]

    pro_StoresDetails = ' '.join(config.store_profile_unique.pop())
    pro_storeid = pro_StoresDetails.split(' ')[0]
    pro_lat = pro_StoresDetails.split(' ')[1]
    pro_lon = pro_StoresDetails.split(' ')[2]

    user = UserInfo(pro_login, pro_storeid, pro_lat, pro_lon)
    return user


def read_common_file(name):
    return _read_file(current_folder, name)


def read_module_file(name):
    return _read_file(module_folder, name)


def _read_file(folder, path):
    return open(os.path.join(folder, path))


env = os.environ['ENV_NAME']

logging.warning(f"Loading ConfigService ({env})")
with read_common_file("env_configs.json") as f:
    __file_content = f.read()
    __data = json.loads(__file_content)
    __current_env = __data[env]
    config: Config = cattrs.structure_attrs_fromdict(__current_env, Config)

    # --------Normal Update Profile------

