import sys
import yaml
import datetime
import pandas as pd
from time import sleep
from dateutil import tz

from influxdb_wrapper import influxdb_wrapper
from collections import defaultdict
import warnings

warnings.filterwarnings("ignore")

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
    config = settings['CONFIG']
    data  = settings['FORECAST']
    print(settings)

    # 初期化
    infwrap = influxdb_wrapper(
                    url     =  config['INFLUXDB_URL'],
                    token   =  config['INFLUXDB_TOKEN'],
                    org     =  config['INFLUXDB_ORG'],
                    bucket  =  config['INFLUXDB_BUCKET'],
                    )
   

    # 諸々TODO

    output = modelmaker(influxdb_wrapper=infwrap,config=data)
    
    if not output:
        sys.exit


def modelmaker(infwrap :influxdb_wrapper,config :dict) -> str:

    """予測藻モデルを書き出す
    """

    HORIZON  = int() # forecast len, e.g. 3
    TIMECOL  = str() # timestamp col, e.g. '_time'
    VALUECOL = str() # value col, e.g. 'High'
    FREQ     = str() # freq of data e.g. '4H'

    # specify dataset information
    metadata = MetadataParam(
    time_col="_time",  # name of the time column ("date" in example above)
    value_col="High",  # name of the value column ("sessions" in example above)
    freq="4H"          # "H" for hourly, "D" for daily, "W" for weekly, etc.
            # Any format accepted by `pandas.date_range`
    )

    # いる？
    tick = {
        'Bid':'max',
        'Ask':'min',   
    }
    d_ohlc = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    }

    # TODO change
    start = datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))-datetime.timedelta(days=14)
    
    stop = datetime.datetime.now(tz=tz.gettz('Asia/Tokyo'))
   

    infwrap.get_last_time(measurement='AUDJPY',timeframe='Tick')
    df = infwrap.get_dataframe(measurement='USDJPY',timeframe='TIMEFRAME_H4',data_type='ohlc',start='2022',stop='2023-10-04')
    #df = infwrap.get_dataframe(measurement='AUDJPY',timeframe='Tick',data_type='tick',start='2022',stop='2023-10-04')
    #df = df.resample('h').agg(tick).dropna()
    df.reset_index(inplace=True)
    # バグるのでタイムゾーンあったら消す
    df['_time'] = df['_time'].dt.tz_localize(None)
        


    forecaster = Forecaster()  # Creates forecasts and stores the result

    result = forecaster.run_forecast_config(  # result is also stored as `forecaster.forecast_result`.
                df=df,
                config=ForecastConfig(
                    model_template=ModelTemplateEnum.SILVERKITE.name,
                    #model_template=ModelTemplateEnum.PROPHET.name,
                    #model_components_param=ModelComponentsParam(seasonality=dict(seasonality_mode='multiplicative')),
                    forecast_horizon=HORIZON,  # forecasts 365 steps ahead
                    coverage=0.95,         # 95% prediction intervals
                    metadata_param=metadata
                    )
        )
    
    forecaster.dump_forecast_result(
                destination_dir='forecast_nodinfo',
                object_name="forecast_object",
                dump_design_info=False,
                overwrite_exist_dir=False
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
