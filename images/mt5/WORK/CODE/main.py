import datetime
from time import sleep
import schedule
from dateutil import tz

import MetaTrader5 as mt5

from influxdb_wrapper import influxdb_wrapper
import mt5_wrapper

# TODO
# 設定ファイルからのロード
# 認証


TOKEN = '78mdMPrH02UaKsrsb6Q2Ofj0neRVfRNDaFfrN2RWqreobbh3RtP7jyKX9-Ktvt-JBAthd1FPnZggkRANHi9T8w=='
ORG = "influxdata"
BUCKET = "test"
URL = "http://192.168.0.15"
SYMBOL = "EURJPY"
TF=mt5.TIMEFRAME_H4
REP=20
BAR_OR_TICK="Tick"

start=datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(hours=1)

h=influxdb_wrapper(
                url=URL,
                token=TOKEN,
                org=ORG,
                bucket=BUCKET
                )

#print(h.get_last_time("GBPJPY"))
#print(h.get_dataframe(measurement="GBPJPY",data_type="ohlc",start="2022-12-01",stop="2023-01-01"))

#h.write_dataframe(data=bars,mj="USDJPY",tag="Smybol")

h.write_dataframe(data=mt5_wrapper.get_ticks(symbol=SYMBOL,start=start),
                  measurement=SYMBOL,
                  tag="Smybol"
                  )


def upload_task():
    #TODO Symbol を時系＋Symbolにする

    SYM=SYMBOL
    TIMEFRAME=TF
    last=None
    ticks=None
    #try:
    last=h.get_last_time(measurement=SYMBOL)
    #except Exception as e:
    #    print("except get lasttime")
 #       raise e

    print("execute task")

    if not last:
        last=datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(minutes=1)

    print(last)

    if BAR_OR_TICK == "Tick":
        ticks = mt5_wrapper.get_ticks(symbol=SYMBOL,start=last)
        print(ticks)
        h.write_dataframe(data=ticks,measurement=SYMBOL,tag="Smybol")

    elif BAR_OR_TICK == "Bar":
        bars = mt5_wrapper.get_bars(symbol=SYMBOL,tf=TF,start=start)
        print(bars)
        h.write_dataframe(data=bars,mj=SYMBOL,tag="Symbol")


schedule.every(REP).seconds.do(upload_task)

while True:
	schedule.run_pending()
	sleep(1)
