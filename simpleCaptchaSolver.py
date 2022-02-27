import base64
import json
import logging
import re
import requests
import time
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models
logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
                logging.warning("[Captcha Solver] You are using the demo apikey.")
                logging.warning("There is no guarantee that demo apikey will work in the future!")
                # because using demo apikey
                text = re.findall(r"RESULT  IS . (.*) .", solved_text)[0]
            else:
                # using your own apikey
                logging.info("[Captcha Solver] You are using your own apikey.")
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
            logging.info(solved)
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
    '''reCaptha V3 解析 -- 原配合 selenium 使用'''

    def __init__(self, SECRETID:str, SECRETKEY:str, driver, timeout=15):
        '''使用腾讯云的免费语音识别, 传入腾讯云账户的 SECRETID, SECRETKEY 和 selenium 的 driver 对象'''
        self.SECRETID, self.SECRETKEY, self.timeout = SECRETID, SECRETKEY, timeout
        self.driver = driver

    def _solve_p(self, url:str):
        msg_url = url
        result1 = upload(msg_url, self.SECRETID, self.SECRETKEY)  # 上传链接返回结果
        return result1


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
        logging.info(st)
        return st
    except TencentCloudSDKException as err:
        logging.error(err)
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
        logging.error(err)
        return False
