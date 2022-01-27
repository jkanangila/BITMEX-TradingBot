""" Changes made:   1.  Stripped Strategy3's signal-generator to its bare minimum i.e. entries are determined
                        by considering only the ohlc and bollinger bands values of the actual and previous 
                        trading range. Whenever a signal is identifyied, ohlc and indicator functions will be
                        saved and used later on in a machine learning classifier. The classifier will be given
                        a number of data points (parameters at entry) and 2 outcomes i.e. wether the trade was
                        positive or not.
"""

from exchanges_v4 import * # TODO Modify when needed

# binance = BinanceExchange(**keys['binance'])
bitmex = BitmexExchange(**keys['bitmex-testnet'])
oanda = OandaExchange(**keys['oanda-practice'])
# poloniex = PoloniexEchange()
# client = bitmex.client()

# SECTION class Strategy2
class Strategy2(UserDefinedFxns):

    def __init__(self):
        UserDefinedFxns.__init__(self)

    # ANCHOR time
    @staticmethod
    def time():
        return datetime.datetime.now().replace(microsecond=0)

    # ANCHOR moving_avg_exp
    def moving_avg_exp(self, datafr, period):
        return datafr['close'].ewm(span=period, adjust=False).mean()
    
    # ANCHOR moving_avg_simp
    def moving_avg_simp(self, datafr, period):
        return datafr['close'].rolling(window=period).mean()
        
    # ANCHOR resistance_level
    def resistance_level(self, datafr):
        # locate and identify values of turning points in the market
        turning_points = self.turning_points(datafr=datafr) 
        # Determine average of peaks-high 
        resistance = turning_points['peaks']['high'].mean()
        # check if the market is in consolidation
        # consolidation = self.consolidation_check(datafr=datafr, trend=trend)
        # if consolidation:
            # the resistance is halfway between the highest-high and the level determined previously
        return resistance + (turning_points['highest-high'] - resistance)/2 # chng local_min_max to highest-high
        # else:
        #     return 'N/A'

    # ANCHOR support_level
    def support_level(self, datafr):
        # locate and identify values of turning points in the market
        turning_points = self.turning_points(datafr=datafr) 
        # Determine average of local minimums
        support = turning_points['bottoms']['lows'].mean()
        # check if the market is in consolidation
        # consolidation = self.consolidation_check(datafr=datafr, trend=trend)
        # if consolidation:
            # the support is halfway between the lowest-low and the level determined previously
        return support - (support - turning_points['lowest-low'])/2 # chng local_min_max to highest-high
        # else:
        #     return 'N/A'
        
    # ANCHOR trendIdentifyer
    def trendIdentifyer(self, datafr, trendType):
        try:
            # time = datetime.datetime.now().replace(microsecond=0)
            # print("%s | Trying to decide on %s trend..." % (self.time(), trendType))
            if trendType == "longTerm":
                numTradingPeriods = 10
            elif trendType == "intermTerm":
                numTradingPeriods = 30
            elif trendType == "shortTerm":
                numTradingPeriods = 40
                
            # input_df = self.CandlesticksData(self.instrument, params=self.params['itermediate'])
            # ema10 = self.moving_avg_exp(datafr=datafr, period=10)
            ema21 = self.moving_avg_exp(datafr=datafr, period=21)
            sma50 = self.moving_avg_simp(datafr=datafr, period=50)
            sma100 = self.moving_avg_simp(datafr=datafr, period=100)
            
            # Check if the last MAs are in correct order i.e ema21>sma50>sma100>sma200 or ema21<sma50<sma100<sma200
            # notice that sma200 has been added to this test
            if ema21.iloc[-1] > sma50.iloc[-1] > sma100.iloc[-1]:
                mask1 = 1
            elif ema21.iloc[-1] < sma50.iloc[-1] < sma100.iloc[-1]:
                mask1 = -1
            else:
                mask1 = 0
            
            # Check if the price has been trading above or below ema21 for the last 15 hours (30 periods)
            test_up = [i > j for i,j in zip(datafr['close'][-numTradingPeriods:], sma50[-numTradingPeriods:])]
            test_dwn = [i < j for i,j in zip(datafr['close'][-numTradingPeriods:], sma50[-numTradingPeriods:])]
            if round((test_up.count(True)/len(test_up))*100, 2) >= 80:
                mask2 = 1
            elif round((test_dwn.count(True)/len(test_dwn))*100, 2) >= 90:
                mask2 = -1
            else:
                mask2 = 0
                
            # Check if long term MAs are advancing or retreating 
            if sma50.iloc[-1] >= sma50.iloc[-2] and sma100.iloc[-1] >= sma100.iloc[-2]:
                mask3 = 1
            elif sma50.iloc[-1] <= sma50.iloc[-2] and sma100.iloc[-1] <= sma100.iloc[-2]:
                mask3 = -1
            else:
                mask3 = 0
                
            # actual trend
            if mask1 == mask2 == mask3== 1:
                return 1
            elif mask1 == mask2 == mask3 == -1:
                return -1
            else:
                return 0
        except:
            # time = datetime.datetime.now().replace(microsecond=0)
            print("%s | Exception while deciding on %s trend." % (self.time(), trendType))
            raise StopIteration("exceptionDuringTrendIdentification")

    # ANCHOR getOHLC
    # @staticmethod
    def getOHLC(self, exchange, instrument, param_dict, trendType):
        # binance
        if exchange in ["binance", "bitmex", "poloniex"]:
            i = 0
            while i < 5:
                try:
                    # time = datetime.datetime.now().replace(microsecond=0)
                    # print("%s | Requesting %s ohlc data from %s for %s..." % (self.time(), trendType, exchange, instrument))
                    response =  {
                        "data":eval(exchange).get_klines(instrument, **param_dict[exchange][trendType]),
                        "status":200
                    }
                    break
                except:
                    seconds(5)
                    print("%s - #%s| Exception while requesting ohlc data from %s. Retrying..." % (self.time(), (i+1), exchange))
                    i += 1
            if i == 5:
                response = {"data":[], "status":"Exception"}
                return response
            else:
                return response
            
        # oanda
        elif exchange == "oanda":
            i = 0
            while i < 5:
                try:
                    # time = datetime.datetime.now().replace(microsecond=0)
                    # print("%s | Requesting %s ohlc data from %s for %s..." % (self.time(), trendType, exchange, instrument))
                    response =  {
                        "data":oanda.get_klines(instrument=instrument, params=param_dict[exchange][trendType]),
                        "status":200
                    }
                    break
                except:
                    seconds(5)
                    print("%s - #%s| Exception while requesting ohlc data from %s. Retrying..." % (self.time(), (i+1), exchange))
                    i += 1
            if i == 5:
                response = {"data":[], "status":"Exception"}
                return response
            else:
                return response
            
        else:
            raise LookupError("Key '%s' not found" % exchange)

    # ANCHOR choppIdx
    @staticmethod
    def choppIdx(datafr, timeperiod):

        # TODO test accuracy of method --> compared with value on bitmex
        high = datafr.high
        low = datafr.low
        close = datafr.close
        atr = datafr.atr # NOTE changed period to 1
        output = deque()

        for i in range(len(datafr)):
            if i < timeperiod*2:
                output.append(0)
            else:
                nmrt = np.log10(np.sum(atr[i-timeperiod:i])/(max(high[i-timeperiod:i]) - min(low[i-timeperiod:i])))
                dnmnt = np.log10(timeperiod)
                output.append(100*nmrt / dnmnt)

        return output

    # ANCHOR: chopp    
    @staticmethod
    def chopp(df, n):
        
        # Rety dataframe with stockstat
        df2 = df.copy()
        df2 = StockDataFrame.retype(df2)
        # Calculate 
        df2['atr1'] = df2['atr_1']
        df2['sumTrueRange'] = df2['atr1'].rolling(n).sum()
        df2['trueHigh'] = df2['high'].rolling(n).max()
        df2['trueLow'] = df2['low'].rolling(n).min()
        
        return (100*log10(df2['sumTrueRange']/(df2['trueHigh']-df2['trueLow'])))/log10(n)

    # ANCHOR: testChopp
    @staticmethod
    # def testChopp(data, n, pos=3):
    def testChopp(data):
        """
        A function designed to determine if the market was choppy starting from a given position going back
        
        data: array containing choppiness index values
        n: number of trading periods to use during test
        pos: position from the end at which the test should start (e.g. actual, previous,... candles)
        """
        # if pos >= 1:
        #     mask = [61.8 < i < 38.2 for i in data.iloc[-(n+pos):-(pos-1)]]
        # elif pos in [0,None]:
        #     mask = [61.8 < i < 38.2 for i in data.iloc[-n:]]
        
        # return mask.count(True)/len(mask) > 0.7

        return data.iloc[-1] < 38.2
    
    # ANCHOR tradeParameters
    def tradeParameters(self, exchange, instrument, param_dict, trendType):
        try:
            # print("%s | Computing indicator functions..." % self.time())
            # datafr = bitmex.get_klines(instrument=instrument, **params_bitmex[timeframe])
            datafr = self.getOHLC(exchange, instrument, param_dict, trendType)
            if datafr["status"] == 200:
                datafr = datafr["data"]
            else:
                raise StopIteration("exceptionRequestOHLC")
                
            datafr.columns = ['open', 'high', 'low', 'close', 'volume', 'complete']
            datafr = StockDataFrame.retype(datafr.copy())
            # ADX
            datafr['adx'] = datafr['adx']
            # +DI, default to 14 days
            datafr['pdi'] = datafr['pdi']
            # -DI, default to 14 days
            datafr['mdi'] = datafr['mdi']
            # ema21
            datafr['ema21'] = datafr['close_21_ema']
            # sma50
            datafr['sma50'] = datafr['close_50_sma']
            # sma100
            datafr['sma100'] = datafr['close_100_sma']
            datafr['chopp'] = self.chopp(datafr, 14)
            datafr = datafr[['open', 'high', 'low', 'close', 'volume', 'pdi', 'mdi', 
                                'ema21', 'sma50', 'sma100', 'adx', 'chopp']]
            
            return datafr
        except:
            print("%s | Exception while computing indicator functions." % self.time())
            raise StopIteration("exceptionWhileComputingIndicatorFunctions")


    # def tradeParameters(self, exchange, instrument, param_dict, trendType):
    #     try:
    #         time = datetime.datetime.now().replace(microsecond=0)
    #         print("%s | Computing indicator functions..." % time)
    #         # datafr = bitmex.get_klines(instrument=instrument, **params_bitmex[timeframe])
    #         datafr = self.getOHLC(exchange, instrument, param_dict, trendType)
    #         if datafr["status"] == 200:
    #             datafr = datafr["data"]
    #         else:
    #             raise StopIteration("exceptionRequestOHLC")

    #         inputs = {
    #             'open': np.array(datafr.o),
    #             'high': np.array(datafr.h),
    #             'low': np.array(datafr.l),
    #             'close': np.array(datafr.c),
    #             'volume': np.array(datafr.v)
    #         }
    #         adx = ADX(inputs, timeperiod=14)
    #         plusDM = PLUS_DI(inputs, timeperiod=14)
    #         minusDM = MINUS_DI(inputs, timeperiod=14)
    #         DIchange = [self.diff(i, j) for i,j in zip(plusDM,minusDM)]
    #         choppiness = self.choppIdx(datafr=datafr, timeperiod=14)
    #         # [o,h,l,c,adx,DIplus,DIminus,DI_diff,choppiness]
    #         datafr["adx"] = adx
    #         datafr["DIplus"] = plusDM
    #         datafr["DIminus"] = minusDM
    #         datafr["DI_diff"] = DIchange
    #         datafr["choppiness"] = choppiness
            
    #         return datafr
    #     except:
    #         time = datetime.datetime.now().replace(microsecond=0)
    #         print("%s | Exception while computing indicator functions." % time)
    #         raise StopIteration("exceptionWhileComputingIndicatorFunctions")

    # ANCHOR signalGenerator
    def signalGenerator(self, exchange, instrument, param_dict):
        try:
            time = datetime.datetime.now().replace(microsecond=0)
            # print("%s | Generating trade signal for %s..." % (time, instrument))
            datafrLongTerm = self.tradeParameters(exchange, instrument, param_dict, trendType="longTerm")
            datafrShortTerm = self.tradeParameters(exchange, instrument, param_dict, trendType="shortTerm")
            l_trend = self.trendIdentifyer(datafrLongTerm, trendType="longTerm")
            s_trend = self.trendIdentifyer(datafrShortTerm, trendType="shortTerm")

            if l_trend == 1:
                key_level = self.resistance_level(datafr=datafrShortTerm[-120:])
            elif l_trend == -1:
                key_level = self.support_level(datafr=datafrShortTerm[-120:])
            else:
                key_level = 0
            

            trn_points = self.turning_points(datafrShortTerm[-40:-1])
            curr_prc = eval(exchange).curr_price(symbol=instrument) # ***
            
            max_peak = trn_points['highest-high'] # most recent high
            lwst_point = trn_points['lowest-low'] # most recent low

            # NOTE place the values used to decide on the trade signal inside a dictionary
            data = {}
            for column in datafrShortTerm.columns:
                data[column] = [datafrShortTerm[column].iloc[-1]]
            
            data["last_price"] = [curr_prc]
            data["Res/sup"] = [key_level]
            data["max_peak"] = [max_peak]
            data["lwst_point"] = [lwst_point]

            if (curr_prc > key_level
            and curr_prc >= max_peak
            and max_peak > key_level
            and datafrShortTerm["adx"].iloc[-1] > 28
            and datafrShortTerm["chopp"].iloc[-1] < 38.2
            and s_trend==l_trend==1):
                data['signal'] = [1]
                return {"data":data, "signal":1}

            elif (curr_prc < key_level
            and curr_prc <= lwst_point
            and lwst_point < key_level
            and datafrShortTerm["adx"].iloc[-1] > 28
            and datafrShortTerm["chopp"].iloc[-1] < 38.2
            and s_trend==l_trend==-1):
                data['signal'] = [-1]
                return {"data":data, "signal":-1}

            else:
                data['signal'] = [0]
                return {"data":{}, "signal":0}
        except:
            time = datetime.datetime.now().replace(microsecond=0)
            print("%s | Trade signal generation failed." % time)
            raise StopIteration("exceptionWhileGeneratingTradeSignal")
    # !SECTION END OF STRATEGY2

# SECTION class Strategy3
class Strategy3(UserDefinedFxns): 
    """BB breakout strategy: use choppines, directional indexes, price actions, and volume to confirm breakouts"""

    def __init__(self):
        UserDefinedFxns.__init__(self)
    
    # ANCHOR time
    @staticmethod
    def time():
        return datetime.datetime.now().replace(microsecond=0)
        
    # ANCHOR z_score
    @staticmethod
    def z_score(param):
        avg = mean(param)
        stdev = std(param)

        return (param - avg)/stdev
    
    # ANCHOR getOHLC
    def getOHLC(self, exchange, instrument, param_dict, trendType):
        # binance
        if exchange in ["binance", "bitmex", "poloniex"]:
            i = 0
            while i < 5:
                try:
                    response =  {
                        "data":eval(exchange).get_klines(instrument, **param_dict[exchange][trendType]),
                        "status":200
                    }
                    break
                except:
                    seconds(5)
                    print("%s - #%s| Exception while requesting ohlc data from %s for %s. Retrying..." % 
                            (self.time(), (i+1), exchange, instrument))
                    i += 1
            if i == 5:
                response = {"data":[], "status":"Exception"}
                return response
            else:
                return response
            
        # oanda
        elif exchange == "oanda":
            i = 0
            while i < 5:
                try:
                    response =  {
                        "data":oanda.get_klines(instrument=instrument, params=param_dict[exchange][trendType]),
                        "status":200
                    }
                    break
                except:
                    seconds(5)
                    print("%s - #%s| Exception while requesting ohlc data from %s for %s. Retrying..." % 
                        (self.time(), (i+1), exchange, instrument))
                    i += 1
            if i == 5:
                response = {"data":[], "status":"Exception"}
                return response
            else:
                return response
            
        else:
            raise LookupError("Key '%s' not found" % exchange)
        
    # ANCHOR: chopp    
    @staticmethod
    def chopp(df, n):
        
        # Rety dataframe with stockstat
        df2 = df.copy()
        df2 = StockDataFrame.retype(df2)
        # Calculate 
        df2['atr1'] = df2['atr_1']
        df2['sumTrueRange'] = df2['atr1'].rolling(n).sum()
        df2['trueHigh'] = df2['high'].rolling(n).max()
        df2['trueLow'] = df2['low'].rolling(n).min()
        
        return (100*log10(df2['sumTrueRange']/(df2['trueHigh']-df2['trueLow'])))/log10(n)
    
    # ANCHOR: color
    @staticmethod
    def color(o,c):
        if o > c:
            return "RED"
        elif o < c:
            return "GREEN"
        else:
            return "N/A"
        
    # ANCHOR shadows
    def shadows(self, datafr):
        """
        shadows()

        Returns
        -------
        -> dict
            a list in which each element is composed of the following ratios: upper-shadow to body, 
            lower-shadow to body and lower to upper shadow, respectively.
        """
        colors = [self.color(o, c) for o,c in zip(datafr['open'], datafr['close'])]
        candleBody = lambda x,y : abs(x - y)
    
        wicks = {
            'uW/b':[], 
            'lW/b':[], 
            'lW/uW':[]
                }
        for _open, high, low, close, color in zip(datafr['open'], datafr['high'], datafr['low'], datafr['close'], colors):
            
            # Determine range of candlestick
            b = candleBody(_open, close)
        
            if color == 'GREEN':
                upper_wick = high  - close
                lower_wick = _open - low
            elif color == 'RED':
                upper_wick = high  - _open
                lower_wick = close - low
            elif color == 'N/A':
                upper_wick = high  - _open
                lower_wick = close - low


            if b == 0 and upper_wick != 0:
                upper_wick_to_body = round(upper_wick, 4)
                lower_wick_to_body = round(lower_wick, 4)
                lower_wick_to_upper_wick = round(lower_wick/upper_wick, 4)
            
            elif b == 0 and upper_wick == 0:
                upper_wick_to_body = round(upper_wick, 4)
                lower_wick_to_body = round(lower_wick, 4)
                lower_wick_to_upper_wick = round(lower_wick, 4)
        
            elif b != 0 and upper_wick == 0:
                upper_wick_to_body = round(upper_wick/b, 4)
                lower_wick_to_body = round(lower_wick/b, 4)
                lower_wick_to_upper_wick = round(lower_wick, 4)
        
            else:
                upper_wick_to_body = round(upper_wick/b, 4)
                lower_wick_to_body = round(lower_wick/b, 4)
                lower_wick_to_upper_wick = round(lower_wick/upper_wick, 4)
            
            wicks['uW/b'].append(upper_wick_to_body)
            wicks['lW/b'].append(lower_wick_to_body)
            wicks['lW/uW'].append(lower_wick_to_upper_wick)  
        return wicks
        
    # ANCHOR: testChopp
    @staticmethod
    def testChopp(data, n, pos=3):
        """
        A function designed to determine if the market was choppy starting from a given position going back
        
        data: array containing choppiness index values
        n: number of trading periods to use during test
        pos: position from the end at which the test should start (e.g. actual, previous,... candles)
        """
        if pos >= 1:
            mask = [61.8 < i < 38.2 for i in data.iloc[-(n+pos):-(pos-1)]]
        elif pos in [0,None]:
            mask = [61.8 < i < 38.2 for i in data.iloc[-n:]]
        
        return mask.count(True)/len(mask) > 0.7
    
    # ANCHOR: testChopp2
    @staticmethod
    def testChopp2(data):
        """
        A function designed to determine if the market was choppy starting from a given position going back
        
        args
            (pd.core.dataframe)    data: array containing choppiness index values
            (int)    n: number of trading periods to use during test
            (int)    pos: position from the end at which the test should start (e.g. actual, previous,... candles)

        Return
        (bool) True or False depending on test results
        """
        return data.iloc[-1] < 38.2
    
    # ANCHOR: testBb
    def testBb(self, datafr,n,pos=3):
        """ 
        For the time period specified, test if the candlesticks opened and closed within inside the boolinger band.
        Return True if at least  90 percent of the data passed the test

        args
            (pd.core.dataframe)    data: array containing choppiness index values
            (int)    n: number of trading periods to use during test
            (int)    pos: position from the end at which the test should start (e.g. actual, previous,... candles)

        Return
        (bool) True or False depending on test results
        """
        ub = datafr['ub'].iloc[-(n+pos):-(pos-1)]
        lb = datafr['lb'].iloc[-(n+pos):-(pos-1)]
        o = datafr['open'].iloc[-(n+pos):-(pos-1)]
        c = datafr['close'].iloc[-(n+pos):-(pos-1)]
        
        mask = []
        for i,j,w,z in zip(o,c,lb,ub):
            color = self.color(i,j)
            if color == "GREEN":
                test = j < z and i > w
                mask.append(test)
            elif color == "RED":
                test = i < z and j > w
                mask.append(test)
            else:
                test = "N/A"
                mask.append(test)
        
        return mask.count(True)/len(mask) > 0.9
    
    # ANCHOR testDIs
    @staticmethod
    def testDIs(df_lTerm, df_iTerm):
        tests = {}
        
        # Determine position of direction indices on longterm timeframe
        if df_lTerm['pdi'].iloc[-1] > df_lTerm['mdi'].iloc[-1]:
            tests['longTerm'] = 1
        elif df_lTerm['pdi'].iloc[-1] < df_lTerm['mdi'].iloc[-1]:
            tests['longTerm'] = -1
        else:
            tests['longTerm'] = 0
            
        # Determine position of direction indices on intermediate timeframe
        if df_iTerm['pdi'].iloc[-1] > df_iTerm['mdi'].iloc[-1]:
            tests['intermTerm'] = 1
        elif df_iTerm['pdi'].iloc[-1] < df_iTerm['mdi'].iloc[-1]:
            tests['intermTerm'] = -1
        else:
            tests['intermTerm'] = 0
            
        return tests
    
    # ANCHOR tradeParameters
    def tradeParameters(self, exchange, instrument, param_dict, trendType):
        try:
            datafr = self.getOHLC(exchange, instrument, param_dict, trendType)
            if datafr["status"] == 200:
                datafr = datafr["data"]
            else:
                raise StopIteration("exceptionRequestOHLC")
                
            datafr.columns = ['open', 'high', 'low', 'close', 'volume', 'complete']
            pd.set_option('mode.chained_assignment', None)
            datafr = StockDataFrame.retype(datafr.copy())
            # +DI, default to 14 days
            datafr['pdi'] = datafr['pdi']
            # -DI, default to 14 days
            datafr['mdi'] = datafr['mdi']
            # compute percentage difference of DIs
#             datafr['diffDI'] = self.var_diff(datafr.pdi, datafr.mdi)
            datafr['diffDI'] = [self.var_diff(i,j) for i,j in zip(datafr.pdi, datafr.mdi)]
            # ema21
            datafr['ema21'] = datafr['close_21_ema']
            # sma50
            datafr['sma50'] = datafr['close_50_sma']
            # sma100
            datafr['sma100'] = datafr['close_100_sma']
            # bolling, including upper band and lower band
            datafr['bb'] = datafr['boll']
            datafr['ub'] = datafr['boll_ub']
            datafr['lb'] = datafr['boll_lb']
            # Standardise volume readings
            datafr['z_volume'] = self.z_score(datafr['volume'])
            # choppines index
            datafr['chopp'] = self.chopp(datafr, 14)
            s = self.shadows(datafr)
            datafr['uW/b'], datafr['lW/b'], datafr['lW/uW'] = s['uW/b'],s['lW/b'],s['lW/uW']
            datafr = datafr[['open', 'high', 'low', 'close', 'volume', 'pdi', 'mdi', 'ema21', 'sma50', 
                            'sma100', 'ub', 'lb', 'diffDI', 'z_volume', 'chopp', 'uW/b', 'lW/b', 'lW/uW']]
#             datafr = datafr[['open', 'high', 'low', 'close', 'volume', 'pdi', 'mdi', 
#                              'ema21', 'sma50', 'sma100', 'ub', 'lb', 'z_volume', 'chopp', 'diffDI']]
            
            return datafr
        except:
            print("%s | Exception while computing indicator functions." % self.time())
            raise StopIteration("exceptionWhileComputingIndicatorFunctions")
            
    # ANCHOR signalGenerator
    def signalGenerator(self, exchange, instrument, param_dict):
        try:
#             print("%s | Generating trade signal for %s..." % (self.time(), instrument))
            datafr = self.tradeParameters(
                                    exchange=exchange, 
                                    instrument=instrument, 
                                    param_dict=param_dict, 
                                    trendType='shortTerm')
            
            # Extract actual and previous values for different indicators and ohlc
            data = {}
            for column in datafr.columns:
                data[column] = {}
                data[column]['actual'] = datafr[column].iloc[-1]
                data[column]['previous'] = datafr[column].iloc[-2]
            
            actlPrice = eval(exchange).curr_price(instrument)
            prevColor = self.color(data['open']['previous'], data['close']['previous'])
            # testBB = self.testBb(datafr, 12)
            # testCHOPP = self.testChopp(datafr['chopp'], 12)
            
            # UPPER BAND BREAKOUT
            if (prevColor == "GREEN" and data['open']['previous'] < data['ub']['previous'] 
                    and data['close']['previous'] > data['ub']['previous'] 
                    # and testBB 
                    # and data['chopp']['previous'] < 38.2 
                    # and data['chopp']['actual'] < 38.2 
                    and actlPrice > data['ub']['actual']
                    and actlPrice > data['close']['previous']):
                    # and actlPrice > data['ema21']['actual']
                    # and data['close']['previous'] > data['ema21']['previous']  
                    # and data['pdi']['actual'] > data['mdi']['actual']
                    # and data['diffDI']['actual'] > 0.6
                    # and data['z_volume']['previous'] > 1
                    # and data['uW/b']['previous'] < 0.5):
                
                return {'signal':1, 'data':data}
            
            # LOWER BAND BREAKOUT
            elif (prevColor == "RED"and data['open']['previous'] > data['lb']['previous']
                    and data['close']['previous'] < data['lb']['previous']
                    # and testBB 
                    # and data['chopp']['previous'] < 38.2 
                    # and data['chopp']['actual'] < 38.2
                    and actlPrice < data['lb']['actual']
                    and actlPrice < data['close']['previous']):
                    # and actlPrice < data['ema21']['actual']
                    # and data['close']['previous'] < data['ema21']['previous']
                    # and data['pdi']['actual'] < data['mdi']['actual']
                    # and data['diffDI']['actual'] > 0.6
                    # and data['z_volume']['previous'] > 1
                    # and data['lW/b']['previous'] < 0.5):
                
                return {'signal':-1, 'data':data}
            
            else:
                return {'signal':0, 'data':[]}

        except:
            print("%s | Trade signal generation failed." % self.time())
            raise StopIteration("exceptionWhileGeneratingTradeSignal")
    # !SECTION 

# SECTION  class Log_folder_init
class Log_folder_init(object):
    # Note: The dictionary "columns" reffered to in the next line is located inside the configuration file
    list_folders_noExt = list(columns.keys())
    list_folders_Ext = [i + '.csv' for i in list_folders_noExt]
    
    # 'instrument', 'tradeID', 'orderID', 'exchange', 'quantity','entryPrice', 'side', 'trailing_distance'

    @ staticmethod
    # ANCHOR get_script_path
    def get_script_path():
        """Returns the path(folder) in which the script is located"""
        return os.path.dirname(os.path.realpath(__file__))    
    
    # ANCHOR list_of_paths_dir
    @ staticmethod
    def list_of_paths_dir(directory, file_extension):
        """ Return a list of paths for all the files matching an extension in a given directory."""
        return glob.glob(os.path.join(directory, '*.' + file_extension))
    
    @staticmethod
    def check_csv_state(file_name, path):
        try:
            # try to load the csv. If the csv does not have any columns or rows it will return an exception
            pd.read_csv(path)
        except:
            # Then call the template() method for the provided file name and add the columns. 
            csv_file = template(file_name, 'df')
            csv_file.to_csv(path, index=True)
    
    # ANCHOR file_paths_dictionary
    def file_paths_dictionary(self):
        """Returns a dictionary of log-files-paths where the basenames are used as keys"""
        output = {}
        
        # main_directory = os.getcwd()
        main_directory = self.get_script_path() # TODO change to this in actual python file
        
        logfiles_path = os.path.join(main_directory, "log")
        # check if log folder exists. If it does not, create it.
        if not os.path.exists(logfiles_path):
            os.makedirs(logfiles_path)
        
        # create log files if they do not exist
        list_of_files_dir = os.listdir(logfiles_path)
#         for file in ['signal_data_log.csv', 'trade_data_log.csv', 'closed_trade_summary.csv', 'open_trades_summary.csv']:
        for file in Log_folder_init.list_folders_Ext:
            if file not in list_of_files_dir:
                files = open(os.path.join(logfiles_path, file), "x")
                files.close()

        list_of_paths_csv = self.list_of_paths_dir(logfiles_path, 'csv')

        for entry in list_of_paths_csv:
            output[os.path.basename(entry).split(".")[0]] = entry
            
        # add column names to the created log files
        for file_name in Log_folder_init.list_folders_noExt:
            path = output[file_name] 
            self.check_csv_state(file_name, path)
        
        # try:
        #     df1 = pd.read_csv(output['trade_data_log'])
        # except:
        #     c_trade_data_log = template('trade_data_log', 'df')
        #     c_trade_data_log.to_csv(output['trade_data_log'], index=True)
        
        # #2. closed_trade_summary
        # try:
        #     df2 = pd.read_csv(output['closed_trade_summary'])
        # except:
        #     c_closed_trade_summary = template('closed_trade_summary', 'df')
        #     c_closed_trade_summary.to_csv(output['closed_trade_summary'], index=True)
        
        # #3. open_trades_summary
        # # These information should come from the market order response
        # try:
        #     df3 = pd.read_csv(output['open_trades_summary'])
        # except:
        #     c_open_trades_summary = template('open_trades_summary', 'df')
        #     c_open_trades_summary.to_csv(output['open_trades_summary'], index=True)

        return output
    # !SECTION 
    
    # SECTION  class Data_logger
class Data_logger(Log_folder_init):
    
    def __init__(self):
        Log_folder_init.__init__(self)
        self.files_path_dict = self.file_paths_dictionary()
    
    # ANCHOR logdata_tocsv
    def logdata_tocsv(self, datafr, filename, mode=None, index=bool):
        """ Append provided dataframe to the specified spreadsheet log.
        
        Params:
        ------
        index: bool - True/False - specify whether the index should be saved
        datafr: dataframe to append
        """
        # NOTE: if a mode is passsed, use it. But by default use append. 
        if mode == 'a':
    #         intermdf = pd.read_csv(self.files_path_dict[filename])
    #         if not intermdf.empty:
            datafr.to_csv(self.files_path_dict[filename], mode='a', header=False, index=index)
    #         else:
    #             datafr.to_csv(self.files_path_dict[filename], mode='a', header=True, index=index)
        else:
            datafr.to_csv(self.files_path_dict[filename], mode=mode, header=True, index=index)
    
    # ANCHOR readcsv
    def readcsv(self, filename):
        """
        Read one of the csvs in the log folder.
        Acceptable file names: signal_data_log, trade_data_log, trade_summary, open_trades_summary"""
        a = pd.read_csv(self.files_path_dict[filename])
        return a
    # !SECTION 