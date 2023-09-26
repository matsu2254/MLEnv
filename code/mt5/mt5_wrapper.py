#from datetime import datetime
import datetime 
import pandas as pd

import MetaTrader5 as mt5
from dateutil import tz


class mt5_wrapper:
   def __init__(self) -> None:
      # TODO auth infomation ?
      pass

   def get_varname(self,var):
      for k, v in vars(mt5).items():
         if var == v:
            return k
      return None

   def get_varofname(self,name):
      for k,v in vars(mt5).items():
         if name in k:
            return v

   def get_ticks(self,symbol: str,start :datetime) -> pd.DataFrame:
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
      ticks['Timeframe']='Tick'
      return ticks

   def get_bars(self,symbol: str,tf,start :datetime) -> pd.DataFrame:
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
      bars['Timeframe']=self.get_varname(tf)
      return bars

