import csv
import time
import os
import random
import re
import string
import sys
import tempfile
import uuid
from locust import (
    SequentialTaskSet,
    HttpUser,
    between,
    task,
    constant,
    events,
    FastHttpUser,
)

from tests.builders.promotionmanagement_header import HeaderBuilder
import tests.common.prommodule as prommodule
from tests.common.configservice import get_user, config, MarketParams


promotion_name = "".join(random.choices(string.ascii_letters + string.digits, k=8))

promotion_code = str(random.randint(1, 1000000))

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
        self.token1 = ""

    @task
    def SamlToken(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/rfmLogin.action",
            name="promotionmanagement_Launch_SamlToken",
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
            name="promotionmanagement_Launch_redirect1",
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
            name="promotionmanagement_Launch_redirect2",
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
            name="promotionmanagement_Azure_Login",
            headers=HeaderBuilder.login_dcs(self.SAMLRequest),
            params=[(b"Username", b"e7130038")],
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

    #
    @task
    def login3(self):
        with self.client.post(
            f"{config.endpoints.hostr}/api/Account/Login",
            name="promotionmanagement_Account_Login",
            headers=HeaderBuilder.login1_dcs(
                self.SAMLRequest, self.RequestVerificationToken
            ),
            params=[
                (b"Username", b"e7130038"),
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
            name="promotionmanagement_login_4",
            headers=HeaderBuilder.login2_dcs(self.SAMLRequest),
            data=[
                ("__RequestVerificationToken", self.RequestVerificationToken),
                (b"AuthMethod", b"FormsAuthentication"),
                (b"HomeRealmSelection", b"AD AUTHORITY"),
                (b"UserName", b"LABNARESTMGMT\\e7130038"),
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
            name="promotionmanagement_Login_6",
            data=[("SAMLResponse", self.SAMLToken2)],
            headers=HeaderBuilder.login4_dcs(),
            catch_response=True,
        ) as Login6:
            try:
                status10 = Login6.status_code
                if status10 == 200:
                    print("Login 6 is successfull")
                    token1 = re.findall(
                        r"<input type=\"hidden\" name=\"token\" value=\'(.*?)\' >",
                        Login6.text,
                    )
                    self.token1 = random.choice(token1)
                    print(self.token1)
                else:
                    print("Login 6 is unsuccessfull", Login6.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def login7(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/persistLang.action?request_locale=de_AT&token={self.token1}",
            name="promotionmanagement_Login_6",
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
            name="promotionmanagement_Login_7",
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
            name="promotionmanagement_select market 1",
            data=[
                ("token", self.token1),
                (b"isSaveAsCSV", b""),
                (b"refreshRandomNumber", b"0.9292607922522051"),
                (b"refreshRandomNumber", b"0.9292607922522051"),
                (b"mktName", b"Austria"),
                (b"marketId", b"22"),
                (b"node_id", b"1483"),
                (b"node_name", b"UK"),
                (b"selectedLanguage", b"de_AT"),
                (b"closePOPUP", b"TRUE"),
                (b"defaultLang", b"TRUE"),
                (b"request_locale", b" en_UK"),
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
            f"{config.endpoints.host}/rfm2OnlineApp/persistLang.action?request_locale=en_UK&token={self.token1}",
            name="promotionmanagement_Select Market 2",
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

    @task
    def NavigatetoPromotionManagement(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/promotionSearch_loadPromotionSearch.action",
            name="promotion_management_Navigate to Promotion Management",
            data=[
                (b"token", self.token1),
                (b"isSaveAsCSV", b""),
                (b"refreshRandomNumber", b"0.16696773750319993"),
                (b"refreshRandomNumber", b"0.16696773750319993"),
                (b"mktName", b"UK"),
                (b"marketId", b"22"),
                (b"node_id", b"1483"),
                (b"node_name", b"UK"),
                (b"selectedLanguage", b"en_UK"),
                (b"closePOPUP", b"FALSE"),
                (b"defaultLang", b"FALSE"),
                (b"request_locale", b"en_UK"),
                (b"helpFunctionId", b"3021"),
            ],
            headers=HeaderBuilder.NavigatetoPromotionManagement_dcs(
                config.endpoints.host
            ),
            catch_response=True,
        ) as NavigatetoPromotionManagement:
            try:
                status15 = NavigatetoPromotionManagement.status_code
                if status15 == 200:
                    print("Navigate to Promotion Management successfull")

                else:
                    print(
                        "Navigate to Promotion Management is unsuccessfull",
                        NavigatetoPromotionManagement.text,
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def NewPromotionPage(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/promotionSearch_openNewPromotionPopup.action?param=addNewPromo&random=1688721218593&token={self.token1}",
            name="promotion_management_New Promotion Page",
            headers=HeaderBuilder.NewPromotionPage_dcs(config.endpoints.host),
            catch_response=True,
        ) as NewPromotionPage:
            try:
                status16 = NewPromotionPage.status_code
                if status16 == 200:
                    print("New Promotion Page is successfull")

                else:
                    print("New Promotion Page is unsuccessfull", NewPromotionPage.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def nodeselector(self):
        with self.client.get(
            f"{config.endpoints.host}rfm2OnlineApp/menuItemPriceCreate_loadNodeHierarchySelector.action?token={self.token1}",
            name="promotion_management_node selector",
            headers=HeaderBuilder.NewPromotionPage_dcs(config.endpoints.host),
            catch_response=True,
        ) as nodeselector:
            try:
                status17 = nodeselector.status_code
                if status17 == 200:
                    print("node selector is successfull")

                else:
                    print("node selector is unsuccessfull", nodeselector.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def viewpromotion(self):
        with self.client.get(
            f"{config.endpoints.host}rfm2OnlineApp/menuItemPriceCreate_loadNodeHierarchySelector.action?token={self.token1}",
            name="promotion_management_view promotion",
            headers=HeaderBuilder.viewpromotion_dcs(config.endpoints.host, self.token1),
            catch_response=True,
        ) as viewpromotion:
            try:
                status18 = viewpromotion.status_code
                if status18 == 200:
                    print("viewpromotion is successfull")

                else:
                    print("viewpromotion is unsuccessfull", viewpromotion.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def checkpromotion(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/promotionSearch_checkPromotionName.action?promotionName={promotion_name}&uniqueFlag=1688721258806&promotionCodeId=null&token={self.token1}",
            name="promotion_management_checkpromotion",
            headers=HeaderBuilder.viewpromotion_dcs(config.endpoints.host, self.token1),
            catch_response=True,
        ) as checkpromotion:
            try:
                status19 = checkpromotion.status_code
                if status19 == 200:
                    print("checkpromotion is successfull")

                else:
                    print("checkpromotion is unsuccessfull", checkpromotion.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def createpromotion(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/promotion_createPromotion.action",
            name="promotion_management_createpromotion",
            data=[
                (b"token", b"17129073230072835179124367479803"),
                (b"isSaveAsCSV", b""),
                (b"refreshRandomNumber", b"0.08828702767453622"),
                (b"promotionSearchDTO.nodeIdFilter", b""),
                (b"promotionSearchDTO.fullList", b"true"),
                (b"promotionSearchDTO.pageNumber", b"1"),
                (b"promotionSearchDTO.sortField", b"headerNumber"),
                (b"promotionSearchDTO.searchMode", b"fullList"),
                (b"promotionSearchDTO.sortOrder", b"DESC"),
                (b"promotionSearchDTO.nodeId", b""),
                (b"promotionSearchDTO.nodeName", b""),
                (b"promotionSearchDTO.levelId", b""),
                (b"promotionSearchDTO.operation", b""),
                (b"custNodeId", b""),
                (b"custNodeName", b""),
                (b"custNodeLevel", b""),
                (b"copyFlag", b""),
                (b"copyInstance", b""),
                (b"copyPromotion", b""),
                (b"promotionSearchDTO.expiredFilter", b"false"),
                (b"custNodeType", b""),
                (b"custNodeTop", b""),
                (b"promotionSearchDTO.searchOption", b"2"),
                (b"promotionSearchDTO.searchString", b""),
                (b"promotionSearchDTO.status", b"2"),
                (b"level", b"-2"),
                (b"promotionSearchDTO.statusFilter", b"2"),
                (b"promotionSearchDTO.hiddenStatusFilter", b"2"),
                (b"__checkbox_expiredFilterChkBx", b"true"),
                (b"promotionDTO.nodeId", b"1483"),
                (b"promotionDTO.nodeName", b"UK"),
                (b"promotionDTO.promoBasicInfoDTO.promotionName", b"Combo offer"),
                (
                    b"promotionDTO.promoBasicInfoDTO.selectedTemplateId",
                    b"11f3b552-718b-4fa0-af8a-4bf2431cec20",
                ),
                (
                    b"promotionDTO.promoBasicInfoDTO.selectedTemplateName",
                    b"Buy One Get Two - Reduced Price",
                ),
                (b"selectedPageNo", b""),
                (b"noOfRecordsPerPage", b"20"),
                (b"noOfPaginationDepth", b"10"),
                (b"maxPageNoInResultSet", b"0"),
                (b"minPageNoInResultSet", b"1"),
                (b"currentPageNumber", b"1"),
                (b"totalPageCount", b"0"),
                (b"previousRendered", b"false"),
                (b"resetSelectPage", b"true"),
            ],
            headers=HeaderBuilder.NewPromotionPage_dcs(config.endpoints.host),
            catch_response=True,
        ) as createpromotion:
            try:
                status20 = createpromotion.status_code
                if status20 == 200:
                    print("create promotion successfull")

                else:
                    print("create promotion is unsuccessfull", createpromotion.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def checkpromotionname(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/promotionSearch_checkPromotionName.action?promotionName={promotion_name}&uniqueFlag=1688721293453&promotionCodeId={promotion_code}&token={self.token1}",
            name="promotion_management_checkpromotionname",
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as checkpromotionname:
            try:
                status21 = checkpromotionname.status_code
                if status21 == 200:
                    print("check promotion name is successfull")

                else:
                    print(
                        "check promotion name  is unsuccessfull",
                        checkpromotionname.text,
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def checkpromotioncode(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/promotion_checkPromotionCode.action?promotionCode={promotion_code}&promoNodeId=11451&randomNumber=1688721293711&token={self.token1}",
            name="promotion_management_checkpromotioncode",
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as checkpromotioncode:
            try:
                status22 = checkpromotioncode.status_code
                if status22 == 200:
                    print("check promotion code is successfull")

                else:
                    print(
                        "check promotion code  is unsuccessfull",
                        checkpromotioncode.text,
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def menuitemselector(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/marketPromotionMenuItemSelector_loadMenuItemSelector.action?paramType=ProductSet&menuItemLevel=restaurant&token={self.token1}",
            name="promotion_management_menuitemselector",
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as menuitemselector:
            try:
                status23 = menuitemselector.status_code
                if status23 == 200:
                    print("menu item selector is successfull")

                else:
                    print("menu item selector  is unsuccessfull", menuitemselector.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def searchmenuitem(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/marketPromotionMenuItemSelector_searchMenuItems.action?paramType=ProductSet&token={self.token1}",
            name="promotion_management_search menu item",
            data=[
                (b"token", self.token1),
                (b"isSaveAsCSV", b""),
                (b"refreshRandomNumber", b"0.5489224845379852"),
                (b"menuItemSelectorSearchDTO.layeringLogicType", b"1"),
                (b"requestType", b"2"),
                (b"asscDataIdList", b""),
                (b"menuItemSelectorSearchDTO.sortField", b"headerNumber"),
                (b"selectedPageNo", b"1"),
                (b"pageNo", b"1"),
                (b"menuItemSelectorSearchDTO.fullList", b"true"),
                (b"viewCurrentChanges", b""),
                (
                    b"menuItemSelectorSearchDTO.helperType",
                    b"marketpromotionMenuItemHelper",
                ),
                (b"menuItemSelectorSearchDTO.menuItemLevel", b"master"),
                (b"moduleFunctionId", b"3021"),
                (b"menuItemSelectorSearchDTO.restaurantNodeId", b"1483"),
                (b"menuItemSelectorSearchDTO.searchOption", b"2"),
                (b"menuItemSelectorSearchDTO.searchText", b""),
                (b"menuItemSelectorSearchDTO.familyGroup", b"0"),
                (b"menuItemSelectorSearchDTO.aprvlStatus", b"2"),
            ],
            headers=HeaderBuilder.searchmenuitem_dcs(
                config.endpoints.host, self.token1
            ),
            catch_response=True,
        ) as searchmenuitem:
            try:
                status24 = searchmenuitem.status_code
                if status24 == 200:
                    print("search menu item successfull")

                else:
                    print("search menu item is unsuccessfull", searchmenuitem.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def menuitemselector2(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/marketPromotionMenuItemSelector_loadMenuItemSelector.action?paramType=ProductSet&menuItemLevel=restaurant&token={self.token1}",
            name="promotion_management_menuitemselector2",
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as menuitemselector2:
            try:
                status25 = menuitemselector2.status_code
                if status25 == 200:
                    print("menu item selector 2 is successfull")

                else:
                    print(
                        "menu item selector 2  is unsuccessfull", menuitemselector2.text
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def searchmenuitem2(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/marketPromotionMenuItemSelector_searchMenuItems.action?paramType=ProductSet&token={self.token1}",
            name="promotion_management_search menu item2",
            data=[
                (b"token", self.token1),
                (b"isSaveAsCSV", b""),
                (b"refreshRandomNumber", b"0.2711732487593428"),
                (b"menuItemSelectorSearchDTO.layeringLogicType", b"1"),
                (b"requestType", b"2"),
                (b"asscDataIdList", b""),
                (b"menuItemSelectorSearchDTO.sortField", b"headerNumber"),
                (b"selectedPageNo", b"1"),
                (b"pageNo", b"1"),
                (b"menuItemSelectorSearchDTO.fullList", b"true"),
                (b"viewCurrentChanges", b""),
                (
                    b"menuItemSelectorSearchDTO.helperType",
                    b"marketpromotionMenuItemHelper",
                ),
                (b"menuItemSelectorSearchDTO.menuItemLevel", b"master"),
                (b"moduleFunctionId", b"3021"),
                (b"menuItemSelectorSearchDTO.restaurantNodeId", b"1483"),
                (b"menuItemSelectorSearchDTO.searchOption", b"2"),
                (b"menuItemSelectorSearchDTO.searchText", b""),
                (b"menuItemSelectorSearchDTO.familyGroup", b"0"),
                (b"menuItemSelectorSearchDTO.aprvlStatus", b"2"),
            ],
            headers=HeaderBuilder.searchmenuitem_dcs(
                config.endpoints.host, self.token1
            ),
            catch_response=True,
        ) as searchmenuitem2:
            try:
                status26 = searchmenuitem2.status_code
                if status26 == 200:
                    print("search menu item 2 successfull")

                else:
                    print("search menu item 2 is unsuccessfull", searchmenuitem2.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def checkpromotioncode2(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/promotion_checkPromotionCode.action?promotionCode={promotion_code}&promoNodeId=11451&randomNumber=1688721375089&token={self.token1}",
            name="promotion_management_checkpromotioncode2",
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as checkpromotioncode2:
            try:
                status27 = checkpromotioncode2.status_code
                if status27 == 200:
                    print("check promotion code 2 is successfull")

                else:
                    print(
                        "check promotion code 2 is unsuccessfull",
                        checkpromotioncode2.text,
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def checkpromotionname2(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/promotionSearch_checkPromotionName.action?promotionName={promotion_name}&uniqueFlag=1688721293453&promotionCodeId={promotion_code}&token={self.token1}",
            name="promotion_management_checkpromotionname2",
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as checkpromotionname2:
            try:
                status28 = checkpromotionname2.status_code
                if status28 == 200:
                    print("check promotion name 2 is successfull")

                else:
                    print(
                        "check promotion name 2 is unsuccessfull",
                        checkpromotionname2.text,
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def checkpromotioncode3(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/promotion_checkPromotionCode.action?promotionCode={promotion_code}&promoNodeId=11451&randomNumber=1688721375089&token={self.token1}",
            name="promotion_management_checkpromotioncode3",
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as checkpromotioncode3:
            try:
                status29 = checkpromotioncode3.status_code
                if status29 == 200:
                    print("check promotion code 3 is successfull")

                else:
                    print(
                        "check promotion code 3 is unsuccessfull",
                        checkpromotioncode3.text,
                    )
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def setlock(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/promotion_checkPromotionCode.action?promotionCode={promotion_code}&promoNodeId=11451&randomNumber=1688721375089&token={self.token1}",
            name="promotion_management_setlock",
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as setlock:
            try:
                status30 = setlock.status_code
                if status30 == 200:
                    print("set lock is successfull")

                else:
                    print("set lock is unsuccessfull", setlock.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def savepromotion(self):
        with self.client.post(
            f"{config.endpoints.host}/rfm2OnlineApp/marketPromotionMenuItemSelector_searchMenuItems.action?paramType=ProductSet&token={self.token1}",
            name="promotion_management_savepromotion",
            data=[
                (b"token", self.token1),
                (b"isSaveAsCSV", b""),
                (b"refreshRandomNumber", b"0.08949519287165342"),
                (b"promotionSearchDTO.operation", b""),
                (b"promotionDTO.nodeId", b"1483"),
                (b"promotionDTO.nodeName", b"UK"),
                (b"promotionDTO.promoId", b"0"),
                (b"promotionDTO.actionType", b"Save"),
                (b"promotionDTO.promoInstanceId", b""),
                (b"promotionDTO.customNode", b"false"),
                (b"promotionDTO.validateWarningMessage", b""),
                (b"promotionDTO.basicConditionsCustomized", b"false"),
                (b"promotionDTO.dynamicConditionsCustomized", b"false"),
                (b"promotionDTO.dayAndTimeCustomized", b"false"),
                (b"promotionDTO.amountItemConditionsCustomized", b"false"),
                (b"promotionDTO.limitToCustomized", b"false"),
                (b"promotionDTO.priority", b""),
                (
                    b"promotionDTO.promoBasicInfoDTO.selectedTemplateId",
                    b"11f3b552-718b-4fa0-af8a-4bf2431cec20",
                ),
                (b"promotionDTO.promoBasicInfoDTO.custNodeId", b""),
                (
                    b"promotionDTO.promoBasicInfoDTO.selectedTemplateName",
                    b"Buy One Get Two - Reduced Price",
                ),
                (b"promotionDTO.menuItemLevel", b"master"),
                (b"promotionDTO.expiredFilter", b"false"),
                (b"promotionDTO.levelIdToFilter", b""),
                (b"promotionDTO.statusIdFilter", b"2"),
                (b"promotionDTO.searchStringFilter", b""),
                (b"promotionDTO.searchWithStatusFilter", b"2"),
                (b"promotionDTO.promotionStatus", b""),
                (b"currentDate.year", b"2024"),
                (b"currentDate.month", b"3"),
                (b"currentDate.date", b"12"),
                (b"promotionDTO.selectedTab", b"promoSpecific"),
                (b"promotionDTO.customized", b"false"),
                (b"promotionDTO.resetTabValues", b"false"),
                (b"image", b""),
                (b"menuItemLevelDetail", b"master"),
                (b"respResultType", b"jsp"),
                (b"AL3002003010_old", b""),
                (b"AL3002003010_new", b""),
                (b"AL3002003010_lookup", b""),
                (b"promotionDTO.promoBasicInfoDTO.imagePath", b""),
                (b"AL3021001006001004_old", b""),
                (b"AL3021001006001004_new", b""),
                (b"AL3021001006001004_lookup", b"N"),
                (b"promotionDTO.promoCodeCheck", b"true"),
                (b"promotionDTO.promoBasicInfoDTO.promotionCode", b"90201"),
                (b"AL3021001006001001_old", b""),
                (b"AL3021001006001001_new", b"90201"),
                (b"AL3021001006001001_lookup", b"N"),
                (b"promoName", b"Combo offer"),
                (b"AL3021001006001002_old", b"Combo offer"),
                (b"AL3021001006001002_new", b"Combo offer"),
                (b"AL3021001006001002_lookup", b"N"),
                (b"promotionDTO.promoBasicInfoDTO.promotionName", b"Combo offer"),
                (b"AL3021001006001003_old", b""),
                (b"AL3021001006001003_new", b"1"),
                (b"AL3021001006001003_lookup", b""),
                (b"promotionDTO.promoBasicInfoDTO.status", b"1"),
                (b"promotionDTO.promoBasicInfoDTO.inheritanceOrder", b"1"),
                (b"promotionDTO.promoNameLanguageDTOList[0].languageName", b"English"),
                (b"promotionDTO.promoNameLanguageDTOList[0].languageId", b"23"),
                (b"promotionDTO.promoNameLanguageDTOList[0].localId", b"60"),
                (
                    b"promotionDTO.promoNameLanguageDTOList[0].promotionName",
                    b"Combo offer",
                ),
                (b"AL3021001001001_old_0", b"Combo offer"),
                (b"AL3021001001001_new_0", b"Combo offer"),
                (b"AL3021001001001_lookup_0", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[0].shortDescription", b""),
                (b"AL3021001001002_old_0", b""),
                (b"AL3021001001002_new_0", b""),
                (b"AL3021001001002_lookup_0", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[0].longDescription", b""),
                (b"AL3021001001003_old_0", b""),
                (b"AL3021001001003_new_0", b""),
                (b"AL3021001001003_lookup_0", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[1].languageName", b"Spanish"),
                (b"promotionDTO.promoNameLanguageDTOList[1].languageId", b"23"),
                (b"promotionDTO.promoNameLanguageDTOList[1].localId", b"63"),
                (b"promotionDTO.promoNameLanguageDTOList[1].promotionName", b""),
                (b"AL3021001001001_old_1", b""),
                (b"AL3021001001001_new_1", b""),
                (b"AL3021001001001_lookup_1", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[1].shortDescription", b""),
                (b"AL3021001001002_old_1", b""),
                (b"AL3021001001002_new_1", b""),
                (b"AL3021001001002_lookup_1", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[1].longDescription", b""),
                (b"AL3021001001003_old_1", b""),
                (b"AL3021001001003_new_1", b""),
                (b"AL3021001001003_lookup_1", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[2].languageName", b"Deutsch"),
                (b"promotionDTO.promoNameLanguageDTOList[2].languageId", b"23"),
                (b"promotionDTO.promoNameLanguageDTOList[2].localId", b"61"),
                (b"promotionDTO.promoNameLanguageDTOList[2].promotionName", b""),
                (b"AL3021001001001_old_2", b""),
                (b"AL3021001001001_new_2", b""),
                (b"AL3021001001001_lookup_2", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[2].shortDescription", b""),
                (b"AL3021001001002_old_2", b""),
                (b"AL3021001001002_new_2", b""),
                (b"AL3021001001002_lookup_2", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[2].longDescription", b""),
                (b"AL3021001001003_old_2", b""),
                (b"AL3021001001003_new_2", b""),
                (b"AL3021001001003_lookup_2", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[3].languageName", b"polish"),
                (b"promotionDTO.promoNameLanguageDTOList[3].languageId", b"23"),
                (b"promotionDTO.promoNameLanguageDTOList[3].localId", b"65"),
                (b"promotionDTO.promoNameLanguageDTOList[3].promotionName", b""),
                (b"AL3021001001001_old_3", b""),
                (b"AL3021001001001_new_3", b""),
                (b"AL3021001001001_lookup_3", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[3].shortDescription", b""),
                (b"AL3021001001002_old_3", b""),
                (b"AL3021001001002_new_3", b""),
                (b"AL3021001001002_lookup_3", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[3].longDescription", b""),
                (b"AL3021001001003_old_3", b""),
                (b"AL3021001001003_new_3", b""),
                (b"AL3021001001003_lookup_3", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[4].languageName", b"Francais"),
                (b"promotionDTO.promoNameLanguageDTOList[4].languageId", b"23"),
                (b"promotionDTO.promoNameLanguageDTOList[4].localId", b"62"),
                (b"promotionDTO.promoNameLanguageDTOList[4].promotionName", b""),
                (b"AL3021001001001_old_4", b""),
                (b"AL3021001001001_new_4", b""),
                (b"AL3021001001001_lookup_4", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[4].shortDescription", b""),
                (b"AL3021001001002_old_4", b""),
                (b"AL3021001001002_new_4", b""),
                (b"AL3021001001002_lookup_4", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[4].longDescription", b""),
                (b"AL3021001001003_old_4", b""),
                (b"AL3021001001003_new_4", b""),
                (b"AL3021001001003_lookup_4", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[5].languageName", b"Welsh"),
                (b"promotionDTO.promoNameLanguageDTOList[5].languageId", b"23"),
                (b"promotionDTO.promoNameLanguageDTOList[5].localId", b"64"),
                (b"promotionDTO.promoNameLanguageDTOList[5].promotionName", b""),
                (b"AL3021001001001_old_5", b""),
                (b"AL3021001001001_new_5", b""),
                (b"AL3021001001001_lookup_5", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[5].shortDescription", b""),
                (b"AL3021001001002_old_5", b""),
                (b"AL3021001001002_new_5", b""),
                (b"AL3021001001002_lookup_5", b"N"),
                (b"promotionDTO.promoNameLanguageDTOList[5].longDescription", b""),
                (b"AL3021001001003_old_5", b""),
                (b"AL3021001001003_new_5", b""),
                (b"AL3021001001003_lookup_5", b"N"),
                (b"promotionDTO.promoBasicInfoDTO.qtyLimit", b"1"),
                (b"AL3021001001004_old", b"1"),
                (b"AL3021001001004_new", b"1"),
                (b"AL3021001001004_lookup", b"N"),
                (b"promotionDTO.promoBasicInfoDTO.exclusivePromo", b"0"),
                (b"AL3021001001005_old", b""),
                (b"AL3021001001005_new", b"0"),
                (b"AL3021001001005_lookup", b""),
                (
                    b"__checkbox_promotionDTO.promoBasicInfoDTO.checkoutTargetPromo",
                    b"true",
                ),
                (b"AL30210010010012_old", b"false"),
                (b"AL30210010010012_new", b"false"),
                (b"AL30210010010012_lookup", b"N"),
                (b"promotionDTO.promoBasicInfoDTO.barCode", b""),
                (b"AL3021001001006_old", b""),
                (b"AL3021001001006_new", b""),
                (b"AL3021001001006_lookup", b"N"),
                (b"promotionDTO.promoBasicInfoDTO.redemptionMode", b"-1"),
                (b"AL30210010010017_old", b""),
                (b"AL30210010010017_new", b"-1"),
                (b"AL30210010010017_lookup", b""),
                (b"promotionDTO.promoBasicInfoDTO.promotionDateFrom", b"04/12/2024"),
                (b"localeFromDate", b"Apr 12, 2024"),
                (b"AL30210010010013_old", b""),
                (b"AL30210010010013_new", b"Apr 12, 2024"),
                (b"AL30210010010013_lookup", b"N"),
                (b"promotionDTO.promoBasicInfoDTO.promotionDateTo", b"04/13/2024"),
                (b"localeToDate", b"Apr 13, 2024"),
                (b"AL30210010010014_old", b""),
                (b"AL30210010010014_new", b"Apr 13, 2024"),
                (b"AL30210010010014_lookup", b"N"),
                (b"promotionDTO.promoBasicInfoDTO.holidayDates", b""),
                (b"AL30210010010016_old", b""),
                (b"AL30210010010016_new", b""),
                (b"promotionDTO.promoBasicInfoDTO.validOnDates", b"0"),
                (b"AL30210010010015_old", b"0"),
                (b"AL30210010010015_new", b"0"),
                (b"AL30210010010015_lookup", b"N"),
                (b"promotionDTO.promoBasicInfoDTO.individualPrices", b"1"),
                (b"AL30210010010018_old", b"1"),
                (b"AL30210010010018_new", b"1"),
                (b"AL30210010010018_lookup", b""),
                (b"promotionDTO.promoBasicInfoDTO.countTowardsPromotionLimit", b"1"),
                (b"AL30210010010019_old", b"1"),
                (b"AL30210010010019_new", b"1"),
                (b"AL30210010010019_lookup", b""),
                (b"suggestiveType", b""),
                (b"suggestiveTemplateId", b""),
                (b"suggestiveTemplateName", b""),
                (b"eligMisTemplateId", b""),
                (b"eligMisTemplateName", b""),
                (b"condMisTemplateId", b""),
                (b"condMisTemplateName", b""),
                (b"suggestiveExist", b"false"),
                (b"promotionDTO.cndtnTyp", b"0"),
                (b"promotionDTO.sections[0].name", b"When Customer Buys"),
                (
                    b"promotionDTO.sections[0].resourceName",
                    b"section.customer.buy.name",
                ),
                (b"promotionDTO.sections[0].sequence", b"4"),
                (b"promotionDTO.sections[0].cols", b"2"),
                (b"promotionDTO.sections[0].rows", b"4"),
                (b"promotionDTO.sections[0].attrId", b"1"),
                (b"promotionDTO.sections[0].attrId", b"1"),
                (b"promotionDTO.sections[0].attrId", b"1"),
                (b"promotionDTO.sections[0].attrId", b"1"),
                (
                    b"promotionDTO.sections[0].parameterList[0].paramName",
                    b"Conditional Products",
                ),
                (b"promotionDTO.sections[0].parameterList[0].paramType", b"ProductSet"),
                (b"promotionDTO.sections[0].parameterList[0].id", b""),
                (b"promotionDTO.sections[0].parameterList[0].attrId", b"1"),
                (b"promotionDTO.sections[0].parameterList[0].oldValue", b""),
                (
                    b"promotionDTO.sections[0].parameterList[0].currentValue",
                    b"147954@~4@~10P@~P",
                ),
                (
                    b"promotionDTO.sections[0].parameterList[1].paramName",
                    b"Quantity Needed",
                ),
                (b"promotionDTO.sections[0].parameterList[1].paramType", b"Integer"),
                (b"promotionDTO.sections[0].parameterList[1].id", b""),
                (b"promotionDTO.sections[0].parameterList[1].attrId", b"1"),
                (b"promotionDTO.sections[0].parameterList[1].oldValue", b"1"),
                (b"promotionDTO.sections[0].parameterList[1].currentValue", b"1"),
                (b"AL3021001009016001002_old", b""),
                (b"AL3021001009016001002_new", b""),
                (b"AL3021001009016001002_lookup", b"N"),
                (
                    b"promotionDTO.sections[0].parameterList[2].paramName",
                    b"Eligible Products 1",
                ),
                (b"promotionDTO.sections[0].parameterList[2].paramType", b"ProductSet"),
                (b"promotionDTO.sections[0].parameterList[2].id", b""),
                (b"promotionDTO.sections[0].parameterList[2].attrId", b"1"),
                (b"promotionDTO.sections[0].parameterList[2].oldValue", b""),
                (
                    b"promotionDTO.sections[0].parameterList[2].currentValue",
                    b"147959@~1003@~LSM-VCH HAMBURGER@~P",
                ),
                (
                    b"promotionDTO.sections[0].parameterList[3].paramName",
                    b"Minimum Quantity Given 1",
                ),
                (b"promotionDTO.sections[0].parameterList[3].paramType", b"Integer"),
                (b"promotionDTO.sections[0].parameterList[3].id", b""),
                (b"promotionDTO.sections[0].parameterList[3].attrId", b"1"),
                (b"promotionDTO.sections[0].parameterList[3].oldValue", b"1"),
                (b"promotionDTO.sections[0].parameterList[3].currentValue", b"1"),
                (b"AL3021001009016001004_old", b""),
                (b"AL3021001009016001004_new", b""),
                (b"AL3021001009016001004_lookup", b"N"),
                (
                    b"promotionDTO.sections[0].parameterList[4].paramName",
                    b"Maximum Quantity Given 1",
                ),
                (b"promotionDTO.sections[0].parameterList[4].paramType", b"Integer"),
                (b"promotionDTO.sections[0].parameterList[4].id", b""),
                (b"promotionDTO.sections[0].parameterList[4].attrId", b"1"),
                (b"promotionDTO.sections[0].parameterList[4].oldValue", b"1"),
                (b"promotionDTO.sections[0].parameterList[4].currentValue", b"1"),
                (b"AL3021001009016001005_old", b""),
                (b"AL3021001009016001005_new", b""),
                (b"AL3021001009016001005_lookup", b"N"),
                (
                    b"promotionDTO.sections[0].parameterList[5].paramName",
                    b"Eligible Products 2",
                ),
                (b"promotionDTO.sections[0].parameterList[5].paramType", b"ProductSet"),
                (b"promotionDTO.sections[0].parameterList[5].id", b""),
                (b"promotionDTO.sections[0].parameterList[5].attrId", b"1"),
                (b"promotionDTO.sections[0].parameterList[5].oldValue", b""),
                (
                    b"promotionDTO.sections[0].parameterList[5].currentValue",
                    b"147962@~1016@~2 CHEESEBURGERS (MP)@~P",
                ),
                (
                    b"promotionDTO.sections[0].parameterList[6].paramName",
                    b"Minimum Quantity Given 2",
                ),
                (b"promotionDTO.sections[0].parameterList[6].paramType", b"Integer"),
                (b"promotionDTO.sections[0].parameterList[6].id", b""),
                (b"promotionDTO.sections[0].parameterList[6].attrId", b"1"),
                (b"promotionDTO.sections[0].parameterList[6].oldValue", b"1"),
                (b"promotionDTO.sections[0].parameterList[6].currentValue", b"1"),
                (b"AL3021001009016001007_old", b""),
                (b"AL3021001009016001007_new", b""),
                (b"AL3021001009016001007_lookup", b"N"),
                (
                    b"promotionDTO.sections[0].parameterList[7].paramName",
                    b"Maximum Quantity Given 2",
                ),
                (b"promotionDTO.sections[0].parameterList[7].paramType", b"Integer"),
                (b"promotionDTO.sections[0].parameterList[7].id", b""),
                (b"promotionDTO.sections[0].parameterList[7].attrId", b"1"),
                (b"promotionDTO.sections[0].parameterList[7].oldValue", b"1"),
                (b"promotionDTO.sections[0].parameterList[7].currentValue", b"1"),
                (b"AL3021001009016001008_old", b""),
                (b"AL3021001009016001008_new", b""),
                (b"AL3021001009016001008_lookup", b"N"),
                (b"promotionDTO.sections[1].name", b"What Customer Gets"),
                (
                    b"promotionDTO.sections[1].resourceName",
                    b"section.customer.get.name",
                ),
                (b"promotionDTO.sections[1].sequence", b"2"),
                (b"promotionDTO.sections[1].cols", b"2"),
                (b"promotionDTO.sections[1].rows", b"2"),
                (b"promotionDTO.sections[1].attrId", b"1"),
                (b"promotionDTO.sections[1].attrId", b"1"),
                (
                    b"promotionDTO.sections[1].parameterList[0].paramName",
                    b"New Price 1",
                ),
                (b"promotionDTO.sections[1].parameterList[0].paramType", b"Price"),
                (b"promotionDTO.sections[1].parameterList[0].id", b""),
                (b"promotionDTO.sections[1].parameterList[0].attrId", b"1"),
                (b"promotionDTO.sections[1].parameterList[0].oldValue", b"-0.00"),
                (b"promotionDTO.sections[1].parameterList[0].currentValue", b"+600.00"),
                (b"locale_priceValue_1_0", b"600.00"),
                (b"AL3021001009016002001_old", b""),
                (b"AL3021001009016002001_old", b"fixed"),
                (b"AL3021001009016002001_old", b"percent"),
                (b"AL3021001009016002001_old", b"relative"),
                (b"AL3021001009016002001_new", b""),
                (b"AL3021001009016002001_new", b""),
                (b"AL3021001009016002001_new", b""),
                (b"AL3021001009016002001_new", b""),
                (b"AL3021001009016002001_lookup", b"N"),
                (b"AL3021001009016002001_lookup", b"N"),
                (b"AL3021001009016002001_lookup", b"N"),
                (b"AL3021001009016002001_lookup", b"N"),
                (b"priceValue_1_0", b"600.00"),
                (b"New Price 1_1_0_radio", b"relative"),
                (
                    b"promotionDTO.sections[1].parameterList[1].paramName",
                    b"New Price 2",
                ),
                (b"promotionDTO.sections[1].parameterList[1].paramType", b"Price"),
                (b"promotionDTO.sections[1].parameterList[1].id", b""),
                (b"promotionDTO.sections[1].parameterList[1].attrId", b"1"),
                (b"promotionDTO.sections[1].parameterList[1].oldValue", b"-0.00"),
                (b"promotionDTO.sections[1].parameterList[1].currentValue", b"+300.00"),
                (b"locale_priceValue_1_1", b"300.00"),
                (b"AL3021001009016002002_old", b""),
                (b"AL3021001009016002002_old", b"fixed"),
                (b"AL3021001009016002002_old", b"percent"),
                (b"AL3021001009016002002_old", b"relative"),
                (b"AL3021001009016002002_new", b""),
                (b"AL3021001009016002002_new", b""),
                (b"AL3021001009016002002_new", b""),
                (b"AL3021001009016002002_new", b""),
                (b"AL3021001009016002002_lookup", b"N"),
                (b"AL3021001009016002002_lookup", b"N"),
                (b"AL3021001009016002002_lookup", b"N"),
                (b"AL3021001009016002002_lookup", b"N"),
                (b"priceValue_1_1", b"300.00"),
                (b"New Price 2_1_1_radio", b"relative"),
                (
                    b"promotionDTO.sections[1].parameterList[2].paramName",
                    b"Discount Limit 1",
                ),
                (b"promotionDTO.sections[1].parameterList[2].paramType", b"Decimal"),
                (b"promotionDTO.sections[1].parameterList[2].id", b""),
                (b"promotionDTO.sections[1].parameterList[2].attrId", b"1"),
                (b"promotionDTO.sections[1].parameterList[2].oldValue", b"0.00"),
                (b"locale_currentValue_1_2", b"200.00"),
                (b"AL3021001009016002003_old", b"0.00"),
                (b"AL3021001009016002003_new", b""),
                (b"AL3021001009016002003_lookup", b"N"),
                (b"promotionDTO.sections[1].parameterList[2].currentValue", b"200.00"),
                (
                    b"promotionDTO.sections[1].parameterList[3].paramName",
                    b"Discount Limit 2",
                ),
                (b"promotionDTO.sections[1].parameterList[3].paramType", b"Decimal"),
                (b"promotionDTO.sections[1].parameterList[3].id", b""),
                (b"promotionDTO.sections[1].parameterList[3].attrId", b"1"),
                (b"promotionDTO.sections[1].parameterList[3].oldValue", b"0.00"),
                (b"locale_currentValue_1_3", b"100.00"),
                (b"AL3021001009016002004_old", b"0.00"),
                (b"AL3021001009016002004_new", b""),
                (b"AL3021001009016002004_lookup", b"N"),
                (b"promotionDTO.sections[1].parameterList[3].currentValue", b"100.00"),
                (b"promotionDTO.promotionGenericConditionDTO.dayPart", b"1"),
                (b"promotionDTO.promotionGenericConditionDTO.dayPart", b"2"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.dayPart", b"1"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.dayPart", b"2"),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.dayPart",
                    b"147950",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.dayPart",
                    b"147948",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.dayPart",
                    b"147949",
                ),
                (b"AL3021001007001001_old", b""),
                (b"AL3021001007001001_new", b"1,2"),
                (b"AL3021001007001001_lookup", b""),
                (
                    b"__multiselect_promotionDTO.promotionGenericConditionDTO.dayPart",
                    b"",
                ),
                (
                    b"__checkbox_promotionDTO.promotionTimeRangeList[0].monValidAllDayFlag",
                    b"",
                ),
                (
                    b"__checkbox_promotionDTO.promotionTimeRangeList[0].tueValidAllDayFlag",
                    b"",
                ),
                (
                    b"__checkbox_promotionDTO.promotionTimeRangeList[0].wedValidAllDayFlag",
                    b"",
                ),
                (
                    b"__checkbox_promotionDTO.promotionTimeRangeList[0].thuValidAllDayFlag",
                    b"",
                ),
                (
                    b"__checkbox_promotionDTO.promotionTimeRangeList[0].friValidAllDayFlag",
                    b"",
                ),
                (
                    b"__checkbox_promotionDTO.promotionTimeRangeList[0].satValidAllDayFlag",
                    b"",
                ),
                (
                    b"__checkbox_promotionDTO.promotionTimeRangeList[0].sunValidAllDayFlag",
                    b"",
                ),
                (b"__checkbox_monValidFlag", b"true"),
                (b"__checkbox_tueValidFlag", b"true"),
                (b"__checkbox_wedValidFlag", b"true"),
                (b"__checkbox_thuValidFlag", b"true"),
                (b"__checkbox_friValidFlag", b"true"),
                (b"__checkbox_satValidFlag", b"true"),
                (b"__checkbox_sunValidFlag", b"true"),
                (b"promotionDTO.promotionTimeRangeList[0].monFromTime", b""),
                (b"AL3021001007001002_old", b""),
                (b"AL3021001007001002_old", b""),
                (b"AL3021001007001002_old", b""),
                (b"AL3021001007001002_old", b""),
                (b"AL3021001007001002_old", b""),
                (b"AL3021001007001002_old", b""),
                (b"AL3021001007001002_old", b""),
                (b"AL3021001007001002_new", b""),
                (b"AL3021001007001002_new", b""),
                (b"AL3021001007001002_new", b""),
                (b"AL3021001007001002_new", b""),
                (b"AL3021001007001002_new", b""),
                (b"AL3021001007001002_new", b""),
                (b"AL3021001007001002_new", b""),
                (b"AL3021001007001002_lookup", b"N"),
                (b"AL3021001007001002_lookup", b"N"),
                (b"AL3021001007001002_lookup", b"N"),
                (b"AL3021001007001002_lookup", b"N"),
                (b"AL3021001007001002_lookup", b"N"),
                (b"AL3021001007001002_lookup", b"N"),
                (b"AL3021001007001002_lookup", b"N"),
                (b"promotionDTO.promotionTimeRangeList[0].tueFromTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].wedFromTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].thuFromTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].friFromTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].satFromTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].sunFromTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].monToTime", b""),
                (b"AL3021001007001003_old", b""),
                (b"AL3021001007001003_old", b""),
                (b"AL3021001007001003_old", b""),
                (b"AL3021001007001003_old", b""),
                (b"AL3021001007001003_old", b""),
                (b"AL3021001007001003_old", b""),
                (b"AL3021001007001003_old", b""),
                (b"AL3021001007001003_new", b""),
                (b"AL3021001007001003_new", b""),
                (b"AL3021001007001003_new", b""),
                (b"AL3021001007001003_new", b""),
                (b"AL3021001007001003_new", b""),
                (b"AL3021001007001003_new", b""),
                (b"AL3021001007001003_new", b""),
                (b"AL3021001007001003_lookup", b"N"),
                (b"AL3021001007001003_lookup", b"N"),
                (b"AL3021001007001003_lookup", b"N"),
                (b"AL3021001007001003_lookup", b"N"),
                (b"AL3021001007001003_lookup", b"N"),
                (b"AL3021001007001003_lookup", b"N"),
                (b"AL3021001007001003_lookup", b"N"),
                (b"promotionDTO.promotionTimeRangeList[0].tueToTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].wedToTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].thuToTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].friToTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].satToTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].sunToTime", b""),
                (b"promotionDTO.promotionTimeRangeList[0].dltdFlag", b"0"),
                (b"rowNo", b"1"),
                (b"promotionDTO.promotionGenericConditionDTO.id", b""),
                (b"locale_saleAmount", b""),
                (b"AL3021001004001_old", b""),
                (b"AL3021001004001_new", b""),
                (b"AL3021001004001_lookup", b"N"),
                (
                    b"promotionDTO.promotionGenericConditionDTO.saleAmountDTO.saleAmount",
                    b"",
                ),
                (b"AL3021001004007_old", b"0"),
                (b"AL3021001004007_new", b"0"),
                (b"AL3021001004007_lookup", b""),
                (b"AL3021001004002_old", b"0"),
                (b"AL3021001004002_new", b"0"),
                (b"AL3021001004002_lookup", b""),
                (b"AL3021001004003_old", b"0"),
                (b"AL3021001004003_new", b"0"),
                (b"AL3021001004003_lookup", b""),
                (b"oldExItemsString_1", b""),
                (
                    b"promotionDTO.promotionGenericConditionDTO.saleAmountDTO.excludeCodes",
                    b"",
                ),
                (
                    b"promotionDTO.promotionGenericConditionDTO.saleAmountDTO.cndtnValIdForPrdTyp",
                    b"",
                ),
                (
                    b"promotionDTO.promotionGenericConditionDTO.saleAmountDTO.cndtnValIdForMGTyp",
                    b"",
                ),
                (b"maxExItmsForSaleAmt", b"50"),
                (
                    b"promotionDTO.promotionGenericConditionDTO.itemQuantityDTO.numberOfItem",
                    b"",
                ),
                (b"AL3021001004004_old", b""),
                (b"AL3021001004004_new", b""),
                (b"AL3021001004004_lookup", b"N"),
                (b"AL3021001004005_old", b""),
                (b"AL3021001004005_new", b"0"),
                (b"AL3021001004005_lookup", b""),
                (b"AL3021001004006_old", b""),
                (b"AL3021001004006_new", b"0"),
                (b"AL3021001004006_lookup", b""),
                (b"oldExItemsString_2", b""),
                (
                    b"promotionDTO.promotionGenericConditionDTO.itemQuantityDTO.excludeCodes",
                    b"",
                ),
                (
                    b"promotionDTO.promotionGenericConditionDTO.itemQuantityDTO.cndtnValIdForPrdTyp",
                    b"",
                ),
                (
                    b"promotionDTO.promotionGenericConditionDTO.itemQuantityDTO.cndtnValIdForMGTyp",
                    b"",
                ),
                (b"maxExItmsForSaleItm", b"50"),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.saleType",
                    b"EAT-IN",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.saleType",
                    b"OTHER",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.saleType",
                    b"TAKE-OUT",
                ),
                (b"AL3021001005001_old", b""),
                (b"AL3021001005001_new", b""),
                (b"AL3021001005001_lookup", b""),
                (
                    b"__multiselect_promotionDTO.promotionGenericConditionDTO.saleType",
                    b"",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.paymentType",
                    b"147856",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.paymentType",
                    b"147857",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.paymentType",
                    b"147854",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.paymentType",
                    b"147855",
                ),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.paymentType",
                    b"286441",
                ),
                (b"AL3021001005004_old", b""),
                (b"AL3021001005004_new", b""),
                (b"AL3021001005004_lookup", b""),
                (
                    b"__multiselect_promotionDTO.promotionGenericConditionDTO.paymentType",
                    b"",
                ),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"1"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"2"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"3"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"4"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"5"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"6"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"7"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"8"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"9"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"10"),
                (b"__checkbox_promotionDTO.promotionGenericConditionDTO.pod", b"11"),
                (b"AL3021001005002_old", b""),
                (b"AL3021001005002_new", b""),
                (b"AL3021001005002_lookup", b""),
                (b"__multiselect_promotionDTO.promotionGenericConditionDTO.pod", b""),
                (
                    b"__checkbox_promotionDTO.promotionGenericConditionDTO.saleChannel",
                    b"KIOSK",
                ),
                (b"AL3021001005005_old", b""),
                (b"AL3021001005005_new", b""),
                (b"AL3021001005005_lookup", b""),
                (
                    b"__multiselect_promotionDTO.promotionGenericConditionDTO.saleChannel",
                    b"",
                ),
                (b"promotionDTO.promotionGenericConditionDTO.maxOrderCount", b""),
                (b"AL3021001005006_old", b""),
                (b"AL3021001005006_new", b""),
                (b"AL3021001005006_lookup", b"N"),
                (b"AL3021001005007_old", b"0"),
                (b"AL3021001005007_new", b"0"),
                (b"AL3021001005007_lookup", b""),
                (b"promotionDTO.promotionGenericConditionDTO.orderValidityDate", b""),
                (b"AL3021001005008_old", b""),
                (b"AL3021001005008_new", b""),
                (b"AL3021001005008_lookup", b"N"),
            ],
            headers=HeaderBuilder.checkpromotionname_dcs(config.endpoints.host),
            catch_response=True,
        ) as savepromotion:
            try:
                status31 = savepromotion.status_code
                if status31 == 200:
                    print("save promotion successfull")

                else:
                    print("save promotion is unsuccessfull", savepromotion.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()

    @task
    def Logout(self):
        with self.client.get(
            f"{config.endpoints.host}/rfm2OnlineApp/logout.action",
            name="promotion_management_Logout",
            headers=HeaderBuilder.logout_dcs(config.endpoints.host),
            catch_response=True,
        ) as Logoutuser:
            try:
                status32 = Logoutuser.status_code
                if status32 == 200:
                    print("Logout is successfull")
                else:
                    print("Logout is unsuccessfull", Logoutuser.text)
                    self.interrupt()
            except Exception as e:
                print(e)
                self.interrupt()


class promotionmanagement(HttpUser):
    tasks = [Profile]
    # wait_time = constant(2)
    # host = "https://mcd-na-perf01.digitalecp.mcd.com"

    weight = config.features.PROMOTIONMANAGEMENT.weight

    FastHttpUser.connection_timeout = config.time_out
    FastHttpUser.network_timeout = config.time_out
    if len(config.wait_time) > 1:
        wait_time = between(config.wait_time[0], config.wait_time[1])
    else:
        wait_time = constant(config.wait_time[0])


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    prommodule.on_stop(environment, **kwargs)
