"""
Получает график токена в формате ohcl.
На вход нужно заменить плейсхолдеры:
    - key
    - value
    - time_unit
    - time_count
Пример использования:

chart_query_template.format(key=key, value=value, time_unit=time_unit, time_count=time_count)
"""

chart_query_template = """
query MyQuery {{
  Solana {{
    ohcl: DEXTradeByTokens(
          orderBy: {{descendingByField: "Block_Timefield"}}
          where: {{
            Trade: {{
              Currency: {{
                {key}: {{is: "{value}"}}
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
            price_last: PriceInUSD(maximum: Block_Slot)
          }}
          count
        }}
    token_info: DEXTradeByTokens(
      where: {{
        Trade: {{
          Currency: {{
            {key}: {{is: "{value}"}}
          }}
        }}
      }}
      orderBy: {{descending: Block_Time}}
      limit: {{count: 1}}
    ) {{
      Trade {{
        Currency {{
          Name
          Symbol
          Uri
          MintAddress
        }}
        PriceInUSD
        Price
      }}
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
Получает информацию о токене по его идентификатору.
На вход нужно заменить плейсхолдеры:
    - key - по чему искать токен (са, имя, тикер)
    - value - значение поиска (сам са, имя, тикер)
    - since_time_formatted
    - now_time_formatted
Пример использования:

token_info_template.format(key=key, value=value, since_time_formatted=since_time_formatted, now_time_formatted=now_time_formatted)
"""
token_info_template = """
query MyQuery {{
  Solana {{
    DEXTradeByTokens(
      where: {{
        Transaction: {{Result: {{Success: true}}}},
        Trade: {{Currency: {{{key}: {{is: "{value}"}}}}}},
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
      where: {{TokenSupplyUpdate: {{Currency: {{{key}: {{is: "{value}"}}}}}}}}
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
            BalanceUpdate: {{Currency: {{{key}: {{is: "{value}"}}}}}}
          }}
        ) {{
          count: count(distinct: BalanceUpdate_Account_Owner)
      }}
  }}
}}
"""

"""
Выводит топ трейдеров по обьему по токену.
На вход нужно заменить плейсхолдеры:
    - key
    - value
    - since_time_formatted
Пример использования:

top_traders_template.format(key=key, value=value, since_time_formatted=since_time_formatted)
"""

top_traders_template = """
query TopTraders {{
  Solana {{
    DEXTradeByTokens(
      orderBy: {{descendingByField: "volumeUsd"}}
      limit: {{count: 20}}
      where: {{Trade: {{Currency: {{{key}: {{is: "{value}"}}}}, Side: {{Amount: {{gt: "0"}}}}}}, Transaction: {{Result: {{Success: true}}}}, Block: {{Time: {{since: "{since_time_formatted}"}}}}}}
    ) {{
      Trade {{
        Account {{
          Owner
        }}
      }}
      buys: count(if: {{Trade: {{Side: {{Type: {{is: buy}}}}}}}})
      sells: count(if: {{Trade: {{Side: {{Type: {{is: sell}}}}}}}})
      bought: sum(of: Trade_Amount, if: {{Trade: {{Side: {{Type: {{is: buy}}}}}}}})
      sold: sum(of: Trade_Amount, if: {{Trade: {{Side: {{Type: {{is: sell}}}}}}}})
      volume: sum(of: Trade_Amount)
      volumeUsd: sum(of: Trade_Side_AmountInUSD)
    }}
  }}
}}

"""

top_holders_template = """
query MyQuery {{
  Solana {{
    TokenSupplyUpdates(
      where: {{TokenSupplyUpdate: {{Currency: {{{key}: {{is: "{value}"}}}}}}}}
      limit: {{count: 1}}
      orderBy: {{descending: Block_Time}}
    ) {{
      TokenSupplyUpdate {{
        PostBalance
        PostBalanceInUSD
      }}
    }}
    Top_holders: BalanceUpdates(
      orderBy: {{descendingByField: "BalanceUpdate_balance_maximum"}}
      limit: {{count: 20}}
      where: {{BalanceUpdate: {{Currency: {{{key}: {{is: "{value}"}}}}}}, Block: {{Time: {{since: "{since_time_formatted}"}}}}}}
    ) {{
      BalanceUpdate {{
        Account {{
          Owner
        }}
        balance: PostBalance(maximum: Block_Slot)
      }}
    }}
  }}
}}
"""

top_trending_template = """
query {{
  Solana {{
    DEXTradeByTokens(
      where: {{
        Transaction: {{
          Result: {{
            Success: true
          }}
        }}, 
        Block: {{
          Time: {{after: "{since_time_formatted}"}}
        }}, 
        Trade: {{
          Dex: {{
            ProtocolFamily: {{not: "pump"}}
          }}
        }}, 
        any: [
          {{
            Trade: {{
              Currency: {{
                MintAddress: {{notIn: ["EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"]}}
              }}
            }}
          }}, {{
            Trade: {{
              Currency: {{
                MintAddress: {{notIn: ["EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "So11111111111111111111111111111111111111112"]}}
              }}, 
              Side: {{
                Currency: {{
                  MintAddress: {{is: "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}}
                }}
              }}
            }}
          }}, {{
            Trade: {{
              Currency: {{
                MintAddress: {{notIn: ["Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", "So11111111111111111111111111111111111111112"]}}
              }}
              Side: {{
                Currency: {{
                  MintAddress: {{is: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"}}
                }}
              }}
            }}
          }}, {{
            Trade: {{
              Currency: {{
                MintAddress: {{notIn: ["So11111111111111111111111111111111111111112", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"]}}
              }},
              Side: {{
                Currency: {{
                  MintAddress: {{notIn: ["So11111111111111111111111111111111111111112", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"]}}
                }}
              }}
            }}
          }}
        ]
      }}
      orderBy: {{descendingByField: "usd"}}
      limit: {{count: 20}}
      limitBy: {{
        by: Trade_Currency_MintAddress,
        count: 1
      }}
    ) {{
      Trade {{
        Currency {{
          Symbol
          Name
          MintAddress
          Uri
        }}
        price_last: PriceInUSD(maximum: Block_Slot)
        price_1h_ago: PriceInUSD(minimum: Block_Slot)
      }}
      dexes: uniq(of: Trade_Dex_ProgramAddress)
      amount: sum(of: Trade_Side_Amount)
      usd: sum(of: Trade_Side_AmountInUSD)
      traders: uniq(of: Trade_Account_Owner)
      count(selectWhere: {{ge: "100"}})
    }}
  }}
}}

"""

"""
Retrieve balance of wallet.
Placeholders:
    - mint_address
Usage:

balance_template.format(mint_address=mint_address)
"""
balance_template = """
query MyQuery {{
  Solana {{
    BalanceUpdates(
      limit: {{count: 20}}
      where: {{BalanceUpdate: {{Account: {{Owner: {{is: "{mint_address}"}}}}}}}}
      orderBy: {{descendingByField: "BalanceUpdate_Balance_maximum"}}
    ) {{
      BalanceUpdate {{
        Balance: PostBalance(maximum: Block_Slot)
        Currency {{
          Name
          Symbol
          MintAddress
          Uri
        }}
      }}
    }}
  }}
}}
"""
