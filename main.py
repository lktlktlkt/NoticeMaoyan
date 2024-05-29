from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from maoyan import notice, projects

scheduler = BlockingScheduler(timezone='Asia/Shanghai')

long = {
    # "林俊杰武汉": "280019",
    # "王嘉尔广州": "289336",
    # "陈奕迅成都": "282291",
    # "陈奕迅广州": "289532",

}

short = {
    "周杰伦长沙": "307490",
    "陈奕迅佛山": "327144"
}

items = {**short, **long}
logger.info(items)

for alias, item_id in long.items():
    scheduler.add_job(notice, "interval", seconds=20, args=(scheduler, item_id, alias), id=item_id)

for alias, item_id in short.items():
    scheduler.add_job(notice, "interval", seconds=2, args=(scheduler, item_id, alias), id=item_id)


scheduler.add_job(projects, "cron", hour=12, minute=0, second=0, args=(items,))
scheduler.add_job(projects, "cron", hour=23, minute=59, second=59, args=(items,))

scheduler.start()
