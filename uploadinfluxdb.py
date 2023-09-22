#from datetime import datetime
import datetime 
from time import sleep
import schedule
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import MetaTrader5 as mt5
from dateutil import tz

import dbcall

token = '78mdMPrH02UaKsrsb6Q2Ofj0neRVfRNDaFfrN2RWqreobbh3RtP7jyKX9-Ktvt-JBAthd1FPnZggkRANHi9T8w=='
org = "influxdata"
bucket = "test"
url = "http://192.168.0.15"


def get_ticks(symbol: str,start :datetime) -> pd.DataFrame:
   if not mt5.initialize():
      print("initialize() failed")
      mt5.shutdown()
      return None
   now = datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))
   try:
      ticks = pd.DataFrame(mt5.copy_ticks_range(symbol, start, now, mt5.COPY_TICKS_ALL))
   except Exception as e:
      print(e)
      try:
         ticks = pd.DataFrame(mt5.copy_ticks_range(symbol, now - datetime.timedelta(days=30), now, mt5.COPY_TICKS_ALL))
      except Exception as e:
         print(e)
         raise Exception
   finally:
      mt5.shutdown()
   ticks['time_msc'] = pd.to_datetime(ticks['time_msc'],unit='ms',origin='unix')
   ticks = ticks.set_index('time_msc')
   ticks = ticks.drop(['time','last','volume','volume_real'],axis=1)
   ticks.columns = ['Bid','Ask','Flags']
   ticks['Symbol']=symbol
   return ticks

def get_bars(symbol: str,tf,start :datetime) -> pd.DataFrame:
   # TODO
   # add column for describe datafame
   if not mt5.initialize():
      print("initialize() failed")
      mt5.shutdown()
      return None
   now = datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))
   try:
      bars = pd.DataFrame(mt5.copy_rates_range(symbol, tf, start, now, ))
   except Exception as e:
      print(e)
      try:
         bars = pd.DataFrame(mt5.copy_rates_range(symbol, tf, now - datetime.timedelta(days=30), now, mt5.COPY_TICKS_ALL))
      except Exception as e:
         print(e)
         raise Exception
   finally:
      mt5.shutdown()
   bars['time'] = pd.to_datetime(bars['time'],unit='s',origin='unix')
   bars = bars.set_index('time')
   bars.columns = ['Open','High','Low','Close','Tick_olume','Spread','Real_volume']
   ticks['Symbol']=symbol
   return bars

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

    ticks = get_ticks(symbol=SYM,start=last)
    #bars = get_bars(symbol=SYM,tf=RATE,start=start)
    print(last)
    print(ticks)
    #h.write_dataframe(data=bars,mj=SYM,tag="Symbol")
    h.write_dataframe(data=ticks,measurement=SYM,tag="Smybol")




schedule.every(20).seconds.do(upload_task)
while True:
	schedule.run_pending()
	sleep(1)
