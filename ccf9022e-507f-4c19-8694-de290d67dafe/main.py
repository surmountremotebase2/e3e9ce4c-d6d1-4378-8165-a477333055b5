from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, EMA, SMA, MACD, MFI, BB
from surmount.logging import log

class TradingStrategy(Strategy):

   @property
   def assets(self):
      return ["MNQ"]

   @property
   def interval(self):
      return "1min"

   # Helper functions for different types of moving averages
   def ma(source, length, ma_type='SMA'):
      if ma_type == 'SMA':
         return ta.SMA(source, length)
      elif ma_type == 'EMA':
         return ta.EMA(source, length)
      elif ma_type == 'WMA':
         return ta.WMA(source, length)
      elif ma_type == 'DEMA':
         return ta.DEMA(source, length)
      elif ma_type == 'TEMA':
         return ta.TEMA(source, length)
      elif ma_type == 'TRIMA':
         return ta.TRIMA(source, length)
      elif ma_type == 'KAMA':
         return ta.KAMA(source, length)
      elif ma_type == 'MAMA':
         mama, fama = ta.MAMA(source)
         return mama
      elif ma_type == 'T3':
         return ta.T3(source, length)
      else:
         raise ValueError(f"Unsupported MA type: {ma_type}")

   def run(self, data):
      data = data["ohlcv"]
      # Define constants
      ATR_PERIOD = 14
      ATR_MULTIPLIER = 1.5
      MA_PERIOD = 55
      MA_TYPE = 'EMA'
      SSL2_PERIOD = 5
      SSL3_PERIOD = 15
      mnq_stake = 0
      # Calculate ATR
      data['ATR'] = ta.ATR(data['High'], data['Low'], data['Close'], timeperiod=ATR_PERIOD)
      data['ATR_Up'] = data['Close'] + (ATR_MULTIPLIER * data['ATR'])
      data['ATR_Low'] = data['Close'] - (ATR_MULTIPLIER * data['ATR'])
      # Calculate MA values
      data['MA'] = self.ma(data['Close'], MA_PERIOD, MA_TYPE)
      data['SSL1_High'] = self.ma(data['High'], MA_PERIOD, MA_TYPE)
      data['SSL1_Low'] = self.ma(data['Low'], MA_PERIOD, MA_TYPE)
      data['SSL2_High'] = self.ma(data['High'], SSL2_PERIOD, 'JMA')  # Example using 'JMA' for SSL2
      data['SSL2_Low'] = self.ma(data['Low'], SSL2_PERIOD, 'JMA')
      data['SSL3_High'] = self.ma(data['High'], SSL3_PERIOD, 'HMA')  # Example using 'HMA' for SSL3
      data['SSL3_Low'] = self.ma(data['Low'], SSL3_PERIOD, 'HMA')

      # Calculate SSL conditions
      data['Hlv1'] = (data['Close'] > data['SSL1_High']).astype(int) - (data['Close'] < data['SSL1_Low']).astype(int)
      data['SSL1'] = data.apply(lambda row: row['SSL1_High'] if row['Hlv1'] < 0 else row['SSL1_Low'], axis=1)
      data['Hlv2'] = (data['Close'] > data['SSL2_High']).astype(int) - (data['Close'] < data['SSL2_Low']).astype(int)
      data['SSL2'] = data.apply(lambda row: row['SSL2_High'] if row['Hlv2'] < 0 else row['SSL2_Low'], axis=1)
      data['Hlv3'] = (data['Close'] > data['SSL3_High']).astype(int) - (data['Close'] < data['SSL3_Low']).astype(int)
      data['SSL3'] = data.apply(lambda row: row['SSL3_High'] if row['Hlv3'] < 0 else row['SSL3_Low'], axis=1)

      # Entry and exit signals
      data['Long_Entry'] = (data['Close'] > data['SSL1']) & (data['Close'] > data['MA'])
      data['Short_Entry'] = (data['Close'] < data['SSL1']) & (data['Close'] < data['MA'])
      data['Long_Exit'] = data['Close'] < data['SSL3']
      data['Short_Exit'] = data['Close'] > data['SSL3']
      if data['Long_Entry']:
         mnq_stake = 1
      if data['Short_Entry']:
         mnq_stake = -1
      if data['Long_Exit'] or data['Short_Exit']:
         mnq_stake = 0
      return TargetAllocation({"MNQ": mnq_stake})