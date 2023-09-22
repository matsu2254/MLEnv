#from datetime import datetime
import datetime 
from time import sleep
import schedule
import pandas as pd
from dateutil import tz

import MetaTrader5 as mt5

import dbcall
import uploadinfluxdb

token = '78mdMPrH02UaKsrsb6Q2Ofj0neRVfRNDaFfrN2RWqreobbh3RtP7jyKX9-Ktvt-JBAthd1FPnZggkRANHi9T8w=='
org = "influxdata"
bucket = "test"
url = "http://192.168.0.15"


start=datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(hours=1)
#ticks = get_ticks(symbol="USDJPY",start=start)
#bars = get_bars(symbol="USDJPY",tf=mt5.TIMEFRAME_H4,start=start)


#print ( bars)
 
 # 確認
h=dbcall.db_call(url=url,token=token,org=org,bucket=bucket)
#
#print(h.get_last_time("GBPJPY"))
#print(h.get_dataframe(measurement="GBPJPY",data_type="ohlc",start="2022-12-01",stop="2023-01-01"))
#
#h.write_dataframe(data=bars,mj="USDJPY",tag="Smybol")

h.write_dataframe(data=get_ticks(symbol="AUDJPY",start=start),measurement="AUDJPY",tag="Smybol")


def upload_task():
    SYM="AUDJPY"
    RATE=mt5.TIMEFRAME_H4
    last=None
    ticks=None
    #try:
    last=h.get_last_time(measurement=SYM)
    #except Exception as e:
    #    print("except get lasttime")
 #       raise e
    print("execute task")
    if not last:
        last=datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(minutes=1)

    ticks = uploadinfluxdb.get_ticks(symbol=SYM,start=last)
    #bars = get_bars(symbol=SYM,tf=RATE,start=start)
    print(last)
    print(ticks)
    #h.write_dataframe(data=bars,mj=SYM,tag="Symbol")
    h.write_dataframe(data=ticks,measurement=SYM,tag="Smybol")


schedule.every(20).seconds.do(upload_task)

while True:
	schedule.run_pending()
	sleep(1)
