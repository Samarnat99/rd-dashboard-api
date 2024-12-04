import csv
import time
import os
import random
import re
import sys
import tempfile
import uuid
import operator
from locust import (
    SequentialTaskSet,
    HttpUser,
    between,
    task,
    constant,
    events,
    FastHttpUser,
    run_single_user,
)
import logging

from datetime import datetime, timedelta

"""
Pre-requisites:

User1 has Global Admin role assigned and has full field permissions for Action Item Management module

User2 has Restaurant Admin with OO Portal role assigned and full permissions for PTA and MII modules
User2 has only a single COOP assigned (including its sub-levels) - COOP1

"""

os.environ["ENV_NAME"] = "rd-perf01"

from actionitemmanagement_header import HeaderBuilder
import prommodule as prommodule
from configservice import get_user, config, MarketParams



def get_date(delta):
    return (datetime.today() + timedelta(delta)).strftime('%Y-%m-%d')


def get_date_slash(delta):
    return (datetime.today() + timedelta(delta)).strftime("%m/%d/%Y")

ai_correct_and_delivered = False

class Profile(SequentialTaskSet):
    stagename: str

    def __init__(self, parent):
        super().__init__(parent)
        self.stagename = ""
        self.time_1 = 0
        self.time_2 = 0
        self.login = 0
        self.diff = 0
        self.time_diff = 10
        self.authorization = ""
        self.authorization1 = ""
        self.refreshToken = ""
        self.firstname = ""
        self.lastname = ""
        self.email = ""
        self.hashedDcsId = ""
        self.loginUserName = ""
        self.deviceID = ""
        self.latitude = ""
        self.longitude = ""
        self.iteration = 0
        self.SAMLRequest = ""
        self.userid = ""
        self.password = ""
        self.RequestVerificationToken = ""
        self.token1 = ""  # token for legacy
        self.country = ""
        self.lang = ""
        self.selectedLanguage = ""
        self.node_name = ""
        self.accesstoken = ""  # token for all OOP
        self.userToken = ""  # EID + first 13 digits of token1

        self.user1EID = "e7130038"
        self.user2EID = "e7130036"
        self.user2REGION = "ANGLIA"  # COOP1 name assigned to user2
        self.approved_MIs = []
        self.rest_list = []
        self.MI_list = []
        self.selected_rests = []
        self.selected_MIs = []
        self.request_id = 0
        self.pta_AI = ""
        self.pta_AI_id = 0
        self.actionitemmanagement_AI = ""
        self.actionitemmanagement_AI_id = 0

        self.userEID = self.user1EID  # set current user as user1

        
    @task
    def SamlToken(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/rfmLogin.action",
            name="actionitemmanagement_Launch_SamlToken",
            headers=HeaderBuilder.launch_dcs(),
            catch_response=True,
        ) as Launch:
            try:
                status1 = Launch.status_code
                if status1 == 200:
                    print("Launch is successfull")

                    SAMLRequest = re.findall(
                        r"&SAMLRequest=([^&]+)&RelayState=", Launch.text
                    )
                    self.SAMLRequest = random.choice(SAMLRequest)
                else:
                    print("Launch is unsuccessfull", Launch.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def launch1(self):
        with self.client.get(
            f"{config.endpoints.hostr}/adfs/ls/?binding=urn%3Aoasis%3Anames%3Atc%3ASAML%3A2.0%3Abindings%3AHTTP-Redirect&SAMLRequest="
            + self.SAMLRequest
            + "&RelayState=",
            name="actionitemmanagement_Launch_redirect1",
            headers=HeaderBuilder.launch_dcs(),
            catch_response=True,
        ) as Launch1:
            try:
                status2 = Launch1.status_code
                if status2 == 200:
                    print("Launch redirect 1 is successfull")
                else:
                    print("Launch redirect 1 is unsuccessfull", Launch1.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def launch2(self):
        with self.client.get(
            f"{config.endpoints.hostr}/api/Account/Login?returnUrl=https%3A%2F%2Fgasstg.mcd.com%2Fadfs%2Fls%2F%3Fbinding%3Durn%253Aoasis%253Anames%253Atc%253ASAML%253A2.0%253Abindings%253AHTTP-Redirect&SAMLRequest={self.SAMLRequest}&RelayState=",
            name="actionitemmanagement_Launch_redirect2",
            headers=HeaderBuilder.launch1_dcs(self.SAMLRequest),
            catch_response=True,
        ) as Launch2:
            try:
                status3 = Launch2.status_code
                if status3 == 200:
                    print("Launch redirect 2 is successfull")
                    RequestVerificationToken = re.findall(
                        r'(?<=<input name="__RequestVerificationToken" type="hidden" value=").*?(?=" />)',
                        Launch2.text,
                    )
                    self.RequestVerificationToken = random.choice(
                        RequestVerificationToken
                    )
                else:
                    print("Launch redirect 2 is unsuccessfull", Launch2.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def login2(self):
        with self.client.post(
            f"{config.endpoints.hostr}/api/Account/AzureLoginCheck",
            name="actionitemmanagement_Azure_Login",
            headers=HeaderBuilder.login_dcs(self.SAMLRequest),
            data=[(b"Username", self.user1EID)],
            catch_response=True,
        ) as login2:
            try:
                status6 = login2.status_code
                if status6 == 200:
                    print("Login 3 was successfull")
                else:
                    print("Login 3 failed ", login2.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def login3(self):
        with self.client.post(
            f"{config.endpoints.hostr}/api/Account/Login",
            name="actionitemmanagement_Account_Login",
            headers=HeaderBuilder.login1_dcs(
                self.SAMLRequest, self.RequestVerificationToken
            ),
            data=[
                (b"Username", self.user1EID),
                (b"Password", b"Bigmac00"),
                (
                    b"postUrl",
                    b"https://gasstg.mcd.com/adfs/ls/?binding=urn%3Aoasis%3Anames%3Atc%3ASAML%3A2.0%3Abindings%3AHTTP-Redirect&SAMLRequest= + self.SAMLRequest +&RelayState=",
                ),
                (b"kmsi", b"false"),
                (b"userType", b"Corporate"),
            ],
            catch_response=True,
        ) as login3:
            try:
                status7 = login3.status_code
                if status7 == 200:
                    print("Login 4 was successfull")
                else:
                    print("Login 4 failed ", login3.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def login4(self):
        with self.client.post(
            f"{config.endpoints.hostr}/adfs/ls/?binding=urn%3Aoasis%3Anames%3Atc%3ASAML%3A2.0%3Abindings%3AHTTP-Redirect&SAMLRequest={self.SAMLRequest}&RedirectToIdentityProvider=AD+AUTHORITY",
            name="actionitemmanagement_login_4",
            headers=HeaderBuilder.login2_dcs(self.SAMLRequest),
            data=[
                ("__RequestVerificationToken", self.RequestVerificationToken),
                (b"AuthMethod", b"FormsAuthentication"),
                (b"HomeRealmSelection", b"AD AUTHORITY"),
                (b"UserName", f"LABNARESTMGMT\{self.user1EID}"),
                (b"Password", b"Bigmac00"),
                (b"btnSubmit", b"Login"),
            ],
            catch_response=True,
        ) as login4:
            try:
                status8 = login4.status_code
                if status8 == 200:
                    print("Login 5 was successfull")
                    SAMLToken2 = re.findall(
                        r'(?<=<input type="hidden" name="SAMLResponse" value=").*?(?=" />)',
                        login4.text,
                    )
                    self.SAMLToken2 = random.choice(SAMLToken2)
                else:
                    print("Login 5 failed ", login4.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def login6(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/rfmLogin.action",
            name="actionitemmanagement_Login_6",
            data=[("SAMLResponse", self.SAMLToken2)],
            headers=HeaderBuilder.login4_dcs(),
            catch_response=True,
        ) as Login6:
            try:
                status10 = Login6.status_code
                if status10 == 200:
                    print("Login 6 is successfull")
                    token1 = re.findall(
                        r"<input type=\"hidden\" name=\"token\" value=\'(.*?)\' >", Login6.text)
                    self.token1 = random.choice(token1)
                    self.userid = re.findall(r"var userId=\"userId=([^&]+)\";\n\tvar firstName=", Login6.text)[0]
                    print(self.token1)
                    print("User ID:", self.userid)

                else:
                    print("Login 6 is unsuccessfull", Login6.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def login7(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/persistLang.action?request_locale=en_US&token={self.token1}",
            name="actionitemmanagement_Login_6",
            headers=HeaderBuilder.login5_dcs(config.endpoints.host),
            catch_response=True,
        ) as Login7:
            try:
                status11 = Login7.status_code
                if status11 == 200:
                    print("Login 7 is successfull")

                else:
                    print("Login 7 is unsuccessfull", Login7.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def login8(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/openHierarchy.action?token={self.token1}",
            name="actionitemmanagement_Login_7",
            headers=HeaderBuilder.login6_dcs(config.endpoints.host),
            catch_response=True,
        ) as Login8:
            try:
                status12 = Login8.status_code
                if status12 == 200:
                    print("Login 8 is successfull")

                else:
                    print("Login 8 is unsuccessfull", Login8.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def select_market_1(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/rfmLogin.action",
            name="actionitemmanagement_select market 1",
            data=[
                ("token", self.token1),
                (b"isSaveAsCSV", b""),
                (b"refreshRandomNumber", b"0.3444336993420203"),
                (b"refreshRandomNumber", b"0.3444336993420203"),
                (b"mktName", b"US Country Office"),
                (b"marketId", b"2"),
                (b"node_id", b"2"),
                (b"node_name", b"UK"),
                (b"selectedLanguage", b"en_US"),
                (b"closePOPUP", b"TRUE"),
                (b"defaultLang", b"TRUE"),
                (b"request_locale", b" en_US"),
                (b"helpFunctionId", b"2000"),
            ],
            headers=HeaderBuilder.market1_dcs(config.endpoints.host),
            catch_response=True,
        ) as Select_market:
            try:
                status13 = Select_market.status_code
                if status13 == 200:
                    print("select market 1 is successfull")

                else:
                    print("select market 1 is Unsuccessfull", Select_market.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def market_2(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/persistLang.action?request_locale=en_US&token={self.token1}",
            name="actionitemmanagement_Select Market 2",
            headers=HeaderBuilder.login5_dcs(config.endpoints.host),
            catch_response=True,
        ) as Market_2:
            try:
                status14 = Market_2.status_code
                if status14 == 200:
                    print("Select market 2 is successfull")

                else:
                    print("Select market 2 is unsuccessfull", Market_2.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    ####################### LEGACY LOGIN DONE ##########################

    @task
    def NavigatetoRFMPORTAL(self):
        split_number = self.token1[:13]
        self.userToken = self.user1EID + split_number
        print(self.userToken)
        with self.client.get(
            f"{config.endpoints.host}/owner-operator-homepage;localeLangDesc=English;layeringLogicType=1;marketId=22;selectedLanguage=en_UK;selectedDateFormat=MMM%20d,%20yyyy;localeLangID=60;rfmRefreshPage={config.endpoints.host}owner-operator-homepage;ptaURL={config.endpoints.host};marketName=UK;userEid={self.user1EID};userToken={self.userToken};timeZone=Etc/GMT;isSessionStorage=true;accessToken={self.accesstoken};isGlobalUser=1;userId=258719;firstName=Test;lastName=User28;isRest=notR;token={self.token1}",
            name="actionitemmanagement_Navigate to Restaurant portal",
            headers=HeaderBuilder.NavigatetoRFMPortal_dcs(
                config.endpoints.host),
            catch_response=True,
        ) as Navigatetorfmportal:
            try:
                status15 = Navigatetorfmportal.status_code
                if status15 == 200:
                    print("Navigate to RFM Portal successfull")

                else:
                    print(
                        "Navigate to RFM Portal unsuccessfull", Navigatetorfmportal.text
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def APILogin(self):
        split_number = self.token1[:13]
        self.userToken = self.user1EID + split_number
        with self.client.post(
            f"{config.endpoints.host}/rfmRefreshApp/api/login",
            name="actionitemmanagement_APILogin",
            json={
                "userEid": self.user1EID,
                "marketId": "22",
                "selectedLanguage": "en_UK",
                "userToken": self.userToken,
                "isRest": "notR",
            },
            headers=HeaderBuilder.APILogin_dcs(
                config.endpoints.host,
                self.user1EID,
                self.userToken,
                self.accesstoken,
                self.token1,
            ),
            catch_response=True,
        ) as APILogin:
            try:
                status16 = APILogin.status_code
                if status16 == 200:
                    print("API Login successfull")

                else:
                    print("API Login unsuccessfull", APILogin.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    ######### OOP LOGIN DONE ###########

    @task
    def getValueFromGlobalParam(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getValueFromGlobalParam",
            name="actionitemmanagement_getValueFromGlobalParam",
            allow_redirects=False,
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                f"{config.endpoints.host}/owner-operator-homepage;localeLangDesc=English;layeringLogicType=1;marketId=22;selectedLanguage=en_UK;selectedDateFormat=MMM%20d,%20yyyy;localeLangID=60;rfmRefreshPage={config.endpoints.host}owner-operator-homepage;ptaURL={config.endpoints.host};marketName=UK;userEid={self.user1EID};userToken={self.userToken};timeZone=Etc/GMT;isSessionStorage=true;accessToken={self.accesstoken};isGlobalUser=1;userId={self.userid};firstName=Test;lastName=User28;isRest=notR;token={self.token1}",
            ),
            json={"marketId": "22", "paramName": "ENABLE_WALKME"},
        ) as global_params:
            try:
                status = global_params.status_code
                if status == 200:
                    print("getValueFromGlobalParam successfull")
                else:
                    print("getValueFromGlobalParam unsuccessfull",
                          global_params.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def homepage(self):
        with self.client.get(
            url=f"{config.endpoints.host}/owner-operator-homepage",
            name="actionitemmanagement_homepage",
            allow_redirects=False,
            headers=HeaderBuilder.homepage_dcs(config.endpoints.host),
        ) as homepage:
            try:
                status = homepage.status_code
                if status == 200:
                    print("homepage successfull")
                else:
                    print("homepage unsuccessfull", homepage.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def APILogin1(self):
        split_number = self.token1[:13]
        self.userToken = self.user1EID + split_number
        with self.client.post(
            f"{config.endpoints.host}/rfmRefreshApp/api/login",
            name="actionitemmanagement_APILogin1",
            json={
                "userEid": self.user1EID,
                "marketId": "22",
                "selectedLanguage": "en_UK",
                "userToken": self.userToken,
                "isRest": "notR",
            },
            headers=HeaderBuilder.APILogin_dcs(
                config.endpoints.host,
                self.user1EID,
                self.userToken,
                self.accesstoken,
                self.token1,
            ),
            catch_response=True,
        ) as APILogin1:
            try:
                status16 = APILogin1.status_code
                if status16 == 200:
                    print("API Login 1 successfull")

                else:
                    print("API Login 1 unsuccessfull", APILogin1.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def getValueFromGlobalParam1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getValueFromGlobalParam",
            name="actionitemmanagement_getValueFromGlobalParam1",
            allow_redirects=False,
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                f"{config.endpoints.host}/owner-operator-homepage;localeLangDesc=English;layeringLogicType=1;marketId=22;selectedLanguage=en_UK;selectedDateFormat=MMM%20d,%20yyyy;localeLangID=60;rfmRefreshPage={config.endpoints.host}owner-operator-homepage;ptaURL={config.endpoints.host};marketName=UK;userEid={self.user1EID};userToken={self.userToken};timeZone=Etc/GMT;isSessionStorage=true;accessToken={self.accesstoken};isGlobalUser=1;userId=258665;firstName=Test;lastName=User28;isRest=notR;token={self.token1}",
            ),
            json={"marketId": "22", "paramName": "ENABLE_WALKME"},
        ) as global_params1:
            try:
                status = global_params1.status_code
                if status == 200:
                    print("getValueFromGlobalParam1 successfull")
                else:
                    print("getValueFromGlobalParam1 unsuccessfull",
                          global_params1.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def notification_count(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/notificationCounts",
            name="actionitemmanagement_notification_count",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "/owner-operator-homepage",
            ),
            json={
                "permissionMap": [
                    "REFRESH_OWNER_OPERATOR_HOMEPAGE_MESSAGES"
                ],
                "userBean": {
                    "userEid": self.user1EID,
                    "marketId": "22",
                    "localeLangID": "60",
                    "userToken": self.userToken,
                    "isRest": "notR",
                    "selectedLanguage": "en_UK",
                },
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("notification_count successfull")
                else:
                    print("notification_count unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def notification_count1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/notificationCounts",
            name="actionitemmanagement_notification_count1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "/owner-operator-homepage",
            ),
            json={
                'permissionMap': ['REFRESH_OWNER_OPERATOR_HOMEPAGE_MESSAGES',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_PRICE_TAX_AND_ACTIVATE',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_POS_LAYOUT',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_REPORTS',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_PACKAGE_GENERATION,REFRESH_PACKAGE_GENERATION_GENERATE_NOW',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_MENU_ITEM_INACTIVATION',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_MESSAGES', 'REFRESH_OWNER_OPERATOR_MASS_MI_DELETE'],
                'userBean': {'userEid': self.user1EID, 'marketId': '22', 'localeLangID': '60',
                             'userToken': self.userToken, 'isRest': 'notR', 'selectedLanguage': 'en_UK'}},
        ) as notification_count1:
            try:
                status = notification_count1.status_code
                if status == 200:
                    print("notification_count1 successfull")
                else:
                    print("notification_count1 unsuccessfull",
                          notification_count1.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()
############ NOTIFICATION PART ENDS HERE #########################
                
    @task
    def load_AI_types_1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={'userEid': self.user1EID, 'marketId': '22', 'localeLangId': '60'},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_1 successfull")
                else:
                    print("load_AI_types_1 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_AIs_1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
            name="aim_get_AIs_1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={'recipientNodeSearch': '', 'menuItemSearch': '',
                                          'userBean': {'userEid': self.user1EID, 'marketId': '22'}, 'userData': {},
                                          'page': 1, 'pageSize': 100, 'includeTotalCount': True},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_AIs_1 successfull")
                else:
                    print("get_AIs_1 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()


    @task
    def get_global_param_1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
            name="aim_get_global_param_1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={'marketId': '22', 'functionId': 0,
                                          'parameterName': 'NO_CHAR_AUTO_SUGGESTION'},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_global_param_1 successfull")
                else:
                    print("get_global_param_1 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_cur_date_1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_get_cur_date_1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={'userId': '', 'marketId': 22, 'exactMatch': False, 'searchString': '',
                                          'setType': '', 'node': None, 'userEID': self.user1EID},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_cur_date_1 successfull")
                else:
                    print("get_cur_date_1 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def load_AI_types_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'userEid': self.user1EID, 'marketId': '22', 'localeLangId': '60'},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_2 successfull")
                else:
                    print("load_AI_types_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_AIs_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
            name="aim_get_AIs_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'recipientNodeSearch': '', 'menuItemSearch': '',
                                          'userBean': {'userEid': self.user1EID, 'marketId': '22'}, 'userData': {},
                                          'page': 1, 'pageSize': 100, 'includeTotalCount': True},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_AIs_2 successfull")
                else:
                    print("get_AIs_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_global_param_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
            name="aim_get_global_param_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'marketId': '22', 'functionId': 0,
                                          'parameterName': 'NO_CHAR_AUTO_SUGGESTION'},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_global_param_2 successfull")
                else:
                    print("get_global_param_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def load_AI_types_3(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_3",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'userEid': self.user1EID, 'marketId': '22', 'localeLangId': '60'},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_3 successfull")
                else:
                    print("load_AI_types_3 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_cur_date_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_get_cur_date_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'userId': '', 'marketId': 22, 'exactMatch': False, 'searchString': '',
                                          'setType': '', 'node': None, 'userEID': self.user1EID},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_cur_date_2 successfull")
                else:
                    print("get_cur_date_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def tree_generator(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getTreeGenerator",
            name="aim_getTreeGenerator",
            allow_redirects=False,
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'marketIdList': ['22'], 'userId': self.user1EID, 'localeLangID': '1',
                                          'moduleName': 'USER', 'searchString': None, 'searchOption': None,
                                          'selectByID': None, 'returnStatus': 0, 'isSearchRequired': False,
                                          'id': self.userid},
        ) as getTreeGenerator:
            try:
                status = getTreeGenerator.status_code
                if status == 200:
                    print("getTreeGenerator successfull")

                    loaded_tree = getTreeGenerator.json()

                    # extract list of stores of COOP of user 2 - self.user2COOP
                    all_stores = []
                    for local_group in loaded_tree["children"]:
                        if "children" in local_group and local_group["name"] == self.user2REGION:
                            for store in local_group["children"]:
                                all_stores.append(store)
                    self.selected_rests = random.choices(all_stores, k=3)
                    # selecting random restaurants
                    # self.selected_rests = random.choices(self.rest_list, k=3)

                else:
                    print("getTreeGenerator unsuccessfull", getTreeGenerator.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_mid_level_nodes(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getMidLevelNodesDetailsNew",
            name="aim_get_mid_level_nodes_2",
            allow_redirects=False,
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'marketIdList': ['22'], 'userId': self.user1EID, 'localeLangID': '1',
                                          'moduleName': 'USER', 'searchString': None, 'searchOption': None,
                                          'selectByID': None, 'isSearchRequired': False},
        ) as get_mid_level_nodes:
            try:
                status = get_mid_level_nodes.status_code
                if status == 200:
                    print("get_mid_level_nodes successfull")
                else:
                    print("get_mid_level_nodes unsuccessfull", get_mid_level_nodes.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_lookups(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getlookUps",
            name="aim_get_lookups_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'userEid': self.user1EID, 'marketId': '22'},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_lookups successfull")
                else:
                    print("get_lookups unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_MI_list_count_1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getMenuItemListCount",
            name="aim_get_MI_list_count_1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={'status': [], 'marketId': 22, 'userEid': self.user1EID,
                                          'effectiveDate': get_date(0), 'nodesIds': [self.selected_rests[0]["child"]], 'exactMatch': False,
                                          'prd_ds': [], 'prd_cd': [], 'prodClassFilter': [], 'nextRows': 1,
                                          'fetchRows': 100},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_MI_list_count_1 successfull")
                else:
                    print("get_MI_list_count_1 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_approved_MIs(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getMenuItem",
            name="aim_get_approved_MIs",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "",
            ),
            json={
                "searchOption": 2,
                "approvalStatus": "1",
                "userBean": {"userEid": self.user1EID, "marketId": "22"},
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_approved_MIs successfull")
                    MIs = response.json()
                    self.approved_MIs = [MI["menuItemCode"] for MI in MIs]
                else:
                    print("get_approved_MIs unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def create_pta_AI(self):
        global ai_correct_and_delivered
        while not ai_correct_and_delivered:
            search_MI_IDs = [str(i) for i in random.choices(self.approved_MIs, k=5)]
            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/getMenuItemListNoStatus",
                name="aim_get_MI_list_NS_1",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item/create",
                ),
                json={'status': [], 'marketId': 22, 'userEid': self.user1EID, 'exactMatch': True,
                                          'prd_ds': search_MI_IDs, 'prd_cd': search_MI_IDs, 'prodClassFilter': [],
                                          'effectiveDate': get_date(0), 'nodesIds': [int(store["child"]) for store in self.selected_rests], 'nextRows': 1,
                                          'fetchRows': 100},
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("get_MI_list_NS_1 successfull")

                        self.selected_MIs = response.json()  # save the selected MI list

                    else:
                        print("get_MI_list_NS_1 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            self.pta_AI = f"test_pta_{random.randint(1000000, 9999999)}"

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/addActionItem",
                name="aim_add_action_item",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item/create",
                ),
                json={
                    "actionItemSubject": self.pta_AI,
                    "actionItemType": 1,
                    "menuItemValues": [
                        {
                            "productId": MI["productId"],
                            "productDescription": MI["productDS"],
                            "productCode": MI["productCode"],
                        }
                        for MI in self.selected_MIs
                    ],
                    "nodeIdValues": [
                        {
                            "restaurantNumber": int(store["restNu"]),
                            "restName": store["restName"],
                            "restaurantNodeId": store["child"],
                            "parentNodeId": store["parent"],
                        }
                        for store in self.selected_rests
                    ],
                    "sendDate": get_date_slash(0),
                    "userBean": {"marketId": "22", "userEid": self.user1EID},
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("add_action_item successfull")
                        self.request_id = response.json()["actionItemResponse"][
                            "actionItemRequestId"
                        ]
                        print("requestid:",self.request_id)
                    else:
                        print("add_action_item unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()
###
            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
                name="aim_load_AI_types_4",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item",
                ),
                json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("load_AI_types_4 successfull")
                    else:
                        print("load_AI_types_4 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
                name="aim_get_AIs_3",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item",
                ),
                json={
                    "recipientNodeSearch": "",
                    "menuItemSearch": "",
                    "userBean": {"userEid": self.user1EID, "marketId": "22"},
                    "userData": {},
                    "page": 1,
                    "pageSize": 100,
                    "includeTotalCount": True,
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("get_AIs_3 successfull")
                    else:
                        print("get_AIs_3 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
                name="aim_get_global_param_3",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item",
                ),
                json={
                    "marketId": "22",
                    "functionId": 0,
                    "parameterName": "NO_CHAR_AUTO_SUGGESTION",
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("get_global_param_3 successfull")
                    else:
                        print("get_global_param_3 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
                name="aim_get_cur_date_3",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item",
                ),
                json={
                    "userId": "",
                    "marketId": 22,
                    "exactMatch": False,
                    "searchString": "",
                    "setType": "",
                    "node": None,
                    "userEID": self.user1EID,
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("get_cur_date_3 successfull")
                    else:
                        print("get_cur_date_3 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
                name="aim_load_AI_types_5",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item/view",
                ),
                json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("load_AI_types_5 successfull")
                    else:
                        print("load_AI_types_5 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            check_again = True
            while check_again:
                with self.client.post(
                    url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItemRequestStatus",
                    name="aim_get_ai_request_status",
                    headers=HeaderBuilder.generic_OOP_dcs(
                        config.endpoints.host,
                        self.accesstoken,
                        "action-item",
                    ),
                    json={
                        "requestIDs": [self.request_id],
                        "userBean": {"userEid": self.user1EID, "marketId": "22"},
                    },
                ) as response:
                    print(response)
                    try:
                        status = response.status_code
                        ai_status = response.json()[0]
                        print(ai_status)
                        if status == 200:
                            if (
                                (ai_status["requestID"] == self.request_id)
                                and ("actionItemStatus" in ai_status)
                                and (ai_status["actionItemStatus"] == "Delivered")
                                ):
                                print("get_ai_request_status successfull and delivered")
                                self.mii_AI_id = ai_status["actionItemID"]
                                ai_correct_and_delivered = True
                                check_again = False
                                continue
                            elif (ai_status["requestID"] == self.request_id) and (
                                (
                                    ("actionItemStatus" in ai_status)
                                    and (ai_status["actionItemStatus"] != "Delivered")
                                )
                            ):
                                print(
                                    "get_ai_request_status successfull but not yet delivered, checking again."
                                )
                                continue
                            elif (
                                (ai_status["requestID"] == self.request_id)
                                and (
                                    ("actionItemStatus" in ai_status)
                                    and (ai_status["actionItemStatus"] == "Failed")
                                )
                                or (
                                    (
                                        ("actionItemStatus" not in ai_status)
                                        and (ai_status["requestStatus"] == "Failed")
                                    )
                                )
                            ):
                                print(
                                    "get_ai_request_status successfull but action item creation failed, creating again with different menu items."
                                )
                                check_again = False
                                continue
                        else:
                            print("get_ai_request_status unsuccessfull", response.text)
                            self.interrupt()
                    except Exception as e:
                        print(e)
                        self.interrupt()

    @task
    def get_AIs_4(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
            name="aim_get_AIs_4",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={
                "recipientNodeSearch": "",
                "menuItemSearch": "",
                "userBean": {"userEid": self.user1EID, "marketId": "22"},
                "userData": {},
                "page": 1,
                "pageSize": 100,
                "includeTotalCount": True,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_AIs_4 successfull")
                    AI_list = response.json()["listActionItem"]
                    self.pta_AI_id = [
                        AI["actionItemId"]
                        for AI in AI_list
                        if AI["actionItemSubject"] == self.pta_AI
                    ][0]
                else:
                    print("get_AIs_4 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_global_param_4(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
            name="aim_get_global_param_4",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={
                "marketId": "22",
                "functionId": 0,
                "parameterName": "NO_CHAR_AUTO_SUGGESTION",
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_global_param_4 successfull")
                else:
                    print("get_global_param_4 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def view_AI(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/viewActionItem",
            name="aim_view_AI",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={
                "userBean": {"userEid": self.user1EID, "marketId": "22"},
                "userData": {},
                "actionItemId": self.pta_AI_id,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("view_AI successfull")
                    AI = response.json()["listActionItem"][0]

                    AI_rest_list = [
                        {
                            "child": rest["child"],
                            "parent": rest["parent"],
                            "restNu": rest["restNu"],
                            "restName": rest["restName"],
                        }
                        for rest in AI["restList"]
                    ].sort(key=operator.itemgetter("restNu"))
                    selected_rest_list = [
                        {
                            "child": rest["child"],
                            "parent": rest["parent"],
                            "restNu": int(rest["restNu"]),
                            "restName": rest["restName"],
                        }
                        for rest in self.selected_rests
                    ].sort(key=operator.itemgetter("restNu"))

                    if AI["actionItemSubject"] == self.pta_AI:
                        print("Action item subject retrieved is correct")

                    if AI_rest_list == selected_rest_list:
                        print("Action item restaurant list is correct")

                    self.pta_menuItemSet = AI["menuItemSet"]
                    self.pta_restNode = AI["restNode"]

                else:
                    print("view_AI unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def load_AI_types_6(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_6",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_6 successfull")
                else:
                    print("load_AI_types_6 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def load_AI_types_7(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_7",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_7 successfull")
                else:
                    print("load_AI_types_7 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_AIs_5(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
            name="aim_get_AIs_5",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={
                "recipientNodeSearch": "",
                "menuItemSearch": "",
                "userBean": {"userEid": self.user1EID, "marketId": "22"},
                "userData": {},
                "page": 1,
                "pageSize": 100,
                "includeTotalCount": True,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_AIs_5 successfull")
                else:
                    print("get_AIs_5 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_global_param_5(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
            name="aim_get_global_param_5",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={
                "marketId": "22",
                "functionId": 0,
                "parameterName": "NO_CHAR_AUTO_SUGGESTION",
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_global_param_5 successfull")
                else:
                    print("get_global_param_5 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_cur_date_4(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_get_cur_date_4",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={
                "userId": "",
                "marketId": 22,
                "exactMatch": False,
                "searchString": "",
                "setType": "",
                "node": None,
                "userEID": self.user1EID,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_cur_date_4 successfull")
                else:
                    print("get_cur_date_4 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def load_AI_types_8(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_8",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_8 successfull")
                else:
                    print("load_AI_types_8 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_AIs_6(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
            name="aim_get_AIs_6",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={
                "recipientNodeSearch": "",
                "menuItemSearch": "",
                "userBean": {"userEid": self.user1EID, "marketId": "22"},
                "userData": {},
                "page": 1,
                "pageSize": 100,
                "includeTotalCount": True,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_AIs_6 successfull")
                else:
                    print("get_AIs_6 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_global_param_6(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
            name="aim_get_global_param_6",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={
                "marketId": "22",
                "functionId": 0,
                "parameterName": "NO_CHAR_AUTO_SUGGESTION",
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_global_param_6 successfull")
                else:
                    print("get_global_param_6 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def load_AI_types_9(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_9",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_9 successfull")
                else:
                    print("load_AI_types_9 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_cur_date_5(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_get_cur_date_5",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={
                "userId": "",
                "marketId": 22,
                "exactMatch": False,
                "searchString": "",
                "setType": "",
                "node": None,
                "userEID": self.user1EID,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_cur_date_5 successfull")
                else:
                    print("get_cur_date_5 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def tree_generator_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getTreeGenerator",
            name="aim_tree_generator_2",
            allow_redirects=False,
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={
                "marketIdList": ["22"],
                "userId": self.user1EID,
                "localeLangID": "1",
                "moduleName": "USER",
                "searchString": None,
                "searchOption": None,
                "selectByID": None,
                "returnStatus": 0,
                "isSearchRequired": False,
                "id": self.userid,
            },
        ) as getTreeGenerator:
            try:
                status = getTreeGenerator.status_code
                if status == 200:
                    print("tree_generator_2 successfull")

                    loaded_tree = getTreeGenerator.json()

                    # extract list of stores of COOP of user 2 - self.user2COOP
                    all_stores = []
                    for local_group in loaded_tree["children"]:
                        if "children" in local_group and local_group["name"] == self.user2REGION:
                            for store in local_group["children"]:
                                all_stores.append(store)
                    self.selected_rests = random.choices(all_stores, k=3)

                    # selecting random restaurants
                    # self.selected_rests = random.choices(self.rest_list, k=3)

                else:
                    print("tree_generator_2 unsuccessfull", getTreeGenerator.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_mid_level_nodes_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getMidLevelNodesDetailsNew",
            name="aim_get_mid_level_nodes_2",
            allow_redirects=False,
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={
                "marketIdList": ["22"],
                "userId": self.user1EID,
                "localeLangID": "1",
                "moduleName": "USER",
                "searchString": None,
                "searchOption": None,
                "selectByID": None,
                "isSearchRequired": False,
            },
        ) as get_mid_level_nodes_2:
            try:
                status = get_mid_level_nodes_2.status_code
                if status == 200:
                    print("get_mid_level_nodes_2 successfull")
                else:
                    print("get_mid_level_nodes_2 unsuccessfull", get_mid_level_nodes_2.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_lookups_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getlookUps",
            name="aim_get_lookups_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={
                "userEid": self.user1EID,
                "marketId": "22",
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_lookups_2 successfull")
                else:
                    print("get_lookups_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_MI_list_count_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getMenuItemListCount",
            name="aim_get_MI_list_count_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/create",
            ),
            json={
                "status": [],
                "marketId": 22,
                "userEid": self.user1EID,
                "effectiveDate": get_date(0),
                "nodesIds": [self.selected_rests[0]["child"]],
                "exactMatch": False,
                "prd_ds": [],
                "prd_cd": [],
                "prodClassFilter": [],
                "nextRows": 1,
                "fetchRows": 100,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_MI_list_count_2 successfull")
                else:
                    print("get_MI_list_count_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def create_mii_AI(self):
        global ai_correct_and_delivered
        ai_correct_and_delivered = False
        while not ai_correct_and_delivered:
            search_MI_IDs = [str(i) for i in random.choices(self.approved_MIs, k=5)]
            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/getMenuItemListNoStatus",
                name="aim_get_MI_list_NS_2",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item/create",
                ),
                json={
                    "status": [],
                    "marketId": 22,
                    "userEid": self.user1EID,
                    "effectiveDate": get_date(0),
                    "exactMatch": True,
                    "prd_ds": search_MI_IDs,
                    # search for any 5 random MI Ids
                    "prd_cd": search_MI_IDs,
                    "prodClassFilter": [],
                    # node IDs of selected restaurants - self.selected_rests
                    "nodesIds": [int(store["child"]) for store in self.selected_rests],
                    "nextRows": 1,
                    "fetchRows": 100,
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("get_MI_list_NS_2 successfull")

                        self.selected_MIs = response.json()  # save the selected MI list

                    else:
                        print("get_MI_list_NS_2 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            self.mii_AI = f"test_mii_{random.randint(1000000, 9999999)}"

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/addActionItem",
                name="aim_add_action_item_2",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item/create",
                ),
                json={
                    "actionItemSubject": self.mii_AI,
                    "actionItemType": 2,  # MII action item
                    "menuItemValues": [
                        {
                            "productId": MI["productId"],
                            "productDescription": MI["productDS"],
                            "productCode": MI["productCode"],
                        }
                        for MI in self.selected_MIs
                    ],
                    "nodeIdValues": [
                        {
                            "restaurantNumber": int(store["restNu"]),
                            "restName": store["restName"],
                            "restaurantNodeId": store["child"],
                            "parentNodeId": store["parent"],
                        }
                        for store in self.selected_rests
                    ],
                    "sendDate": get_date_slash(0),
                    "userBean": {"marketId": "22", "userEid": self.user1EID},
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("add_action_item_2 successfull")
                        self.request_id = response.json()["actionItemResponse"][
                            "actionItemRequestId"
                        ]
                    else:
                        print("add_action_item_2 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
                name="aim_load_AI_types_10",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item",
                ),
                json={
                    "userEid": self.user1EID,
                    "marketId": "22",
                    "localeLangId": "60",
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("load_AI_types_10 successfull")
                    else:
                        print("load_AI_types_10 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
                name="aim_get_AIs_7",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item",
                ),
                json={
                    "recipientNodeSearch": "",
                    "menuItemSearch": "",
                    "userBean": {"userEid": self.user1EID, "marketId": "22"},
                    "userData": {},
                    "page": 1,
                    "pageSize": 100,
                    "includeTotalCount": True,
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("get_AIs_7 successfull")
                    else:
                        print("get_AIs_7 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
                name="aim_get_global_param_7",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item",
                ),
                json={
                    "marketId": "22",
                    "functionId": 0,
                    "parameterName": "NO_CHAR_AUTO_SUGGESTION",
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("get_global_param_7 successfull")
                    else:
                        print("get_global_param_7 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            with self.client.post(
                url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
                name="aim_get_cur_date_6",
                headers=HeaderBuilder.generic_OOP_dcs(
                    config.endpoints.host,
                    self.accesstoken,
                    "action-item",
                ),
                json={
                    "userId": "",
                    "marketId": 22,
                    "exactMatch": False,
                    "searchString": "",
                    "setType": "",
                    "node": None,
                    "userEID": self.user1EID,
                },
            ) as response:
                try:
                    status = response.status_code
                    if status == 200:
                        print("get_cur_date_6 successfull")
                    else:
                        print("get_cur_date_6 unsuccessfull", response.text)
                        self.interrupt()
                except Exception as e:
                    print(e)
                    self.interrupt()

            check_again = True
            while check_again:
                with self.client.post(
                    url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItemRequestStatus",
                    name="aim_get_ai_request_status_2",
                    headers=HeaderBuilder.generic_OOP_dcs(
                        config.endpoints.host,
                        self.accesstoken,
                        "action-item",
                    ),
                    json={
                        "requestIDs": [self.request_id],
                        "userBean": {"userEid": self.user1EID, "marketId": "22"},
                    },
                ) as response:
                    try:
                        status = response.status_code
                        ai_status = response.json()[0]
                        if status == 200:
                            if (
                                (ai_status["requestID"] == self.request_id)
                                and ("actionItemStatus" in ai_status)
                                and (ai_status["actionItemStatus"] == "Delivered")
                            ):
                                print("get_ai_request_status successfull and delivered")
                                self.mii_AI_id = ai_status["actionItemID"]
                                ai_correct_and_delivered = True
                                check_again = False
                                continue
                            elif (ai_status["requestID"] == self.request_id) and (
                                (
                                    ("actionItemStatus" in ai_status)
                                    and (ai_status["actionItemStatus"] != "Delivered")
                                )
                            ):
                                print(
                                    "get_ai_request_status successfull but not yet delivered, checking again."
                                )
                                continue
                            elif (
                                (ai_status["requestID"] == self.request_id)
                                and (
                                    ("actionItemStatus" in ai_status)
                                    and (ai_status["actionItemStatus"] == "Failed")
                                )
                                or (
                                    (
                                        ("actionItemStatus" not in ai_status)
                                        and (ai_status["requestStatus"] == "Failed")
                                    )
                                )
                            ):
                                print(
                                    "get_ai_request_status successfull but action item creation failed, creating again with different menu items."
                                )
                                check_again = False
                                continue
                        else:
                            print("get_ai_request_status unsuccessfull", response.text)
                            self.interrupt()
                    except Exception as e:
                        print(e)
                        self.interrupt()

    @task
    def load_AI_types_11(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_11",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_11 successfull")
                else:
                    print("load_AI_types_11 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_AIs_8(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
            name="aim_get_AIs_8",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={
                "recipientNodeSearch": "",
                "menuItemSearch": "",
                "userBean": {"userEid": self.user1EID, "marketId": "22"},
                "userData": {},
                "page": 1,
                "pageSize": 100,
                "includeTotalCount": True,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_AIs_8 successfull")
                else:
                    print("get_AIs_8 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_global_param_8(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
            name="aim_get_global_param_8",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={
                "marketId": "22",
                "functionId": 0,
                "parameterName": "NO_CHAR_AUTO_SUGGESTION",
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_global_param_8 successfull")
                else:
                    print("get_global_param_8 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def view_AI_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/viewActionItem",
            name="aim_view_AI_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={
                "userBean": {"userEid": self.user1EID, "marketId": "22"},
                "userData": {},
                "actionItemId": self.mii_AI_id,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("view_AI_2 successfull")
                    AI = response.json()["listActionItem"][0]

                    AI_MI_list = [
                        {
                            "productDesc": MI["productDesc"],
                            "productId": MI["productId"],
                            "productCode": MI["productCode"],
                        }
                        for MI in AI["menuItemSet"]
                    ].sort(key=operator.itemgetter("productCode"))
                    selected_MI_list = [
                        {
                            "productDesc": MI["productDS"],
                            "productId": MI["productId"],
                            "productCode": MI["productCode"],
                        }
                        for MI in self.selected_MIs
                    ].sort(key=operator.itemgetter("productCode"))

                    AI_rest_list = [
                        {
                            "child": rest["child"],
                            "parent": rest["parent"],
                            "restNu": rest["restNu"],
                            "restName": rest["restName"],
                        }
                        for rest in AI["restList"]
                    ].sort(key=operator.itemgetter("restNu"))
                    selected_rest_list = [
                        {
                            "child": rest["child"],
                            "parent": rest["parent"],
                            "restNu": int(rest["restNu"]),
                            "restName": rest["restName"],
                        }
                        for rest in self.selected_rests
                    ].sort(key=operator.itemgetter("restNu"))

                    if AI["actionItemSubject"] == self.mii_AI:
                        print("MII action item subject retrieved is correct")
                    if AI_MI_list == selected_MI_list:
                        print("MII action item menu item list is correct")
                    if AI_rest_list == selected_rest_list:
                        print("MII action item restaurant list is correct")

                    self.mii_menuItemSet = AI["menuItemSet"]
                    self.mii_restNode = AI["restNode"]

                else:
                    print("view_AI_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def load_AI_types_12(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_12",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item/view",
            ),
            json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_12 successfull")
                else:
                    print("load_AI_types_12 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def load_AI_types_13(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_load_AI_types_13",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={"userEid": self.user1EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("load_AI_types_13 successfull")
                else:
                    print("load_AI_types_13 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_AIs_9(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItems",
            name="aim_get_AIs_9",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={
                "recipientNodeSearch": "",
                "menuItemSearch": "",
                "userBean": {"userEid": self.user1EID, "marketId": "22"},
                "userData": {},
                "page": 1,
                "pageSize": 100,
                "includeTotalCount": True,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_AIs_9 successfull")
                else:
                    print("get_AIs_9 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_global_param_9(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getGlobalParam",
            name="aim_get_global_param_9",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={
                "marketId": "22",
                "functionId": 0,
                "parameterName": "NO_CHAR_AUTO_SUGGESTION",
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_global_param_9 successfull")
                else:
                    print("get_global_param_9 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def get_cur_date_7(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_get_cur_date_7",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "action-item",
            ),
            json={
                "userId": "",
                "marketId": 22,
                "exactMatch": False,
                "searchString": "",
                "setType": "",
                "node": None,
                "userEID": self.user1EID,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("get_cur_date_7 successfull")
                else:
                    print("get_cur_date_7 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    ####### logout user 1 #########

    @task
    def user1_OOP_nav_home(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/topMenu.action?param=HOME&token=/rfm2OnlineApp/logout.action",
            name="aim_user1_OOP_nav_home",
            headers=HeaderBuilder.OOP_nav_home_dcs(config.endpoints.host),
            catch_response=True,
        ) as OOP_nav_home_response:
            try:
                OOP_nav_home_status = OOP_nav_home_response.status_code
                if OOP_nav_home_status == 200:
                    print("OOP_nav_home is successful")

                else:
                    print("OOP_nav_home is unsuccessful", OOP_nav_home_response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user1_OOP_logout(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/logout.action",
            name="aim_user1_OOP_logout",
            headers=HeaderBuilder.OOP_logout_dcs(config.endpoints.host),
            catch_response=True,
        ) as OOP_logout_response:
            try:
                OOP_logout_status = OOP_logout_response.status_code
                if OOP_logout_status == 200:
                    print("OOP_logout is successful")

                else:
                    print("OOP_logout is unsuccessful", OOP_logout_response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user1_OOP_logout2(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/logout.action",
            name="aim_user1_OOP_logout2",
            headers=HeaderBuilder.OOP_logout_dcs(config.endpoints.host),
            catch_response=True,
        ) as OOP_logout2_response:
            try:
                OOP_logout2_status = OOP_logout2_response.status_code
                if OOP_logout2_status == 200:
                    print("OOP_logout2 is successful")
                    self.client.cookies.clear()
                    self.client.close()
                else:
                    print("OOP_logout2 is unsuccessful", OOP_logout2_response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    ######## Login with User 2 #######

        
    @task
    def user2_SamlToken(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/rfmLogin.action",
            name="actionitemmanagement_user2_Launch_SamlToken",
            headers=HeaderBuilder.launch_dcs(),
            catch_response=True,
        ) as Launch:
            try:
                status1 = Launch.status_code
                if status1 == 200:
                    print("Launch is successfull")

                    SAMLRequest = re.findall(
                        r"&SAMLRequest=([^&]+)&RelayState=", Launch.text
                    )
                    self.SAMLRequest = random.choice(SAMLRequest)
                else:
                    print("Launch is unsuccessfull", Launch.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_launch1(self):
        with self.client.get(
            f"{config.endpoints.hostr}/adfs/ls/?binding=urn%3Aoasis%3Anames%3Atc%3ASAML%3A2.0%3Abindings%3AHTTP-Redirect&SAMLRequest="
            + self.SAMLRequest
            + "&RelayState=",
            name="actionitemmanagement_user2_Launch_redirect1",
            headers=HeaderBuilder.launch_dcs(),
            catch_response=True,
        ) as Launch1:
            try:
                status2 = Launch1.status_code
                if status2 == 200:
                    print("Launch redirect 1 is successfull")
                else:
                    print("Launch redirect 1 is unsuccessfull", Launch1.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_launch2(self):
        with self.client.get(
            f"{config.endpoints.hostr}/api/Account/Login?returnUrl=https%3A%2F%2Fgasstg.mcd.com%2Fadfs%2Fls%2F%3Fbinding%3Durn%253Aoasis%253Anames%253Atc%253ASAML%253A2.0%253Abindings%253AHTTP-Redirect&SAMLRequest={self.SAMLRequest}&RelayState=",
            name="actionitemmanagement_user2_Launch_redirect2",
            headers=HeaderBuilder.launch1_dcs(self.SAMLRequest),
            catch_response=True,
        ) as Launch2:
            try:
                status3 = Launch2.status_code
                if status3 == 200:
                    print("Launch redirect 2 is successfull")
                    RequestVerificationToken = re.findall(
                        r'(?<=<input name="__RequestVerificationToken" type="hidden" value=").*?(?=" />)',
                        Launch2.text,
                    )
                    self.RequestVerificationToken = random.choice(
                        RequestVerificationToken
                    )
                else:
                    print("Launch redirect 2 is unsuccessfull", Launch2.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_login2(self):
        with self.client.post(
            f"{config.endpoints.hostr}/api/Account/AzureLoginCheck",
            name="actionitemmanagement_user2_Azure_Login",
            headers=HeaderBuilder.login_dcs(self.SAMLRequest),
            data=[(b"Username", self.user2EID)],
            catch_response=True,
        ) as login2:
            try:
                status6 = login2.status_code
                if status6 == 200:
                    print("Login 3 was successfull")
                else:
                    print("Login 3 failed ", login2.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_login3(self):
        with self.client.post(
            f"{config.endpoints.hostr}/api/Account/Login",
            name="actionitemmanagement_user2_Account_Login",
            headers=HeaderBuilder.login1_dcs(
                self.SAMLRequest, self.RequestVerificationToken
            ),
            data=[
                (b"Username", self.user2EID),
                (b"Password", b"Bigmac00"),
                (
                    b"postUrl",
                    b"https://gasstg.mcd.com/adfs/ls/?binding=urn%3Aoasis%3Anames%3Atc%3ASAML%3A2.0%3Abindings%3AHTTP-Redirect&SAMLRequest= + self.SAMLRequest +&RelayState=",
                ),
                (b"kmsi", b"false"),
                (b"userType", b"Corporate"),
            ],
            catch_response=True,
        ) as login3:
            try:
                status7 = login3.status_code
                if status7 == 200:
                    print("Login 4 was successfull")
                else:
                    print("Login 4 failed ", login3.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_login4(self):
        with self.client.post(
            f"{config.endpoints.hostr}/adfs/ls/?binding=urn%3Aoasis%3Anames%3Atc%3ASAML%3A2.0%3Abindings%3AHTTP-Redirect&SAMLRequest={self.SAMLRequest}&RedirectToIdentityProvider=AD+AUTHORITY",
            name="actionitemmanagement_user2_login_4",
            headers=HeaderBuilder.login2_dcs(self.SAMLRequest),
            data=[
                ("__RequestVerificationToken", self.RequestVerificationToken),
                (b"AuthMethod", b"FormsAuthentication"),
                (b"HomeRealmSelection", b"AD AUTHORITY"),
                (b"UserName", f"LABNARESTMGMT\{self.user2EID}"),
                (b"Password", b"Bigmac00"),
                (b"btnSubmit", b"Login"),
            ],
            catch_response=True,
        ) as login4:
            try:
                status8 = login4.status_code
                if status8 == 200:
                    print("Login 5 was successfull")
                    SAMLToken2 = re.findall(
                        r'(?<=<input type="hidden" name="SAMLResponse" value=").*?(?=" />)',
                        login4.text,
                    )
                    self.SAMLToken2 = random.choice(SAMLToken2)
                else:
                    print("Login 5 failed ", login4.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_login6(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/rfmLogin.action",
            name="actionitemmanagement_user2_Login_6",
            data=[("SAMLResponse", self.SAMLToken2)],
            headers=HeaderBuilder.login4_dcs(),
            catch_response=True,
        ) as Login6:
            try:
                status10 = Login6.status_code
                if status10 == 200:
                    print("Login 6 is successfull")
                    token1 = re.findall(
                        r"<input type=\"hidden\" name=\"token\" value=\'(.*?)\' >", Login6.text)
                    self.token1 = random.choice(token1)
                    self.userid = re.findall(r"var userId=\"userId=([^&]+)\";\n\tvar firstName=", Login6.text)[0]
                    print(self.token1)
                    print("User ID:", self.userid)

                else:
                    print("Login 6 is unsuccessfull", Login6.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_login7(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/persistLang.action?request_locale=en_US&token={self.token1}",
            name="actionitemmanagement_user2_Login_6",
            headers=HeaderBuilder.login5_dcs(config.endpoints.host),
            catch_response=True,
        ) as Login7:
            try:
                status11 = Login7.status_code
                if status11 == 200:
                    print("Login 7 is successfull")

                else:
                    print("Login 7 is unsuccessfull", Login7.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_login8(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/openHierarchy.action?token={self.token1}",
            name="actionitemmanagement_user2_Login_7",
            headers=HeaderBuilder.login6_dcs(config.endpoints.host),
            catch_response=True,
        ) as Login8:
            try:
                status12 = Login8.status_code
                if status12 == 200:
                    print("Login 8 is successfull")

                else:
                    print("Login 8 is unsuccessfull", Login8.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_select_market_1(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/rfmLogin.action",
            name="actionitemmanagement_user2_select market 1",
            data=[
                ("token", self.token1),
                (b"isSaveAsCSV", b""),
                (b"refreshRandomNumber", b"0.3444336993420203"),
                (b"refreshRandomNumber", b"0.3444336993420203"),
                (b"mktName", b"US Country Office"),
                (b"marketId", b"2"),
                (b"node_id", b"2"),
                (b"node_name", b"UK"),
                (b"selectedLanguage", b"en_US"),
                (b"closePOPUP", b"TRUE"),
                (b"defaultLang", b"TRUE"),
                (b"request_locale", b" en_US"),
                (b"helpFunctionId", b"2000"),
            ],
            headers=HeaderBuilder.market1_dcs(config.endpoints.host),
            catch_response=True,
        ) as Select_market:
            try:
                status13 = Select_market.status_code
                if status13 == 200:
                    print("select market 1 is successfull")

                else:
                    print("select market 1 is Unsuccessfull", Select_market.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_market_2(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/persistLang.action?request_locale=en_US&token={self.token1}",
            name="actionitemmanagement_user2_Select Market 2",
            headers=HeaderBuilder.login5_dcs(config.endpoints.host),
            catch_response=True,
        ) as Market_2:
            try:
                status14 = Market_2.status_code
                if status14 == 200:
                    print("Select market 2 is successfull")

                else:
                    print("Select market 2 is unsuccessfull", Market_2.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    ####################### LEGACY LOGIN DONE for user2 ##########################

    @task
    def user2_NavigatetoRFMPORTAL(self):
        split_number = self.token1[:13]
        self.userToken = self.user2EID + split_number
        print(self.userToken)
        with self.client.get(
            f"{config.endpoints.host}/owner-operator-homepage;localeLangDesc=English;layeringLogicType=1;marketId=22;selectedLanguage=en_UK;selectedDateFormat=MMM%20d,%20yyyy;localeLangID=60;rfmRefreshPage={config.endpoints.host}owner-operator-homepage;ptaURL={config.endpoints.host};marketName=UK;userEid={self.user2EID};userToken={self.userToken};timeZone=Etc/GMT;isSessionStorage=true;accessToken={self.accesstoken};isGlobalUser=1;userId=258719;firstName=Test;lastName=User28;isRest=notR;token={self.token1}",
            name="actionitemmanagement_user2_Navigate to Restaurant portal",
            headers=HeaderBuilder.NavigatetoRFMPortal_dcs(
                config.endpoints.host),
            catch_response=True,
        ) as Navigatetorfmportal:
            try:
                status15 = Navigatetorfmportal.status_code
                if status15 == 200:
                    print("Navigate to RFM Portal successfull")

                else:
                    print(
                        "Navigate to RFM Portal unsuccessfull", Navigatetorfmportal.text
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def APILogin(self):
        split_number = self.token1[:13]
        self.userToken = self.user2EID + split_number
        with self.client.post(
            f"{config.endpoints.host}/rfmRefreshApp/api/login",
            name="actionitemmanagement_user2_APILogin",
            json={
                "userEid": self.user2EID,
                "marketId": "22",
                "selectedLanguage": "en_UK",
                "userToken": self.userToken,
                "isRest": "notR",
            },
            headers=HeaderBuilder.APILogin_dcs(
                config.endpoints.host,
                self.user2EID,
                self.userToken,
                self.accesstoken,
                self.token1,
            ),
            catch_response=True,
        ) as APILogin:
            try:
                status16 = APILogin.status_code
                if status16 == 200:
                    print("API Login successfull")

                else:
                    print("API Login unsuccessfull", APILogin.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    ######### OOP LOGIN DONE for User2 ###########


    @task
    def user2_getValueFromGlobalParam(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getValueFromGlobalParam",
            name="actionitemmanagement_user2_getValueFromGlobalParam",
            allow_redirects=False,
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                f"{config.endpoints.host}/owner-operator-homepage;localeLangDesc=English;layeringLogicType=1;marketId=22;selectedLanguage=en_UK;selectedDateFormat=MMM%20d,%20yyyy;localeLangID=60;rfmRefreshPage={config.endpoints.host}owner-operator-homepage;ptaURL={config.endpoints.host};marketName=UK;userEid={self.user2EID};userToken={self.userToken};timeZone=Etc/GMT;isSessionStorage=true;accessToken={self.accesstoken};isGlobalUser=1;userId={self.userid};firstName=Test;lastName=User28;isRest=notR;token={self.token1}",
            ),
            json={"marketId": "22", "paramName": "ENABLE_WALKME"},
        ) as global_params:
            try:
                status = global_params.status_code
                if status == 200:
                    print("getValueFromGlobalParam successfull")
                else:
                    print("getValueFromGlobalParam unsuccessfull",
                          global_params.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_homepage(self):
        with self.client.get(
            url=f"{config.endpoints.host}/owner-operator-homepage",
            name="actionitemmanagement_user2_homepage",
            allow_redirects=False,
            headers=HeaderBuilder.homepage_dcs(config.endpoints.host),
        ) as homepage:
            try:
                status = homepage.status_code
                if status == 200:
                    print("homepage successfull")
                else:
                    print("homepage unsuccessfull", homepage.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_APILogin1(self):
        split_number = self.token1[:13]
        self.userToken = self.user1EID + split_number
        with self.client.post(
            f"{config.endpoints.host}/rfmRefreshApp/api/login",
            name="actionitemmanagement_user2_APILogin1",
            json={
                "userEid": self.user2EID,
                "marketId": "22",
                "selectedLanguage": "en_UK",
                "userToken": self.userToken,
                "isRest": "notR",
            },
            headers=HeaderBuilder.APILogin_dcs(
                config.endpoints.host,
                self.user2EID,
                self.userToken,
                self.accesstoken,
                self.token1,
            ),
            catch_response=True,
        ) as APILogin1:
            try:
                status16 = APILogin1.status_code
                if status16 == 200:
                    print("API Login 1 successfull")

                else:
                    print("API Login 1 unsuccessfull", APILogin1.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_getValueFromGlobalParam1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getValueFromGlobalParam",
            name="actionitemmanagement_user2_getValueFromGlobalParam1",
            allow_redirects=False,
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                f"{config.endpoints.host}/owner-operator-homepage;localeLangDesc=English;layeringLogicType=1;marketId=22;selectedLanguage=en_UK;selectedDateFormat=MMM%20d,%20yyyy;localeLangID=60;rfmRefreshPage={config.endpoints.host}owner-operator-homepage;ptaURL={config.endpoints.host};marketName=UK;userEid={self.user2EID};userToken={self.userToken};timeZone=Etc/GMT;isSessionStorage=true;accessToken={self.accesstoken};isGlobalUser=1;userId=258665;firstName=Test;lastName=User28;isRest=notR;token={self.token1}",
            ),
            json={"marketId": "22", "paramName": "ENABLE_WALKME"},
        ) as global_params1:
            try:
                status = global_params1.status_code
                if status == 200:
                    print("getValueFromGlobalParam1 successfull")
                else:
                    print("getValueFromGlobalParam1 unsuccessfull",
                          global_params1.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_notification_count(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/notificationCounts",
            name="actionitemmanagement_user2_notification_count",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "/owner-operator-homepage",
            ),
            json={
                "permissionMap": [
                    "REFRESH_OWNER_OPERATOR_HOMEPAGE_MESSAGES"
                ],
                "userBean": {
                    "userEid": self.user2EID,
                    "marketId": "22",
                    "localeLangID": "60",
                    "userToken": self.userToken,
                    "isRest": "notR",
                    "selectedLanguage": "en_UK",
                },
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("notification_count successfull")
                else:
                    print("notification_count unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_notification_count1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/notificationCounts",
            name="actionitemmanagement_user2_notification_count1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "/owner-operator-homepage",
            ),
            json={
                'permissionMap': ['REFRESH_OWNER_OPERATOR_HOMEPAGE_MESSAGES',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_PRICE_TAX_AND_ACTIVATE',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_POS_LAYOUT',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_REPORTS',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_PACKAGE_GENERATION,REFRESH_PACKAGE_GENERATION_GENERATE_NOW',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_MENU_ITEM_INACTIVATION',
                                  'REFRESH_OWNER_OPERATOR_HOMEPAGE_MESSAGES', 'REFRESH_OWNER_OPERATOR_MASS_MI_DELETE'],
                'userBean': {'userEid': self.user2EID, 'marketId': '22', 'localeLangID': '60',
                             'userToken': self.userToken, 'isRest': 'notR', 'selectedLanguage': 'en_UK'}},
        ) as notification_count1:
            try:
                status = notification_count1.status_code
                if status == 200:
                    print("notification_count1 successfull")
                else:
                    print("notification_count1 unsuccessfull",
                          notification_count1.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()
############ NOTIFICATION PART ENDS HERE for User2 #########################

    @task
    def user2_get_cur_date_1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_user2_get_cur_date_1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "owneroperatorview/ptaView",
            ),
            json={
                "userId": "",
                "marketId": 22,
                "exactMatch": False,
                "searchString": "",
                "setType": "",
                "node": None,
                "userEID": self.user2EID,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("user2_get_cur_date_1 successfull")
                else:
                    print("user2_get_cur_date_1 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_load_AI_types_1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_user2_load_AI_types_1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "owneroperatorview/ptaView",
            ),
            json={"userEid": self.user2EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("user2_load_AI_types_1 successfull")
                else:
                    print("user2_load_AI_types_1 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_get_cur_date_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_user2_get_cur_date_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "owneroperatorview/ptaView",
            ),
            json={
                "userId": "",
                "marketId": 22,
                "exactMatch": False,
                "searchString": "",
                "setType": "",
                "node": None,
                "userEID": self.user2EID,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("user2_get_cur_date_2 successfull")
                else:
                    print("user2_get_cur_date_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_get_AIs_by_userId_1(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItemsByUserId",
            name="aim_user2_get_AIs_by_userId_1",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "owneroperatorview/ptaView",
            ),
            json={
                "actionItemType": "1",
                "userBean": {"marketId": "22", "userEid": self.user2EID},
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("user2_get_AIs_by_userId_1 successfull")
                    AI_list = response.json()["actionItemByUserIdResponseVOList"]
                    required_AI = [
                        AI for AI in AI_list if AI["actionItemId"] == self.pta_AI_id
                    ]

                    if self.pta_menuItemSet.sort(
                        key=operator.itemgetter("productCode")
                    ) == required_AI[0]["menuItemSet"].sort(
                        key=operator.itemgetter("productCode")
                    ):
                        print("Menu Items retrieved are correct as created.")
                    if self.pta_restNode.sort(
                        key=operator.itemgetter("restNumber")
                    ) == required_AI[0]["restNode"].sort(
                        key=operator.itemgetter("restNumber")
                    ):
                        print("Menu Items retrieved are correct as created.")
                else:
                    print("user2_get_AIs_by_userId_1 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_get_cur_date_3(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_user2_get_cur_date_3",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "owneroperatorview/miiView",
            ),
            json={
                "userId": "",
                "marketId": 22,
                "exactMatch": False,
                "searchString": "",
                "setType": "",
                "node": None,
                "userEID": self.user2EID,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("user2_get_cur_date_3 successfull")
                else:
                    print("user2_get_cur_date_3 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_load_AI_types_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/loadActionItemTypeLookup",
            name="aim_user2_load_AI_types_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "owneroperatorview/miiView",
            ),
            json={"userEid": self.user2EID, "marketId": "22", "localeLangId": "60"},
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("user2_load_AI_types_2 successfull")
                else:
                    print("user2_load_AI_types_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_get_cur_date_4(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getCurrentDateFromUser",
            name="aim_user2_get_cur_date_4",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "owneroperatorview/miiView",
            ),
            json={
                "userId": "",
                "marketId": 22,
                "exactMatch": False,
                "searchString": "",
                "setType": "",
                "node": None,
                "userEID": self.user2EID,
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("user2_get_cur_date_4 successfull")
                else:
                    print("user2_get_cur_date_4 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def user2_get_AIs_by_userId_2(self):
        with self.client.post(
            url=f"{config.endpoints.host}/rfmRefreshApp/api/getActionItemsByUserId",
            name="aim_user2_get_AIs_by_userId_2",
            headers=HeaderBuilder.generic_OOP_dcs(
                config.endpoints.host,
                self.accesstoken,
                "owneroperatorview/ptaView",
            ),
            json={
                "actionItemType": "2",
                "userBean": {"marketId": "22", "userEid": self.user2EID},
            },
        ) as response:
            try:
                status = response.status_code
                if status == 200:
                    print("user2_get_AIs_by_userId_2 successfull")
                    AI_list = response.json()["actionItemByUserIdResponseVOList"]
                    required_AI = [
                        AI for AI in AI_list if AI["actionItemId"] == self.mii_AI_id
                    ]
                    if self.mii_menuItemSet.sort(
                        key=operator.itemgetter("productCode")
                    ) == required_AI[0]["menuItemSet"].sort(
                        key=operator.itemgetter("productCode")
                    ):
                        print("Menu Items retrieved are correct as created.")
                    if self.mii_restNode.sort(
                        key=operator.itemgetter("restNumber")
                    ) == required_AI[0]["restNode"].sort(
                        key=operator.itemgetter("restNumber")
                    ):
                        print("Menu Items retrieved are correct as created.")
                else:
                    print("user2_get_AIs_by_userId_2 unsuccessfull", response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    ######### OOP Navigate to home and logout ########

    @task
    def OOP_nav_home(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/topMenu.action?param=HOME&token=/rfm2OnlineApp/logout.action",
            name="aim_OOP_nav_home",
            headers=HeaderBuilder.OOP_nav_home_dcs(config.endpoints.host),
            catch_response=True,
        ) as OOP_nav_home_response:
            try:
                OOP_nav_home_status = OOP_nav_home_response.status_code
                if OOP_nav_home_status == 200:
                    print("OOP_nav_home is successful")

                else:
                    print("OOP_nav_home is unsuccessful", OOP_nav_home_response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def OOP_logout(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/logout.action",
            name="aim_OOP_logout",
            headers=HeaderBuilder.OOP_logout_dcs(config.endpoints.host),
            catch_response=True,
        ) as OOP_logout_response:
            try:
                OOP_logout_status = OOP_logout_response.status_code
                if OOP_logout_status == 200:
                    print("OOP_logout is successful")

                else:
                    print("OOP_logout is unsuccessful", OOP_logout_response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def OOP_logout2(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/logout.action",
            name="aim_OOP_logout2",
            headers=HeaderBuilder.OOP_logout_dcs(config.endpoints.host),
            catch_response=True,
        ) as OOP_logout2_response:
            try:
                OOP_logout2_status = OOP_logout2_response.status_code
                if OOP_logout2_status == 200:
                    print("OOP_logout2 is successful")

                else:
                    print("OOP_logout2 is unsuccessful", OOP_logout2_response.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()



# ## Logout Part
#     @task
#     def OOP_logout(self):
#         with self.client.get(
#             f"{config.endpoints.host}/rfm2OnlineApp/logout.action",
#             name="actionitemmanagement_OOP_logout",
#             headers=HeaderBuilder.OOP_logout_dcs(config.endpoints.host),
#             catch_response=True,
#         ) as OOP_logout_response:
#             try:
#                 OOP_logout_status = OOP_logout_response.status_code
#                 if OOP_logout_status == 200:
#                     print("OOP_logout is successful")

#                 else:
#                     print("OOP_logout is unsuccessful",
#                           OOP_logout_response.text)
#                     self.interrupt()
#             except Exception as e:
#                 print(e)
#                 self.interrupt()

#     @task
#     def OOP_logout2(self):
#         with self.client.get(
#             f"{config.endpoints.host}/rfm2OnlineApp/logout.action",
#             name="actionitemmanagement_OOP_logout2",
#             headers=HeaderBuilder.OOP_logout_dcs(config.endpoints.host),
#             catch_response=True,
#         ) as OOP_logout2_response:
#             try:
#                 OOP_logout2_status = OOP_logout2_response.status_code
#                 if OOP_logout2_status == 200:
#                     print("OOP_logout2 is successful")

#                 else:
#                     print("OOP_logout2 is unsuccessful",
#                           OOP_logout2_response.text)
#                     self.interrupt()
#             except Exception as e:
#                 print(e)
#                 self.interrupt()

class UpdateProfile(HttpUser):
    tasks = [Profile]
    # wait_time = constant(2)

    host = "http://localhost"

    weight = config.features.ACTIONITEMMANAGEMENT.weight

    FastHttpUser.connection_timeout = config.time_out
    FastHttpUser.network_timeout = config.time_out
    if len(config.wait_time) > 1:
        wait_time = between(config.wait_time[0], config.wait_time[1])
    else:
        wait_time = constant(config.wait_time[0])



@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    prommodule.on_stop(environment, **kwargs)


# if launched directly, e.g. "python3 debugging.py", not "locust -f debugging.py"
if __name__ == "__main__":
    run_single_user(UpdateProfile)
