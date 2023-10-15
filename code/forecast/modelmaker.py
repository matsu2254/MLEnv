import sys
import yaml
import datetime
import math
from dateutil import tz

from influxdb_wrapper import influxdb_wrapper
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

    output = modelmaker(infwrap=infwrap,config=data)
    
    if not output:
        sys.exit(1)


def modelmaker(infwrap :influxdb_wrapper,config :dict) -> str:

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
    
    # specify dataset information
    metadata = MetadataParam(
                    time_col=TIMECOL,  # name of the time column ("date" in example above)
                    value_col=VALUECOL,  # name of the value column ("sessions" in example above)
                    freq=FREQ          # "H" for hourly, "D" for daily, "W" for weekly, etc.
                                        # Any format accepted by `pandas.date_range`
                )

    # インデクスを列へ変更し、バグるのでタイムゾーンあったら消す
    df.reset_index(inplace=True)
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
                destination_dir=forecaster_name,
                object_name="forecast_object",
                dump_design_info=False,
                overwrite_exist_dir=False
        )

    glob.glob(SYMBOL + "_forecaster_" + "[2-9][0-9][0-9][0-9][0-1][0-9][0-3][0-9]T[0-2][0-9][0-5][0-9]")[1].split('_')[-1]

    import glob
    sorted(glob.glob(SYMBOL + "_forecaster_" + "[0-9]+++++++T[0-9]+++"))

    return forecaster_name

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

