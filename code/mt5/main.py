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
# add tag to influxd func
# log


def main(settings :dict) -> None:
    """scheduleをセットし、MetaTrader5 からデータを取得し、influxdataに書き込む
        Args:
            settings : dict セッティングデータ
        Returns:
            None
        Raises:
        Notes:
    """
    # 設定ファイルバリデーション
    if settings['kind'] != "mt5_uploader_config" or settings['apiVersion'] != "v0.1":
        print('kind or version error')
        exit(1)
    
    settings = settings['data']
    config = settings['CONFIG']
    print(settings)

    # 初期化
    mt5wrap = mt5_wrapper()
    infwrap = influxdb_wrapper(
                    url     =  config['INFLUXDB_URL'],
                    token   =  config['INFLUXDB_TOKEN'],
                    org     =  config['INFLUXDB_ORG'],
                    bucket  =  config['INFLUXDB_BUCKET'],
                    )
    # 
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
    """スケジュールタスクをマルチスレッド化する
    """
    jt = threading.Thread(target=upload_task,args=(infwrap,mt5wrap,data))
    jt.start()

def upload_task(infwrap :influxdb_wrapper,mt5wrap :mt5_wrapper,data :dict) -> None:
    """mt5のデータをアップロードする
    Args:
        infwrap : class influxdbのラッパ
        mt5wrap : class mt5のラッパ
        data    : dict  設定データ
    Returns:
        None
    Raises:
        TODO
    Notes:
    """
    
    print("execute task")
    
    symbol      = data["SYMBOL"]            # 銘柄・通貨ペア
    tag         = data["TAG"]               # influxdbに設定するタグ,基本的にTimeframe
    timeframe   = data["TIMEFRAME"]         # 時間軸。"tick" or int or  任意の文字列
    output      = None                      # outputデータ。
    last        = infwrap.get_last_time(    # USDJPYの４時間足、最後のデータのタイムスタンプを取得
                    measurement=symbol,
                    timeframe=timeframe,
                    )

    # 末尾データのタイムスタンプが得られなければ現在時刻から1分前
    if not last:
        last = datetime.datetime.now(tz=tz.ƒettz('Asia/Tokyo'))-datetime.timedelta(minutes=1)

    print(last)

    # tickならばget_ticksを呼ぶ
    if str(timeframe).lower() == "tick":
        output = mt5wrap.get_ticks(
                    symbol  = symbol,
                    start   = last,
                    )
        
    # 上記以外ならば文字列から変数の値を引く
    elif isinstance(mt5wrap.get_varofname(name=str(timeframe)),int):
        timeframe = mt5wrap.get_varofname(name=str(timeframe))
        output = mt5wrap.get_bars(
                    symbol  = symbol,
                    tf      = timeframe,
                    start   = last,
                    )
        
    # 数値ならそのまま使う
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
        sys.exit(1)

    settings={}

    try:
        with open(sys.argv[1]) as file:
            settings = yaml.safe_load(file)

    except Exception as e:
        print('Exception occurred while loading YAML...', file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)
    
    main(settings=settings)
