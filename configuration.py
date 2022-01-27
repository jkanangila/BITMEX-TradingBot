import datetime
import pandas as pd 

# ANCHOR keys dictionary
keys = {}

# ANCHOR Paramas dictionary
ohlcRequestParams = {
        "binance":{
                'longTerm': {"timeframe": '1 year ago UTC', "interval": '1d'},
                'intermTerm': {"timeframe": '7 day ago UTC', "interval": '30m'},
                'shortTerm': {"timeframe": '2 day ago UTC', "interval": '5m'}},

        "bitmex":{
                'longTerm': {"count": 300, "binSize": '1d'},
                'intermTerm': {"count": 300, "binSize": '1h'},
                'shortTerm': {"count": 300, "binSize": '5m'}},

        "oanda":{
                'longTerm': {"count": 300, "granularity": 'D'},
                'intermTerm': {"count": 300, "granularity": 'M30'},
                'shortTerm': {"count": 300, "granularity": 'M5'}
        },

        "poloniex":{
                'longTerm': {'period' : 24*60*60, 'end' : datetime.datetime.now(), 
                        'start' : [datetime.datetime.now() - 200*datetime.timedelta(days=1)]},
                'intermTerm': {'period' : 30*60, 'end' : datetime.datetime.now(),
                        'start' : [datetime.datetime.now() - 7*datetime.timedelta(days=1)]},
                'shortTerm': {'period' : 5*60, 'end' : datetime.datetime.now(),
                        'start' : [datetime.datetime.now() - 2*datetime.timedelta(days=1)]}
        }
}

ohlcRequestParams2 = {
        "binance":{
                'longTerm': {"timeframe": '1 year ago UTC', "interval": '4h'},
                'intermTerm': {"timeframe": '7 day ago UTC', "interval": '30m'},
                'shortTerm': {"timeframe": '2 day ago UTC', "interval": '5m'}},

        "bitmex":{
                'longTerm': {"count": 300, "binSize": '4h'},
                'intermTerm': {"count": 300, "binSize": '1h'},
                'shortTerm': {"count": 300, "binSize": '5m'}},

        "oanda":{
                'longTerm': {"count": 300, "granularity": 'H1'},
                'intermTerm': {"count": 300, "granularity": 'M15'},
                'shortTerm': {"count": 300, "granularity": 'M5'}
        },

        "poloniex":{
                'longTerm': {'period' : 24*60*60, 'end' : datetime.datetime.now(), 
                        'start' : [datetime.datetime.now() - 200*datetime.timedelta(days=1)]},
                'intermTerm': {'period' : 30*60, 'end' : datetime.datetime.now(),
                        'start' : [datetime.datetime.now() - 7*datetime.timedelta(days=1)]},
                'shortTerm': {'period' : 5*60, 'end' : datetime.datetime.now(),
                        'start' : [datetime.datetime.now() - 2*datetime.timedelta(days=1)]}
        }
}

# ANCHOR Binance
# list_of_tuples = [
#         ('ADAUSDT', 5, 1), ('BCHABCUSDT', 2, 5), ('BCHSVUSDT', 2, 5), ('BNBUSDT', 4, 2), ('BTCUSDT', 2, 6),
#         ('EOSUSDT', 4, 2), ('ETCUSDT', 4, 2), ('ETHUSDT', 2, 5), ('ICXUSDT', 4, 2), ('IOTAUSDT', 4, 2), 
#         ('LTCUSDT', 2, 5), ('NEOUSDT', 3, 3), ('NULSUSDT', 4, 2), ('ONTUSDT', 3, 3), ('QTUMUSDT', 3, 3),
#         ('TRXUSDT', 5, 1), ('VETUSDT', 5, 1), ('XLMUSDT', 5, 1), ('XRPUSDT', 5, 1)
#                     ] 
#                     #  (Symbol, price, quantity)

list_of_pair = [
        'ETHBTC', 'LTCBTC', 'BNBBTC', 'NEOBTC', 'BCCBTC', 'GASBTC', 'BTCUSDT', 'ETHUSDT', 'HSRBTC', 'MCOBTC', 
        'WTCBTC', 'LRCBTC', 'QTUMBTC', 'YOYOBTC', 'OMGBTC', 'ZRXBTC', 'STRATBTC', 'SNGLSBTC', 'BQXBTC', 'KNCBTC', 
        'FUNBTC', 'SNMBTC', 'IOTABTC', 'LINKBTC', 'XVGBTC', 'SALTBTC', 'MDABTC', 'MTLBTC', 'SUBBTC', 'EOSBTC', 
        'SNTBTC', 'ETCBTC', 'MTHBTC', 'ENGBTC', 'DNTBTC', 'ZECBTC', 'BNTBTC', 'ASTBTC', 'DASHBTC', 'OAXBTC', 
        'ICNBTC', 'BTGBTC', 'EVXBTC', 'REQBTC', 'VIBBTC', 'TRXBTC', 'POWRBTC', 'ARKBTC', 'XRPBTC', 'MODBTC', 
        'ENJBTC', 'STORJBTC', 'BNBUSDT', 'VENBTC', 'KMDBTC', 'RCNBTC', 'NULSBTC', 'RDNBTC', 'XMRBTC', 'DLTBTC', 
        'AMBBTC', 'BCCUSDT', 'BATBTC', 'BCPTBTC', 'ARNBTC', 'GVTBTC', 'CDTBTC', 'GXSBTC', 'NEOUSDT', 'POEBTC', 
        'QSPBTC', 'BTSBTC', 'XZCBTC', 'LSKBTC', 'TNTBTC', 'FUELBTC', 'MANABTC', 'BCDBTC', 'DGDBTC', 'ADXBTC', 
        'ADABTC', 'PPTBTC', 'CMTBTC', 'XLMBTC', 'CNDBTC', 'LENDBTC', 'WABIBTC', 'LTCUSDT', 'TNBBTC', 'WAVESBTC', 
        'GTOBTC', 'ICXBTC', 'OSTBTC', 'ELFBTC', 'AIONBTC', 'NEBLBTC', 'BRDBTC', 'EDOBTC', 'WINGSBTC', 'NAVBTC', 
        'LUNBTC', 'TRIGBTC', 'APPCBTC', 'VIBEBTC', 'RLCBTC', 'INSBTC', 'PIVXBTC', 'IOSTBTC', 'CHATBTC', 'STEEMBTC', 
        'NANOBTC', 'VIABTC', 'BLZBTC', 'AEBTC', 'RPXBTC', 'NCASHBTC', 'POABTC', 'ZILBTC', 'ONTBTC', 'STORMBTC', 
        'QTUMUSDT', 'XEMBTC', 'WANBTC', 'WPRBTC', 'QLCBTC', 'SYSBTC', 'GRSBTC', 'ADAUSDT', 'CLOAKBTC', 'GNTBTC', 
        'LOOMBTC', 'XRPUSDT', 'BCNBTC', 'REPBTC', 'TUSDBTC', 'ZENBTC', 'SKYBTC', 'EOSUSDT', 'CVCBTC', 'THETABTC', 
        'TUSDUSDT', 'IOTAUSDT', 'XLMUSDT', 'IOTXBTC', 'QKCBTC', 'AGIBTC', 'NXSBTC', 'DATABTC', 'ONTUSDT', 'TRXUSDT', 
        'ETCUSDT', 'ICXUSDT', 'SCBTC', 'NPXSBTC', 'VENUSDT', 'KEYBTC', 'NASBTC', 'MFTBTC', 'DENTBTC', 'ARDRBTC', 
        'NULSUSDT', 'HOTBTC', 'VETBTC', 'VETUSDT', 'DOCKBTC', 'POLYBTC', 'PHXBTC', 'HCBTC', 'GOBTC', 'PAXBTC', 
        'PAXUSDT', 'RVNBTC', 'DCRBTC', 'USDCBTC', 'MITHBTC', 'BCHABCBTC', 'BCHSVBTC', 'BCHABCUSDT', 'BCHSVUSDT', 
        'RENBTC', 'USDCUSDT', 'LINKUSDT', 'WAVESUSDT', 'BTTBTC', 'BTTUSDT', 'USDSUSDT', 'ONGBTC', 'ONGUSDT', 
        'HOTUSDT', 'ZILUSDT', 'ZRXUSDT', 'FETBTC', 'FETUSDT', 'BATUSDT'
                        ]

list_of_pair_v2 = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'LTCUSDT', 'ADAUSDT', 'XRPUSDT', 'EOSUSDT', 'XLMUSDT', 'BTTUSDT', 
        'ETHBTC', 'LTCBTC', 'BNBBTC', 'MCOBTC', 'KNCBTC', 'LINKBTC', 'MDABTC', 'EOSBTC', 'TRXBTC', 'ARKBTC', 
        'XRPBTC', 'ENJBTC', 'STORJBTC', 'ARNBTC', 'ADABTC', 'XLMBTC', 'ICXBTC', 'BRDBTC', 'VIABTC', 'WANBTC', 
        'GRSBTC', 'LOOMBTC', 'TUSDBTC', 'CVCBTC', 'THETABTC', 'RVNBTC', 'BTTBTC', 'FETBTC'
                ]

# list_of_pair = [i[0] for i in list_of_tuples]
# price_dcmls = [j[1] for j in list_of_tuples]
# qty_dcmls =  [j[2] for j in list_of_tuples]



# ANCHOR  Bitmex
# LTCH19, TRXH19,  too volatile
#longterm_binSize = '6h'
# list_of_symbols = ['XBTUSD', 'XBTJPY', 'ADAH19', 'BCHH19', 'EOSH19', 'ETHXBT', 'XRPH19' ]
list_of_symbols = ['XBTUSD', 'ETHUSD' ]



# ANCHOR Oanda
instrumentsDict = {'instrument': ['USD_ZAR', 'NATGAS_USD', 'USB05Y_USD', 'GBP_HKD', 'US30_USD', 'SUGAR_USD', 'XPD_USD', 'US2000_USD', 'EUR_GBP', 'XAU_HKD', 'GBP_SGD', 'USD_SEK', 'EUR_CAD', 'HK33_HKD', 'USD_TRY', 'GBP_JPY', 'GBP_PLN', 'WHEAT_USD', 'EUR_JPY', 'TWIX_USD', 'XAU_JPY', 'EUR_HKD', 'USB02Y_USD', 'XAU_AUD', 'IN50_USD', 'USD_CNH', 'XAU_CAD', 'NZD_USD', 'XAG_AUD', 'XAG_HKD', 'EUR_HUF', 'JP225_USD', 'SGD_HKD', 'AUD_NZD', 'SPX500_USD', 'EUR_USD', 'USD_PLN', 'GBP_AUD', 'USD_CZK', 'EUR_TRY', 'USD_JPY', 'EUR_SEK', 'USD_SGD', 'EUR_SGD', 'CHF_JPY', 'USD_DKK', 'XAU_GBP', 'XAG_USD', 'UK10YB_GBP', 'XAG_JPY', 'EUR_AUD', 'USD_HKD', 'NZD_CAD', 'XAG_EUR', 'SOYBN_USD', 'GBP_ZAR', 'NZD_SGD', 'ZAR_JPY', 'XAG_CHF', 'XPT_USD', 'EU50_EUR', 'CAD_JPY', 'GBP_CAD', 'USD_SAR', 'XAU_CHF', 'EUR_PLN', 'BCO_USD', 'NZD_HKD', 'NZD_CHF', 'XAG_GBP', 'UK100_GBP', 'AUD_JPY', 'USD_CAD', 'XCU_USD', 'DE30_EUR', 'NAS100_USD', 'EUR_ZAR', 'XAU_EUR', 'CAD_SGD', 'USD_NOK', 'HKD_JPY', 'NZD_JPY', 'XAG_NZD', 'FR40_EUR', 'USD_HUF', 'EUR_CZK', 'CHF_ZAR', 'AUD_HKD', 'GBP_NZD', 'CN50_USD', 'XAG_SGD', 'XAU_SGD', 'USD_INR', 'CAD_HKD', 'SGD_CHF', 'CAD_CHF', 'AUD_SGD', 'EUR_NOK', 'SG30_SGD', 'AU200_AUD', 'EUR_CHF', 'USB30Y_USD', 'XAG_CAD', 'GBP_USD', 'USD_MXN', 'USD_CHF', 'XAU_USD', 'AUD_CHF', 'EUR_DKK', 'CORN_USD', 'AUD_USD', 'NL25_EUR', 'WTICO_USD', 'DE10YB_EUR', 'CHF_HKD', 'USD_THB', 'GBP_CHF', 'TRY_JPY', 'XAU_XAG', 'XAU_NZD', 'AUD_CAD', 'SGD_JPY', 'EUR_NZD', 'USB10Y_USD'], 
'instrType': ['CURRENCY', 'COMMODITY', 'BOND', 'CURRENCY', 'INDEX', 'COMMODITY', 'COMMODITY', 'INDEX', 'CURRENCY', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'INDEX', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'CURRENCY', 'INDEX', 'COMMODITY', 'CURRENCY', 'BOND', 'COMMODITY', 'INDEX', 'CURRENCY', 'COMMODITY', 'CURRENCY', 'COMMODITY', 'COMMODITY', 'CURRENCY', 'INDEX', 'CURRENCY', 'CURRENCY', 'INDEX', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'COMMODITY', 'BOND', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'COMMODITY', 'INDEX', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'CURRENCY', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'INDEX', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'INDEX', 'INDEX', 'CURRENCY', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'INDEX', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'INDEX', 'COMMODITY', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'INDEX', 'INDEX', 'CURRENCY', 'BOND', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'CURRENCY', 'INDEX', 'COMMODITY', 'BOND', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'COMMODITY', 'COMMODITY', 'CURRENCY', 'CURRENCY', 'CURRENCY', 'BOND']}

instrumentsDf = pd.DataFrame(instrumentsDict)
instrumentsDf.set_index('instrument', inplace=True)

# ANCHOR Poloniex

list_of_tickers = [
                        'BTC_BCN', 'BTC_BTS', 'BTC_BURST', 'BTC_CLAM', 'BTC_DASH', 'BTC_DGB', 'BTC_DOGE', 'BTC_GAME', 
                        'BTC_HUC', 'BTC_LTC', 'BTC_MAID', 'BTC_OMNI', 'BTC_NAV', 'BTC_NMC', 'BTC_NXT', 'BTC_PPC', 
                        'BTC_STR', 'BTC_SYS', 'BTC_VIA', 'BTC_VTC', 'BTC_XCP', 'BTC_XEM', 'BTC_XMR', 'BTC_XPM', 
                        'BTC_XRP', 'USDT_BTC', 'USDT_DASH', 'USDT_LTC', 'USDT_NXT', 'USDT_STR', 'USDT_XMR', 'USDT_XRP',
                        'XMR_BCN', 'XMR_DASH', 'XMR_LTC', 'XMR_MAID', 'XMR_NXT', 'BTC_ETH', 'USDT_ETH', 'BTC_SC', 
                        'BTC_FCT', 'BTC_DCR', 'BTC_LSK', 'ETH_LSK', 'BTC_LBC', 'BTC_STEEM', 'ETH_STEEM', 'BTC_SBD', 
                        'BTC_ETC', 'ETH_ETC', 'USDT_ETC', 'BTC_REP', 'USDT_REP', 'ETH_REP', 'BTC_ARDR', 'BTC_ZEC', 
                        'ETH_ZEC', 'USDT_ZEC', 'XMR_ZEC', 'BTC_STRAT', 'BTC_PASC', 'BTC_GNT', 'ETH_GNT', 'BTC_BCH',
                        'ETH_BCH', 'USDT_BCH', 'BTC_ZRX', 'ETH_ZRX', 'BTC_CVC', 'ETH_CVC', 'BTC_OMG', 'ETH_OMG', 
                        'BTC_GAS', 'ETH_GAS', 'BTC_STORJ', 'BTC_EOS', 'ETH_EOS', 'USDT_EOS', 'BTC_SNT', 'ETH_SNT',
                        'USDT_SNT', 'BTC_KNC', 'ETH_KNC', 'USDT_KNC', 'BTC_BAT', 'ETH_BAT', 'USDT_BAT', 'BTC_LOOM',
                        'ETH_LOOM', 'USDT_LOOM', 'USDT_DOGE', 'USDT_GNT', 'USDT_LSK', 'USDT_SC', 'USDT_ZRX', 'BTC_QTUM',
                        'ETH_QTUM', 'USDT_QTUM', 'USDC_BTC', 'USDC_ETH', 'USDC_USDT', 'BTC_MANA', 'ETH_MANA', 'USDT_MANA',
                        'BTC_BNT', 'ETH_BNT', 'USDT_BNT', 'USDC_BCH', 'BTC_BCHABC', 'USDC_BCHABC', 'BTC_BCHSV', 
                        'USDC_XRP', 'USDC_XMR', 'USDC_STR', 'USDC_DOGE', 'USDC_LTC', 'USDC_ZEC', 'BTC_FOAM', 'USDC_FOAM', 
                        'BTC_NMR', 'BTC_POLY', 'BTC_LPT', 'BTC_GRIN', 'USDC_GRIN', 'BTC_ATOM', 'USDC_ATOM', 'USDC_BCHSV'
                ]

list_of_tickers2 = [
        
                        'BTC_BCN', 'BTC_BURST', 'BTC_DGB', 'BTC_DOGE', 'BTC_STR', 'BTC_XEM', 'BTC_XRP', 
                        'BTC_SC', 'USDT_NXT', 'USDT_STR', 'USDT_XRP', 'USDT_DOGE', 'USDT_SC', 'USDC_USDT', 
                        'USDC_XRP', 'USDC_STR', 'ETH_GNT', 'ETH_KNC', 'ETH_LOOM', 'ETH_MANA', 'XMR_BCN', 
                        'XMR_NXT'
        
                        ]

# ANCHOR color dict
color = {
                'black' : '#000000',
                'white' : '#FFFFFF',
                'maroon' : '#800000',
                'green' : '#008000',
                'navy' : '#000080',
                'silver' : '#C0C0C0',
                'red' : '#FF0000',
                'lime' : '#00FF00',
                'blue' : '#0000FF',
                'gray' : '#808080',
                'purple' : '#800080',
                'olive' : '#808000',
                'teal' : '#008080',
                'fuchsia' : '#FF00FF',
                'yellow' : '#FFFF00',
                'aqua' : '#00FFFF',
                'orange' : '#FF9900'
        }

# ANCHOR column names
columns = {
        'trade_data_log':['instrument','instrument_type', 'exchange', 'tradeID', 'orderID',
                                'open', 'high', 'low', 'close','percent_profit','adx', 'chopp', 
                                'ema21', 'sma50', 'sma100', 'mdi', 'pdi','time'],
        'closed_trade_summary':['instrument', 'instrument_type', 'exchange', 'tradeID', 'orderID', 'side',
                                'entry_price', 'exit_price', 'trailing_SL_dist', 'tp', 'sl', 'realizedPNL',
                                'percent_profit', 'openTime', 'closeTime', 'quantity'],
        'open_trades_summary':['instrument', 'exchange', 'tradeID', 'orderID', 'quantity','entryPrice', 
                                'side', 'trailing_distance', 'tp', 'sl'],
        'entry_conditions':['instrument', 'open', 'high', 'low', 'close', 'volume', 'pdi', 'mdi', 'ema21',
                                'sma50', 'sma100', 'ub', 'lb', 'diffdi', 'z_volume', 'chopp', 'uw/b',
                                'lw/b', 'lw/uw', 'tradeID', 'time_pos']
        }

def template(file_name, _type):
    """Return a template df whose shape is equal to the ones in the log folders.
    Params
    ------
    file_name: file for which template is required."""
    dictionary = {}
    for entry in columns[file_name]:
        dictionary[entry] = []
    dataframe = pd.DataFrame(dictionary)
    dataframe.set_index('instrument', inplace=True)
    if _type in ['dict', 'dictionary']:
        return dictionary
    elif _type in ['df', 'dataframe']:
        return dataframe 
