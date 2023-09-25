import datetime
import schedule
import threading
from time import sleep
from dateutil import tz


import MetaTrader5 as mt5

from influxdb_wrapper import influxdb_wrapper
import mt5_wrapper

# TODO
# 設定ファイルからのロード
# 認証


settings = {   
        CONFIG:{
            INFLUXDB_TOKEN: '78mdMPrH02UaKsrsb6Q2Ofj0neRVfRNDaFfrN2RWqreobbh3RtP7jyKX9-Ktvt-JBAthd1FPnZggkRANHi9T8w==',
            INFLUXDB_URL: "http://192.168.0.15",
            INFKUXDB_ORG: "influxdata",
            INFLUXDB_TAG: "timeframe",

        },
        GETDATA:[
            {
                SYMBOL: "USDJPY",
                TIMEFRAME: mt5.TIMEFRAME_H4,
                REPEAT: 20
            },
            {
                SYMBOL: "AUDJPY",
                TIMEFRAME: "Tickers",
                REPEAT: 20

            },
        ]
     }


# TOKEN = '78mdMPrH02UaKsrsb6Q2Ofj0neRVfRNDaFfrN2RWqreobbh3RtP7jyKX9-Ktvt-JBAthd1FPnZggkRANHi9T8w=='
# ORG = "influxdata"
# BUCKET = "test"
# URL = "http://192.168.0.15"
# SYMBOL = "EURJPY"
# TF=mt5.TIMEFRAME_H4
# REP=20
# BAR_OR_TICK="Tick"

def upload_task(infwrap :influxdb_wrapper,mt5wrap :mt5_wrapper,data :dict):
        #TODO Symbol を時系＋Symbolにする
        
        print("execute task")
        
        symbol      = data["SYMBOL"]
        tag         = data["TAG"]
        timeframe   = data["TIMEFRAME"]
        last        = None
        ticks       = None

        last        = infwrap.get_last_time(measurement=symbol)

        if not last:
            last = datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(minutes=1)

        print(last)

        if str(timeframe) == "Tick":
            ticks = mt5wrap.get_ticks(
                            symbol  = symbol,
                            start   = last,
                            )
            print(ticks)
            
            infwrap.write_dataframe(
                            data        = ticks,
                            measurement = symbol,
                            tag         = tag,
                            )

        else:
            bars = mt5wrap.get_bars(
                            symbol  = symbol,
                            tf      = timeframe,
                            start   = last,
                            )
            print(bars)

            infwrap.write_dataframe(
                            data    = bars,
                            mj      = symbol,
                            tag     = tag,
                            )

def make_thread(infwrap :influxdb_wrapper,mt5wrap :mt5_wrapper,data :dict):
    jt = threading.Thread(target=upload_task,args=(infwrap,mt5wrap,data))
    jt.start()
    

def main():
    start = datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(hours=1)
    config = settings['CONFIG']

    mt5wrap = mt5_wrapper()

    infwrap = influxdb_wrapper(
                    url     =  config['INFLUXDB_URL'],
                    token   =  config['INFLUXDB_TOKEN'],
                    org     =  config['INFLUXDB_ORG'],
                    bucket  =  config['INFLUXDB_BUCKET'],
                    )

    #print(h.get_last_time("GBPJPY"))
    #print(h.get_dataframe(measurement="GBPJPY",data_type="ohlc",start="2022-12-01",stop="2023-01-01"))
    #h.write_dataframe(data=bars,mj="USDJPY",tag="Smybol")

    # prewrite
    # infwrap.write_dataframe(
    #                 data=mt5_wrapper.get_ticks(symbol=SYMBOL,start=start),
    #                 measurement=SYMBOL,
    #                 tag="Smybol"
    #                 )


    
    for d in settings['GET_DATA']: 
        schedule.every(d['REPEAT']).seconds.do(make_thread,infwrap=infwrap,mt5wrap=mt5wrap,data=d)

    while True:
        schedule.run_pending()
        sleep(1)

if __name__ == "__main__":
    main()