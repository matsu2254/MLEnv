import sys
import yaml
import datetime
import schedule
import threading
from time import sleep
from dateutil import tz

from influxdb_wrapper import influxdb_wrapper
from mt5_wrapper import mt5_wrapper

# TODO
# 設定ファイルからのロード
# 認証

# TODO
# add tag to influxd func


# TODO 
# log

#TODO
# 設定を分離

# TIMEFRAME_M1   1
# TIMEFRAME_M2   2
# TIMEFRAME_M3   3
# TIMEFRAME_M4   4
# TIMEFRAME_M5   5
# TIMEFRAME_M6   6
# TIMEFRAME_M10   10
# TIMEFRAME_M12   12
# TIMEFRAME_M15   15
# TIMEFRAME_M20   20
# TIMEFRAME_M30   30
# TIMEFRAME_H1   16385
# TIMEFRAME_H2   16386
# TIMEFRAME_H4   16388
# TIMEFRAME_H3   16387
# TIMEFRAME_H6   16390
# TIMEFRAME_H8   16392
# TIMEFRAME_H12   16396
# TIMEFRAME_D1   16408
# TIMEFRAME_W1   32769
# TIMEFRAME_MN1   49153

# settings = {
#         'CONFIG':{
#             'INFLUXDB_TOKEN': "78mdMPrH02UaKsrsb6Q2Ofj0neRVfRNDaFfrN2RWqreobbh3RtP7jyKX9-Ktvt-JBAthd1FPnZggkRANHi9T8w==",
#             'INFLUXDB_URL': "http://192.168.0.15",
#             'INFLUXDB_ORG': "influxdata",
#             'INFLUXDB_BUCKET': "test",

#         },
#         'GETDATA':[
#             {
#                 'SYMBOL': "USDJPY",
#                 'TIMEFRAME': "TIMEFRAME_H4",
#                 'TAG': "Timeframe",
#                 'REPEAT': 20
#             },
#             {
#                 'SYMBOL': "AUDJPY",
#                 'TIMEFRAME': "Tick",
#                 'TAG': "Timeframe",
#                 'REPEAT': 20

#             },
#         ]
#      }



def main(settings :dict) -> None:
    print(settings)
    config = settings['CONFIG']

    mt5wrap = mt5_wrapper()

    infwrap = influxdb_wrapper(
                    url     =  config['INFLUXDB_URL'],
                    token   =  config['INFLUXDB_TOKEN'],
                    org     =  config['INFLUXDB_ORG'],
                    bucket  =  config['INFLUXDB_BUCKET'],
                    )
    
    for d in settings['GETDATA']: 
        schedule.every(d['REPEAT']).seconds.do(
                                make_thread,
                                infwrap=infwrap,
                                mt5wrap=mt5wrap,
                                data=d
                                )

    while True:
        schedule.run_pending()
        sleep(1)

def make_thread(infwrap :influxdb_wrapper,mt5wrap :mt5_wrapper,data :dict) -> None:
    jt = threading.Thread(target=upload_task,args=(infwrap,mt5wrap,data))
    jt.start()

def upload_task(infwrap :influxdb_wrapper,mt5wrap :mt5_wrapper,data :dict) -> None:
    #TODO Symbol を時系＋Symbolにする
    
    print("execute task")
    
    symbol      = data["SYMBOL"]
    tag         = data["TAG"]
    timeframe   = data["TIMEFRAME"]
    output      = None
    last        = infwrap.get_last_time(measurement=symbol)

    if not last:
        last = datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(minutes=1)

    print(last)

    if str(timeframe).lower() == "tick":
        output = mt5wrap.get_ticks(
                    symbol  = symbol,
                    start   = last,
                    )

    elif isinstance(mt5wrap.get_varofname(name=str(timeframe)),int):
        timeframe = mt5wrap.get_varofname(name=str(timeframe))
        output = mt5wrap.get_bars(
                    symbol  = symbol,
                    tf      = timeframe,
                    start   = last,
                    )

    elif isinstance(timeframe,int):
        output = mt5wrap.get_bars(
                    symbol  = symbol,
                    tf      = timeframe,
                    start   = last,
                    )
    
    else:
        raise ValueError
    
    print(output)

    if len(output) != 0:
        infwrap.write_dataframe(
                        data        = output,
                        measurement = symbol,
                        tag         = tag,
                        )

  
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Takes only one argument. Please specify the config file")
        exit(1)

    settings={}

    try:
        with open(sys.argv[1]) as file:
            settings = yaml.safe_load(file)

    except Exception as e:
        print('Exception occurred while loading YAML...', file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)
    
    if settings['kind'] != "mt5_uploader_config" or settings['apiVersion'] != "v0.1":
        print('kind or version error')
        exit(1)
    main(settings=settings['data'])
