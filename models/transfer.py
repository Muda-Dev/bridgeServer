import requests

class ExchangeRateModel:
    def __init__(self, api_key):
        self.api_url = "https://api.exchangerateapi.com/v4/latest/"
        self.api_key = api_key
    
    def get_exchange_rate(self, base_currency, target_currency, amount):
        url = f"{self.api_url}{base_currency}?access_key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            rate = rates.get(target_currency, 0)
            if rate:
                converted_amount = rate * amount
                return {
                    "rate": rate,
                    "converted_amount": converted_amount,
                    "fiat_amount": converted_amount,
                    "asset_amount": converted_amount,
                }
            else:
                return {"error": "Target currency not found."}
        else:
            return {"error": "Failed to fetch exchange rates."}