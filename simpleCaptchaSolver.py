import base64
import json
import random
import re
import requests
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models


class simpleSolver():
    '''解析简单的图片验证码'''

    def __init__(self, TRUECAPTCHA_USERID:str, TRUECAPTCHA_APIKEY:str, timeout=15) -> None:
        '''
        传入 TRUECAPTCHA 的 键钥对
        '''
        self.TRUECAPTCHA_USERID, self.TRUECAPTCHA_APIKEY, self.timeout = TRUECAPTCHA_USERID, TRUECAPTCHA_APIKEY, timeout

    def solve(self, f:str) -> dict:  # f是png文件名字，你需要保存验证码为本地图片再进行此操作
        '''上传本地图片文件,返回 json 数据'''
        with open(f, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        # print(encoded_string)
        url = 'https://api.apitruecaptcha.org/one/gettext'

        data = {'userid': self.TRUECAPTCHA_USERID,
                'apikey': self.TRUECAPTCHA_APIKEY,  'data': str(encoded_string)[2:-1]}
        r = requests.post(url=url, json=data)
        j = json.loads(r.text)
        return(j)

    def handle_captcha_solved_result(solved: dict) -> str:
        """Since CAPTCHA sometimes appears as a very simple binary arithmetic expression.
        But since recognition sometimes doesn't show the result of the calculation directly,
        that's what this function is for.
        """
        if "result" in solved:
            solved_text = solved["result"]
            if "RESULT  IS" in solved_text:
                print("[Captcha Solver] You are using the demo apikey.")
                print("There is no guarantee that demo apikey will work in the future!")
                # because using demo apikey
                text = re.findall(r"RESULT  IS . (.*) .", solved_text)[0]
            else:
                # using your own apikey
                print("[Captcha Solver] You are using your own apikey.")
                text = solved_text
            operators = ["X", "x", "+", "-"]
            if any(x in text for x in operators):
                for operator in operators:
                    operator_pos = text.find(operator)
                    if operator == "x" or operator == "X":
                        operator = "*"
                    if operator_pos != -1:
                        left_part = text[:operator_pos]
                        right_part = text[operator_pos + 1:]
                        if left_part.isdigit() and right_part.isdigit():
                            return eval(
                                "{left} {operator} {right}".format(
                                    left=left_part, operator=operator, right=right_part
                                )
                            )
                        else:
                            # Because these symbols("X", "x", "+", "-") do not appear at the same time,
                            # it just contains an arithmetic symbol.
                            return text
            else:
                return text
        else:
            print(solved)
            raise KeyError("Failed to find parsed results.")

    def get_captcha_solver_usage(self) -> dict:
        url = "https://api.apitruecaptcha.org/one/getusage"

        params = {
            "username": self.TRUECAPTCHA_USERID,
            "apikey": self.TRUECAPTCHA_APIKEY,
        }
        r = requests.get(url=url, params=params)
        j = json.loads(r.text)
        return j


class reCapthaSolver():
    '''reCaptha V3 解析 -- 配合 selenium 使用'''

    def __init__(self, SECRETID:str, SECRETKEY:str, driver, timeout=15):
        '''使用腾讯云的免费语音识别, 传入腾讯云账户的 SECRETID, SECRETKEY 和 selenium 的 driver 对象'''
        self.SECRETID, self.SECRETKEY, self.timeout = SECRETID, SECRETKEY, timeout
        self.driver = driver

    def _solve_p(self, url:str):
        msg_url = url
        result1 = upload(msg_url, self.SECRETID, self.SECRETKEY)  # 上传链接返回结果
        return result1

    # 关键点，下面两函数直接套着用就行了，不用管，这里是重点
    def solve_selen(self, XPathInfo:str):
        '''传入验证框 iframe 对应的 XPath'''
        # 等待加载上验证框，验证框iframe被套在一个form中
        WebDriverWait(self.driver, self.timeout*2, 0.5).until(
            EC.visibility_of_element_located((By.XPATH, XPathInfo)))
        # 进入验证框所在iframe
        time.sleep(random.uniform(0.1, 0.5))
        self.driver.switch_to.frame(
            self.driver.find_element(By.XPATH, XPathInfo))
        # '//*[@id="form-submit"]/div[2]/div/div/div/iframe'))
        print("加载验证中")
        # 等待勾选框可点击再点击
        WebDriverWait(self.driver, self.timeout, 0.5).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#recaptcha-anchor"))).click()
        # 随机2~3秒避免加载不出来
        time.sleep(random.uniform(2, 3))
        print(1)
        try:
            # 回到默认页面
            self.driver.switch_to.default_content()
            # 等待点击勾选框后的弹窗界面iframe有没有加载出来
            WebDriverWait(self.driver, self.timeout, 0.5).until(
                EC.visibility_of_element_located((By.XPATH, '/html/body/div[10]/div[4]/iframe')))
            # 进入弹窗界面的iframe
            self.driver.switch_to.frame(self.driver.find_element(
                By.XPATH, '/html/body/div[10]/div[4]/iframe'))
            print(2)
            # 等待语音按钮是否加载出来，注意，这里在shadow-root里面，不可以直接用css选择器或xpath路径点击
            WebDriverWait(self.driver, self.timeout*2, 0.5).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="recaptcha-audio-button"]')))
            print(3)
            # 选中语音按钮
            self.driver.find_element(
                By.XPATH, '//*[@id="recaptcha-audio-button"]')
            # 初始化键盘事件
            Ac = ActionChains(self.driver)
            # tab按键选中
            time.sleep(random.uniform(0.5, 1))
            Ac.send_keys(Keys.TAB).perform()
            # enter按键点击
            time.sleep(random.uniform(0.7, 1.8))
            Ac.send_keys(Keys.ENTER).perform()
            print("点击了语音按钮")
            # 等待页面跳转出现下载按钮，跳转后会出现语音下载按钮，需要捕获它的href值，它就是音频链接msg_url
            WebDriverWait(self.driver, self.timeout*2, 0.5).until(
                EC.visibility_of_element_located((By.XPATH, '/html/body/div/div/div[7]/a')))
            msg_url = self.driver.find_element(
                By.XPATH, '/html/body/div/div/div[7]/a').get_attribute("href")  # 获取链接
            print(4)
            result1 = upload(msg_url, self.SECRETID,
                             self.SECRETKEY)  # 上传链接返回结果
            time.sleep(1)
            print(5)
            print("识别结果为：")
            print(result1)
            # 等待加载填写框
            WebDriverWait(self.driver, self.timeout, 0.5).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="audio-response"]')))
            # 选中填写框
            self.driver.find_element(
                By.XPATH, '//*[@id="audio-response"]').send_keys(result1)
            print(6)
            # 随机时长，避免判断为机器人
            time.sleep(random.uniform(1.5, 3))
            # 等待加载verify验证按钮
            WebDriverWait(self.driver, self.timeout, 0.5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="recaptcha-verify-button"]')))
            # 选中点击verify按钮
            self.driver.find_element(
                By.XPATH, '//*[@id="recaptcha-verify-button"]').click()
            time.sleep(random.uniform(0.7, 2))
            print("语音验证结束")
        except Exception as e:
            print(e)
        print(7)
        # 回到初始页面，进行下一步操作
        self.driver.switch_to.default_content()
        print(8)
        return


def upload(msg_url:str, SECRETID:str, SECRETKEY:str):
    '''上传音频链接msg_url'''
    try:
        cred = credential.Credential(SECRETID, SECRETKEY)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "asr.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = asr_client.AsrClient(cred, "", clientProfile)

        req = models.CreateRecTaskRequest()
        params = {
            "EngineModelType": "16k_en",
            "ChannelNum": 1,
            "ResTextFormat": 0,
            "SourceType": 0,
            "Url": msg_url
        }
        req.from_json_string(json.dumps(params))

        resp = client.CreateRecTask(req)
        # print(resp)
        ID = json.loads(resp.to_json_string())["Data"]["TaskId"]
        # print(ID)
        count = 0
        while True:
            st = get_result(int(ID), SECRETID, SECRETKEY)
            if st != False:
                break
            time.sleep(0.7)
            count += 1
            if count > 120:
                return False
        print(st)
        return st
    except TencentCloudSDKException as err:
        print(err)
        return False


def get_result(id_d:str, SECRETID:str, SECRETKEY:str) -> str:
    try:
        cred = credential.Credential(SECRETID, SECRETKEY)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "asr.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = asr_client.AsrClient(cred, "", clientProfile)

        req = models.DescribeTaskStatusRequest()
        params = {
            "TaskId": id_d
        }
        req.from_json_string(json.dumps(params))

        resp = client.DescribeTaskStatus(req)
        # print(resp.to_json_string())
        if json.loads(resp.to_json_string())["Data"]["StatusStr"] == "waiting" or json.loads(resp.to_json_string())["Data"]["StatusStr"] == "doing":
            return False
        try:
            json.loads(resp.to_json_string())[
                "Data"]["Result"].split("]")[-1][2:]
        except:
            # print(json.loads(resp.to_json_string()))
            return False
        return json.loads(resp.to_json_string())["Data"]["Result"].split("]")[-1][2:-1]

    except TencentCloudSDKException as err:
        print(err)
        return False
