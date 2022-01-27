""" Now using strategy_v1_2.py. See comments inside file"""
from strategy_v1_2 import *

class MainLoopOanda(OandaExchange, Data_logger, Strategy3): # TODO: change to strategy3 in actual module
    signals_dict = {'instrument':[], 'signal':[], 'exchange':[], 'strategy':[], 'data':[]}
    openPositions = []
    
    # def __init__(self, access_token, accountID, fractAccTraded, exchange='oanda', environment=None):
    def __init__(self, exchange, fractAccTraded = 0.01):
        # OandaExchange.__init__(self, access_token, accountID, environment=None)
        Data_logger.__init__(self)
        Strategy3.__init__(self)
        self.fractAccTraded = fractAccTraded
        self.exchange = exchange
        
#         self.openTradeDf = self.readcsv('open_trades_summary')
#         self.openTradeDf.set_index('instrument', inplace=True)
    # ANCHOR openPositionsList
    def openPositionsList(self, exchange): # NOTE tested -> STATUS==WORKING
        i=0
        while i < 5:
            try:
                print("%s | Requesting list of open positions from exchange. Standby..." % self.time())
                # Load local list of open positions from log folder and set instrument-column as index
                openPositionsLocal = self.readcsv('open_trades_summary')
                openPositionsLocal.set_index('instrument', inplace=True)

                # Request list of open positions from exchange
                openPositionsExchange = eval(exchange).get_open_positions(exchange)

                # 'if-clause' to determine if there are any entries in the local list of open positions
                if not openPositionsLocal.empty:
                    # Compare local_list to the one from the exchange. If an instrument does not apear on the list obtained 
                    # from the exchange, the trade has been closed. Remove it from the openPositionsLocal and log the information.
                    for instrument in openPositionsLocal.index.values.tolist():
                        # 'if clause' to identify the instruments for which positions has been closed
                        if instrument not in openPositionsExchange.index.values.tolist():
                            # i. Save summary of trade information
                            # i.1 Generate args to pass to trade summary method
                            param = {'exchange':openPositionsLocal['exchange'].loc[instrument],
                                    'orderID':int(openPositionsLocal['orderID'].loc[instrument]), 
                                    'tradeID':int(openPositionsLocal['tradeID'].loc[instrument]), 
                                    'quantity':openPositionsLocal['quantity'].loc[instrument],
                                    'side':openPositionsLocal['side'].loc[instrument], 
                                    'trailing_SL_dist':openPositionsLocal['trailing_distance'].loc[instrument]}
                            # ii. Remove insturment from openPositionsLocal
                            openPositionsLocal.drop(instrument, inplace=True)
                            # iii. Run trade summary method to retrieve predertimed paramaters from the exchange
                            trade_summary = eval(exchange).trade_summary(**param)
                            # iv. export response of ii.2 to trade_summary.csv in log folder
                            self.logdata_tocsv(trade_summary, 'closed_trade_summary', mode='a', index=True)
                    print("%s | Open positions dataframe sucessfully initialized." % self.time())
                    return openPositionsExchange
                else:
                    print("%s | Open positions dataframe sucessfully initialized." % self.time())
                    return openPositionsExchange
            except:
                i += 1
                seconds(5)
                print("%s | Request of open positions from exchange failed. Retrying..." % self.time())
                if i == 5:
                    print("%s | After 5 attempts: Failed to retrieve open positions. Shutting down." % self.time())
                    raise StopIteration
        
    # ANCHOR filter_list_of_instruments
    def filter_list_of_instruments(self, exchange, instruments_list): # NOTE tested -> STATUS==WORKING
        i=0
        while i < 5:
            try:
                print("%s | Filtering initial list of instrument based on predetermined criteria..." % self.time())
                
                out = {'instrument':[], 'direction':[]}
                results = {}
                
                # Generate tests that will be used in 'if-statements'
                for instrument in instruments_list:
                    tests = {}
                    # Call trade parameters for the primary and secondary timeframe using ohlcRequestParams2
                    # In ohlcRequestParams2, an alternate primary timeframe has been chosen
                    df_lTerm=self.tradeParameters(exchange=exchange, instrument=instrument, 
                                                param_dict=ohlcRequestParams2, trendType='longTerm')
                    df_iTerm=self.tradeParameters(exchange=exchange, instrument=instrument, 
                                                param_dict=ohlcRequestParams2, trendType='intermTerm')
                    tests['chopp'] = {}
                    tests['chopp']['longTerm'] = self.testChopp2(data=df_lTerm['chopp'])
                    tests['chopp']['intermTerm'] = self.testChopp2(data=df_iTerm['chopp'])
                    
                    tests['DIs'] = self.testDIs(df_lTerm, df_iTerm)
                    tests_df = pd.DataFrame(tests)
                    
                    results[instrument] = tests_df
                    seconds(0.5)
                    
                for instrument in results.keys():
                    # if choppiness_idx < 38.2 on both the longterm and intermediary timeframes
                    # and "pdi > mdi" on both timeframes, select the instrument
                    if (results[instrument]['chopp'].loc['longTerm']
                        and results[instrument]['chopp'].loc['intermTerm']
                        and results[instrument]['DIs'].loc['longTerm'] == 1
                        and results[instrument]['DIs'].loc['intermTerm'] == 1):
                        
                        out['instrument'].append(instrument)
                        out['direction'].append(1)
                        
                    # if choppiness_idx < 38.2 on both the longterm and intermediary timeframes
                    # and "pdi < mdi" on both timeframes, select the instrument    
                    elif (results[instrument]['chopp'].loc['longTerm']
                        and results[instrument]['chopp'].loc['intermTerm']
                        and results[instrument]['DIs'].loc['longTerm'] == -1
                        and results[instrument]['DIs'].loc['intermTerm'] == -1):
                        
                        out['instrument'].append(instrument)
                        out['direction'].append(-1)
                        
                print("%s | Success!" % self.time())
                return out
            
            except:
                i += 1
                seconds(5)
                print("%s | Failed to filter initial list of instrument. Retrying..." % self.time())
                if i == 5:
                    print("%s | After 5 attempts: Failed to filter initial list of instrument. Shutting down." % self.time())
                    raise StopIteration
    
    # ANCHOR time_task_scheduler
    def time_task_scheduler(self):
        if self.time().hour in range(0, 24, 1) and self.time().minute in [0,1]: # TODO make change here too
            stage = "REINITIALIZE"
        else:
            stage = "NORMAL OPERATIONS"
        
        if stage == "REINITIALIZE":
            return 'break'
        
        elif stage == "NORMAL OPERATIONS":
            actual_time = self.time()
            _min,_sec = UserDefinedFxns().interval_counter(actual_time)
            time_to_sleep = _min*60 + _sec
            wake_up = actual_time + datetime.timedelta(seconds=time_to_sleep)
            return time_to_sleep, wake_up
    
    def action(self):
        # perform an action based on the time keeper method respones
        pass

    # ANCHOR log_trade_params
    def log_trade_params(self, openPositionsDF): # NOTE tested -> STATUS==WORKING
        i=0
        while i < 5:
            try:
                print("%s | Attempting to log various positions parameters..." % self.time())
                
                # log trade parameters (indicator functions) for open positions
                if not openPositionsDF.empty:
                    for instrument in openPositionsDF.index.values.tolist():
                        # Check if the position if still open. If it is log latest ohlc and indicator functions
                        r = trades.TradeDetails(accountID=eval(openPositionsDF['exchange'].loc[instrument]).accountID, 
                                                tradeID=openPositionsDF['tradeID'].loc[instrument]) # NOTE: change here to adapt
                        rv = eval(openPositionsDF['exchange'].loc[instrument]).Client().request(r)# NOTE: change here to adapt
                        if rv['trade']['state'] == 'OPEN':# NOTE: change here to adapt
                            trade_data = self.tradeParameters(exchange=openPositionsDF['exchange'].loc[instrument], instrument=instrument, 
                                                            param_dict=ohlcRequestParams, trendType='shortTerm')# NOTE: change here to adapt
                            trade_data = pd.DataFrame(trade_data.iloc[-1]).transpose()
                            trade_data['exchange'] = openPositionsDF['exchange'].loc[instrument]
                            trade_data['orderID'] = openPositionsDF['orderID'].loc[instrument]
                            trade_data['instrument_type'] = self.intrument_type(instrument)
                            trade_data['tradeID'] = openPositionsDF['tradeID'].loc[instrument]
                            trade_data['instrument'] = instrument
                            if openPositionsDF['side'].loc[instrument] == 'SHORT':
                                percentage = lambda i,f: round(((i-f)/i)*100, 2)
                            else:
                                percentage = lambda i,f: round(((f-i)/i)*100, 2)
                            profit = percentage(float(openPositionsDF['entryPrice'].loc[instrument]), 
                                                        float(trade_data['close'].iloc[-1]))
                            trade_data['percent_profit'] = profit
                            trade_data['time'] = trade_data.index.values.tolist()
                            trade_data.set_index('instrument', inplace=True)
                            del trade_data['volume']
                            temp = template('trade_data_log', 'df')
                            temp.index.insert(-1, instrument)
                            output = pd.concat([temp, trade_data], sort=False)
                            self.logdata_tocsv(output, 'trade_data_log', mode='a', index=True)
                            seconds(0.5)
                print("%s | Data logging completed" % self.time())
                break
            
            except:
                i += 1
                seconds(5)
                print("%s | Data logging failed. Retrying..." % self.time())
                if i == 5:
                    print("%s | After 5 attempts: Failed to log trade parameters." % self.time())
        #             raise StopIteration

    # ANCHOR open_new_pos_and_log
    def open_new_pos_and_log(self, signals_df, openPositionsDF): # NOTE tested -> STATUS==WORKING
        i=0
        while i < 5:
            try:
                print("%s | Attempting to open positions for selected instruments..." % self.time())

                signals_df2 = signals_df.copy()
                openPositionsDF2 = openPositionsDF.copy()
                # drop the instruments for which positions are already open 
                if not signals_df2.empty and type(openPositionsDF2) == pd.core.frame.DataFrame:
                    # for every instrument for which a signal was identified
                    for instrument in signals_df2.index.values.tolist():
                        # if the instrument in question has already an open position, drop it.
                        if instrument in openPositionsDF2.index.values.tolist():
                            signals_df2.drop(instrument, inplace=True)

                    # open new position for remaining instruments
                    for instrument in signals_df2.index.values.tolist():
                        marketOrder = eval(signals_df2['exchange'].loc[instrument]).market_order2(
                            instrument=instrument, side=int(signals_df2['signal'].loc[instrument]), 
                                fractAccTraded=self.fractAccTraded, exchange=signals_df2['exchange'].loc[instrument])
                        # Add instrument to the list of open trades
                        openPositionsDF2.index.insert(-1, instrument)
                        new_entry = marketOrder['data']
                        del new_entry['instrument']
                        openPositionsDF2.loc[instrument] = new_entry
                        # log trade information in open_trades_summary
                        self.logdata_tocsv(datafr=openPositionsDF2, filename='open_trades_summary', mode='a', index=True)
                        # log entry conditions(actual and previous parameters)
                        entry_param = pd.DataFrame(signals_df2['data'].loc[instrument])
                        template_df = template('entry_conditions', 'df')
                        entry_param['instrument'] = instrument
                        entry_param['tradeID'] = marketOrder['data']['tradeID']
                        entry_param['time_pos'] = 'actual','previous'
                        entry_param.set_index('instrument', inplace=True)
                        output = pd.concat([template_df, entry_param])
                        self.logdata_tocsv(datafr=output, filename='entry_conditions', mode='a', index=True)
                        seconds(0.5)
                    print("%s | Positions sucessfully opened. Check log folder for details." % self.time())
                    return openPositionsDF2
                else:
                    print("%s | No instrument was selected. Moving on." % self.time())
                    return template('open_trades_summary', 'df')
            
            except:
                i += 1
                seconds(5)
                print("%s | Failed to open new positions. Retrying..." % self.time())
                if i == 5:
                    print("%s | After 5 attempts: Failed to open new positions." % self.time())
        #             raise StopIteration
        
    # ANCHOR signal_generation
    def signal_generation(self, list_of_instruments):
        i = 0
        while i < 5:
            try:
                print("%s | Attempting to generate trade signals for selected instruments..." % self.time())
                signals_dict = {'instrument':[], 'signal':[], 'exchange':[], 'strategy':[], 'data':[]}
                for instrument, direction in zip(list_of_instruments['instrument'],
                                                    list_of_instruments['direction']):
                    # run signal generator method
                    signal = self.signalGenerator(
                                        exchange=self.exchange, 
                                        instrument=instrument, 
                                        param_dict=ohlcRequestParams)
                    # note: the direction parameter accounts for trend alignment. It is determined by the 
                    # relative position of pdi and mdi on the long and intermediate timeframes
                    if (signal['signal'] == 1 and direction == 1 
                    or signal['signal'] == -1 and direction == -1):
                        signals_dict['instrument'].append(instrument)
                        signals_dict['signal'].append(signal['signal'])
                        signals_dict['exchange'].append(self.exchange)
                        signals_dict['data'].append(signal['data'])
                        if signal['signal'] == 1:
                            signals_dict['strategy'].append('UB_Breakout')
                        else:
                            signals_dict['strategy'].append('LB_Breakout')
                    seconds(0.5)
                if len(signals_dict['instrument']) != 0:
                    print("%s | Signals generation complete. %s trade signals identified." % 
                            (self.time(), len(signals_dict['instrument'])))
                else:
                    print("%s | 0 trade signals identified." % self.time())
                return signals_dict
            except:
                i += 1
                seconds(5)
                print("%s | Failed to generate trade signals. Retrying..." % self.time())
                if i == 5:
                    print("%s | After 5 attempts: Failed to generate trade signals." % self.time())

                return signals_dict

    # ANCHOR active_trader: consider name : position mannager
    def active_trader(self):
        # Outer loop
        while True:
            # Initialise open trades list using the openPositionsList method
            get_open_positions = self.openPositionsList(self.exchange)
            MainLoopOanda.openPositions = get_open_positions
            # After the initialization, overwrite the local list of open positions found in /open_trades_summary.csv
            self.logdata_tocsv(get_open_positions, 'open_trades_summary', mode='w', index=True)
            
            # filter list of instruments based on choppiness values
            list_of_instruments_initial = instrumentsDict['instrument']
            list_of_instruments = self.filter_list_of_instruments(
                exchange=self.exchange, instruments_list=list_of_instruments_initial)
            print('\n%s' % list_of_instruments)
            
            # Inner loop
            while True:
                # Break out of inner if it is 00:00 UTC
                if self.time_task_scheduler() == 'break':
                    break
                    
                # Run program normally if the time is in the interval range(0,60,5)
                elif self.time_task_scheduler() != 'break' and self.time().minute in range(0,60,5):
                    # log trade parameters for instruments in open position dataframe
                    # generate trade signals
                    # open new position and append results to open position dataframe
                    # Log indicator functions for open parameters
                    self.log_trade_params(openPositionsDF=MainLoopOanda.openPositions)

                    # Generate trade signals for the instruments selected previously
                    MainLoopOanda.signals_dict = self.signal_generation(list_of_instruments)
                                
#                                 if MainLoopOanda.openPositions.empty:
#                                     raise StopIteration
                    try:
                        signals_df = pd.DataFrame(MainLoopOanda.signals_dict)
                        signals_df.set_index('instrument', inplace=True)
                        
                        if signals_df.empty:
                            seconds(5)
                            continue
                    except:
                        # if there are any problems with signal generation, return to the main loop.
                        break

                    # Open new positions for instrument for which signals were generate
                    new_positions = self.open_new_pos_and_log(
                                        signals_df=signals_df, 
                                        openPositionsDF=MainLoopOanda.openPositions)
                    pd.concat([MainLoopOanda.openPositions, new_positions], sort=False)

                    print("\n%s" % eval(self.exchange).open_positions())
                    seconds(60)

                # Pause the program until the conclusion of the actual 5min interval
                else:
                    time_to_sleep, wake_up = self.time_task_scheduler()
                    # if not MainLoopOanda.openPositions.empty:
                    #     print(MainLoopOanda.openPositions)
                    # else:
                    print("\n%s | No new trade signal identified." % self.time())
                    print("\n%s" % eval(self.exchange).open_positions())
                    print('                    | ' + "Scheduled shutdown. Normal operations to resume"
                            + "  in %s seconds.\n" % wake_up)
                    seconds(time_to_sleep + 5)