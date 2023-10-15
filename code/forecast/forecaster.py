import sys
import yaml
import datetime
import math
import glob
from dateutil import tz

import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from influxdb_wrapper import influxdb_wrapper


from greykite.common.data_loader import DataLoader
from greykite.framework.templates.autogen.forecast_config import ForecastConfig
from greykite.framework.templates.autogen.forecast_config import MetadataParam
from greykite.framework.templates.forecaster import Forecaster
from greykite.framework.templates.model_templates import ModelTemplateEnum
from greykite.framework.utils.result_summary import summarize_grid_search_results
from greykite.framework.templates.autogen.forecast_config import ModelComponentsParam

from influxdb_wrapper import influxdb_wrapper


# TODO
# 設定ファイルからのロード
# 認証
# add tag to influxd func
# log


def main(settings :dict) -> None:
    """
    Args:
    Returns:
    Raises:
    Notes:
    """
    # 設定ファイルバリデーション
    if settings['kind'] != "forecaster_config" or settings['apiVersion'] != "v0.1":
        print('kind or version error')
        sys.exit(1)
    
    settings = settings['data']
    config   = settings['CONFIG']
    data     = settings['FORECAST']
    print(settings)

    # 初期化
    infwrap = influxdb_wrapper(
                    url     =  config['INFLUXDB_URL'],
                    token   =  config['INFLUXDB_TOKEN'],
                    org     =  config['INFLUXDB_ORG'],
                    bucket  =  config['INFLUXDB_BUCKET'],
                    )
   

    # 諸々TODO

    output = forecaster(infwrap=infwrap,config=data)
    
    if not output:
        sys.exit(1)
    
    infwrap.write_dataframe(
                data=output,
                measurement=SYMBOL,
                tag=tag
            )


def forecaster(infwrap :influxdb_wrapper,config :dict) -> str:

    """予測藻モデルを書き出す
    """

    HORIZON   = config['HORIZON']   # forecast len, e.g. 3
    TIMECOL   = config['TIMECOL'  ] # timestamp col, e.g. '_time'
    VALUECOL  = config['VALUECOL']  # value col, e.g. 'High'
    FREQ      = config['FREQ']      # freq of data e.g. '4H'
    GOBACK    = config['GOBACK']

    SYMBOL    = config['SYMBOL']
    TYPE      = config['TYPE']
    TIMEFRAME = config['TIMEFRAME']

    # 現在時刻を取得し、現在時刻から指定分遡る 
    global start
    stop  =  datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))
    exec(f"global start; start = stop-datetime.timedelta({GOBACK})")    

    forecaster_name = SYMBOL + '_forecaster_' + stop.strftime('%Y%m%dT%H%M')

    df = infwrap.get_dataframe(
                        measurement=SYMBOL.upper(),
                        timeframe=TIMEFRAME,
                        data_type=TYPE.lower(),
                        start=int(math.floor(start.timestamp())), # 整数値unix time(少数切り捨て)
                        stop=int(math.ceil(stop.timestamp()))     # （少数切り上げ）
                        )
    
    # 保存したデータをロードする
    # インデクスを列へ変更し、バグるのでタイムゾーンあったら消す
    df.reset_index(inplace=True)
    df['_time'] = df['_time'].dt.tz_localize(None)
        
    timestamp   = "[2-9][0-9][0-9][0-9][0-1][0-9][0-3][0-9]T[0-2][0-9][0-5][0-9]"
    model_list  = glob.glob(SYMBOL + "_forecaster_" + timestamp)

    sorted_list = sorted(
                    model_list,
                    key = lambda x: datetime.datetime.strptime(x.split('_')[-1],'%Y%m%dT%H%M'),
                    reverse=True
                    )
    last = sorted_list[0]

    forecaster  = Forecaster()  # Creates forecasts and stores the result
    
    forecaster.load_forecast_result(source_dir=last,load_design_info=False)
    print("loaded")
    
    result = forecaster.run_forecast_config(  # result is also stored as `forecaster.forecast_result`.
                df=df,
                config=ForecastConfig(
                    model_template=ModelTemplateEnum.SILVERKITE.name,
                    #model_template=ModelTemplateEnum.PROPHET.name,
                    #model_components_param=ModelComponentsParam(seasonality=dict(seasonality_mode='multiplicative')),
                    forecast_horizon=2,  # forecasts 365 steps ahead
                    coverage=0.95,         # 95% prediction intervals
                    metadata_param=metadata
                    )
        )


    return forecaster_data

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

