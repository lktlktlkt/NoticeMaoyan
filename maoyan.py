import datetime
import time

import requests
from loguru import logger


# your access_token
dingding_token = ""
feishu_token = ""

if not(dingding_token or feishu_token):
    raise SystemExit(f"{__file__} 任意配置一个机器人token!")


class Views:

    def __init__(self):
        self.headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                           " (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"),
            'Referer': 'https://wx.maoyan.com/qqw',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

    def get_start_time_and_name(self, item_id):
        url = f"https://wx.maoyan.com/maoyansh/myshow/ajax/v2/performance/{item_id}?"
        params = {
            "buyInstructionType": "1", "optimus_risk_level": "71", "optimus_code": "10",
            "sellChannel": "7", "cityId": "30", "yodaReady": "h5", "csecplatform": "4",
            "csecversion": "2.3.0"
        }
        headers = {
            'Referer': 'https://show.maoyan.com/qqw',
            'Host': 'wx.maoyan.com',
            'Content-Type': 'application/json',
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                          " (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }
        data = requests.get(url, params=params, headers=headers).json().get("data", {})
        return data["name"], data["saleRemindVO"]["onSaleTime"]

    def get_calendar_id_list(self, item_id):
        data = self.make_perform_request(item_id)
        calendar = data.get("data", [])
        return [view.get("showId") for view in calendar]

    def fetch_show_info(self, item_id, data_id):
        params = {
            "performanceId": item_id,
            "optimus_risk_level": "71", "optimus_code": "10", "sellChannel": "7",
            "cityId": "30", "yodaReady": "h5", "csecplatform": "4", "csecversion": "2.3.0",
        }
        url = f"https://show.maoyan.com/maoyansh/myshow/ajax/v2/show/{data_id}/tickets?"
        response = requests.get(url, headers=self.headers, timeout=3, params=params)
        return response.json()

    def get_ticket_remaining_stock(self, item_id, data_id):
        resp = self.fetch_show_info(item_id, data_id)
        sku_list = resp.get("data", [])
        return "\n".join(f'{sku["ticketName"]}{int(sku["ticketPrice"])}：有票'
                         if sku["remainingStock"] else f'{sku["ticketName"]}{int(sku["ticketPrice"])}：无票'
                         for sku in sku_list)

    def make_perform_request(self, item_id):
        url = "https://show.maoyan.com/maoyansh/myshow/ajax/v2/performance/{}/shows/0?performanceId={}"
        response = requests.get(url.format(item_id, item_id), headers=self.headers, timeout=3)
        return response.json()


def send_text_to_feishu(text):
    url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{feishu_token}"
    payload = {
        "msg_type": "text",
        "content": {"text": text}
    }
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers)
    logger.info(response.text)


def send_text_to_dingding(text):
    url = "https://oapi.dingtalk.com/robot/send"
    querystring = {"access_token": dingding_token}
    payload = {
        "msgtype": "text",
        "text": {"content": text}
    }
    headers = {"content-type": "application/json"}
    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
    logger.info(response.text)


def notice(scheduler, item_id, alias=''):
    view = Views()
    perform = view.make_perform_request(item_id)

    if perform.get("code") == 1005:
        name, sell_date = view.get_start_time_and_name(item_id)
        sell_date = datetime.datetime.fromtimestamp(int(sell_date) / 1000)
        send_text_to_dingding(f"【猫眼】\n\n{name}\n\n可预约，售票时间：{sell_date}，前往猫眼查看！")
        # send_text_to_feishu(f"【猫眼】\n\n{name}\n\n可预约，售票时间：{sell_date}，前往猫眼查看！")
        scheduler.remove_job(item_id)
        return

    name = ""
    sessions = perform.get("data", [])

    for session in sessions:
        inventory = session.get("hasInventory")
        logger.info(f"{alias} {item_id} {inventory}")

        if not inventory:
            continue

        if not name:
            name, _ = view.get_start_time_and_name(item_id)

        text = f'{session["name"]}\n{view.get_ticket_remaining_stock(item_id, session["showId"])}'
        logger.info(f'{name}\n{text}')
        send_text_to_dingding(f'【猫眼】\n\n{name}\n\n{text}\n\n前往猫眼购买！')
        # send_text_to_feishu(f'【猫眼】\n\n{name}\n\n{text}\n\n前往猫眼购买！')


def projects(items: dict):
    text = "【猫眼】\n\n 监控演出如下：\n\n"
    view = Views()
    for _, item_id in items.items():
        name, _ = view.get_start_time_and_name(item_id)
        text += name + '\n\n'
        time.sleep(1)
    send_text_to_dingding(text)
    # send_text_to_feishu(text)

