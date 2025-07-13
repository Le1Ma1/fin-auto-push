from app.fetcher.farside import fetch_farside_flows

if __name__ == "__main__":
    flows = fetch_farside_flows()
    print("金流資料前5筆：")
    print(flows.head())