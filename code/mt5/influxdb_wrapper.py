from datetime import datetime
import pandas as pd

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


#   |> filter(fn: (r) => r["Timeframe"] == "Tick")


class influxdb_wrapper:
    def __init__(self,url :str,token : str,bucket :str,org : str,write_opt=SYNCHRONOUS):

        self.url        = url           # 
        self.token      = token         # 
        self.bucket     = bucket        # 
        self.org        = org           # 
        self.write_opt  = write_opt     # 
        #TODO
        # bucketなかったら作る

#TODO add tag
    def get_last_time(self, measurement :str, timeframe :str) -> datetime:
        """その銘柄・通貨ペアの最後のデータからタイムスタンプを取得する
        Args:
            measurement : str 銘柄・通貨ペア
            timeframe   : str 時間足・MT５の変数名
        Returns:
            datetime    : 指定の組み合わせの最後のデータからタイムスタンプ
        Raises:
        Note:
        """
        #TODO: エラーハンドリング、
        # queryの実行　DB呼び出し
        # GBPJPYの末尾をとるクエリ
        
        with InfluxDBClient(url=self.url, token=self.token, org=self.org) as client:
            # ohlcそれぞれが一行になってしまうので結合
            last = client.query_api().query(
                    org=self.org,
                    query=f'from(bucket: "{self.bucket}") \
                            |> range(start: 1) \
                            |> filter(fn: (r) => r["_measurement"] == "{measurement}") \
                            |> filter(fn: (r) => r["Timeframe"] == "{timeframe}") \
                            |> tail(n:1) \
                            |> pivot(rowKey:["_time"],columnKey:["_field"],valueColumn:"_value")'
                    )
            client.close()
            
            if len(last) <= 0:
                return None
            
            return last[0].records[0].get_time()

    def get_dataframe(self,measurement :str, timeframe :str, data_type :str, start, stop) -> pd.DataFrame:
        """influxdbからデータを取得する
        Args:
            measurement  : str 銘柄・通貨ペア
            timeframe    : str 時間足・MT５の変数名
            data_type    : "tick" or "ohlc"
            start        : スタート時間
            stop         : ストップ時間
        Returns:
            pd.DataFrame :
        Raises:
        Notes:
        """
        with InfluxDBClient(url=self.url, token=self.token, org=self.org) as client:
            
            if data_type == "ohlc":
                keep='["_time","Ticker","Open","High","Low","Close"]'
            
            elif data_type == "tick":
                keep='["_time","Ticker","Bid","Ask"]'
                
            else:
                return None
            
            query_api = client.query_api()
            # TODO 
            # start, stop　フォーマットを良い感じに
            data_frames = query_api.query_data_frame(
                            f'from(bucket:"{self.bucket}") '
                            f'|> range(start: {start}, stop:{stop}) '
                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement}")'
                            f'|> filter(fn: (r) => r["Timeframe"] == "{timeframe}")'
                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                            f'|> keep(columns: {keep})'
                           )

            client.close()
            
            # 複数またがって取得した場合、dataframeのリストとして渡されるので、適当に結合する
            if type(data_frames) is pd.DataFrame:
                return_data=data_frames
            
            elif type(data_frames) is list:
                return_data=None
                for data_frame in data_frames:
                        return_data = pd.concat([return_data,data_frame])

            return return_data.drop(['result','table'],axis=1).dropna().set_index('_time')

    def write_dataframe(self,data :pd.DataFrame, measurement :str, tag :str) -> bool:
        """influxdbにデータを書き込む
        Args:
            data        : pd.Dataframe 書き込むデータ
            measurement : 通貨ペア・銘柄名
            tag         : influxdbのタグ
        Returns:
            TODO
        Raises:
        Notes:
            influxdbのタグはほぼ”Timeframe”で決め打ち
        """    
        with InfluxDBClient(url=self.url, token=self.token, org=self.org)as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(
                    self.bucket,
                    self.org,
                    record=data, # dataframe
                    data_frame_measurement_name=measurement, # インデックス名相当？
                    data_frame_tag_columns=[tag] # tagが必要?
                   )
            client.close()

    def check_bucket(self,name) -> bool:
        #TODO ?
        pass

    def create_bucket(self,name) -> bool:
        #TODO ?
        pass

