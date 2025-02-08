"""
Получает график токена в формате ohcl.
На вход нужно заменить плейсхолдеры:
    - mint_address
    - time_unit
    - time_count
Пример использования:

chart_query_template.format(mint_address=mint_address, time_unit=time_unit, time_count=time_count)
"""

chart_query_template = """
query MyQuery {{
  Solana {{
    DEXTradeByTokens(
      orderBy: {{descendingByField: "Block_Timefield"}}
      where: {{
        Trade: {{
          Currency: {{
            MintAddress: {{is: "{mint_address}"}}
          }}
          Side: {{
            Currency: {{
              MintAddress: {{is: "So11111111111111111111111111111111111111112"}}
            }}
          }}
          PriceAsymmetry: {{lt: 0.1}}
        }}
      }}
      limit: {{count: 100}}
    ) {{
      Block {{
        Timefield: Time(interval: {{in: {time_unit}, count: {time_count}}})
      }}
      volume: sum(of: Trade_Amount)
      Trade {{
        high: Price(maximum: Trade_Price)
        low: Price(minimum: Trade_Price)
        open: Price(minimum: Block_Slot)
        close: Price(maximum: Block_Slot)
      }}
      count
    }}
  }}
}}
"""

""""
Получает топ 10 токенов с pumpfun.
"""

pumpfun_token_sorted_by_marketcap = """
   {
  Solana {
    DEXTrades(
      limitBy: {by: Trade_Buy_Currency_MintAddress, count: 1}
      orderBy: {descending: Trade_Buy_Price}
      where: {Trade: {Dex: {ProtocolName: {is: "pump"}}, Buy: {Currency: {MintAddress: {notIn: ["11111111111111111111111111111111"]}}}}, Transaction: {Result: {Success: true}}}
      limit: {count: 10}
    ) {
      Trade {
        Buy {
          Price
          PriceInUSD
          Currency {
            Name
            Symbol
            MintAddress
            Decimals
            Fungible
            Uri
          }
        }
      }
    }
  }
}
"""

"""
Получает информацию о токене по его контракту.
На вход нужно заменить плейсхолдеры:
    - mint_address
    - since_time_formatted
    - now_time_formatted
Пример использования:

token_info_by_mint_address_template.format(mint_address=mint_address, since_time_formatted=since_time_formatted, now_time_formatted=now_time_formatted)
"""
token_info_by_mint_address_template = """
query MyQuery {{
  Solana {{
    DEXTradeByTokens(
      where: {{
        Transaction: {{Result: {{Success: true}}}},
        Trade: {{Currency: {{MintAddress: {{is: "{mint_address}"}}}}}},
        Block: {{Time: {{since: "{since_time_formatted}"}}}}
      }}
    ) {{
      Trade {{
        Currency {{
          Name
          MintAddress
          Symbol
        }}
        start: PriceInUSD(minimum: Block_Time)
        min5: PriceInUSD(
          minimum: Block_Time
          if: {{Block: {{Time: {{after: "{now_time_formatted}"}}}}}}
        )
        end: PriceInUSD(maximum: Block_Time)
        Dex {{
          ProtocolName
          ProtocolFamily
          ProgramAddress
        }}
        Market {{
          MarketAddress
        }}
        Side {{
          Currency {{
            Symbol
            Name
            MintAddress
          }}
        }}
      }}
      makers: count(distinct: Transaction_Signer)
      makers_5min: count(distinct: Transaction_Signer if: {{Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
      buyers: count(distinct: Transaction_Signer if: {{Trade: {{Side: {{Type: {{is: buy}}}}}}}})
      buyers_5min: count(distinct: Transaction_Signer if: {{Trade: {{Side: {{Type: {{is: buy}}}}}}, Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
      sellers: count(distinct: Transaction_Signer if: {{Trade: {{Side: {{Type: {{is: sell}}}}}}}})
      sellers_5min: count(distinct: Transaction_Signer if: {{Trade: {{Side: {{Type: {{is: sell}}}}}}, Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
      trades: count
      trades_5min: count(if: {{Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
      traded_volume: sum(of: Trade_Side_AmountInUSD)
      traded_volume_5min: sum(of: Trade_Side_AmountInUSD if: {{Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
      buy_volume: sum(of: Trade_Side_AmountInUSD if: {{Trade: {{Side: {{Type: {{is: buy}}}}}}}})
      buy_volume_5min: sum(of: Trade_Side_AmountInUSD if: {{Trade: {{Side: {{Type: {{is: buy}}}}}}, Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
      sell_volume: sum(of: Trade_Side_AmountInUSD if: {{Trade: {{Side: {{Type: {{is: sell}}}}}}}})
      sell_volume_5min: sum(of: Trade_Side_AmountInUSD if: {{Trade: {{Side: {{Type: {{is: sell}}}}}}, Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
      buys: count(if: {{Trade: {{Side: {{Type: {{is: buy}}}}}}}})
      buys_5min: count(if: {{Trade: {{Side: {{Type: {{is: buy}}}}}}, Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
      sells: count(if: {{Trade: {{Side: {{Type: {{is: sell}}}}}}}})
      sells_5min: count(if: {{Trade: {{Side: {{Type: {{is: sell}}}}}}, Block: {{Time: {{after: "{now_time_formatted}"}}}}}})
    }}
    TokenSupplyUpdates(
      where: {{TokenSupplyUpdate: {{Currency: {{MintAddress: {{is: "{mint_address}"}}}}}}}}
      limit: {{count: 1}}
      orderBy: {{descending: Block_Time}}
    ) {{
      TokenSupplyUpdate {{
        PostBalance
        PostBalanceInUSD
      }}
    }}
      BalanceUpdates(
          where: {{
            BalanceUpdate: {{Currency: {{MintAddress: {{is: "{mint_address}"}}}}}}
          }}
        ) {{
          count: count(distinct: BalanceUpdate_Account_Owner)
      }}
  }}
}}
"""