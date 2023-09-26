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
