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
        Timefield: Time(interval: {{in: minutes, count: 1}})
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
