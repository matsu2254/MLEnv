#from datetime import datetime
import datetime 
from time import sleep
import schedule
from dateutil import tz

import MetaTrader5 as mt5

import dbcall
import uploadinfluxdb

TOKEN = '78mdMPrH02UaKsrsb6Q2Ofj0neRVfRNDaFfrN2RWqreobbh3RtP7jyKX9-Ktvt-JBAthd1FPnZggkRANHi9T8w=='
ORG = "influxdata"
BUCKET = "test"
URL = "http://192.168.0.15"
SYMBOL = "EURJPY"
TF=mt5.TIMEFRAME_H4
REP=20


start=datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(hours=1)

#ticks = get_ticks(symbol="USDJPY",start=start)
#bars = get_bars(symbol="USDJPY",tf=mt5.TIMEFRAME_H4,start=start)


#print ( bars)
 
 # 確認
h=dbcall.db_call(
                url=URL,
                token=TOKEN,
                org=ORG,
                bucket=BUCKET
                )
#
#print(h.get_last_time("GBPJPY"))
#print(h.get_dataframe(measurement="GBPJPY",data_type="ohlc",start="2022-12-01",stop="2023-01-01"))
#
#h.write_dataframe(data=bars,mj="USDJPY",tag="Smybol")

h.write_dataframe(data=uploadinfluxdb.get_ticks(symbol=SYMBOL,start=start),
                  measurement=SYMBOL,
                  tag="Smybol"
                  )


def upload_task():
    SYM=SYMBOL
    TIMEFRAME=TF
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
    #bars = uploadinfluxdb.get_bars(symbol=SYM,tf=TIMEFRAME,start=start)
    print(last)
    print(ticks)
    #h.write_dataframe(data=bars,mj=SYM,tag="Symbol")
    h.write_dataframe(data=ticks,measurement=SYM,tag="Smybol")


schedule.every(REP).seconds.do(upload_task)

while True:
	schedule.run_pending()
	sleep(1)
