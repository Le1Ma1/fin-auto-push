import pandas as pd
import datetime

def process_etf_flows_json(json_data, symbol):
    # 解析 Coinglass flow-history 結構，產出 DataFrame
    flows = []
    for day in json_data['data']:
        date = datetime.datetime.fromtimestamp(day['timestamp']//1000).strftime('%Y-%m-%d')
        total = day.get('flow_usd', day.get('change_usd', 0))
        etf_flows = day.get('etf_flows') or day.get('etf_flow') or day.get('etf_flows', [])
        for etf in etf_flows:
            flows.append({
                "date": date,
                "asset": symbol,
                "etf_ticker": etf['etf_ticker'] if 'etf_ticker' in etf else etf.get('ticker', ''),
                "flow_usd": etf['flow_usd'] if 'flow_usd' in etf else etf.get('change_usd', 0),
                "total_flow_usd": total,
                "price_usd": day.get('price_usd') or day.get('price') or None
            })
    df = pd.DataFrame(flows)
    return df
