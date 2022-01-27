import glob
import json
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import bitmex
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pytz
from numpy import log10, mean, std
from pause import seconds
from scipy.signal import argrelmax, argrelmin
from stockstats import StockDataFrame

from configuration import *

# from mpl_finance import candlestick2_ohlc
# from poloniex.poloniex import Poloniex

contract_price_dict = {
            'XBTUSD': 1, 'ADAZ19': 1, 'BCHZ19': 1, 'EOSZ19': 1,
            'ETHUSD': 0.0001, 'LTCZ19': 1, 'TRXZ19': 1, 'XRPZ19': 1
            }

# SECTION  BitmexExchange
class BitmexExchange(object):
    def __init__(self, api_key, api_secret, test):
        self.api_key=api_key
        self.api_secret=api_secret
        self.test=test
    
    # ANCHOR client
    def client(self):
        client = bitmex.bitmex(
            test=self.test,
            api_key=self.api_key,
            api_secret=self.api_secret)
        return client
    
    # ANCHOR get_klines
    def get_klines(self, instrument=str, binSize=str, count=int):
            ohlc = pd.DataFrame(self.client().Trade.Trade_getBucketed(
                    binSize=binSize,
                    columns='close,high,open,low,timestamp,volume',
                    symbol=instrument,
                    partial=True,
                    count=count,
                    reverse=True
                ).result()[0])

            _time = [i.to_pydatetime() for i in ohlc['timestamp']]
            ohlc = ohlc[['open', 'high', 'low', 'close', 'volume']]
            ohlc['time'] = _time
            ohlc.columns = ['o', 'h', 'l', 'c', 'v', 'time']
            ohlc = ohlc.reindex(index=ohlc.index[::-1])

            # Change count to appropriate number of days
            return ohlc.reset_index(drop=True)
    
    # ANCHOR curr_price
    def curr_price(self, symbol):
        ticker = self.client().Trade.Trade_getBucketed(
            symbol=symbol, 
            binSize='1m', 
            count=1, 
            partial=True, 
            reverse=True
                        ).result()[0]
        return float(ticker[0]['close'])

    # ANCHOR new_order
    def new_order(self, symbol, orderQty, text, side=None, price=None, stopPx=None, ordType=None):
        """
        Post a mew order
        Params
        ------
        symbol: string - Instrument symbol. e.g. 'XBTUSD'.
        side: string - Valid options: Buy, Sell. Defaults to 'Buy' unless orderQty is negative.
        orderQty: double - Optional Order quantity in units of the instrument (i.e. contracts)
        price: double - Optional limit price for 'Limit', 'StopLimit', and 'LimitIfTouched' orders.
        stopPx: double - Optional trigger price for 'Stop', 'StopLimit', 'MarketIfTouched', and 
                'LimitIfTouched' orders. Use a price below the current price for stop-sell 
                orders and buy-if-touched orders. Use execInst of 'MarkPrice' or 'LastPrice' 
                to define the current price used for triggering.
        ordType: string - Order type. Valid options: Market, Limit, Stop, StopLimit, MarketIfTouched, 
                LimitIfTouched, Pegged. Defaults to 'Limit' when price is specified. Defaults 
                to 'Stop' when stopPx is specified. Defaults to 'StopLimit' when price and 
                stopPx are specified.
        text: string - order annotation. e.g. 'Take profit'.
        """
        # NOTE always update leverage then place order
        return self.client().Order.Order_new(
            symbol=symbol ,
            side=side,
            orderQty=orderQty,
            price=price,
            stopPx=stopPx,
            ordType=ordType,
            timeInForce='GoodTillCancel',
            text=text
        ).result()[0]

    # ANCHOR order_quantity
    def order_quantity(self, symbol, frctn):
        """ 
        Calculate the order quantity as a fraction of the account's balance
        Params
        ------
        symbol: string - Instrument symbol. e.g. 'XBTUSD'.
        frctn: double - Fraction of the account to use. (units - percent) 
        """
        margin = self.client().User.User_getMargin().result()[0]
        balanceBTC = margin['availableMargin']
        balanceBTC = balanceBTC/100000000
        price = self.curr_price(symbol=symbol)
        balanceQuote = balanceBTC*price
        
        perc_balance = frctn/100
        quantity = balanceQuote*perc_balance
        if quantity < 1:
            return 1
        else:
            return quantity

    # ANCHOR order_quantity2
    def order_quantity2(self, symbol, frctn, leverage):
        """ 
        Calculate the order quantity as a fraction of the account's balance
        Params
        ------
        symbol: string - Instrument symbol. e.g. 'XBTUSD'.
        frctn: double - Fraction of the account to use. (units - percent)
        leverage: double - leverage to be applied on the position
        """
        margin = self.client().User.User_getMargin().result()[0]
        balanceBTC = margin['availableMargin']
        balanceBTC = balanceBTC/100000000
        contract_price = contract_price_dict[symbol]
        price = self.curr_price(symbol=symbol)
        if symbol == 'XBTUSD':
            trade_balance = balanceBTC*price*(frctn/100)
        else:
            trade_balance = balanceBTC*(frctn/100)
            if symbol not in ['ETHUSD', 'XBTUSD']:
                contract_price = contract_price_dict[symbol]*price
        return round((trade_balance / contract_price) * leverage)

    # ANCHOR update_leverage
    def update_leverage(self, symbol, leverage):
        """ 
        Update leverage of position for a specific symbol
        Params
        ------
        symbol: string - Instrument symbol. e.g. 'XBTUSD'.
        leverage:   Leverage value. Send a number between 0.01 and 100 
                    to enable isolated margin with a fixed leverage. 
                    Send 0 to enable cross margin.
        """
        # NOTE cross margin means using the entire account's margin
        # NOTE always update leverage then place order
        return self.client().Position.Position_updateLeverage(
            symbol=symbol, 
            leverage=leverage).result()[0]
    
    # ANCHOR get_orderID
    def get_orderID(self, symbol, text):
        """
        Retrieve orderID from account using the text provide when placing order
        Params
        ------
        symbol: string - Instrument symbol. e.g. 'XBTUSD'.\n
        text: string - order annotation. e.g. 'Take profit'.
        """
        orderbook = self.client().Order.Order_getOrders(symbol=symbol).result()[0]
        orderbook = pd.DataFrame(orderbook)
        orderID_index = orderbook[orderbook['text']==text].index[0]
        return orderbook.loc[orderID_index]['orderID']

    # ANCHOR cancel_order
    def cancel_order(self, orderID, text=None):
        """
        Cancel a specific active order\n
        Params
        ------
        orderID: Order ID(s);\n
        text: e.g. Optional cancellation annotation. e.g. 'Spread Exceeded'
        """
        return self.client().Order.Order_cancel(
                orderID=orderID, 
                text=text).result()[0]
    
    # ANCHOR cancel_allOrders
    def cancel_allOrders(self, symbol=None):
        """
        Cancel all open orders
        Params
        ------
        symbol: str - Optional. If provided, only cancels orders for that symbol
        """
        return self.client().Order.Order_cancelAll(symbol=symbol).result()[0]

    # ANCHOR close_position
    def close_position(self, symbol, orderQty, price=None):
        """
        symbol: string - Instrument symbol. e.g. 'XBTUSD'.
        price: if price is not provided, the position will be closed at market price
        orderQty: the sign of the orderQty should be opposition to the sign of the orderQty in the entry order
        """
        return self.client().Order.Order_new(
            symbol=symbol, 
            orderQty=orderQty, 
            price=price, 
            execInst='Close'
            ).result()[0]

    # ANCHOR Create order
    def create_order(self,symbol,side, frctn,leverage, ordType="Market",price=None):
        counter1 = 0
        while counter1 < 5:
            try:
                # ANCHOR  Submit Market Buy Order
                print("%s | Attempting to submit market %s order for %s..." % 
                                ((datetime.datetime.now().replace(microsecond=0)),side, symbol))
                
                text = "Entry %s" % datetime.datetime.now().replace(microsecond=0)
                        # change to self.client().Order.Order_new() in exchange module

                orderQty = self.order_quantity2(symbol=symbol, frctn=frctn, leverage=leverage)

                entryOrder = self.client().Order.Order_new(
                                    symbol=symbol,
                                    side=side,
                                    orderQty=orderQty,
                                    price=price,
                                    ordType=ordType,
                                    timeInForce="GoodTillCancel",
                                    text=text).result()[0]
                
                print("%s | Market %s order for %s submitted\n" % 
                                ((datetime.datetime.now().replace(microsecond=0)),side, symbol))
                seconds(0.5)

                entryOrderID = entryOrder['orderID']
                if entryOrder['ordStatus'] == 'Filled':
                    entryPrice = float(entryOrder['avgPx'])
                    print("%s | Market %s order filled.\n" % 
                                    ((datetime.datetime.now().replace(microsecond=0)), side))
                    counter2 = 0
                else:
                    entryOrderID = entryOrder['orderID']
                    # ANCHOR check order status
                    counter2 = 0
                    while counter2 < 5:
                        try:
                            print("%s | Checking market %s order status..." % 
                                    ((datetime.datetime.now().replace(microsecond=0)), side))
                            
                                    # change to self.client().Order.Order_getOrders() in exchange module
                            status = self.client().Order.Order_getOrders(
                                        symbol=symbol, 
                                        filter=json.dumps({'open': True})
                                                    ).result()[0]
                            if len(status) == 0:
                                print("%s | Market %s order filled.\n" % 
                                    ((datetime.datetime.now().replace(microsecond=0)), side))
                            
                                # retrieve entry price
                                latestOrder = self.client().Order.Order_getOrders(
                                    symbol=symbol, count=1, reverse=True).result()[0]
                                if latestOrder[-1]["orderID"] == entryOrderID:
                                    entryPrice = float(latestOrder[-1]['avgPx'])
                                else:
                                    raise RuntimeError("entryPriceNotSet")
                                    msg = "RuntimeError('entryPriceNotSet')"
                                seconds(0.5)
                                break

                            else:
                                print("%s | Market %s order pending...\n" % 
                                    ((datetime.datetime.now().replace(microsecond=0)), side))
                                seconds(0.5)

                        except:
                            print("%s | Operation failed - #%s: get %s order status. Retrying...\n" % 
                                ((datetime.datetime.now().replace(microsecond=0), (counter2 + 1), side)))
                            seconds(5)
                            counter2 += 1
                
                # If order status check failed
                if counter2 == 5:
                    msg = "Could not check %s order status" % side
                    closePosition = self.client().Order.Order_closePosition(symbol=symbol).result()[0]
                    cancelOrders = self.client().Order.Order_cancelAll().result()[0]
                    raise StopIteration(msg)
                else:
                    pass

                return {"entryOrderID":entryOrderID, "entryPrice":entryPrice, "orderQty":orderQty}
            
            except:
                seconds(5)
                counter1 += 1
            if counter1 == 5:
                msg = "%s | Failed to create market %s order" % (datetime.datetime.now().replace(microsecond=0), side)
                closePosition = self.client().Order.Order_closePosition(symbol=symbol).result()[0]
                cancelOrders = self.client().Order.Order_cancelAll().result()[0]
                raise StopIteration(msg)

    # # ANCHOR positionOpenCloseBitmex
    # def positionOpenClose(self, symbol=str, side=str, orderQty=float, takeProfitPercent=float, 
    #                             stopLossPercent=float, leverage=float, orderType="Market"):
    #     """
    #     Submit a market entry-order to exchange. Upon excecution, submit a take-profit limit and a market
    #     stop-loss order.\n
        
    #     Parameters
    #     ----------
    #     symbol: Instrument symbol - str\n
    #     side: Order side - Entry. Valid options: Buy, Sell - str\n
    #     orderQty: Order quantity in units of the instrument (i.e. contracts) - Entry - double\n
    #     takeProfit:  Limit price for take profit order - str\n
    #     stopLoss: Stop price for stop market order\n
    #     leverage: Leverage value. Send a number between 0.01 and 100 to enable isolated margin 
    #             with a fixed leverage. Send 0 to enable cross margin.
    #     """
    #     msg = ""
    #     msgList = ["Could not check %s order status" % side,
    #     "Failed to update leverage for %s order" % side,
    #     "Failed to create take profit order for %s" % symbol,
    #     "Failed to create stop loss order for %s" % symbol]

    #     self.create_order(self,symbol,side, frctn,leverage, ordType="Market",price=None)
                        
    #             # ANCHOR Amend leverage
    #             counter3 = 0
    #             while counter3 < 5:
    #                 try:
    #                     print("%s | Attempting to update leverage..." % 
    #                             datetime.datetime.now().replace(microsecond=0))
                        
    #                                 # change to self.client().Position.Position_updateLeverage() in exchange module
    #                     newLeverage = self.client().Position.Position_updateLeverage(
    #                                         symbol=symbol, 
    #                                         leverage=leverage
    #                                                 ).result()[0]
    #                     liquidationPrice = float(newLeverage["liquidationPrice"])
    #                     avgEntryPrice = float(newLeverage["avgEntryPrice"])
                        
    #                     print("%s | Leverage sucessfully set to %s.\n" % 
    #                             ((datetime.datetime.now().replace(microsecond=0)), leverage))
    #                     seconds(0.5)
    #                     break
    #                 except:
    #                     print("%s | Operation failed - #%s: Update leverage for %s order. Retrying...\n" % 
    #                         ((datetime.datetime.now().replace(microsecond=0), (counter3 + 1), side)))
    #                     seconds(5)
    #                     counter3 += 1
                
    #             # If leverage update failed
    #             if counter3 == 5:
    #                 msg = "Failed to update leverage for %s order" % side
    #                 closePosition = self.client().Order.Order_closePosition(symbol=symbol).result()[0]
    #                 cancelOrders = self.client().Order.Order_cancelAll().result()[0]
    #                 raise StopIteration(msg)
    #             else:
    #                 pass
                        
    #             # ANCHOR Create take profit
    #             counter4 = 0
    #             while counter4 < 5:
    #                 try:
    #                     print("%s | Attempting to create take profit order for %s..." % 
    #                             ((datetime.datetime.now().replace(microsecond=0)), symbol))
                        
    #                     if side == "Buy":
    #                         tpSide = "Sell"
    #                         takeProfit = round(entryPrice*(1 + (takeProfitPercent/100)))
    #                     else:
    #                         tpSide = "Buy"
    #                         takeProfit = round(entryPrice*(1 - (takeProfitPercent/100)))

    #                     textTp = "Take profit %s" % datetime.datetime.now().replace(microsecond=0)
    #                     takeProfitLimit = self.client().Order.Order_new(
    #                                         symbol=symbol ,
    #                                         side=tpSide,
    #                                         price=takeProfit,
    #                                         ordType="Limit",
    #                                         execInst = "Close",
    #                                         timeInForce="GoodTillCancel",
    #                                         text=textTp).result()[0]
                        
    #                     print("%s | Take profit order sucessfully created.\n" % 
    #                             datetime.datetime.now().replace(microsecond=0))
    #                     seconds(0.5)
    #                     break
    #                 except:
    #                     print("%s | Operation failed - #%s: Create take profit order for %s. Retrying...\n" % 
    #                         ((datetime.datetime.now().replace(microsecond=0), (counter4 + 1), symbol)))
    #                     seconds(5)
    #                     counter4 += 1
                
    #             # # If create take profit failed
    #             if counter4 == 5:
    #                 msg = "Failed to create take profit order for %s" % symbol
    #                 closePosition = self.client().Order.Order_closePosition(symbol=symbol).result()[0]
    #                 cancelOrders = self.client().Order.Order_cancelAll().result()[0]
    #                 raise StopIteration(msg)
    #             else:
    #                 pass
                
    # #             Status = checkOrderStatus(symbol=symbol, text=textTp) # self.checkOrderStatus(symbol=symbol, text=textTp)
    # #             orderID_TP = Status['orderID']
    # #             orderStatus_TP = Status['orderStatus']
                
    #             # ANCHOR Create stop loss
    #             counter5 = 0
    #             while counter5 < 5:
    #                 try:
    #                     print("%s | Attempting to create stop loss order for %s..." % 
    #                             ((datetime.datetime.now().replace(microsecond=0)), symbol))
                        
    #                     if side == "Buy":
    #                         slSide = "Sell"
    #                         stopLoss = round(entryPrice*(1 - (stopLossPercent/100)))

    #                         if stopLoss < liquidationPrice:
    #                             stopLoss = liquidationPrice*1.05 # stop loss set a 105 % of liquidation
    #                     else:
    #                         slSide = "Buy"
    #                         stopLoss = round(entryPrice*(1 + (stopLossPercent/100)))

    #                         if stopLoss > liquidationPrice:
    #                             stopLoss = liquidationPrice*0.95 # stop loss set a 95 % of liquidation

    #                     textSl = "stop loss %s" % datetime.datetime.now().replace(microsecond=0)
    #                     stopLossitLimit = self.client().Order.Order_new(
    #                                         symbol=symbol ,
    #                                         side=slSide,
    #                                         stopPx=stopLoss,
    #                                         ordType="Stop",
    #                                         execInst = "Close",
    #                                         timeInForce="GoodTillCancel",
    #                                         text=textSl).result()[0]
                        
    #                     print("%s | Stop loss order sucessfully created.\n" % 
    #                             datetime.datetime.now().replace(microsecond=0))
    #                     seconds(0.5)
    #                     break
    #                 except:
    #                     print("%s | Operation failed - #%s: Create stop loss order for %s. Retrying..." % 
    #                         ((datetime.datetime.now().replace(microsecond=0), (counter5 + 1), symbol)))
    #                     seconds(5)
    #                     counter5 += 1
                
    #             # If leverage update failed
    #             if counter5 == 5:
    #                 msg = "Failed to create stop loss order for %s" % symbol
    #                 closePosition = self.client().Order.Order_closePosition(symbol=symbol).result()[0]
    #                 cancelOrders = self.client().Order.Order_cancelAll().result()[0]
    #                 raise StopIteration(msg)
    #             else:
    #                 pass
                
    # #             Status = checkOrderStatus(symbol=symbol, text=textSl) # self.checkOrderStatus(symbol=symbol, text=textTp)
                
    # #             orderID_SL = Status['orderID'] 
    # #             orderStatus_SL = Status['orderStatus']
                
    #             break
                
    #         except:
    #             if msg in msgList:
    #                 raise StopIteration(msg)

    #             print("%s | Operation failed - #%s: market %s order - %s. Retrying..." % 
    #                     ((datetime.datetime.now().replace(microsecond=0)), (counter1 + 1), side, symbol))
    #             seconds(5)
    #             counter1 += 1
                
    #     # If market order creation failed
    #     if counter1 == 5:
    #         msg = "%s | Failed to create market %s order" % (datetime.datetime.now().replace(microsecond=0), side)
    #         closePosition = self.client().Order.Order_closePosition(symbol=symbol).result()[0]
    #         cancelOrders = self.client().Order.Order_cancelAll().result()[0]
    #         raise StopIteration(msg)
        
    #     return {"entryPrice":entryPrice,
    #             "entryOrderID":entryOrderID,
    #             "takeProfit":takeProfit,
    #             "stopLoss":stopLoss,
    #             "orderID_TP":takeProfitLimit['orderID'],
    #             "orderID_SL":stopLossitLimit['orderID']}

# !SECTION end of BitmexExchange class

# SECTION  UserDefinedFxns
class UserDefinedFxns(object):

    @staticmethod
    def unix_converter(dt=datetime):
        """ Convert datetime object to 
            unix timestamp
        """
        return time.mktime(dt.timetuple())
    
    # ANCHOR turning_points
    @staticmethod
    def turning_points(datafr):
        c = np.array(datafr['close'])
        h = np.array(datafr['high'])
        l = np.array(datafr['low'])
        
        peaks_index = argrelmax(c)
        peaks_closes = c[peaks_index]
        peaks_highs = h[peaks_index]

        bottoms_index = argrelmin(c)
        bottoms_closes = c[bottoms_index]
        bottoms_lows = l[bottoms_index]
        
        local_max = peaks_closes.max()
        local_min = bottoms_closes.min()
        zenith = peaks_highs[np.where(peaks_closes==local_max)] # high of local max
        nadir = bottoms_lows[np.where(bottoms_closes==local_min)] # low of local min
        
        return {
            'highest-high': zenith[-1], 
            'lowest-low' : nadir[-1],
            'peaks': {'close': peaks_closes, 'high': peaks_highs},
            'bottoms': {'close': bottoms_closes, 'lows': bottoms_lows}
                }
    
    # ANCHOR fib_levels
    def fib_levels(self, datafr):
        c = np.array(datafr['close'])
        TurningPoints = self.turning_points(datafr)
        max_price = TurningPoints['local_min_max'][0]
        min_price = TurningPoints['local_min_max'][1]
        diff = max_price - min_price
        zenith_index = np.where(c == max_price)
        nadir_index = np.where(c == min_price)

        if zenith_index[-1][-1] > nadir_index[-1][-1]:
            level_0 = max_price
            level_1 = max_price - 0.236*diff
            level_2 = max_price - 0.382*diff
            level_3 = max_price - 0.5*diff
            level_4 = max_price - 0.618*diff
            level_5 = max_price - 0.786*diff
            level_6 = max_price - 0.886*diff
            level_7 = min_price
            level_8 = max_price - 1.27*diff
            
            return {'price_direction':'higer',
                    'fib_leves': [level_0, level_1, level_2, level_3, level_4, 
                    level_5, level_6, level_7, level_8]}

        elif zenith_index[-1][-1] < nadir_index[-1][-1]:
            level_0 = min_price
            level_1 = min_price + 0.236*diff
            level_2 = min_price + 0.382*diff
            level_3 = min_price + 0.5*diff
            level_4 = min_price + 0.618*diff
            level_5 = min_price + 0.786*diff
            level_6 = min_price + 0.886*diff
            level_7 = max_price
            level_8 = min_price + 1.27*diff

            return {'price_direction':'lower',
                    'fib_leves': [level_0, level_1, level_2, level_3, level_4, 
                    level_5, level_6, level_7, level_8]}
    
    # ANCHOR key_level_test
    def key_level_test(self, level, datafr):
        test = [i <= level <= j for i,j in zip(datafr['low'], datafr['high'])]
        return test.count(True)
    
    # ANCHOR resistance_test
    def resistance_test(self, level, datafr, percentage):
        """ 
        Return number of times a key support level has been tested
        Parameters
        ----------
        level: float or int
                Price level

        datafr: dictionary of numpy arrays
            dictionary of candlesticks in which: 'open', 'high', 'low', and 'close' are used as keys

        percentage: float
            used to compute the boundaries of the price area tested for resistance

        Returns
        -------
        Ret: int

            number of times the resistance of the area has tested
        """
        input_ = self.turning_points(datafr)
        peak_highs = input_['peaks']['high']
        peak_closes = input_['peaks']['close']

        a_upr = level*(1 + percentage)
        # upper boundary of area
        a_lwr = level*(1 - percentage)
        # lower boundary of area
        bool_mask = []

        for i,j in zip(peak_highs, peak_closes):
            # arr[i][0] = high, arr[i][1] = close 
            if i > a_lwr and i < a_upr and j > a_lwr and j < a_upr:
                    mask = True
                    # both high and close within area
            elif i > a_lwr and i < a_upr and j < a_lwr:
                    mask = True
                    # high within area but close less than lower bound
            elif i > a_upr and j > a_lwr and j < a_upr:
                    mask = True
                    # close within area but high greater than upper bound
            elif i > a_upr and j < a_lwr:
                    mask = True
                    # close lower than lower bound
                    # high greater than upper bound
            else:
                mask = False
        
        return bool_mask.count(True)
    
    # ANCHOR support_test
    def support_test(self, level, datafr, percentage):
        """ Return number of times a key support level has been tested"""
        input_ = self.turning_points(datafr)
        bottoms_lows = input_['bottoms']['lows']
        bottoms_closes = input_['bottoms']['close']

        a_upr = level*(1 + percentage)
        # upper boundary of area
        a_lwr = level*(1 - percentage)
        # lower boundary of area
        
        bool_mask = []
        for i,j in zip(bottoms_lows, bottoms_closes):
            if i > a_lwr and i < a_upr and j > a_lwr and j < a_upr:
                mask = True
                
            elif i < a_lwr and j > a_lwr and j < a_upr:
                mask = True
                
            elif i > a_lwr and i < a_upr and j > a_upr:
                mask = True
            
            elif (i < a_lwr and j > a_upr):
                mask = True
                
            else:
                mask = False
            bool_mask.append(mask)

        return bool_mask.count(True)
    
    # ANCHOR send_email
    @staticmethod
    def send_email(SUBJECT, BODY):
        """With this function we send out an email with a html body"""
        
        # Create message container - the correct MIME type is multipart/alternative here!
        TO = 'jkanangila@gmail.com'
        FROM ='avinaedi9@gmail.com'
        MESSAGE = MIMEMultipart('alternative')
        MESSAGE['subject'] = SUBJECT
        MESSAGE['To'] = TO
        MESSAGE['From'] = FROM
        
        # Record the MIME type text/html.
        HTML_BODY = MIMEText(BODY, 'html')
        
        # Attach parts into message container. 
        # According to RFC 2046, the last part of a multipart message, in this case 
        # the HTML message, is best and preferred.
        MESSAGE.attach(HTML_BODY)
        
        # The actual sending of the e-mail
        server = smtplib.SMTP('smtp.gmail.com:587')    
        # Credentials (if needed) for sending the mail
        password = "esaie1990"
        
        server.starttls() 
        server.login(FROM,password) 
        server.sendmail(FROM, [TO], MESSAGE.as_string()) 
        server.quit()

        print("%s" % datetime.datetime.now().replace(microsecond=0)
        + " Email Notification Sent to user\n")
    
    # ANCHOR interval_counter
    # @staticmethod
    # def interval_counter(dt=datetime):
    #     """ Compute the number of minutes and seconds to the next 5-min interval"""
    #     # if the number of minutes is either less than 5 or
    #     # between 5 and 10
    #     if dt.minute <= 5:
    #         # convert minutes to seconds and substract from
    #         # the equivalent of5 minute in seconds
    #         # return integral part i.e the integer
    #         # and the modulus (rest, already in seconds)
    #         min_to_sec = 5*60 - (dt.minute*60 + dt.second)
    #         if min_to_sec < 60:
    #             return [0, min_to_sec]
    #         else:
    #             return [min_to_sec//60, min_to_sec%60]
        
    #     elif 5 < dt.minute <= 10:
    #         # convert minutes to seconds and substract from
    #         # the equivalent of 10 minute in seconds
    #         min_to_sec = 10*60 - (dt.minute*60 + dt.second)
    #         if min_to_sec < 60:
    #             return [0, min_to_sec]
    #         else:
    #             return [min_to_sec//60, min_to_sec%60]
        
    #     # if the number of minutes is greater than 10, apply 
    #     # same logic as before to the last digit of the number
    #     elif dt.minute > 10 and int(str(dt.minute)[1]) <= 5:
    #         min_to_sec = 5*60 - (int(str(dt.minute)[1])*60 + dt.second)
    #         if min_to_sec < 60:
    #             return [0, min_to_sec]
    #         else:
    #             return [min_to_sec//60, min_to_sec%60]
        
    #     elif dt.minute > 10 and 5 < int(str(dt.minute)[1]) <= 10:
    #         min_to_sec = 10*60 - (int(str(dt.minute)[1])*60 + dt.second)
    #         if min_to_sec < 60:
    #             return [0, min_to_sec]
    #         else:
    #             return [min_to_sec//60, min_to_sec%60]

    # ANCHOR datetime_chng_tz
    @staticmethod
    def datetime_chng_tz(dt, tz_loc='Africa/Johannesburg', from_local=True, tz_norm=None):
        """ 
        Returns a datetime objected converted to a target timezone
        
        args
            (datetime) dt - required: datetime object to convert 
            (str) tz_loc - required: local timezone
            (str) tz_norm - required: target timezone
            (bool) from_local - specify if we are converting from our
        list of timezones strs available @: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        """
        if from_local and tz_norm:
            tz_localized,  tz_normalized = pytz.timezone(tz_loc), pytz.timezone(tz_norm)
            time_localized = tz_localized.localize(dt)
            return tz_normalized.normalize(time_localized)
        else:
            return dt.astimezone(pytz.timezone(tz_loc))
        

    # ANCHOR weekend_check
    def weekend_check(self):
        """Determine wether it weekend and returns the number of seconds to the end of the weekend."""
        # convert actual time to UTC
        actual_time = datetime.datetime.utcnow().replace(microsecond=0)
        # actual_time = self.datetime_chng_tz(actual_time, tz_loc='Africa/Johannesburg', tz_norm='UTC')
        # NOTE: find way to specify timezone automatically

        # Determine if it's weekend and return amount of time program should sleep
        if actual_time.weekday() in (5,6):
            if actual_time.weekday() == 5:
                weekend_start = datetime.datetime.combine(actual_time.date(), datetime.time(0))
            elif actual_time.weekday() == 6:
                saturday = actual_time - datetime.timedelta(1)
                weekend_start = datetime.datetime.combine(saturday, datetime.time(0))

            date_to_unix = lambda dt: time.mktime(dt.timetuple())

            if date_to_unix(actual_time) >= date_to_unix(weekend_start):
                weekend_end = weekend_start + datetime.timedelta(2)
                wake_up = date_to_unix(weekend_end) - date_to_unix(actual_time)

                time_utc = actual_time + datetime.timedelta(seconds=wake_up)

                return {'second':wake_up,
                    'date_time': self.datetime_chng_tz(dt=time_utc, tz_loc='Africa/Johannesburg', from_local=False),
                    'is_weekend':True}
            else:
                return {'second':[],
                'date_time': [],
                'is_weekend':False}
        else:
            return {'second':[],
                'date_time': [],
                'is_weekend':False}

    # ANCHOR interval_counter
    @staticmethod
    def interval_counter(size, unit, max_val):
        """ Compute number of seconds to next time interval
        args
            (int) size - required: size of time inval
            (str) unit - required: unit in which intervals are measured
            (int) max_val - required: maximum value for interval when unit is used

        return
            dict - a dictionary with the following keys: [wakeup_time_secs, wakeup_time_dtls]"""
        dt = datetime.datetime.now().replace(microsecond=0)
        join_datetime = lambda x,y: datetime.datetime.combine(x,y) # fxn to join date and time
        l = [j for j in range(0,max_val,size)] # list of elements within interval
        
        for i in range(0, max_val, size):
            # compute next interval if the current time correspond to a time interval and less 
            # than 20 seconds has passed
            if eval('dt.{}'.format(unit)) < i or eval('dt.{}'.format(unit)) == i and 0 <= dt.second < 20: #
                
                next_interval = (join_datetime(dt.date(), datetime.time(hour=dt.hour, minute=i)) if unit=='minute'
                                else join_datetime(dt.date(), datetime.time(hour=i)))
                break

            # compute next interval if the current time correspond to a time interval and more 
            # than 20 seconds has passed
            elif eval('dt.{}'.format(unit)) == i and dt.second > 20: #
                
                next_interval = (join_datetime(dt.date(), datetime.time(hour=dt.hour, minute=l[l.index(i) + 1]))
                                if unit=='minute' else join_datetime(dt.date(), datetime.time(hour=l[l.index(i) + 1])))
                break

            # account for max_val since it doesn't appear in range()
            elif l.index(i) >= len(l) - 1:
                next_interval = (join_datetime(dt.date(), datetime.time(hour=dt.hour + 1)) if unit=='minute'
                                else join_datetime(dt.date() + datetime.timedelta(1), datetime.time(0)))

        date_to_unix = lambda dt: time.mktime(dt.timetuple())
        time_to_wake = date_to_unix(next_interval) - date_to_unix(dt)

        return {'second':date_to_unix(next_interval) - date_to_unix(dt),
                'date_time': dt + datetime.timedelta(seconds=time_to_wake)}
    
    # ANCHOR time_to_sec
    @staticmethod
    def time_to_sec(dat):
        """ Convert a time object to seconds"""
        return dat.hour*60*60 + dat.minute*60 + dat.second

    # ANCHOR var_diff
    @staticmethod
    def var_diff(x, y):
        if max([x,y]) == 0:
            return 0
        else:
            return abs((x - y) / max([x,y]))

    # ANCHOR diff
    @staticmethod
    def diff(x, y):
        return abs(x - y)

    # ANCHOR appendObjtoAX
    @staticmethod
    def appendObjtoAX(ax, x_val, label=None):
        return ax.plot(x_val, label=label, ls='--', lw=0.5)

    # ANCHOR appendCandlePlot
    # @staticmethod
    # def appendCandlePlot(ax, opens, highs, lows, closes, width=0.6, alpha=0.75):

    #     return candlestick2_ohlc(ax, opens=opens, highs=highs, lows=lows, closes=closes, 
    #         colorup=config.color['green'], colordown=config.color['red'], width=width)

    # ANCHOR formatFig
    @staticmethod
    # def formatFig(fig, ax, time, path, instrument=str):
    #     nTime = [PoloniexEchange.unix_converter(i) for i in time]
    #     xdate = [datetime.datetime.fromtimestamp(i) for i in nTime]
    #     ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
        
    #     def mydate(x,pos):
    #         try:
    #                 return xdate[int(x)]
    #         except IndexError:
    #                 return ''
        
    #     ax.xaxis.set_major_formatter(ticker.FuncFormatter(mydate))
        
    #     fig.autofmt_xdate()
        
        
    #     plt.xlabel('Date')
    #     plt.ylabel('Price')
    #     plt.legend()
    #     plt.title('Historical Data for %s \nFor the period %s to %s' % (instrument, time.iloc[0], time.iloc[-1]))
    #     plt.tight_layout()
    #     plt.savefig(path, bbox_inches="tight")
    #     plt.close(fig)

    # ANCHOR get_decimal_places
    @staticmethod
    def get_decimal_places(current_price):
        return len(str(current_price).replace('.',' ').split()[1])

    # ANCHOR blockPrint
    @staticmethod
    def blockPrint():
        sys.stdout = open(os.devnull, 'w')

    # ANCHOR enablePrint
    @staticmethod
    def enablePrint():
        sys.stdout = sys.__stdout__
# !SECTION end of UserDefinedFxns class

if __name__ == "__main__":
    bitmex = BitmexExchange(**keys['bitmex-testnet'])
    # client = bitmex.client()

    print(bitmex.create_order(symbol="XBTUSD", side="Buy", frctn=1, leverage=25))