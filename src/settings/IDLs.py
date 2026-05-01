true = True
false = False

idl_dlmm = {
  "address": "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
  "metadata": {
    "name": "lb_clmm",
    "version": "0.9.1",
    "spec": "0.1.0",
    "description": "Created with Anchor"
  },
  "instructions": [
    {
      "name": "add_liquidity",
      "discriminator": [181, 157, 89, 67, 143, 182, 52, 72],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "liquidity_parameter",
          "type": {
            "defined": {
              "name": "LiquidityParameter"
            }
          }
        }
      ]
    },
    {
      "name": "add_liquidity2",
      "discriminator": [228, 162, 78, 28, 70, 219, 116, 115],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "liquidity_parameter",
          "type": {
            "defined": {
              "name": "LiquidityParameter"
            }
          }
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "add_liquidity_by_strategy",
      "discriminator": [7, 3, 150, 127, 148, 40, 61, 200],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "liquidity_parameter",
          "type": {
            "defined": {
              "name": "LiquidityParameterByStrategy"
            }
          }
        }
      ]
    },
    {
      "name": "add_liquidity_by_strategy2",
      "discriminator": [3, 221, 149, 218, 111, 141, 118, 213],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "liquidity_parameter",
          "type": {
            "defined": {
              "name": "LiquidityParameterByStrategy"
            }
          }
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "add_liquidity_by_strategy_one_side",
      "discriminator": [41, 5, 238, 175, 100, 225, 6, 205],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token",
          "writable": true
        },
        {
          "name": "reserve",
          "writable": true
        },
        {
          "name": "token_mint"
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "liquidity_parameter",
          "type": {
            "defined": {
              "name": "LiquidityParameterByStrategyOneSide"
            }
          }
        }
      ]
    },
    {
      "name": "add_liquidity_by_weight",
      "discriminator": [28, 140, 238, 99, 231, 162, 21, 149],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "liquidity_parameter",
          "type": {
            "defined": {
              "name": "LiquidityParameterByWeight"
            }
          }
        }
      ]
    },
    {
      "name": "add_liquidity_one_side",
      "discriminator": [94, 155, 103, 151, 70, 95, 220, 165],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token",
          "writable": true
        },
        {
          "name": "reserve",
          "writable": true
        },
        {
          "name": "token_mint"
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "liquidity_parameter",
          "type": {
            "defined": {
              "name": "LiquidityOneSideParameter"
            }
          }
        }
      ]
    },
    {
      "name": "add_liquidity_one_side_precise",
      "discriminator": [161, 194, 103, 84, 171, 71, 250, 154],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token",
          "writable": true
        },
        {
          "name": "reserve",
          "writable": true
        },
        {
          "name": "token_mint"
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "parameter",
          "type": {
            "defined": {
              "name": "AddLiquiditySingleSidePreciseParameter"
            }
          }
        }
      ]
    },
    {
      "name": "add_liquidity_one_side_precise2",
      "discriminator": [33, 51, 163, 201, 117, 98, 125, 231],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token",
          "writable": true
        },
        {
          "name": "reserve",
          "writable": true
        },
        {
          "name": "token_mint"
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "liquidity_parameter",
          "type": {
            "defined": {
              "name": "AddLiquiditySingleSidePreciseParameter2"
            }
          }
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "claim_fee",
      "discriminator": [169, 32, 79, 137, 136, 232, 70, 137],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_lower", "bin_array_upper"]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "claim_fee2",
      "discriminator": [112, 191, 101, 171, 28, 144, 127, 187],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position"]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_program_x"
        },
        {
          "name": "token_program_y"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "min_bin_id",
          "type": "i32"
        },
        {
          "name": "max_bin_id",
          "type": "i32"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "claim_reward",
      "discriminator": [149, 95, 181, 242, 94, 90, 158, 162],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_lower", "bin_array_upper"]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "reward_vault",
          "writable": true
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "user_token_account",
          "writable": true
        },
        {
          "name": "token_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u64"
        }
      ]
    },
    {
      "name": "claim_reward2",
      "discriminator": [190, 3, 127, 119, 178, 87, 157, 183],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position"]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "reward_vault",
          "writable": true
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "user_token_account",
          "writable": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u64"
        },
        {
          "name": "min_bin_id",
          "type": "i32"
        },
        {
          "name": "max_bin_id",
          "type": "i32"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "close_claim_protocol_fee_operator",
      "discriminator": [8, 41, 87, 35, 80, 48, 121, 26],
      "accounts": [
        {
          "name": "claim_fee_operator",
          "writable": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "admin",
          "signer": true
        }
      ],
      "args": []
    },
    {
      "name": "close_position",
      "discriminator": [123, 134, 81, 0, 49, 68, 98, 98],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_lower", "bin_array_upper"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "close_position2",
      "discriminator": [174, 90, 35, 115, 186, 40, 147, 226],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "close_position_if_empty",
      "discriminator": [59, 124, 212, 118, 91, 152, 110, 157],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "close_preset_parameter",
      "discriminator": [4, 148, 145, 100, 134, 26, 181, 61],
      "accounts": [
        {
          "name": "preset_parameter",
          "writable": true
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        }
      ],
      "args": []
    },
    {
      "name": "close_preset_parameter2",
      "discriminator": [39, 25, 95, 107, 116, 17, 115, 28],
      "accounts": [
        {
          "name": "preset_parameter",
          "writable": true
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        }
      ],
      "args": []
    },
    {
      "name": "create_claim_protocol_fee_operator",
      "discriminator": [51, 19, 150, 252, 105, 157, 48, 91],
      "accounts": [
        {
          "name": "claim_fee_operator",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [99, 102, 95, 111, 112, 101, 114, 97, 116, 111, 114]
              },
              {
                "kind": "account",
                "path": "operator"
              }
            ]
          }
        },
        {
          "name": "operator"
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": []
    },
    {
      "name": "decrease_position_length",
      "discriminator": [194, 219, 136, 32, 25, 96, 105, 37],
      "accounts": [
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "owner",
          "signer": true,
          "relations": ["position"]
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "length_to_remove",
          "type": "u16"
        },
        {
          "name": "side",
          "type": "u8"
        }
      ]
    },
    {
      "name": "for_idl_type_generation_do_not_call",
      "discriminator": [180, 105, 69, 80, 95, 50, 73, 108],
      "accounts": [
        {
          "name": "dummy_zc_account"
        }
      ],
      "args": [
        {
          "name": "_ix",
          "type": {
            "defined": {
              "name": "DummyIx"
            }
          }
        }
      ]
    },
    {
      "name": "fund_reward",
      "discriminator": [188, 50, 249, 165, 93, 151, 38, 63],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array"]
        },
        {
          "name": "reward_vault",
          "writable": true
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "funder_token_account",
          "writable": true
        },
        {
          "name": "funder",
          "signer": true
        },
        {
          "name": "bin_array",
          "writable": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u64"
        },
        {
          "name": "amount",
          "type": "u64"
        },
        {
          "name": "carry_forward",
          "type": "bool"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "go_to_a_bin",
      "discriminator": [146, 72, 174, 224, 40, 253, 84, 174],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "bin_array_bitmap_extension",
            "from_bin_array",
            "to_bin_array"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "optional": true
        },
        {
          "name": "from_bin_array",
          "optional": true
        },
        {
          "name": "to_bin_array",
          "optional": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "bin_id",
          "type": "i32"
        }
      ]
    },
    {
      "name": "increase_oracle_length",
      "discriminator": [190, 61, 125, 87, 103, 79, 158, 173],
      "accounts": [
        {
          "name": "oracle",
          "writable": true
        },
        {
          "name": "funder",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "length_to_add",
          "type": "u64"
        }
      ]
    },
    {
      "name": "increase_position_length",
      "discriminator": [80, 83, 117, 211, 66, 13, 33, 149],
      "accounts": [
        {
          "name": "funder",
          "writable": true,
          "signer": true
        },
        {
          "name": "lb_pair",
          "relations": ["position"]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "owner",
          "signer": true,
          "relations": ["position"]
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "length_to_add",
          "type": "u16"
        },
        {
          "name": "side",
          "type": "u8"
        }
      ]
    },
    {
      "name": "initialize_bin_array",
      "discriminator": [35, 86, 19, 185, 78, 212, 75, 211],
      "accounts": [
        {
          "name": "lb_pair"
        },
        {
          "name": "bin_array",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [98, 105, 110, 95, 97, 114, 114, 97, 121]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "arg",
                "path": "index"
              }
            ]
          }
        },
        {
          "name": "funder",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "index",
          "type": "i64"
        }
      ]
    },
    {
      "name": "initialize_bin_array_bitmap_extension",
      "discriminator": [47, 157, 226, 180, 12, 240, 33, 71],
      "accounts": [
        {
          "name": "lb_pair"
        },
        {
          "name": "bin_array_bitmap_extension",
          "docs": [
            "Initialize an account to store if a bin array is initialized."
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [98, 105, 116, 109, 97, 112]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "funder",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "rent",
          "address": "SysvarRent111111111111111111111111111111111"
        }
      ],
      "args": []
    },
    {
      "name": "initialize_customizable_permissionless_lb_pair",
      "discriminator": [46, 39, 41, 135, 111, 183, 200, 64],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [98, 105, 116, 109, 97, 112]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "token_mint_x"
        },
        {
          "name": "token_mint_y"
        },
        {
          "name": "reserve_x",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_x"
              }
            ]
          }
        },
        {
          "name": "reserve_y",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_y"
              }
            ]
          }
        },
        {
          "name": "oracle",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [111, 114, 97, 99, 108, 101]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "user_token_x"
        },
        {
          "name": "funder",
          "writable": true,
          "signer": true
        },
        {
          "name": "token_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "user_token_y"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "CustomizableParams"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_customizable_permissionless_lb_pair2",
      "discriminator": [243, 73, 129, 126, 51, 19, 241, 107],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [98, 105, 116, 109, 97, 112]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "token_mint_x"
        },
        {
          "name": "token_mint_y"
        },
        {
          "name": "reserve_x",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_x"
              }
            ]
          }
        },
        {
          "name": "reserve_y",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_y"
              }
            ]
          }
        },
        {
          "name": "oracle",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [111, 114, 97, 99, 108, 101]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "user_token_x"
        },
        {
          "name": "funder",
          "writable": true,
          "signer": true
        },
        {
          "name": "token_badge_x",
          "optional": true
        },
        {
          "name": "token_badge_y",
          "optional": true
        },
        {
          "name": "token_program_x"
        },
        {
          "name": "token_program_y"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "user_token_y"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "CustomizableParams"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_lb_pair",
      "discriminator": [45, 154, 237, 210, 221, 15, 166, 92],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [98, 105, 116, 109, 97, 112]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "token_mint_x"
        },
        {
          "name": "token_mint_y"
        },
        {
          "name": "reserve_x",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_x"
              }
            ]
          }
        },
        {
          "name": "reserve_y",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_y"
              }
            ]
          }
        },
        {
          "name": "oracle",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [111, 114, 97, 99, 108, 101]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "preset_parameter"
        },
        {
          "name": "funder",
          "writable": true,
          "signer": true
        },
        {
          "name": "token_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "rent",
          "address": "SysvarRent111111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "active_id",
          "type": "i32"
        },
        {
          "name": "bin_step",
          "type": "u16"
        }
      ]
    },
    {
      "name": "initialize_lb_pair2",
      "discriminator": [73, 59, 36, 120, 237, 83, 108, 198],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [98, 105, 116, 109, 97, 112]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "token_mint_x"
        },
        {
          "name": "token_mint_y"
        },
        {
          "name": "reserve_x",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_x"
              }
            ]
          }
        },
        {
          "name": "reserve_y",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_y"
              }
            ]
          }
        },
        {
          "name": "oracle",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [111, 114, 97, 99, 108, 101]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "preset_parameter"
        },
        {
          "name": "funder",
          "writable": true,
          "signer": true
        },
        {
          "name": "token_badge_x",
          "optional": true
        },
        {
          "name": "token_badge_y",
          "optional": true
        },
        {
          "name": "token_program_x"
        },
        {
          "name": "token_program_y"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "InitializeLbPair2Params"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_permission_lb_pair",
      "discriminator": [108, 102, 213, 85, 251, 3, 53, 21],
      "accounts": [
        {
          "name": "base",
          "signer": true
        },
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [98, 105, 116, 109, 97, 112]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "token_mint_x"
        },
        {
          "name": "token_mint_y"
        },
        {
          "name": "reserve_x",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_x"
              }
            ]
          }
        },
        {
          "name": "reserve_y",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "token_mint_y"
              }
            ]
          }
        },
        {
          "name": "oracle",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [111, 114, 97, 99, 108, 101]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              }
            ]
          }
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "token_badge_x",
          "optional": true
        },
        {
          "name": "token_badge_y",
          "optional": true
        },
        {
          "name": "token_program_x"
        },
        {
          "name": "token_program_y"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "rent",
          "address": "SysvarRent111111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "ix_data",
          "type": {
            "defined": {
              "name": "InitPermissionPairIx"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_position",
      "discriminator": [219, 192, 234, 71, 190, 191, 102, 80],
      "accounts": [
        {
          "name": "payer",
          "writable": true,
          "signer": true
        },
        {
          "name": "position",
          "writable": true,
          "signer": true
        },
        {
          "name": "lb_pair"
        },
        {
          "name": "owner",
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "rent",
          "address": "SysvarRent111111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "lower_bin_id",
          "type": "i32"
        },
        {
          "name": "width",
          "type": "i32"
        }
      ]
    },
    {
      "name": "initialize_position_by_operator",
      "discriminator": [251, 189, 190, 244, 117, 254, 35, 148],
      "accounts": [
        {
          "name": "payer",
          "writable": true,
          "signer": true
        },
        {
          "name": "base",
          "signer": true
        },
        {
          "name": "position",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [112, 111, 115, 105, 116, 105, 111, 110]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "base"
              },
              {
                "kind": "arg",
                "path": "lower_bin_id"
              },
              {
                "kind": "arg",
                "path": "width"
              }
            ]
          }
        },
        {
          "name": "lb_pair"
        },
        {
          "name": "owner"
        },
        {
          "name": "operator",
          "docs": ["operator"],
          "signer": true
        },
        {
          "name": "operator_token_x"
        },
        {
          "name": "owner_token_x"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "lower_bin_id",
          "type": "i32"
        },
        {
          "name": "width",
          "type": "i32"
        },
        {
          "name": "fee_owner",
          "type": "pubkey"
        },
        {
          "name": "lock_release_point",
          "type": "u64"
        }
      ]
    },
    {
      "name": "initialize_position_pda",
      "discriminator": [46, 82, 125, 146, 85, 141, 228, 153],
      "accounts": [
        {
          "name": "payer",
          "writable": true,
          "signer": true
        },
        {
          "name": "base",
          "signer": true
        },
        {
          "name": "position",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [112, 111, 115, 105, 116, 105, 111, 110]
              },
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "account",
                "path": "base"
              },
              {
                "kind": "arg",
                "path": "lower_bin_id"
              },
              {
                "kind": "arg",
                "path": "width"
              }
            ]
          }
        },
        {
          "name": "lb_pair"
        },
        {
          "name": "owner",
          "docs": ["owner"],
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "rent",
          "address": "SysvarRent111111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "lower_bin_id",
          "type": "i32"
        },
        {
          "name": "width",
          "type": "i32"
        }
      ]
    },
    {
      "name": "initialize_preset_parameter",
      "discriminator": [66, 188, 71, 211, 98, 109, 14, 186],
      "accounts": [
        {
          "name": "preset_parameter",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112, 114, 101, 115, 101, 116, 95, 112, 97, 114, 97, 109, 101,
                  116, 101, 114
                ]
              },
              {
                "kind": "arg",
                "path": "ix.bin_step"
              },
              {
                "kind": "arg",
                "path": "ix.base_factor"
              }
            ]
          }
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "rent",
          "address": "SysvarRent111111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "ix",
          "type": {
            "defined": {
              "name": "InitPresetParametersIx"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_preset_parameter2",
      "discriminator": [184, 7, 240, 171, 103, 47, 183, 121],
      "accounts": [
        {
          "name": "preset_parameter",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112, 114, 101, 115, 101, 116, 95, 112, 97, 114, 97, 109, 101,
                  116, 101, 114, 50
                ]
              },
              {
                "kind": "arg",
                "path": "ix.index"
              }
            ]
          }
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "ix",
          "type": {
            "defined": {
              "name": "InitPresetParameters2Ix"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_reward",
      "discriminator": [95, 135, 192, 196, 242, 129, 230, 68],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "reward_vault",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "account",
                "path": "lb_pair"
              },
              {
                "kind": "arg",
                "path": "reward_index"
              }
            ]
          }
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "token_badge",
          "optional": true
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "rent",
          "address": "SysvarRent111111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u64"
        },
        {
          "name": "reward_duration",
          "type": "u64"
        },
        {
          "name": "funder",
          "type": "pubkey"
        }
      ]
    },
    {
      "name": "initialize_token_badge",
      "discriminator": [253, 77, 205, 95, 27, 224, 89, 223],
      "accounts": [
        {
          "name": "token_mint"
        },
        {
          "name": "token_badge",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [116, 111, 107, 101, 110, 95, 98, 97, 100, 103, 101]
              },
              {
                "kind": "account",
                "path": "token_mint"
              }
            ]
          }
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": []
    },
    {
      "name": "migrate_bin_array",
      "discriminator": [17, 23, 159, 211, 101, 184, 41, 241],
      "accounts": [
        {
          "name": "lb_pair"
        }
      ],
      "args": []
    },
    {
      "name": "migrate_position",
      "discriminator": [15, 132, 59, 50, 199, 6, 251, 46],
      "accounts": [
        {
          "name": "position_v2",
          "writable": true,
          "signer": true
        },
        {
          "name": "position_v1",
          "writable": true
        },
        {
          "name": "lb_pair",
          "relations": ["position_v1", "bin_array_lower", "bin_array_upper"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "owner",
          "writable": true,
          "signer": true,
          "relations": ["position_v1"]
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "rebalance_liquidity",
      "discriminator": [92, 4, 176, 193, 119, 185, 83, 9],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "owner",
          "signer": true,
          "relations": ["position"]
        },
        {
          "name": "rent_payer",
          "writable": true,
          "signer": true
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "RebalanceLiquidityParams"
            }
          }
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "remove_all_liquidity",
      "discriminator": [10, 51, 61, 35, 112, 105, 24, 85],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "remove_liquidity",
      "discriminator": [80, 85, 209, 72, 24, 206, 177, 108],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "bin_liquidity_removal",
          "type": {
            "vec": {
              "defined": {
                "name": "BinLiquidityReduction"
              }
            }
          }
        }
      ]
    },
    {
      "name": "remove_liquidity2",
      "discriminator": [230, 215, 82, 127, 241, 101, 227, 146],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "bin_liquidity_removal",
          "type": {
            "vec": {
              "defined": {
                "name": "BinLiquidityReduction"
              }
            }
          }
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "remove_liquidity_by_range",
      "discriminator": [26, 82, 102, 152, 240, 74, 105, 26],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": [
            "position",
            "bin_array_bitmap_extension",
            "bin_array_lower",
            "bin_array_upper"
          ]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "from_bin_id",
          "type": "i32"
        },
        {
          "name": "to_bin_id",
          "type": "i32"
        },
        {
          "name": "bps_to_remove",
          "type": "u16"
        }
      ]
    },
    {
      "name": "remove_liquidity_by_range2",
      "discriminator": [204, 2, 195, 145, 53, 145, 145, 205],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "writable": true,
          "optional": true
        },
        {
          "name": "user_token_x",
          "writable": true
        },
        {
          "name": "user_token_y",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "sender",
          "signer": true
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "from_bin_id",
          "type": "i32"
        },
        {
          "name": "to_bin_id",
          "type": "i32"
        },
        {
          "name": "bps_to_remove",
          "type": "u16"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "set_activation_point",
      "discriminator": [91, 249, 15, 165, 26, 129, 254, 125],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        }
      ],
      "args": [
        {
          "name": "activation_point",
          "type": "u64"
        }
      ]
    },
    {
      "name": "set_pair_status",
      "discriminator": [67, 248, 231, 137, 154, 149, 217, 174],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "admin",
          "signer": true
        }
      ],
      "args": [
        {
          "name": "status",
          "type": "u8"
        }
      ]
    },
    {
      "name": "set_pair_status_permissionless",
      "discriminator": [78, 59, 152, 211, 70, 183, 46, 208],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "creator",
          "signer": true,
          "relations": ["lb_pair"]
        }
      ],
      "args": [
        {
          "name": "status",
          "type": "u8"
        }
      ]
    },
    {
      "name": "set_pre_activation_duration",
      "discriminator": [165, 61, 201, 244, 130, 159, 22, 100],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "creator",
          "signer": true,
          "relations": ["lb_pair"]
        }
      ],
      "args": [
        {
          "name": "pre_activation_duration",
          "type": "u64"
        }
      ]
    },
    {
      "name": "set_pre_activation_swap_address",
      "discriminator": [57, 139, 47, 123, 216, 80, 223, 10],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "creator",
          "signer": true,
          "relations": ["lb_pair"]
        }
      ],
      "args": [
        {
          "name": "pre_activation_swap_address",
          "type": "pubkey"
        }
      ]
    },
    {
      "name": "swap",
      "discriminator": [248, 198, 158, 145, 225, 117, 135, 200],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "optional": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "user_token_in",
          "writable": true
        },
        {
          "name": "user_token_out",
          "writable": true
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "oracle",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "host_fee_in",
          "writable": true,
          "optional": true
        },
        {
          "name": "user",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "amount_in",
          "type": "u64"
        },
        {
          "name": "min_amount_out",
          "type": "u64"
        }
      ]
    },
    {
      "name": "swap2",
      "discriminator": [65, 75, 63, 76, 235, 91, 91, 136],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "optional": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "user_token_in",
          "writable": true
        },
        {
          "name": "user_token_out",
          "writable": true
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "oracle",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "host_fee_in",
          "writable": true,
          "optional": true
        },
        {
          "name": "user",
          "signer": true
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "amount_in",
          "type": "u64"
        },
        {
          "name": "min_amount_out",
          "type": "u64"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "swap_exact_out",
      "discriminator": [250, 73, 101, 33, 38, 207, 75, 184],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "optional": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "user_token_in",
          "writable": true
        },
        {
          "name": "user_token_out",
          "writable": true
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "oracle",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "host_fee_in",
          "writable": true,
          "optional": true
        },
        {
          "name": "user",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "max_in_amount",
          "type": "u64"
        },
        {
          "name": "out_amount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "swap_exact_out2",
      "discriminator": [43, 215, 247, 132, 137, 60, 243, 81],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "optional": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "user_token_in",
          "writable": true
        },
        {
          "name": "user_token_out",
          "writable": true
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "oracle",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "host_fee_in",
          "writable": true,
          "optional": true
        },
        {
          "name": "user",
          "signer": true
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "max_in_amount",
          "type": "u64"
        },
        {
          "name": "out_amount",
          "type": "u64"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "swap_with_price_impact",
      "discriminator": [56, 173, 230, 208, 173, 228, 156, 205],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "optional": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "user_token_in",
          "writable": true
        },
        {
          "name": "user_token_out",
          "writable": true
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "oracle",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "host_fee_in",
          "writable": true,
          "optional": true
        },
        {
          "name": "user",
          "signer": true
        },
        {
          "name": "token_x_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "token_y_program",
          "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "amount_in",
          "type": "u64"
        },
        {
          "name": "active_id",
          "type": {
            "option": "i32"
          }
        },
        {
          "name": "max_price_impact_bps",
          "type": "u16"
        }
      ]
    },
    {
      "name": "swap_with_price_impact2",
      "discriminator": [74, 98, 192, 214, 177, 51, 75, 51],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array_bitmap_extension"]
        },
        {
          "name": "bin_array_bitmap_extension",
          "optional": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "user_token_in",
          "writable": true
        },
        {
          "name": "user_token_out",
          "writable": true
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "oracle",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "host_fee_in",
          "writable": true,
          "optional": true
        },
        {
          "name": "user",
          "signer": true
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "amount_in",
          "type": "u64"
        },
        {
          "name": "active_id",
          "type": {
            "option": "i32"
          }
        },
        {
          "name": "max_price_impact_bps",
          "type": "u16"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "update_base_fee_parameters",
      "discriminator": [75, 168, 223, 161, 16, 195, 3, 47],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "admin",
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "fee_parameter",
          "type": {
            "defined": {
              "name": "BaseFeeParameter"
            }
          }
        }
      ]
    },
    {
      "name": "update_dynamic_fee_parameters",
      "discriminator": [92, 161, 46, 246, 255, 189, 22, 22],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "admin",
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "fee_parameter",
          "type": {
            "defined": {
              "name": "DynamicFeeParameter"
            }
          }
        }
      ]
    },
    {
      "name": "update_fees_and_reward2",
      "discriminator": [32, 142, 184, 154, 103, 65, 184, 88],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position"]
        },
        {
          "name": "owner",
          "signer": true
        }
      ],
      "args": [
        {
          "name": "min_bin_id",
          "type": "i32"
        },
        {
          "name": "max_bin_id",
          "type": "i32"
        }
      ]
    },
    {
      "name": "update_fees_and_rewards",
      "discriminator": [154, 230, 250, 13, 236, 209, 75, 223],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["position", "bin_array_lower", "bin_array_upper"]
        },
        {
          "name": "bin_array_lower",
          "writable": true
        },
        {
          "name": "bin_array_upper",
          "writable": true
        },
        {
          "name": "owner",
          "signer": true
        }
      ],
      "args": []
    },
    {
      "name": "update_position_operator",
      "discriminator": [202, 184, 103, 143, 180, 191, 116, 217],
      "accounts": [
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "owner",
          "signer": true,
          "relations": ["position"]
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "operator",
          "type": "pubkey"
        }
      ]
    },
    {
      "name": "update_reward_duration",
      "discriminator": [138, 174, 196, 169, 213, 235, 254, 107],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array"]
        },
        {
          "name": "admin",
          "signer": true
        },
        {
          "name": "bin_array",
          "writable": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u64"
        },
        {
          "name": "new_duration",
          "type": "u64"
        }
      ]
    },
    {
      "name": "update_reward_funder",
      "discriminator": [211, 28, 48, 32, 215, 160, 35, 23],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "admin",
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u64"
        },
        {
          "name": "new_funder",
          "type": "pubkey"
        }
      ]
    },
    {
      "name": "withdraw_ineligible_reward",
      "discriminator": [148, 206, 42, 195, 247, 49, 103, 8],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true,
          "relations": ["bin_array"]
        },
        {
          "name": "reward_vault",
          "writable": true
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "funder_token_account",
          "writable": true
        },
        {
          "name": "funder",
          "signer": true
        },
        {
          "name": "bin_array",
          "writable": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95, 95, 101, 118, 101, 110, 116, 95, 97, 117, 116, 104, 111,
                  114, 105, 116, 121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u64"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    },
    {
      "name": "withdraw_protocol_fee",
      "discriminator": [158, 201, 158, 189, 33, 93, 162, 103],
      "accounts": [
        {
          "name": "lb_pair",
          "writable": true
        },
        {
          "name": "reserve_x",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "reserve_y",
          "writable": true,
          "relations": ["lb_pair"]
        },
        {
          "name": "token_x_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "token_y_mint",
          "relations": ["lb_pair"]
        },
        {
          "name": "receiver_token_x",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  48, 9, 89, 123, 106, 114, 131, 251, 50, 173, 254, 250, 10, 80,
                  160, 84, 143, 100, 81, 249, 134, 112, 30, 213, 50, 166, 239,
                  78, 53, 175, 188, 85
                ]
              },
              {
                "kind": "account",
                "path": "token_x_program"
              },
              {
                "kind": "account",
                "path": "token_x_mint"
              }
            ],
            "program": {
              "kind": "const",
              "value": [
                140, 151, 37, 143, 78, 36, 137, 241, 187, 61, 16, 41, 20, 142,
                13, 131, 11, 90, 19, 153, 218, 255, 16, 132, 4, 142, 123, 216,
                219, 233, 248, 89
              ]
            }
          }
        },
        {
          "name": "receiver_token_y",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  48, 9, 89, 123, 106, 114, 131, 251, 50, 173, 254, 250, 10, 80,
                  160, 84, 143, 100, 81, 249, 134, 112, 30, 213, 50, 166, 239,
                  78, 53, 175, 188, 85
                ]
              },
              {
                "kind": "account",
                "path": "token_y_program"
              },
              {
                "kind": "account",
                "path": "token_y_mint"
              }
            ],
            "program": {
              "kind": "const",
              "value": [
                140, 151, 37, 143, 78, 36, 137, 241, 187, 61, 16, 41, 20, 142,
                13, 131, 11, 90, 19, 153, 218, 255, 16, 132, 4, 142, 123, 216,
                219, 233, 248, 89
              ]
            }
          }
        },
        {
          "name": "claim_fee_operator"
        },
        {
          "name": "operator",
          "docs": ["operator"],
          "signer": true,
          "relations": ["claim_fee_operator"]
        },
        {
          "name": "token_x_program"
        },
        {
          "name": "token_y_program"
        },
        {
          "name": "memo_program",
          "address": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
        }
      ],
      "args": [
        {
          "name": "max_amount_x",
          "type": "u64"
        },
        {
          "name": "max_amount_y",
          "type": "u64"
        },
        {
          "name": "remaining_accounts_info",
          "type": {
            "defined": {
              "name": "RemainingAccountsInfo"
            }
          }
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "BinArray",
      "discriminator": [92, 142, 92, 220, 5, 148, 70, 181]
    },
    {
      "name": "BinArrayBitmapExtension",
      "discriminator": [80, 111, 124, 113, 55, 237, 18, 5]
    },
    {
      "name": "ClaimFeeOperator",
      "discriminator": [166, 48, 134, 86, 34, 200, 188, 150]
    },
    {
      "name": "DummyZcAccount",
      "discriminator": [94, 107, 238, 80, 208, 48, 180, 8]
    },
    {
      "name": "LbPair",
      "discriminator": [33, 11, 49, 98, 181, 101, 177, 13]
    },
    {
      "name": "Oracle",
      "discriminator": [139, 194, 131, 179, 140, 179, 229, 244]
    },
    {
      "name": "Position",
      "discriminator": [170, 188, 143, 228, 122, 64, 247, 208]
    },
    {
      "name": "PositionV2",
      "discriminator": [117, 176, 212, 199, 245, 180, 133, 182]
    },
    {
      "name": "PresetParameter",
      "discriminator": [242, 62, 244, 34, 181, 112, 58, 170]
    },
    {
      "name": "PresetParameter2",
      "discriminator": [171, 236, 148, 115, 162, 113, 222, 174]
    },
    {
      "name": "TokenBadge",
      "discriminator": [116, 219, 204, 229, 249, 116, 255, 150]
    }
  ],
  "events": [
    {
      "name": "AddLiquidity",
      "discriminator": [31, 94, 125, 90, 227, 52, 61, 186]
    },
    {
      "name": "ClaimFee",
      "discriminator": [75, 122, 154, 48, 140, 74, 123, 163]
    },
    {
      "name": "ClaimReward",
      "discriminator": [148, 116, 134, 204, 22, 171, 85, 95]
    },
    {
      "name": "CompositionFee",
      "discriminator": [128, 151, 123, 106, 17, 102, 113, 142]
    },
    {
      "name": "DecreasePositionLength",
      "discriminator": [52, 118, 235, 85, 172, 169, 15, 128]
    },
    {
      "name": "DynamicFeeParameterUpdate",
      "discriminator": [88, 88, 178, 135, 194, 146, 91, 243]
    },
    {
      "name": "FeeParameterUpdate",
      "discriminator": [48, 76, 241, 117, 144, 215, 242, 44]
    },
    {
      "name": "FundReward",
      "discriminator": [246, 228, 58, 130, 145, 170, 79, 204]
    },
    {
      "name": "GoToABin",
      "discriminator": [59, 138, 76, 68, 138, 131, 176, 67]
    },
    {
      "name": "IncreaseObservation",
      "discriminator": [99, 249, 17, 121, 166, 156, 207, 215]
    },
    {
      "name": "IncreasePositionLength",
      "discriminator": [157, 239, 42, 204, 30, 56, 223, 46]
    },
    {
      "name": "InitializeReward",
      "discriminator": [211, 153, 88, 62, 149, 60, 177, 70]
    },
    {
      "name": "LbPairCreate",
      "discriminator": [185, 74, 252, 125, 27, 215, 188, 111]
    },
    {
      "name": "PositionClose",
      "discriminator": [255, 196, 16, 107, 28, 202, 53, 128]
    },
    {
      "name": "PositionCreate",
      "discriminator": [144, 142, 252, 84, 157, 53, 37, 121]
    },
    {
      "name": "Rebalancing",
      "discriminator": [0, 109, 117, 179, 61, 91, 199, 200]
    },
    {
      "name": "RemoveLiquidity",
      "discriminator": [116, 244, 97, 232, 103, 31, 152, 58]
    },
    {
      "name": "swap_python",
      "discriminator": [81, 108, 227, 190, 205, 208, 10, 196]
    },
    {
      "name": "UpdatePositionLockReleasePoint",
      "discriminator": [133, 214, 66, 224, 64, 12, 7, 191]
    },
    {
      "name": "UpdatePositionOperator",
      "discriminator": [39, 115, 48, 204, 246, 47, 66, 57]
    },
    {
      "name": "UpdateRewardDuration",
      "discriminator": [223, 245, 224, 153, 49, 29, 163, 172]
    },
    {
      "name": "UpdateRewardFunder",
      "discriminator": [224, 178, 174, 74, 252, 165, 85, 180]
    },
    {
      "name": "WithdrawIneligibleReward",
      "discriminator": [231, 189, 65, 149, 102, 215, 154, 244]
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "InvalidStartBinIndex",
      "msg": "Invalid start bin index"
    },
    {
      "code": 6001,
      "name": "InvalidBinId",
      "msg": "Invalid bin id"
    },
    {
      "code": 6002,
      "name": "InvalidInput",
      "msg": "Invalid input data"
    },
    {
      "code": 6003,
      "name": "ExceededAmountSlippageTolerance",
      "msg": "Exceeded amount slippage tolerance"
    },
    {
      "code": 6004,
      "name": "ExceededBinSlippageTolerance",
      "msg": "Exceeded bin slippage tolerance"
    },
    {
      "code": 6005,
      "name": "CompositionFactorFlawed",
      "msg": "Composition factor flawed"
    },
    {
      "code": 6006,
      "name": "NonPresetBinStep",
      "msg": "Non preset bin step"
    },
    {
      "code": 6007,
      "name": "ZeroLiquidity",
      "msg": "Zero liquidity"
    },
    {
      "code": 6008,
      "name": "InvalidPosition",
      "msg": "Invalid position"
    },
    {
      "code": 6009,
      "name": "BinArrayNotFound",
      "msg": "Bin array not found"
    },
    {
      "code": 6010,
      "name": "InvalidTokenMint",
      "msg": "Invalid token mint"
    },
    {
      "code": 6011,
      "name": "InvalidAccountForSingleDeposit",
      "msg": "Invalid account for single deposit"
    },
    {
      "code": 6012,
      "name": "PairInsufficientLiquidity",
      "msg": "Pair insufficient liquidity"
    },
    {
      "code": 6013,
      "name": "InvalidFeeOwner",
      "msg": "Invalid fee owner"
    },
    {
      "code": 6014,
      "name": "InvalidFeeWithdrawAmount",
      "msg": "Invalid fee withdraw amount"
    },
    {
      "code": 6015,
      "name": "InvalidAdmin",
      "msg": "Invalid admin"
    },
    {
      "code": 6016,
      "name": "IdenticalFeeOwner",
      "msg": "Identical fee owner"
    },
    {
      "code": 6017,
      "name": "InvalidBps",
      "msg": "Invalid basis point"
    },
    {
      "code": 6018,
      "name": "MathOverflow",
      "msg": "Math operation overflow"
    },
    {
      "code": 6019,
      "name": "TypeCastFailed",
      "msg": "Type cast error"
    },
    {
      "code": 6020,
      "name": "InvalidRewardIndex",
      "msg": "Invalid reward index"
    },
    {
      "code": 6021,
      "name": "InvalidRewardDuration",
      "msg": "Invalid reward duration"
    },
    {
      "code": 6022,
      "name": "RewardInitialized",
      "msg": "Reward already initialized"
    },
    {
      "code": 6023,
      "name": "RewardUninitialized",
      "msg": "Reward not initialized"
    },
    {
      "code": 6024,
      "name": "IdenticalFunder",
      "msg": "Identical funder"
    },
    {
      "code": 6025,
      "name": "RewardCampaignInProgress",
      "msg": "Reward campaign in progress"
    },
    {
      "code": 6026,
      "name": "IdenticalRewardDuration",
      "msg": "Reward duration is the same"
    },
    {
      "code": 6027,
      "name": "InvalidBinArray",
      "msg": "Invalid bin array"
    },
    {
      "code": 6028,
      "name": "NonContinuousBinArrays",
      "msg": "Bin arrays must be continuous"
    },
    {
      "code": 6029,
      "name": "InvalidRewardVault",
      "msg": "Invalid reward vault"
    },
    {
      "code": 6030,
      "name": "NonEmptyPosition",
      "msg": "Position is not empty"
    },
    {
      "code": 6031,
      "name": "UnauthorizedAccess",
      "msg": "Unauthorized access"
    },
    {
      "code": 6032,
      "name": "InvalidFeeParameter",
      "msg": "Invalid fee parameter"
    },
    {
      "code": 6033,
      "name": "MissingOracle",
      "msg": "Missing oracle account"
    },
    {
      "code": 6034,
      "name": "InsufficientSample",
      "msg": "Insufficient observation sample"
    },
    {
      "code": 6035,
      "name": "InvalidLookupTimestamp",
      "msg": "Invalid lookup timestamp"
    },
    {
      "code": 6036,
      "name": "BitmapExtensionAccountIsNotProvided",
      "msg": "Bitmap extension account is not provided"
    },
    {
      "code": 6037,
      "name": "CannotFindNonZeroLiquidityBinArrayId",
      "msg": "Cannot find non-zero liquidity binArrayId"
    },
    {
      "code": 6038,
      "name": "BinIdOutOfBound",
      "msg": "Bin id out of bound"
    },
    {
      "code": 6039,
      "name": "InsufficientOutAmount",
      "msg": "Insufficient amount in for minimum out"
    },
    {
      "code": 6040,
      "name": "InvalidPositionWidth",
      "msg": "Invalid position width"
    },
    {
      "code": 6041,
      "name": "ExcessiveFeeUpdate",
      "msg": "Excessive fee update"
    },
    {
      "code": 6042,
      "name": "PoolDisabled",
      "msg": "Pool disabled"
    },
    {
      "code": 6043,
      "name": "InvalidPoolType",
      "msg": "Invalid pool type"
    },
    {
      "code": 6044,
      "name": "ExceedMaxWhitelist",
      "msg": "Whitelist for wallet is full"
    },
    {
      "code": 6045,
      "name": "InvalidIndex",
      "msg": "Invalid index"
    },
    {
      "code": 6046,
      "name": "RewardNotEnded",
      "msg": "Reward not ended"
    },
    {
      "code": 6047,
      "name": "MustWithdrawnIneligibleReward",
      "msg": "Must withdraw ineligible reward"
    },
    {
      "code": 6048,
      "name": "UnauthorizedAddress",
      "msg": "Unauthorized address"
    },
    {
      "code": 6049,
      "name": "OperatorsAreTheSame",
      "msg": "Cannot update because operators are the same"
    },
    {
      "code": 6050,
      "name": "WithdrawToWrongTokenAccount",
      "msg": "Withdraw to wrong token account"
    },
    {
      "code": 6051,
      "name": "WrongRentReceiver",
      "msg": "Wrong rent receiver"
    },
    {
      "code": 6052,
      "name": "AlreadyPassActivationPoint",
      "msg": "Already activated"
    },
    {
      "code": 6053,
      "name": "ExceedMaxSwappedAmount",
      "msg": "Swapped amount is exceeded max swapped amount"
    },
    {
      "code": 6054,
      "name": "InvalidStrategyParameters",
      "msg": "Invalid strategy parameters"
    },
    {
      "code": 6055,
      "name": "LiquidityLocked",
      "msg": "Liquidity locked"
    },
    {
      "code": 6056,
      "name": "BinRangeIsNotEmpty",
      "msg": "Bin range is not empty"
    },
    {
      "code": 6057,
      "name": "NotExactAmountOut",
      "msg": "Amount out is not matched with exact amount out"
    },
    {
      "code": 6058,
      "name": "InvalidActivationType",
      "msg": "Invalid activation type"
    },
    {
      "code": 6059,
      "name": "InvalidActivationDuration",
      "msg": "Invalid activation duration"
    },
    {
      "code": 6060,
      "name": "MissingTokenAmountAsTokenLaunchProof",
      "msg": "Missing token amount as token launch owner proof"
    },
    {
      "code": 6061,
      "name": "InvalidQuoteToken",
      "msg": "Quote token must be SOL or USDC"
    },
    {
      "code": 6062,
      "name": "InvalidBinStep",
      "msg": "Invalid bin step"
    },
    {
      "code": 6063,
      "name": "InvalidBaseFee",
      "msg": "Invalid base fee"
    },
    {
      "code": 6064,
      "name": "InvalidPreActivationDuration",
      "msg": "Invalid pre-activation duration"
    },
    {
      "code": 6065,
      "name": "AlreadyPassPreActivationSwapPoint",
      "msg": "Already pass pre-activation swap point"
    },
    {
      "code": 6066,
      "name": "InvalidStatus",
      "msg": "Invalid status"
    },
    {
      "code": 6067,
      "name": "ExceededMaxOracleLength",
      "msg": "Exceed max oracle length"
    },
    {
      "code": 6068,
      "name": "InvalidMinimumLiquidity",
      "msg": "Invalid minimum liquidity"
    },
    {
      "code": 6069,
      "name": "NotSupportMint",
      "msg": "Not support token_2022 mint extension"
    },
    {
      "code": 6070,
      "name": "UnsupportedMintExtension",
      "msg": "Unsupported mint extension"
    },
    {
      "code": 6071,
      "name": "UnsupportNativeMintToken2022",
      "msg": "Unsupported native mint token2022"
    },
    {
      "code": 6072,
      "name": "UnmatchTokenMint",
      "msg": "Unmatch token mint"
    },
    {
      "code": 6073,
      "name": "UnsupportedTokenMint",
      "msg": "Unsupported token mint"
    },
    {
      "code": 6074,
      "name": "InsufficientRemainingAccounts",
      "msg": "Insufficient remaining accounts"
    },
    {
      "code": 6075,
      "name": "InvalidRemainingAccountSlice",
      "msg": "Invalid remaining account slice"
    },
    {
      "code": 6076,
      "name": "DuplicatedRemainingAccountTypes",
      "msg": "Duplicated remaining account types"
    },
    {
      "code": 6077,
      "name": "MissingRemainingAccountForTransferHook",
      "msg": "Missing remaining account for transfer hook"
    },
    {
      "code": 6078,
      "name": "NoTransferHookProgram",
      "msg": "Remaining account was passed for transfer hook but there's no hook program"
    },
    {
      "code": 6079,
      "name": "ZeroFundedAmount",
      "msg": "Zero funded amount"
    },
    {
      "code": 6080,
      "name": "InvalidSide",
      "msg": "Invalid side"
    },
    {
      "code": 6081,
      "name": "InvalidResizeLength",
      "msg": "Invalid resize length"
    },
    {
      "code": 6082,
      "name": "NotSupportAtTheMoment",
      "msg": "Not support at the moment"
    },
    {
      "code": 6083,
      "name": "InvalidRebalanceParameters",
      "msg": "Invalid rebalance parameters"
    },
    {
      "code": 6084,
      "name": "InvalidRewardAccounts",
      "msg": "Invalid reward accounts"
    }
  ],
  "types": [
    {
      "name": "AccountsType",
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "TransferHookX"
          },
          {
            "name": "TransferHookY"
          },
          {
            "name": "TransferHookReward"
          },
          {
            "name": "TransferHookMultiReward",
            "fields": ["u8"]
          }
        ]
      }
    },
    {
      "name": "ActivationType",
      "docs": ["Type of the activation"],
      "repr": {
        "kind": "rust"
      },
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Slot"
          },
          {
            "name": "Timestamp"
          }
        ]
      }
    },
    {
      "name": "AddLiquidity",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "from",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "amounts",
            "type": {
              "array": ["u64", 2]
            }
          },
          {
            "name": "active_bin_id",
            "type": "i32"
          }
        ]
      }
    },
    {
      "name": "AddLiquidityParams",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "min_delta_id",
            "type": "i32"
          },
          {
            "name": "max_delta_id",
            "type": "i32"
          },
          {
            "name": "x0",
            "type": "u64"
          },
          {
            "name": "y0",
            "type": "u64"
          },
          {
            "name": "delta_x",
            "type": "u64"
          },
          {
            "name": "delta_y",
            "type": "u64"
          },
          {
            "name": "bit_flag",
            "type": "u8"
          },
          {
            "name": "favor_x_in_active_id",
            "type": "bool"
          },
          {
            "name": "padding",
            "type": {
              "array": ["u8", 16]
            }
          }
        ]
      }
    },
    {
      "name": "AddLiquiditySingleSidePreciseParameter",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bins",
            "type": {
              "vec": {
                "defined": {
                  "name": "CompressedBinDepositAmount"
                }
              }
            }
          },
          {
            "name": "decompress_multiplier",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "AddLiquiditySingleSidePreciseParameter2",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bins",
            "type": {
              "vec": {
                "defined": {
                  "name": "CompressedBinDepositAmount"
                }
              }
            }
          },
          {
            "name": "decompress_multiplier",
            "type": "u64"
          },
          {
            "name": "max_amount",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "BaseFeeParameter",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "protocol_share",
            "docs": [
              "Portion of swap fees retained by the protocol by controlling protocol_share parameter. protocol_swap_fee = protocol_share * total_swap_fee"
            ],
            "type": "u16"
          },
          {
            "name": "base_factor",
            "docs": ["Base factor for base fee rate"],
            "type": "u16"
          },
          {
            "name": "base_fee_power_factor",
            "docs": ["Base fee power factor"],
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "Bin",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "amount_x",
            "docs": [
              "Amount of token X in the bin. This already excluded protocol fees."
            ],
            "type": "u64"
          },
          {
            "name": "amount_y",
            "docs": [
              "Amount of token Y in the bin. This already excluded protocol fees."
            ],
            "type": "u64"
          },
          {
            "name": "price",
            "docs": ["Bin price"],
            "type": "u128"
          },
          {
            "name": "liquidity_supply",
            "docs": [
              "Liquidities of the bin. This is the same as LP mint supply. q-number"
            ],
            "type": "u128"
          },
          {
            "name": "reward_per_token_stored",
            "docs": ["reward_a_per_token_stored"],
            "type": {
              "array": ["u128", 2]
            }
          },
          {
            "name": "fee_amount_x_per_token_stored",
            "docs": ["swap_python fee amount of token X per liquidity deposited."],
            "type": "u128"
          },
          {
            "name": "fee_amount_y_per_token_stored",
            "docs": ["swap_python fee amount of token Y per liquidity deposited."],
            "type": "u128"
          },
          {
            "name": "amount_x_in",
            "docs": [
              "Total token X swap into the bin. Only used for tracking purpose."
            ],
            "type": "u128"
          },
          {
            "name": "amount_y_in",
            "docs": [
              "Total token Y swap into he bin. Only used for tracking purpose."
            ],
            "type": "u128"
          }
        ]
      }
    },
    {
      "name": "BinArray",
      "docs": [
        "An account to contain a range of bin. For example: Bin 100 <-> 200.",
        "For example:",
        "BinArray index: 0 contains bin 0 <-> 599",
        "index: 2 contains bin 600 <-> 1199, ..."
      ],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "index",
            "type": "i64"
          },
          {
            "name": "version",
            "docs": ["Version of binArray"],
            "type": "u8"
          },
          {
            "name": "_padding",
            "type": {
              "array": ["u8", 7]
            }
          },
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "bins",
            "type": {
              "array": [
                {
                  "defined": {
                    "name": "Bin"
                  }
                },
                70
              ]
            }
          }
        ]
      }
    },
    {
      "name": "BinArrayBitmapExtension",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "positive_bin_array_bitmap",
            "docs": [
              "Packed initialized bin array state for start_bin_index is positive"
            ],
            "type": {
              "array": [
                {
                  "array": ["u64", 8]
                },
                12
              ]
            }
          },
          {
            "name": "negative_bin_array_bitmap",
            "docs": [
              "Packed initialized bin array state for start_bin_index is negative"
            ],
            "type": {
              "array": [
                {
                  "array": ["u64", 8]
                },
                12
              ]
            }
          }
        ]
      }
    },
    {
      "name": "BinLiquidityDistribution",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bin_id",
            "docs": ["Define the bin ID wish to deposit to."],
            "type": "i32"
          },
          {
            "name": "distribution_x",
            "docs": [
              "DistributionX (or distributionY) is the percentages of amountX (or amountY) you want to add to each bin."
            ],
            "type": "u16"
          },
          {
            "name": "distribution_y",
            "docs": [
              "DistributionX (or distributionY) is the percentages of amountX (or amountY) you want to add to each bin."
            ],
            "type": "u16"
          }
        ]
      }
    },
    {
      "name": "BinLiquidityDistributionByWeight",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bin_id",
            "docs": ["Define the bin ID wish to deposit to."],
            "type": "i32"
          },
          {
            "name": "weight",
            "docs": ["weight of liquidity distributed for this bin id"],
            "type": "u16"
          }
        ]
      }
    },
    {
      "name": "BinLiquidityReduction",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bin_id",
            "type": "i32"
          },
          {
            "name": "bps_to_remove",
            "type": "u16"
          }
        ]
      }
    },
    {
      "name": "ClaimFee",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "fee_x",
            "type": "u64"
          },
          {
            "name": "fee_y",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "ClaimFeeOperator",
      "docs": ["Parameter that set by the protocol"],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "operator",
            "docs": ["operator"],
            "type": "pubkey"
          },
          {
            "name": "_padding",
            "docs": ["Reserve"],
            "type": {
              "array": ["u8", 128]
            }
          }
        ]
      }
    },
    {
      "name": "ClaimReward",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u64"
          },
          {
            "name": "total_reward",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "CompositionFee",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "from",
            "type": "pubkey"
          },
          {
            "name": "bin_id",
            "type": "i16"
          },
          {
            "name": "token_x_fee_amount",
            "type": "u64"
          },
          {
            "name": "token_y_fee_amount",
            "type": "u64"
          },
          {
            "name": "protocol_token_x_fee_amount",
            "type": "u64"
          },
          {
            "name": "protocol_token_y_fee_amount",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "CompressedBinDepositAmount",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bin_id",
            "type": "i32"
          },
          {
            "name": "amount",
            "type": "u32"
          }
        ]
      }
    },
    {
      "name": "CustomizableParams",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "active_id",
            "docs": ["Pool price"],
            "type": "i32"
          },
          {
            "name": "bin_step",
            "docs": ["Bin step"],
            "type": "u16"
          },
          {
            "name": "base_factor",
            "docs": ["Base factor"],
            "type": "u16"
          },
          {
            "name": "activation_type",
            "docs": [
              "Activation type. 0 = Slot, 1 = Time. Check ActivationType enum"
            ],
            "type": "u8"
          },
          {
            "name": "has_alpha_vault",
            "docs": ["Whether the pool has an alpha vault"],
            "type": "bool"
          },
          {
            "name": "activation_point",
            "docs": ["Decide when does the pool start trade. None = Now"],
            "type": {
              "option": "u64"
            }
          },
          {
            "name": "creator_pool_on_off_control",
            "docs": [
              "Pool creator have permission to enable/disable pool with restricted program validation. Only applicable for customizable permissionless pool."
            ],
            "type": "bool"
          },
          {
            "name": "base_fee_power_factor",
            "docs": ["Base fee power factor"],
            "type": "u8"
          },
          {
            "name": "padding",
            "docs": ["Padding, for future use"],
            "type": {
              "array": ["u8", 62]
            }
          }
        ]
      }
    },
    {
      "name": "DecreasePositionLength",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "length_to_remove",
            "type": "u16"
          },
          {
            "name": "side",
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "DummyIx",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "_pair_status",
            "type": {
              "defined": {
                "name": "PairStatus"
              }
            }
          },
          {
            "name": "_pair_type",
            "type": {
              "defined": {
                "name": "PairType"
              }
            }
          },
          {
            "name": "_activation_type",
            "type": {
              "defined": {
                "name": "ActivationType"
              }
            }
          },
          {
            "name": "_token_program_flag",
            "type": {
              "defined": {
                "name": "TokenProgramFlags"
              }
            }
          },
          {
            "name": "_resize_side",
            "type": {
              "defined": {
                "name": "ResizeSide"
              }
            }
          },
          {
            "name": "_rounding",
            "type": {
              "defined": {
                "name": "Rounding"
              }
            }
          }
        ]
      }
    },
    {
      "name": "DummyZcAccount",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "position_bin_data",
            "type": {
              "defined": {
                "name": "PositionBinData"
              }
            }
          }
        ]
      }
    },
    {
      "name": "DynamicFeeParameter",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "filter_period",
            "docs": [
              "Filter period determine high frequency trading time window."
            ],
            "type": "u16"
          },
          {
            "name": "decay_period",
            "docs": [
              "Decay period determine when the volatile fee start decay / decrease."
            ],
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "docs": [
              "Reduction factor controls the volatile fee rate decrement rate."
            ],
            "type": "u16"
          },
          {
            "name": "variable_fee_control",
            "docs": [
              "Used to scale the variable fee component depending on the dynamic of the market"
            ],
            "type": "u32"
          },
          {
            "name": "max_volatility_accumulator",
            "docs": [
              "Maximum number of bin crossed can be accumulated. Used to cap volatile fee rate."
            ],
            "type": "u32"
          }
        ]
      }
    },
    {
      "name": "DynamicFeeParameterUpdate",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "filter_period",
            "docs": [
              "Filter period determine high frequency trading time window."
            ],
            "type": "u16"
          },
          {
            "name": "decay_period",
            "docs": [
              "Decay period determine when the volatile fee start decay / decrease."
            ],
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "docs": [
              "Reduction factor controls the volatile fee rate decrement rate."
            ],
            "type": "u16"
          },
          {
            "name": "variable_fee_control",
            "docs": [
              "Used to scale the variable fee component depending on the dynamic of the market"
            ],
            "type": "u32"
          },
          {
            "name": "max_volatility_accumulator",
            "docs": [
              "Maximum number of bin crossed can be accumulated. Used to cap volatile fee rate."
            ],
            "type": "u32"
          }
        ]
      }
    },
    {
      "name": "FeeInfo",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "fee_x_per_token_complete",
            "type": "u128"
          },
          {
            "name": "fee_y_per_token_complete",
            "type": "u128"
          },
          {
            "name": "fee_x_pending",
            "type": "u64"
          },
          {
            "name": "fee_y_pending",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "FeeParameterUpdate",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "protocol_share",
            "type": "u16"
          },
          {
            "name": "base_factor",
            "type": "u16"
          }
        ]
      }
    },
    {
      "name": "FundReward",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "funder",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u64"
          },
          {
            "name": "amount",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "GoToABin",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "from_bin_id",
            "type": "i32"
          },
          {
            "name": "to_bin_id",
            "type": "i32"
          }
        ]
      }
    },
    {
      "name": "IncreaseObservation",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "oracle",
            "type": "pubkey"
          },
          {
            "name": "new_observation_length",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "IncreasePositionLength",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "length_to_add",
            "type": "u16"
          },
          {
            "name": "side",
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "InitPermissionPairIx",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "active_id",
            "type": "i32"
          },
          {
            "name": "bin_step",
            "type": "u16"
          },
          {
            "name": "base_factor",
            "type": "u16"
          },
          {
            "name": "base_fee_power_factor",
            "type": "u8"
          },
          {
            "name": "activation_type",
            "type": "u8"
          },
          {
            "name": "protocol_share",
            "type": "u16"
          }
        ]
      }
    },
    {
      "name": "InitPresetParameters2Ix",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "index",
            "type": "u16"
          },
          {
            "name": "bin_step",
            "docs": ["Bin step. Represent the price increment / decrement."],
            "type": "u16"
          },
          {
            "name": "base_factor",
            "docs": [
              "Used for base fee calculation. base_fee_rate = base_factor * bin_step * 10 * 10^base_fee_power_factor"
            ],
            "type": "u16"
          },
          {
            "name": "filter_period",
            "docs": [
              "Filter period determine high frequency trading time window."
            ],
            "type": "u16"
          },
          {
            "name": "decay_period",
            "docs": [
              "Decay period determine when the volatile fee start decay / decrease."
            ],
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "docs": [
              "Reduction factor controls the volatile fee rate decrement rate."
            ],
            "type": "u16"
          },
          {
            "name": "variable_fee_control",
            "docs": [
              "Used to scale the variable fee component depending on the dynamic of the market"
            ],
            "type": "u32"
          },
          {
            "name": "max_volatility_accumulator",
            "docs": [
              "Maximum number of bin crossed can be accumulated. Used to cap volatile fee rate."
            ],
            "type": "u32"
          },
          {
            "name": "protocol_share",
            "docs": [
              "Portion of swap fees retained by the protocol by controlling protocol_share parameter. protocol_swap_fee = protocol_share * total_swap_fee"
            ],
            "type": "u16"
          },
          {
            "name": "base_fee_power_factor",
            "docs": ["Base fee power factor"],
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "InitPresetParametersIx",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bin_step",
            "docs": ["Bin step. Represent the price increment / decrement."],
            "type": "u16"
          },
          {
            "name": "base_factor",
            "docs": [
              "Used for base fee calculation. base_fee_rate = base_factor * bin_step * 10 * 10^base_fee_power_factor"
            ],
            "type": "u16"
          },
          {
            "name": "filter_period",
            "docs": [
              "Filter period determine high frequency trading time window."
            ],
            "type": "u16"
          },
          {
            "name": "decay_period",
            "docs": [
              "Decay period determine when the volatile fee start decay / decrease."
            ],
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "docs": [
              "Reduction factor controls the volatile fee rate decrement rate."
            ],
            "type": "u16"
          },
          {
            "name": "variable_fee_control",
            "docs": [
              "Used to scale the variable fee component depending on the dynamic of the market"
            ],
            "type": "u32"
          },
          {
            "name": "max_volatility_accumulator",
            "docs": [
              "Maximum number of bin crossed can be accumulated. Used to cap volatile fee rate."
            ],
            "type": "u32"
          },
          {
            "name": "protocol_share",
            "docs": [
              "Portion of swap fees retained by the protocol by controlling protocol_share parameter. protocol_swap_fee = protocol_share * total_swap_fee"
            ],
            "type": "u16"
          }
        ]
      }
    },
    {
      "name": "InitializeLbPair2Params",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "active_id",
            "docs": ["Pool price"],
            "type": "i32"
          },
          {
            "name": "padding",
            "docs": ["Padding, for future use"],
            "type": {
              "array": ["u8", 96]
            }
          }
        ]
      }
    },
    {
      "name": "InitializeReward",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "reward_mint",
            "type": "pubkey"
          },
          {
            "name": "funder",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u64"
          },
          {
            "name": "reward_duration",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "LbPair",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "parameters",
            "type": {
              "defined": {
                "name": "StaticParameters"
              }
            }
          },
          {
            "name": "v_parameters",
            "type": {
              "defined": {
                "name": "VariableParameters"
              }
            }
          },
          {
            "name": "bump_seed",
            "type": {
              "array": ["u8", 1]
            }
          },
          {
            "name": "bin_step_seed",
            "docs": ["Bin step signer seed"],
            "type": {
              "array": ["u8", 2]
            }
          },
          {
            "name": "pair_type",
            "docs": ["Type of the pair"],
            "type": "u8"
          },
          {
            "name": "active_id",
            "docs": ["Active bin id"],
            "type": "i32"
          },
          {
            "name": "bin_step",
            "docs": ["Bin step. Represent the price increment / decrement."],
            "type": "u16"
          },
          {
            "name": "status",
            "docs": ["Status of the pair. Check PairStatus enum."],
            "type": "u8"
          },
          {
            "name": "require_base_factor_seed",
            "docs": ["Require base factor seed"],
            "type": "u8"
          },
          {
            "name": "base_factor_seed",
            "docs": ["Base factor seed"],
            "type": {
              "array": ["u8", 2]
            }
          },
          {
            "name": "activation_type",
            "docs": ["Activation type"],
            "type": "u8"
          },
          {
            "name": "creator_pool_on_off_control",
            "docs": [
              "Allow pool creator to enable/disable pool with restricted validation. Only applicable for customizable permissionless pair type."
            ],
            "type": "u8"
          },
          {
            "name": "token_x_mint",
            "docs": ["Token X mint"],
            "type": "pubkey"
          },
          {
            "name": "token_y_mint",
            "docs": ["Token Y mint"],
            "type": "pubkey"
          },
          {
            "name": "reserve_x",
            "docs": ["LB token X vault"],
            "type": "pubkey"
          },
          {
            "name": "reserve_y",
            "docs": ["LB token Y vault"],
            "type": "pubkey"
          },
          {
            "name": "protocol_fee",
            "docs": ["Uncollected protocol fee"],
            "type": {
              "defined": {
                "name": "ProtocolFee"
              }
            }
          },
          {
            "name": "_padding_1",
            "docs": [
              "_padding_1, previous Fee owner, BE CAREFUL FOR TOMBSTONE WHEN REUSE !!"
            ],
            "type": {
              "array": ["u8", 32]
            }
          },
          {
            "name": "reward_infos",
            "docs": ["Farming reward information"],
            "type": {
              "array": [
                {
                  "defined": {
                    "name": "RewardInfo"
                  }
                },
                2
              ]
            }
          },
          {
            "name": "oracle",
            "docs": ["Oracle pubkey"],
            "type": "pubkey"
          },
          {
            "name": "bin_array_bitmap",
            "docs": ["Packed initialized bin array state"],
            "type": {
              "array": ["u64", 16]
            }
          },
          {
            "name": "last_updated_at",
            "docs": ["Last time the pool fee parameter was updated"],
            "type": "i64"
          },
          {
            "name": "_padding_2",
            "docs": [
              "_padding_2, previous whitelisted_wallet, BE CAREFUL FOR TOMBSTONE WHEN REUSE !!"
            ],
            "type": {
              "array": ["u8", 32]
            }
          },
          {
            "name": "pre_activation_swap_address",
            "docs": [
              "Address allowed to swap when the current point is greater than or equal to the pre-activation point. The pre-activation point is calculated as `activation_point - pre_activation_duration`."
            ],
            "type": "pubkey"
          },
          {
            "name": "base_key",
            "docs": ["Base keypair. Only required for permission pair"],
            "type": "pubkey"
          },
          {
            "name": "activation_point",
            "docs": [
              "Time point to enable the pair. Only applicable for permission pair."
            ],
            "type": "u64"
          },
          {
            "name": "pre_activation_duration",
            "docs": [
              "Duration before activation activation_point. Used to calculate pre-activation time point for pre_activation_swap_address"
            ],
            "type": "u64"
          },
          {
            "name": "_padding_3",
            "docs": [
              "_padding 3 is reclaimed free space from swap_cap_deactivate_point and swap_cap_amount before, BE CAREFUL FOR TOMBSTONE WHEN REUSE !!"
            ],
            "type": {
              "array": ["u8", 8]
            }
          },
          {
            "name": "_padding_4",
            "docs": [
              "_padding_4, previous lock_duration, BE CAREFUL FOR TOMBSTONE WHEN REUSE !!"
            ],
            "type": "u64"
          },
          {
            "name": "creator",
            "docs": ["Pool creator"],
            "type": "pubkey"
          },
          {
            "name": "token_mint_x_program_flag",
            "docs": ["token_mint_x_program_flag"],
            "type": "u8"
          },
          {
            "name": "token_mint_y_program_flag",
            "docs": ["token_mint_y_program_flag"],
            "type": "u8"
          },
          {
            "name": "_reserved",
            "docs": ["Reserved space for future use"],
            "type": {
              "array": ["u8", 22]
            }
          }
        ]
      }
    },
    {
      "name": "LbPairCreate",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "bin_step",
            "type": "u16"
          },
          {
            "name": "token_x",
            "type": "pubkey"
          },
          {
            "name": "token_y",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "LiquidityOneSideParameter",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "amount",
            "docs": ["Amount of X token or Y token to deposit"],
            "type": "u64"
          },
          {
            "name": "active_id",
            "docs": ["Active bin that integrator observe off-chain"],
            "type": "i32"
          },
          {
            "name": "max_active_bin_slippage",
            "docs": ["max active bin slippage allowed"],
            "type": "i32"
          },
          {
            "name": "bin_liquidity_dist",
            "docs": ["Liquidity distribution to each bins"],
            "type": {
              "vec": {
                "defined": {
                  "name": "BinLiquidityDistributionByWeight"
                }
              }
            }
          }
        ]
      }
    },
    {
      "name": "LiquidityParameter",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "amount_x",
            "docs": ["Amount of X token to deposit"],
            "type": "u64"
          },
          {
            "name": "amount_y",
            "docs": ["Amount of Y token to deposit"],
            "type": "u64"
          },
          {
            "name": "bin_liquidity_dist",
            "docs": ["Liquidity distribution to each bins"],
            "type": {
              "vec": {
                "defined": {
                  "name": "BinLiquidityDistribution"
                }
              }
            }
          }
        ]
      }
    },
    {
      "name": "LiquidityParameterByStrategy",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "amount_x",
            "docs": ["Amount of X token to deposit"],
            "type": "u64"
          },
          {
            "name": "amount_y",
            "docs": ["Amount of Y token to deposit"],
            "type": "u64"
          },
          {
            "name": "active_id",
            "docs": ["Active bin that integrator observe off-chain"],
            "type": "i32"
          },
          {
            "name": "max_active_bin_slippage",
            "docs": ["max active bin slippage allowed"],
            "type": "i32"
          },
          {
            "name": "strategy_parameters",
            "docs": ["strategy parameters"],
            "type": {
              "defined": {
                "name": "StrategyParameters"
              }
            }
          }
        ]
      }
    },
    {
      "name": "LiquidityParameterByStrategyOneSide",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "amount",
            "docs": ["Amount of X token or Y token to deposit"],
            "type": "u64"
          },
          {
            "name": "active_id",
            "docs": ["Active bin that integrator observe off-chain"],
            "type": "i32"
          },
          {
            "name": "max_active_bin_slippage",
            "docs": ["max active bin slippage allowed"],
            "type": "i32"
          },
          {
            "name": "strategy_parameters",
            "docs": ["strategy parameters"],
            "type": {
              "defined": {
                "name": "StrategyParameters"
              }
            }
          }
        ]
      }
    },
    {
      "name": "LiquidityParameterByWeight",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "amount_x",
            "docs": ["Amount of X token to deposit"],
            "type": "u64"
          },
          {
            "name": "amount_y",
            "docs": ["Amount of Y token to deposit"],
            "type": "u64"
          },
          {
            "name": "active_id",
            "docs": ["Active bin that integrator observe off-chain"],
            "type": "i32"
          },
          {
            "name": "max_active_bin_slippage",
            "docs": ["max active bin slippage allowed"],
            "type": "i32"
          },
          {
            "name": "bin_liquidity_dist",
            "docs": ["Liquidity distribution to each bins"],
            "type": {
              "vec": {
                "defined": {
                  "name": "BinLiquidityDistributionByWeight"
                }
              }
            }
          }
        ]
      }
    },
    {
      "name": "Oracle",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "idx",
            "docs": ["Index of latest observation"],
            "type": "u64"
          },
          {
            "name": "active_size",
            "docs": [
              "Size of active sample. Active sample is initialized observation."
            ],
            "type": "u64"
          },
          {
            "name": "length",
            "docs": ["Number of observations"],
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "PairStatus",
      "docs": [
        "Pair status. 0 = Enabled, 1 = Disabled. Putting 0 as enabled for backward compatibility."
      ],
      "repr": {
        "kind": "rust"
      },
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Enabled"
          },
          {
            "name": "Disabled"
          }
        ]
      }
    },
    {
      "name": "PairType",
      "docs": [
        "Type of the Pair. 0 = Permissionless, 1 = Permission, 2 = CustomizablePermissionless. Putting 0 as permissionless for backward compatibility."
      ],
      "repr": {
        "kind": "rust"
      },
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Permissionless"
          },
          {
            "name": "Permission"
          },
          {
            "name": "CustomizablePermissionless"
          },
          {
            "name": "PermissionlessV2"
          }
        ]
      }
    },
    {
      "name": "Position",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "docs": ["The LB pair of this position"],
            "type": "pubkey"
          },
          {
            "name": "owner",
            "docs": [
              "Owner of the position. Client rely on this to to fetch their positions."
            ],
            "type": "pubkey"
          },
          {
            "name": "liquidity_shares",
            "docs": [
              "Liquidity shares of this position in bins (lower_bin_id <-> upper_bin_id). This is the same as LP concept."
            ],
            "type": {
              "array": ["u64", 70]
            }
          },
          {
            "name": "reward_infos",
            "docs": ["Farming reward information"],
            "type": {
              "array": [
                {
                  "defined": {
                    "name": "UserRewardInfo"
                  }
                },
                70
              ]
            }
          },
          {
            "name": "fee_infos",
            "docs": ["swap_python fee to claim information"],
            "type": {
              "array": [
                {
                  "defined": {
                    "name": "FeeInfo"
                  }
                },
                70
              ]
            }
          },
          {
            "name": "lower_bin_id",
            "docs": ["Lower bin ID"],
            "type": "i32"
          },
          {
            "name": "upper_bin_id",
            "docs": ["Upper bin ID"],
            "type": "i32"
          },
          {
            "name": "last_updated_at",
            "docs": ["Last updated timestamp"],
            "type": "i64"
          },
          {
            "name": "total_claimed_fee_x_amount",
            "docs": ["Total claimed token fee X"],
            "type": "u64"
          },
          {
            "name": "total_claimed_fee_y_amount",
            "docs": ["Total claimed token fee Y"],
            "type": "u64"
          },
          {
            "name": "total_claimed_rewards",
            "docs": ["Total claimed rewards"],
            "type": {
              "array": ["u64", 2]
            }
          },
          {
            "name": "_reserved",
            "docs": ["Reserved space for future use"],
            "type": {
              "array": ["u8", 160]
            }
          }
        ]
      }
    },
    {
      "name": "PositionBinData",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "liquidity_share",
            "type": "u128"
          },
          {
            "name": "reward_info",
            "type": {
              "defined": {
                "name": "UserRewardInfo"
              }
            }
          },
          {
            "name": "fee_info",
            "type": {
              "defined": {
                "name": "FeeInfo"
              }
            }
          }
        ]
      }
    },
    {
      "name": "PositionClose",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "PositionCreate",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "PositionV2",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "docs": ["The LB pair of this position"],
            "type": "pubkey"
          },
          {
            "name": "owner",
            "docs": [
              "Owner of the position. Client rely on this to to fetch their positions."
            ],
            "type": "pubkey"
          },
          {
            "name": "liquidity_shares",
            "docs": [
              "Liquidity shares of this position in bins (lower_bin_id <-> upper_bin_id). This is the same as LP concept."
            ],
            "type": {
              "array": ["u128", 70]
            }
          },
          {
            "name": "reward_infos",
            "docs": ["Farming reward information"],
            "type": {
              "array": [
                {
                  "defined": {
                    "name": "UserRewardInfo"
                  }
                },
                70
              ]
            }
          },
          {
            "name": "fee_infos",
            "docs": ["swap_python fee to claim information"],
            "type": {
              "array": [
                {
                  "defined": {
                    "name": "FeeInfo"
                  }
                },
                70
              ]
            }
          },
          {
            "name": "lower_bin_id",
            "docs": ["Lower bin ID"],
            "type": "i32"
          },
          {
            "name": "upper_bin_id",
            "docs": ["Upper bin ID"],
            "type": "i32"
          },
          {
            "name": "last_updated_at",
            "docs": ["Last updated timestamp"],
            "type": "i64"
          },
          {
            "name": "total_claimed_fee_x_amount",
            "docs": ["Total claimed token fee X"],
            "type": "u64"
          },
          {
            "name": "total_claimed_fee_y_amount",
            "docs": ["Total claimed token fee Y"],
            "type": "u64"
          },
          {
            "name": "total_claimed_rewards",
            "docs": ["Total claimed rewards"],
            "type": {
              "array": ["u64", 2]
            }
          },
          {
            "name": "operator",
            "docs": ["Operator of position"],
            "type": "pubkey"
          },
          {
            "name": "lock_release_point",
            "docs": ["Time point which the locked liquidity can be withdraw"],
            "type": "u64"
          },
          {
            "name": "_padding_0",
            "docs": [
              "_padding_0, previous subjected_to_bootstrap_liquidity_locking, BE CAREFUL FOR TOMBSTONE WHEN REUSE !!"
            ],
            "type": "u8"
          },
          {
            "name": "fee_owner",
            "docs": [
              "Address is able to claim fee in this position, only valid for bootstrap_liquidity_position"
            ],
            "type": "pubkey"
          },
          {
            "name": "_reserved",
            "docs": ["Reserved space for future use"],
            "type": {
              "array": ["u8", 87]
            }
          }
        ]
      }
    },
    {
      "name": "PresetParameter",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bin_step",
            "docs": ["Bin step. Represent the price increment / decrement."],
            "type": "u16"
          },
          {
            "name": "base_factor",
            "docs": [
              "Used for base fee calculation. base_fee_rate = base_factor * bin_step * 10 * 10^base_fee_power_factor"
            ],
            "type": "u16"
          },
          {
            "name": "filter_period",
            "docs": [
              "Filter period determine high frequency trading time window."
            ],
            "type": "u16"
          },
          {
            "name": "decay_period",
            "docs": [
              "Decay period determine when the volatile fee start decay / decrease."
            ],
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "docs": [
              "Reduction factor controls the volatile fee rate decrement rate."
            ],
            "type": "u16"
          },
          {
            "name": "variable_fee_control",
            "docs": [
              "Used to scale the variable fee component depending on the dynamic of the market"
            ],
            "type": "u32"
          },
          {
            "name": "max_volatility_accumulator",
            "docs": [
              "Maximum number of bin crossed can be accumulated. Used to cap volatile fee rate."
            ],
            "type": "u32"
          },
          {
            "name": "min_bin_id",
            "docs": [
              "Min bin id supported by the pool based on the configured bin step."
            ],
            "type": "i32"
          },
          {
            "name": "max_bin_id",
            "docs": [
              "Max bin id supported by the pool based on the configured bin step."
            ],
            "type": "i32"
          },
          {
            "name": "protocol_share",
            "docs": [
              "Portion of swap fees retained by the protocol by controlling protocol_share parameter. protocol_swap_fee = protocol_share * total_swap_fee"
            ],
            "type": "u16"
          }
        ]
      }
    },
    {
      "name": "PresetParameter2",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bin_step",
            "docs": ["Bin step. Represent the price increment / decrement."],
            "type": "u16"
          },
          {
            "name": "base_factor",
            "docs": [
              "Used for base fee calculation. base_fee_rate = base_factor * bin_step * 10 * 10^base_fee_power_factor"
            ],
            "type": "u16"
          },
          {
            "name": "filter_period",
            "docs": [
              "Filter period determine high frequency trading time window."
            ],
            "type": "u16"
          },
          {
            "name": "decay_period",
            "docs": [
              "Decay period determine when the volatile fee start decay / decrease."
            ],
            "type": "u16"
          },
          {
            "name": "variable_fee_control",
            "docs": [
              "Used to scale the variable fee component depending on the dynamic of the market"
            ],
            "type": "u32"
          },
          {
            "name": "max_volatility_accumulator",
            "docs": [
              "Maximum number of bin crossed can be accumulated. Used to cap volatile fee rate."
            ],
            "type": "u32"
          },
          {
            "name": "reduction_factor",
            "docs": [
              "Reduction factor controls the volatile fee rate decrement rate."
            ],
            "type": "u16"
          },
          {
            "name": "protocol_share",
            "docs": [
              "Portion of swap fees retained by the protocol by controlling protocol_share parameter. protocol_swap_fee = protocol_share * total_swap_fee"
            ],
            "type": "u16"
          },
          {
            "name": "index",
            "docs": ["index"],
            "type": "u16"
          },
          {
            "name": "base_fee_power_factor",
            "docs": ["Base fee power factor"],
            "type": "u8"
          },
          {
            "name": "padding_0",
            "docs": ["Padding 0 for future use"],
            "type": "u8"
          },
          {
            "name": "padding_1",
            "docs": ["Padding 1 for future use"],
            "type": {
              "array": ["u64", 20]
            }
          }
        ]
      }
    },
    {
      "name": "ProtocolFee",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "amount_x",
            "type": "u64"
          },
          {
            "name": "amount_y",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "RebalanceLiquidityParams",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "active_id",
            "docs": ["active id"],
            "type": "i32"
          },
          {
            "name": "max_active_bin_slippage",
            "docs": ["max active bin slippage allowed"],
            "type": "u16"
          },
          {
            "name": "should_claim_fee",
            "docs": ["a flag to indicate that whether fee should be harvested"],
            "type": "bool"
          },
          {
            "name": "should_claim_reward",
            "docs": [
              "a flag to indicate that whether rewards should be harvested"
            ],
            "type": "bool"
          },
          {
            "name": "min_withdraw_x_amount",
            "docs": ["threshold for withdraw token x"],
            "type": "u64"
          },
          {
            "name": "max_deposit_x_amount",
            "docs": ["threshold for deposit token x"],
            "type": "u64"
          },
          {
            "name": "min_withdraw_y_amount",
            "docs": ["threshold for withdraw token y"],
            "type": "u64"
          },
          {
            "name": "max_deposit_y_amount",
            "docs": ["threshold for deposit token y"],
            "type": "u64"
          },
          {
            "name": "padding",
            "docs": ["padding 32 bytes for future usage"],
            "type": {
              "array": ["u8", 32]
            }
          },
          {
            "name": "removes",
            "docs": ["removes"],
            "type": {
              "vec": {
                "defined": {
                  "name": "RemoveLiquidityParams"
                }
              }
            }
          },
          {
            "name": "adds",
            "docs": ["adds"],
            "type": {
              "vec": {
                "defined": {
                  "name": "AddLiquidityParams"
                }
              }
            }
          }
        ]
      }
    },
    {
      "name": "Rebalancing",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "x_withdrawn_amount",
            "type": "u64"
          },
          {
            "name": "x_added_amount",
            "type": "u64"
          },
          {
            "name": "y_withdrawn_amount",
            "type": "u64"
          },
          {
            "name": "y_added_amount",
            "type": "u64"
          },
          {
            "name": "x_fee_amount",
            "type": "u64"
          },
          {
            "name": "y_fee_amount",
            "type": "u64"
          },
          {
            "name": "old_min_id",
            "type": "i32"
          },
          {
            "name": "old_max_id",
            "type": "i32"
          },
          {
            "name": "new_min_id",
            "type": "i32"
          },
          {
            "name": "new_max_id",
            "type": "i32"
          },
          {
            "name": "rewards",
            "type": {
              "array": ["u64", 2]
            }
          }
        ]
      }
    },
    {
      "name": "RemainingAccountsInfo",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "slices",
            "type": {
              "vec": {
                "defined": {
                  "name": "RemainingAccountsSlice"
                }
              }
            }
          }
        ]
      }
    },
    {
      "name": "RemainingAccountsSlice",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "accounts_type",
            "type": {
              "defined": {
                "name": "AccountsType"
              }
            }
          },
          {
            "name": "length",
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "RemoveLiquidity",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "from",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "amounts",
            "type": {
              "array": ["u64", 2]
            }
          },
          {
            "name": "active_bin_id",
            "type": "i32"
          }
        ]
      }
    },
    {
      "name": "RemoveLiquidityParams",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "min_bin_id",
            "type": {
              "option": "i32"
            }
          },
          {
            "name": "max_bin_id",
            "type": {
              "option": "i32"
            }
          },
          {
            "name": "bps",
            "type": "u16"
          },
          {
            "name": "padding",
            "type": {
              "array": ["u8", 16]
            }
          }
        ]
      }
    },
    {
      "name": "ResizeSide",
      "docs": ["Side of resize, 0 for lower and 1 for upper"],
      "repr": {
        "kind": "rust"
      },
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Lower"
          },
          {
            "name": "Upper"
          }
        ]
      }
    },
    {
      "name": "RewardInfo",
      "docs": [
        "Stores the state relevant for tracking liquidity mining rewards"
      ],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "mint",
            "docs": ["Reward token mint."],
            "type": "pubkey"
          },
          {
            "name": "vault",
            "docs": ["Reward vault token account."],
            "type": "pubkey"
          },
          {
            "name": "funder",
            "docs": ["Authority account that allows to fund rewards"],
            "type": "pubkey"
          },
          {
            "name": "reward_duration",
            "docs": ["TODO check whether we need to store it in pool"],
            "type": "u64"
          },
          {
            "name": "reward_duration_end",
            "docs": ["TODO check whether we need to store it in pool"],
            "type": "u64"
          },
          {
            "name": "reward_rate",
            "docs": ["TODO check whether we need to store it in pool"],
            "type": "u128"
          },
          {
            "name": "last_update_time",
            "docs": ["The last time reward states were updated."],
            "type": "u64"
          },
          {
            "name": "cumulative_seconds_with_empty_liquidity_reward",
            "docs": [
              "Accumulated seconds where when farm distribute rewards, but the bin is empty. The reward will be accumulated for next reward time window."
            ],
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "Rounding",
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Up"
          },
          {
            "name": "Down"
          }
        ]
      }
    },
    {
      "name": "StaticParameters",
      "docs": ["Parameter that set by the protocol"],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "base_factor",
            "docs": [
              "Used for base fee calculation. base_fee_rate = base_factor * bin_step * 10 * 10^base_fee_power_factor"
            ],
            "type": "u16"
          },
          {
            "name": "filter_period",
            "docs": [
              "Filter period determine high frequency trading time window."
            ],
            "type": "u16"
          },
          {
            "name": "decay_period",
            "docs": [
              "Decay period determine when the volatile fee start decay / decrease."
            ],
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "docs": [
              "Reduction factor controls the volatile fee rate decrement rate."
            ],
            "type": "u16"
          },
          {
            "name": "variable_fee_control",
            "docs": [
              "Used to scale the variable fee component depending on the dynamic of the market"
            ],
            "type": "u32"
          },
          {
            "name": "max_volatility_accumulator",
            "docs": [
              "Maximum number of bin crossed can be accumulated. Used to cap volatile fee rate."
            ],
            "type": "u32"
          },
          {
            "name": "min_bin_id",
            "docs": [
              "Min bin id supported by the pool based on the configured bin step."
            ],
            "type": "i32"
          },
          {
            "name": "max_bin_id",
            "docs": [
              "Max bin id supported by the pool based on the configured bin step."
            ],
            "type": "i32"
          },
          {
            "name": "protocol_share",
            "docs": [
              "Portion of swap fees retained by the protocol by controlling protocol_share parameter. protocol_swap_fee = protocol_share * total_swap_fee"
            ],
            "type": "u16"
          },
          {
            "name": "base_fee_power_factor",
            "docs": ["Base fee power factor"],
            "type": "u8"
          },
          {
            "name": "_padding",
            "docs": ["Padding for bytemuck safe alignment"],
            "type": {
              "array": ["u8", 5]
            }
          }
        ]
      }
    },
    {
      "name": "StrategyParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "min_bin_id",
            "docs": ["min bin id"],
            "type": "i32"
          },
          {
            "name": "max_bin_id",
            "docs": ["max bin id"],
            "type": "i32"
          },
          {
            "name": "strategy_type",
            "docs": ["strategy type"],
            "type": {
              "defined": {
                "name": "StrategyType"
              }
            }
          },
          {
            "name": "parameteres",
            "docs": ["parameters"],
            "type": {
              "array": ["u8", 64]
            }
          }
        ]
      }
    },
    {
      "name": "StrategyType",
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "SpotOneSide"
          },
          {
            "name": "CurveOneSide"
          },
          {
            "name": "BidAskOneSide"
          },
          {
            "name": "SpotBalanced"
          },
          {
            "name": "CurveBalanced"
          },
          {
            "name": "BidAskBalanced"
          },
          {
            "name": "SpotImBalanced"
          },
          {
            "name": "CurveImBalanced"
          },
          {
            "name": "BidAskImBalanced"
          }
        ]
      }
    },
    {
      "name": "swap_python",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "from",
            "type": "pubkey"
          },
          {
            "name": "start_bin_id",
            "type": "i32"
          },
          {
            "name": "end_bin_id",
            "type": "i32"
          },
          {
            "name": "amount_in",
            "type": "u64"
          },
          {
            "name": "amount_out",
            "type": "u64"
          },
          {
            "name": "swap_for_y",
            "type": "bool"
          },
          {
            "name": "fee",
            "type": "u64"
          },
          {
            "name": "protocol_fee",
            "type": "u64"
          },
          {
            "name": "fee_bps",
            "type": "u128"
          },
          {
            "name": "host_fee",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "TokenBadge",
      "docs": ["Parameter that set by the protocol"],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "token_mint",
            "docs": ["token mint"],
            "type": "pubkey"
          },
          {
            "name": "_padding",
            "docs": ["Reserve"],
            "type": {
              "array": ["u8", 128]
            }
          }
        ]
      }
    },
    {
      "name": "TokenProgramFlags",
      "repr": {
        "kind": "rust"
      },
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "TokenProgram"
          },
          {
            "name": "TokenProgram2022"
          }
        ]
      }
    },
    {
      "name": "UpdatePositionLockReleasePoint",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "current_point",
            "type": "u64"
          },
          {
            "name": "new_lock_release_point",
            "type": "u64"
          },
          {
            "name": "old_lock_release_point",
            "type": "u64"
          },
          {
            "name": "sender",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "UpdatePositionOperator",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "old_operator",
            "type": "pubkey"
          },
          {
            "name": "new_operator",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "UpdateRewardDuration",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u64"
          },
          {
            "name": "old_reward_duration",
            "type": "u64"
          },
          {
            "name": "new_reward_duration",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "UpdateRewardFunder",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u64"
          },
          {
            "name": "old_funder",
            "type": "pubkey"
          },
          {
            "name": "new_funder",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "UserRewardInfo",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "reward_per_token_completes",
            "type": {
              "array": ["u128", 2]
            }
          },
          {
            "name": "reward_pendings",
            "type": {
              "array": ["u64", 2]
            }
          }
        ]
      }
    },
    {
      "name": "VariableParameters",
      "docs": ["Parameters that changes based on dynamic of the market"],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "volatility_accumulator",
            "docs": [
              "Volatility accumulator measure the number of bin crossed since reference bin ID. Normally (without filter period taken into consideration), reference bin ID is the active bin of last swap.",
              "It affects the variable fee rate"
            ],
            "type": "u32"
          },
          {
            "name": "volatility_reference",
            "docs": [
              "Volatility reference is decayed volatility accumulator. It is always <= volatility_accumulator"
            ],
            "type": "u32"
          },
          {
            "name": "index_reference",
            "docs": ["Active bin id of last swap."],
            "type": "i32"
          },
          {
            "name": "_padding",
            "docs": ["Padding for bytemuck safe alignment"],
            "type": {
              "array": ["u8", 4]
            }
          },
          {
            "name": "last_update_timestamp",
            "docs": ["Last timestamp the variable parameters was updated"],
            "type": "i64"
          },
          {
            "name": "_padding_1",
            "docs": ["Padding for bytemuck safe alignment"],
            "type": {
              "array": ["u8", 8]
            }
          }
        ]
      }
    },
    {
      "name": "WithdrawIneligibleReward",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lb_pair",
            "type": "pubkey"
          },
          {
            "name": "reward_mint",
            "type": "pubkey"
          },
          {
            "name": "amount",
            "type": "u64"
          }
        ]
      }
    }
  ],
  "constants": [
    {
      "name": "BASIS_POINT_MAX",
      "type": "i32",
      "value": "10000"
    },
    {
      "name": "BIN_ARRAY",
      "type": "bytes",
      "value": "[98, 105, 110, 95, 97, 114, 114, 97, 121]"
    },
    {
      "name": "BIN_ARRAY_BITMAP_SEED",
      "type": "bytes",
      "value": "[98, 105, 116, 109, 97, 112]"
    },
    {
      "name": "BIN_ARRAY_BITMAP_SIZE",
      "type": "i32",
      "value": "512"
    },
    {
      "name": "CLAIM_PROTOCOL_FEE_OPERATOR",
      "type": "bytes",
      "value": "[99, 102, 95, 111, 112, 101, 114, 97, 116, 111, 114]"
    },
    {
      "name": "DEFAULT_BIN_PER_POSITION",
      "type": "u64",
      "value": "70"
    },
    {
      "name": "EXTENSION_BINARRAY_BITMAP_SIZE",
      "type": "u64",
      "value": "12"
    },
    {
      "name": "FEE_PRECISION",
      "type": "u64",
      "value": "1000000000"
    },
    {
      "name": "HOST_FEE_BPS",
      "docs": ["Host fee. 20%"],
      "type": "u16",
      "value": "2000"
    },
    {
      "name": "ILM_PROTOCOL_SHARE",
      "type": "u16",
      "value": "2000"
    },
    {
      "name": "MAX_BASE_FEE",
      "docs": ["Maximum base fee, base_fee / 10^9 = fee_in_percentage"],
      "type": "u128",
      "value": "100000000"
    },
    {
      "name": "MAX_BIN_ID",
      "docs": ["Maximum bin ID supported. Computed based on 1 bps."],
      "type": "i32",
      "value": "443636"
    },
    {
      "name": "MAX_BIN_PER_ARRAY",
      "type": "u64",
      "value": "70"
    },
    {
      "name": "MAX_BIN_STEP",
      "docs": ["Maximum bin step"],
      "type": "u16",
      "value": "400"
    },
    {
      "name": "MAX_FEE_RATE",
      "docs": ["Maximum fee rate. 10%"],
      "type": "u64",
      "value": "100000000"
    },
    {
      "name": "MAX_PROTOCOL_SHARE",
      "docs": ["Maximum protocol share of the fee. 25%"],
      "type": "u16",
      "value": "2500"
    },
    {
      "name": "MAX_RESIZE_LENGTH",
      "type": "u64",
      "value": "70"
    },
    {
      "name": "MAX_REWARD_BIN_SPLIT",
      "type": "u64",
      "value": "15"
    },
    {
      "name": "MAX_REWARD_DURATION",
      "type": "u64",
      "value": "31536000"
    },
    {
      "name": "MINIMUM_LIQUIDITY",
      "type": "u128",
      "value": "1000000"
    },
    {
      "name": "MIN_BASE_FEE",
      "docs": ["Minimum base fee"],
      "type": "u128",
      "value": "100000"
    },
    {
      "name": "MIN_BIN_ID",
      "docs": ["Minimum bin ID supported. Computed based on 1 bps."],
      "type": "i32",
      "value": "-443636"
    },
    {
      "name": "MIN_REWARD_DURATION",
      "type": "u64",
      "value": "1"
    },
    {
      "name": "NUM_REWARDS",
      "type": "u64",
      "value": "2"
    },
    {
      "name": "ORACLE",
      "type": "bytes",
      "value": "[111, 114, 97, 99, 108, 101]"
    },
    {
      "name": "POSITION",
      "type": "bytes",
      "value": "[112, 111, 115, 105, 116, 105, 111, 110]"
    },
    {
      "name": "POSITION_MAX_LENGTH",
      "type": "u64",
      "value": "1400"
    },
    {
      "name": "PRESET_PARAMETER",
      "type": "bytes",
      "value": "[112, 114, 101, 115, 101, 116, 95, 112, 97, 114, 97, 109, 101, 116, 101, 114]"
    },
    {
      "name": "PRESET_PARAMETER2",
      "type": "bytes",
      "value": "[112, 114, 101, 115, 101, 116, 95, 112, 97, 114, 97, 109, 101, 116, 101, 114, 50]"
    },
    {
      "name": "PROTOCOL_SHARE",
      "type": "u16",
      "value": "500"
    }
  ]
}

idl_ammV1 = {
  "version": "0.5.3",
  "name": "amm",
  "docs": [
    "Program for AMM"
  ],
  "instructions": [
    {
      "name": "initializePermissionedPool",
      "docs": [
        "Initialize a new permissioned pool."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Pool account (arbitrary address)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "tokenAMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token A mint of the pool. Eg: USDT"
          ]
        },
        {
          "name": "tokenBMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token B mint of the pool. Eg: USDC"
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token A. Token A of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token B. Token B of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault A"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault B"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "adminTokenA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Admin token account for pool token A mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "adminTokenB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Admin token account for pool token B mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "adminPoolLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Admin pool LP token account. Used to receive LP during first deposit (initialize pool)",
            "Admin pool LP token account. Used to receive LP during first deposit (initialize pool)"
          ]
        },
        {
          "name": "protocolTokenAFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token A. Used to receive trading fee."
          ]
        },
        {
          "name": "protocolTokenBFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token B. Used to receive trading fee."
          ]
        },
        {
          "name": "admin",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Admin account. This account will be the admin of the pool, and the payer for PDA during initialize pool."
          ]
        },
        {
          "name": "feeOwner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent account."
          ]
        },
        {
          "name": "mintMetadata",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "metadataProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. The pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated token program."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "curveType",
          "type": {
            "defined": "CurveType"
          }
        }
      ]
    },
    {
      "name": "initializePermissionlessPool",
      "docs": [
        "Initialize a new permissionless pool."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA address)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "tokenAMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token A mint of the pool. Eg: USDT"
          ]
        },
        {
          "name": "tokenBMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token B mint of the pool. Eg: USDC"
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token A. Token A of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token B. Token B of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault A"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault B"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "payerTokenA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer token account for pool token A mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerTokenB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Admin token account for pool token B mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerPoolLp",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "protocolTokenAFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token A. Used to receive trading fee."
          ]
        },
        {
          "name": "protocolTokenBFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token B. Used to receive trading fee."
          ]
        },
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Admin account. This account will be the admin of the pool, and the payer for PDA during initialize pool."
          ]
        },
        {
          "name": "feeOwner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent account."
          ]
        },
        {
          "name": "mintMetadata",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "metadataProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. The pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated token program."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "curveType",
          "type": {
            "defined": "CurveType"
          }
        },
        {
          "name": "tokenAAmount",
          "type": "u64"
        },
        {
          "name": "tokenBAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "initializePermissionlessPoolWithFeeTier",
      "docs": [
        "Initialize a new permissionless pool with customized fee tier"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA address)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "tokenAMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token A mint of the pool. Eg: USDT"
          ]
        },
        {
          "name": "tokenBMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token B mint of the pool. Eg: USDC"
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token A. Token A of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token B. Token B of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault A"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault B"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "payerTokenA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer token account for pool token A mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerTokenB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Admin token account for pool token B mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerPoolLp",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "protocolTokenAFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token A. Used to receive trading fee."
          ]
        },
        {
          "name": "protocolTokenBFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token B. Used to receive trading fee."
          ]
        },
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Admin account. This account will be the admin of the pool, and the payer for PDA during initialize pool."
          ]
        },
        {
          "name": "feeOwner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent account."
          ]
        },
        {
          "name": "mintMetadata",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "metadataProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. The pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated token program."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "curveType",
          "type": {
            "defined": "CurveType"
          }
        },
        {
          "name": "tradeFeeBps",
          "type": "u64"
        },
        {
          "name": "tokenAAmount",
          "type": "u64"
        },
        {
          "name": "tokenBAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "enableOrDisablePool",
      "docs": [
        "Enable or disable a pool. A disabled pool allow only remove balanced liquidity operation."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "admin",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "Admin account. Must be owner of the pool."
          ]
        }
      ],
      "args": [
        {
          "name": "enable",
          "type": "bool"
        }
      ]
    },
    {
      "name": "swap",
      "docs": [
        "swap_python token A to B, or vice versa. An amount of trading fee will be charged for liquidity provider, and the admin of the pool."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "userSourceToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token account. Token from this account will be transfer into the vault by the pool in exchange for another token of the pool."
          ]
        },
        {
          "name": "userDestinationToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token account. The exchanged token will be transfer into this account from the pool."
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token a. token a of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token b. token b of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Lp token mint of vault a"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Lp token mint of vault b"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "protocolTokenFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account. Used to receive trading fee. It's mint field must matched with user_source_token mint field."
          ]
        },
        {
          "name": "user",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "User account. Must be owner of user_source_token."
          ]
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. the pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        }
      ],
      "args": [
        {
          "name": "inAmount",
          "type": "u64"
        },
        {
          "name": "minimumOutAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "removeLiquiditySingleSide",
      "docs": [
        "Withdraw only single token from the pool. Only supported by pool with stable swap curve."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "userPoolLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User pool lp token account. LP will be burned from this account upon success liquidity removal."
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token A. Token A of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token B. Token B of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault A"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault B"
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "userDestinationToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token account to receive token upon success liquidity removal."
          ]
        },
        {
          "name": "user",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "User account. Must be owner of the user_pool_lp account."
          ]
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. The pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        }
      ],
      "args": [
        {
          "name": "poolTokenAmount",
          "type": "u64"
        },
        {
          "name": "minimumOutAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "addImbalanceLiquidity",
      "docs": [
        "Deposit tokens to the pool in an imbalance ratio. Only supported by pool with stable swap curve."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "userPoolLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "user pool lp token account. lp will be burned from this account upon success liquidity removal."
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token a. token a of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token b. token b of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault a"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault b"
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "userAToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token A account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "userBToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token B account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "user",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "User account. Must be owner of user_a_token, and user_b_token."
          ]
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. the pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        }
      ],
      "args": [
        {
          "name": "minimumPoolTokenAmount",
          "type": "u64"
        },
        {
          "name": "tokenAAmount",
          "type": "u64"
        },
        {
          "name": "tokenBAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "removeBalanceLiquidity",
      "docs": [
        "Withdraw tokens from the pool in a balanced ratio. User will still able to withdraw from pool even the pool is disabled. This allow user to exit their liquidity when there's some unforeseen event happen."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "userPoolLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "user pool lp token account. lp will be burned from this account upon success liquidity removal."
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token a. token a of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token b. token b of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault a"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault b"
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "userAToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token A account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "userBToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token B account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "user",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "User account. Must be owner of user_a_token, and user_b_token."
          ]
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. the pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        }
      ],
      "args": [
        {
          "name": "poolTokenAmount",
          "type": "u64"
        },
        {
          "name": "minimumATokenOut",
          "type": "u64"
        },
        {
          "name": "minimumBTokenOut",
          "type": "u64"
        }
      ]
    },
    {
      "name": "addBalanceLiquidity",
      "docs": [
        "Deposit tokens to the pool in a balanced ratio."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "userPoolLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "user pool lp token account. lp will be burned from this account upon success liquidity removal."
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token a. token a of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token b. token b of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault a"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault b"
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "userAToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token A account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "userBToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token B account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "user",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "User account. Must be owner of user_a_token, and user_b_token."
          ]
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. the pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        }
      ],
      "args": [
        {
          "name": "poolTokenAmount",
          "type": "u64"
        },
        {
          "name": "maximumTokenAAmount",
          "type": "u64"
        },
        {
          "name": "maximumTokenBAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "setPoolFees",
      "docs": [
        "Update trading fee charged for liquidity provider, and admin."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "feeOperator",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "Fee operator account"
          ]
        }
      ],
      "args": [
        {
          "name": "fees",
          "type": {
            "defined": "PoolFees"
          }
        },
        {
          "name": "newPartnerFeeNumerator",
          "type": "u64"
        }
      ]
    },
    {
      "name": "overrideCurveParam",
      "docs": [
        "Update swap curve parameters. This function do not allow update of curve type. For example: stable swap curve to constant product curve. Only supported by pool with stable swap curve.",
        "Only amp is allowed to be override. The other attributes of stable swap curve will be ignored."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "admin",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "Admin account."
          ]
        }
      ],
      "args": [
        {
          "name": "curveType",
          "type": {
            "defined": "CurveType"
          }
        }
      ]
    },
    {
      "name": "getPoolInfo",
      "docs": [
        "Get the general information of the pool."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "aVault",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault account for token a. token a of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault account for token b. token b of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token mint of vault a"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token mint of vault b"
          ]
        }
      ],
      "args": []
    },
    {
      "name": "bootstrapLiquidity",
      "docs": [
        "Bootstrap the pool when liquidity is depleted."
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "userPoolLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "user pool lp token account. lp will be burned from this account upon success liquidity removal."
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token a. token a of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token b. token b of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault a"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault b"
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "userAToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token A account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "userBToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token B account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "user",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "User account. Must be owner of user_a_token, and user_b_token."
          ]
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. the pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        }
      ],
      "args": [
        {
          "name": "tokenAAmount",
          "type": "u64"
        },
        {
          "name": "tokenBAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "createMintMetadata",
      "docs": [
        "Create mint metadata account for old pools"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Pool account"
          ]
        },
        {
          "name": "lpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP mint account of the pool"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault A LP account of the pool"
          ]
        },
        {
          "name": "mintMetadata",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "metadataProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer"
          ]
        }
      ],
      "args": []
    },
    {
      "name": "createLockEscrow",
      "docs": [
        "Create lock account"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Pool account"
          ]
        },
        {
          "name": "lockEscrow",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Lock account"
          ]
        },
        {
          "name": "owner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "lpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer account"
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": []
    },
    {
      "name": "lock",
      "docs": [
        "Lock Lp token"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account"
          ]
        },
        {
          "name": "lpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "lockEscrow",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Lock account"
          ]
        },
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Can be anyone"
          ]
        },
        {
          "name": "sourceTokens",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "owner lp token account"
          ]
        },
        {
          "name": "escrowVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Escrow vault"
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "aVault",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault account for token a. token a of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault account for token b. token b of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token mint of vault a"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token mint of vault b"
          ]
        }
      ],
      "args": [
        {
          "name": "maxAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "claimFee",
      "docs": [
        "Claim fee"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "lockEscrow",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Lock account"
          ]
        },
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Owner of lock account"
          ]
        },
        {
          "name": "sourceTokens",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "owner lp token account"
          ]
        },
        {
          "name": "escrowVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Escrow vault"
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token a. token a of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token b. token b of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault a"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault b"
          ]
        },
        {
          "name": "userAToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token A account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "userBToken",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "User token B account. Token will be transfer from this account if it is add liquidity operation. Else, token will be transfer into this account."
          ]
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. the pool will deposit/withdraw liquidity from the vault."
          ]
        }
      ],
      "args": [
        {
          "name": "maxAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "createConfig",
      "docs": [
        "Create config"
      ],
      "accounts": [
        {
          "name": "config",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "admin",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false
        }
      ],
      "args": [
        {
          "name": "configParameters",
          "type": {
            "defined": "ConfigParameters"
          }
        }
      ]
    },
    {
      "name": "closeConfig",
      "docs": [
        "Close config"
      ],
      "accounts": [
        {
          "name": "config",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "admin",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "rentReceiver",
          "isMut": true,
          "isSigner": false
        }
      ],
      "args": []
    },
    {
      "name": "initializePermissionlessConstantProductPoolWithConfig",
      "docs": [
        "Initialize permissionless pool with config"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA address)"
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "tokenAMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token A mint of the pool. Eg: USDT"
          ]
        },
        {
          "name": "tokenBMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token B mint of the pool. Eg: USDC"
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token A. Token A of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token B. Token B of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault A"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault B"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "payerTokenA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer token account for pool token A mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerTokenB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Admin token account for pool token B mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerPoolLp",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "protocolTokenAFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token A. Used to receive trading fee."
          ]
        },
        {
          "name": "protocolTokenBFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token B. Used to receive trading fee."
          ]
        },
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Admin account. This account will be the admin of the pool, and the payer for PDA during initialize pool."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent account."
          ]
        },
        {
          "name": "mintMetadata",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "metadataProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. The pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated token program."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "tokenAAmount",
          "type": "u64"
        },
        {
          "name": "tokenBAmount",
          "type": "u64"
        }
      ]
    },
    {
      "name": "initializePermissionlessConstantProductPoolWithConfig2",
      "docs": [
        "Initialize permissionless pool with config 2"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA address)"
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "tokenAMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token A mint of the pool. Eg: USDT"
          ]
        },
        {
          "name": "tokenBMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token B mint of the pool. Eg: USDC"
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token A. Token A of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token B. Token B of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault A"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault B"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "payerTokenA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer token account for pool token A mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerTokenB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Admin token account for pool token B mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerPoolLp",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "protocolTokenAFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token A. Used to receive trading fee."
          ]
        },
        {
          "name": "protocolTokenBFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token B. Used to receive trading fee."
          ]
        },
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Admin account. This account will be the admin of the pool, and the payer for PDA during initialize pool."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent account."
          ]
        },
        {
          "name": "mintMetadata",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "metadataProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. The pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated token program."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "tokenAAmount",
          "type": "u64"
        },
        {
          "name": "tokenBAmount",
          "type": "u64"
        },
        {
          "name": "activationPoint",
          "type": {
            "option": "u64"
          }
        }
      ]
    },
    {
      "name": "initializeCustomizablePermissionlessConstantProductPool",
      "docs": [
        "Initialize permissionless pool with customizable params"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA address)"
          ]
        },
        {
          "name": "lpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "tokenAMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token A mint of the pool. Eg: USDT"
          ]
        },
        {
          "name": "tokenBMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token B mint of the pool. Eg: USDC"
          ]
        },
        {
          "name": "aVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token A. Token A of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "bVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Vault account for token B. Token B of the pool will be deposit / withdraw from this vault account."
          ]
        },
        {
          "name": "aTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault A"
          ]
        },
        {
          "name": "bTokenVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token vault account of vault B"
          ]
        },
        {
          "name": "aVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault A"
          ]
        },
        {
          "name": "bVaultLpMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token mint of vault B"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "bVaultLp",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "LP token account of vault B. Used to receive/burn vault LP upon deposit/withdraw from the vault."
          ]
        },
        {
          "name": "payerTokenA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer token account for pool token A mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerTokenB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Admin token account for pool token B mint. Used to bootstrap the pool with initial liquidity."
          ]
        },
        {
          "name": "payerPoolLp",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "protocolTokenAFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token A. Used to receive trading fee."
          ]
        },
        {
          "name": "protocolTokenBFee",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Protocol fee token account for token B. Used to receive trading fee."
          ]
        },
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Admin account. This account will be the admin of the pool, and the payer for PDA during initialize pool."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent account."
          ]
        },
        {
          "name": "mintMetadata",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "metadataProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "vaultProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Vault program. The pool will deposit/withdraw liquidity from the vault."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated token program."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "tokenAAmount",
          "type": "u64"
        },
        {
          "name": "tokenBAmount",
          "type": "u64"
        },
        {
          "name": "params",
          "type": {
            "defined": "CustomizableParams"
          }
        }
      ]
    },
    {
      "name": "updateActivationPoint",
      "docs": [
        "Update activation slot"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "admin",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "Admin account."
          ]
        }
      ],
      "args": [
        {
          "name": "newActivationPoint",
          "type": "u64"
        }
      ]
    },
    {
      "name": "withdrawProtocolFees",
      "docs": [
        "Withdraw protocol fee"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "protocolTokenAFee",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "protocolTokenBFee",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "treasuryTokenA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "treasuryTokenB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false
        }
      ],
      "args": []
    },
    {
      "name": "setWhitelistedVault",
      "docs": [
        "Set whitelisted vault"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "admin",
          "isMut": false,
          "isSigner": true
        }
      ],
      "args": [
        {
          "name": "whitelistedVault",
          "type": "publicKey"
        }
      ]
    },
    {
      "name": "partnerClaimFee",
      "docs": [
        "Partner claim fee"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Pool account (PDA)"
          ]
        },
        {
          "name": "aVaultLp",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "protocolTokenAFee",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "protocolTokenBFee",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "partnerTokenA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "partnerTokenB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "partnerAuthority",
          "isMut": false,
          "isSigner": true
        }
      ],
      "args": [
        {
          "name": "maxAmountA",
          "type": "u64"
        },
        {
          "name": "maxAmountB",
          "type": "u64"
        }
      ]
    },
    {
      "name": "moveLockedLp",
      "docs": [
        "Move locked lp"
      ],
      "accounts": [
        {
          "name": "pool",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Pool account"
          ]
        },
        {
          "name": "lpMint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "LP token mint of the pool"
          ]
        },
        {
          "name": "fromLockEscrow",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "From lock account"
          ]
        },
        {
          "name": "toLockEscrow",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "To lock account"
          ]
        },
        {
          "name": "owner",
          "isMut": false,
          "isSigner": true,
          "docs": [
            "Owner of lock account"
          ]
        },
        {
          "name": "fromEscrowVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "From escrow vault"
          ]
        },
        {
          "name": "toEscrowVault",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "To escrow vault"
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "aVault",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "bVault",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "aVaultLp",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "bVaultLp",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "aVaultLpMint",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "bVaultLpMint",
          "isMut": false,
          "isSigner": false
        }
      ],
      "args": [
        {
          "name": "maxAmount",
          "type": "u64"
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "config",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "poolFees",
            "type": {
              "defined": "PoolFees"
            }
          },
          {
            "name": "activationDuration",
            "type": "u64"
          },
          {
            "name": "vaultConfigKey",
            "type": "publicKey"
          },
          {
            "name": "poolCreatorAuthority",
            "docs": [
              "Only pool_creator_authority can use the current config to initialize new pool. When it's Pubkey::default, it's a public config."
            ],
            "type": "publicKey"
          },
          {
            "name": "activationType",
            "docs": [
              "Activation type"
            ],
            "type": "u8"
          },
          {
            "name": "partnerFeeNumerator",
            "type": "u64"
          },
          {
            "name": "padding",
            "type": {
              "array": [
                "u8",
                219
              ]
            }
          }
        ]
      }
    },
    {
      "name": "lockEscrow",
      "docs": [
        "State of lock escrow account"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "docs": [
              "Pool address"
            ],
            "type": "publicKey"
          },
          {
            "name": "owner",
            "docs": [
              "Owner address"
            ],
            "type": "publicKey"
          },
          {
            "name": "escrowVault",
            "docs": [
              "Vault address, store the lock user lock"
            ],
            "type": "publicKey"
          },
          {
            "name": "bump",
            "docs": [
              "bump, used to sign"
            ],
            "type": "u8"
          },
          {
            "name": "totalLockedAmount",
            "docs": [
              "Total locked amount"
            ],
            "type": "u64"
          },
          {
            "name": "lpPerToken",
            "docs": [
              "Lp per token, virtual price of lp token"
            ],
            "type": "u128"
          },
          {
            "name": "unclaimedFeePending",
            "docs": [
              "Unclaimed fee pending"
            ],
            "type": "u64"
          },
          {
            "name": "aFee",
            "docs": [
              "Total a fee claimed so far"
            ],
            "type": "u64"
          },
          {
            "name": "bFee",
            "docs": [
              "Total b fee claimed so far"
            ],
            "type": "u64"
          },
          {
            "name": "padding",
            "docs": [
              "padding"
            ],
            "type": {
              "array": [
                "u8",
                7
              ]
            }
          }
        ]
      }
    },
    {
      "name": "pool",
      "docs": [
        "State of pool account"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "lpMint",
            "docs": [
              "LP token mint of the pool"
            ],
            "type": "publicKey"
          },
          {
            "name": "tokenAMint",
            "docs": [
              "Token A mint of the pool. Eg: USDT"
            ],
            "type": "publicKey"
          },
          {
            "name": "tokenBMint",
            "docs": [
              "Token B mint of the pool. Eg: USDC"
            ],
            "type": "publicKey"
          },
          {
            "name": "aVault",
            "docs": [
              "Vault account for token A. Token A of the pool will be deposit / withdraw from this vault account."
            ],
            "type": "publicKey"
          },
          {
            "name": "bVault",
            "docs": [
              "Vault account for token B. Token B of the pool will be deposit / withdraw from this vault account."
            ],
            "type": "publicKey"
          },
          {
            "name": "aVaultLp",
            "docs": [
              "LP token account of vault A. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
            ],
            "type": "publicKey"
          },
          {
            "name": "bVaultLp",
            "docs": [
              "LP token account of vault B. Used to receive/burn the vault LP upon deposit/withdraw from the vault."
            ],
            "type": "publicKey"
          },
          {
            "name": "aVaultLpBump",
            "docs": [
              "\"A\" vault lp bump. Used to create signer seeds."
            ],
            "type": "u8"
          },
          {
            "name": "enabled",
            "docs": [
              "Flag to determine whether the pool is enabled, or disabled."
            ],
            "type": "bool"
          },
          {
            "name": "protocolTokenAFee",
            "docs": [
              "Protocol fee token account for token A. Used to receive trading fee."
            ],
            "type": "publicKey"
          },
          {
            "name": "protocolTokenBFee",
            "docs": [
              "Protocol fee token account for token B. Used to receive trading fee."
            ],
            "type": "publicKey"
          },
          {
            "name": "feeLastUpdatedAt",
            "docs": [
              "Fee last updated timestamp"
            ],
            "type": "u64"
          },
          {
            "name": "padding0",
            "type": {
              "array": [
                "u8",
                24
              ]
            }
          },
          {
            "name": "fees",
            "docs": [
              "Store the fee charges setting."
            ],
            "type": {
              "defined": "PoolFees"
            }
          },
          {
            "name": "poolType",
            "docs": [
              "Pool type"
            ],
            "type": {
              "defined": "PoolType"
            }
          },
          {
            "name": "stake",
            "docs": [
              "Stake pubkey of SPL stake pool"
            ],
            "type": "publicKey"
          },
          {
            "name": "totalLockedLp",
            "docs": [
              "Total locked lp token"
            ],
            "type": "u64"
          },
          {
            "name": "bootstrapping",
            "docs": [
              "bootstrapping config"
            ],
            "type": {
              "defined": "Bootstrapping"
            }
          },
          {
            "name": "partnerInfo",
            "type": {
              "defined": "PartnerInfo"
            }
          },
          {
            "name": "padding",
            "docs": [
              "Padding for future pool field"
            ],
            "type": {
              "defined": "Padding"
            }
          },
          {
            "name": "curveType",
            "docs": [
              "The type of the swap curve supported by the pool."
            ],
            "type": {
              "defined": "CurveType"
            }
          },
          {
            "name": "padding1",
            "docs": [
              "padding"
            ],
            "type": {
              "array": [
                "u8",
                19
              ]
            }
          }
        ]
      }
    }
  ],
  "types": [
    {
      "name": "TokenMultiplier",
      "docs": [
        "Multiplier for the pool token. Used to normalized token with different decimal into the same precision."
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "tokenAMultiplier",
            "docs": [
              "Multiplier for token A of the pool."
            ],
            "type": "u64"
          },
          {
            "name": "tokenBMultiplier",
            "docs": [
              "Multiplier for token B of the pool."
            ],
            "type": "u64"
          },
          {
            "name": "precisionFactor",
            "docs": [
              "Record the highest token decimal in the pool. For example, Token A is 6 decimal, token B is 9 decimal. This will save value of 9."
            ],
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "PoolFees",
      "docs": [
        "Information regarding fee charges"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "tradeFeeNumerator",
            "docs": [
              "Trade fees are extra token amounts that are held inside the token",
              "accounts during a trade, making the value of liquidity tokens rise.",
              "Trade fee numerator"
            ],
            "type": "u64"
          },
          {
            "name": "tradeFeeDenominator",
            "docs": [
              "Trade fee denominator"
            ],
            "type": "u64"
          },
          {
            "name": "protocolTradeFeeNumerator",
            "docs": [
              "Protocol trading fees are extra token amounts that are held inside the token",
              "accounts during a trade, with the equivalent in pool tokens minted to",
              "the protocol of the program.",
              "Protocol trade fee numerator"
            ],
            "type": "u64"
          },
          {
            "name": "protocolTradeFeeDenominator",
            "docs": [
              "Protocol trade fee denominator"
            ],
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "Depeg",
      "docs": [
        "Contains information for depeg pool"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "baseVirtualPrice",
            "docs": [
              "The virtual price of staking / interest bearing token"
            ],
            "type": "u64"
          },
          {
            "name": "baseCacheUpdated",
            "docs": [
              "The last time base_virtual_price is updated"
            ],
            "type": "u64"
          },
          {
            "name": "depegType",
            "docs": [
              "Type of the depeg pool"
            ],
            "type": {
              "defined": "DepegType"
            }
          }
        ]
      }
    },
    {
      "name": "ConfigParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "tradeFeeNumerator",
            "type": "u64"
          },
          {
            "name": "protocolTradeFeeNumerator",
            "type": "u64"
          },
          {
            "name": "activationDuration",
            "type": "u64"
          },
          {
            "name": "vaultConfigKey",
            "type": "publicKey"
          },
          {
            "name": "poolCreatorAuthority",
            "type": "publicKey"
          },
          {
            "name": "activationType",
            "type": "u8"
          },
          {
            "name": "index",
            "type": "u64"
          },
          {
            "name": "partnerFeeNumerator",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "CustomizableParams",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "tradeFeeNumerator",
            "docs": [
              "Trading fee."
            ],
            "type": "u32"
          },
          {
            "name": "activationPoint",
            "docs": [
              "The pool start trading."
            ],
            "type": {
              "option": "u64"
            }
          },
          {
            "name": "hasAlphaVault",
            "docs": [
              "Whether the pool support alpha vault"
            ],
            "type": "bool"
          },
          {
            "name": "activationType",
            "docs": [
              "Activation type"
            ],
            "type": "u8"
          },
          {
            "name": "padding",
            "docs": [
              "Padding"
            ],
            "type": {
              "array": [
                "u8",
                90
              ]
            }
          }
        ]
      }
    },
    {
      "name": "Padding",
      "docs": [
        "Padding for future pool fields"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "padding0",
            "docs": [
              "Padding 0"
            ],
            "type": {
              "array": [
                "u8",
                6
              ]
            }
          },
          {
            "name": "padding1",
            "docs": [
              "Padding 1"
            ],
            "type": {
              "array": [
                "u64",
                21
              ]
            }
          },
          {
            "name": "padding2",
            "docs": [
              "Padding 2"
            ],
            "type": {
              "array": [
                "u64",
                21
              ]
            }
          }
        ]
      }
    },
    {
      "name": "PartnerInfo",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "feeNumerator",
            "type": "u64"
          },
          {
            "name": "partnerAuthority",
            "type": "publicKey"
          },
          {
            "name": "pendingFeeA",
            "type": "u64"
          },
          {
            "name": "pendingFeeB",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "Bootstrapping",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "activationPoint",
            "docs": [
              "Activation point, can be slot or timestamp"
            ],
            "type": "u64"
          },
          {
            "name": "whitelistedVault",
            "docs": [
              "Whitelisted vault to be able to buy pool before activation_point"
            ],
            "type": "publicKey"
          },
          {
            "name": "poolCreator",
            "docs": [
              "Need to store pool creator in lauch pool, so they can modify liquidity before activation_point"
            ],
            "type": "publicKey"
          },
          {
            "name": "activationType",
            "docs": [
              "Activation type, 0 means by slot, 1 means by timestamp"
            ],
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "ActivationType",
      "docs": [
        "Type of the activation"
      ],
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Slot"
          },
          {
            "name": "Timestamp"
          }
        ]
      }
    },
    {
      "name": "RoundDirection",
      "docs": [
        "Rounding direction"
      ],
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Floor"
          },
          {
            "name": "Ceiling"
          }
        ]
      }
    },
    {
      "name": "TradeDirection",
      "docs": [
        "Trade (swap) direction"
      ],
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "AtoB"
          },
          {
            "name": "BtoA"
          }
        ]
      }
    },
    {
      "name": "NewCurveType",
      "docs": [
        "Type of the swap curve"
      ],
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "ConstantProduct"
          },
          {
            "name": "Stable",
            "fields": [
              {
                "name": "amp",
                "docs": [
                  "Amplification coefficient"
                ],
                "type": "u64"
              },
              {
                "name": "token_multiplier",
                "docs": [
                  "Multiplier for the pool token. Used to normalized token with different decimal into the same precision."
                ],
                "type": {
                  "defined": "TokenMultiplier"
                }
              },
              {
                "name": "depeg",
                "docs": [
                  "Depeg pool information. Contains functions to allow token amount to be repeg using stake / interest bearing token virtual price"
                ],
                "type": {
                  "defined": "Depeg"
                }
              },
              {
                "name": "last_amp_updated_timestamp",
                "docs": [
                  "The last amp updated timestamp. Used to prevent update_curve_info called infinitely many times within a short period"
                ],
                "type": "u64"
              }
            ]
          },
          {
            "name": "NewCurve",
            "fields": [
              {
                "name": "field_one",
                "type": "u64"
              },
              {
                "name": "field_two",
                "type": "u64"
              }
            ]
          }
        ]
      }
    },
    {
      "name": "CurveType",
      "docs": [
        "Type of the swap curve"
      ],
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "ConstantProduct"
          },
          {
            "name": "Stable",
            "fields": [
              {
                "name": "amp",
                "docs": [
                  "Amplification coefficient"
                ],
                "type": "u64"
              },
              {
                "name": "token_multiplier",
                "docs": [
                  "Multiplier for the pool token. Used to normalized token with different decimal into the same precision."
                ],
                "type": {
                  "defined": "TokenMultiplier"
                }
              },
              {
                "name": "depeg",
                "docs": [
                  "Depeg pool information. Contains functions to allow token amount to be repeg using stake / interest bearing token virtual price"
                ],
                "type": {
                  "defined": "Depeg"
                }
              },
              {
                "name": "last_amp_updated_timestamp",
                "docs": [
                  "The last amp updated timestamp. Used to prevent update_curve_info called infinitely many times within a short period"
                ],
                "type": "u64"
              }
            ]
          }
        ]
      }
    },
    {
      "name": "DepegType",
      "docs": [
        "Type of depeg pool"
      ],
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "None"
          },
          {
            "name": "Marinade"
          },
          {
            "name": "Lido"
          },
          {
            "name": "SplStake"
          }
        ]
      }
    },
    {
      "name": "Rounding",
      "docs": [
        "Round up, down"
      ],
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Up"
          },
          {
            "name": "Down"
          }
        ]
      }
    },
    {
      "name": "PoolType",
      "docs": [
        "Pool type"
      ],
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "Permissioned"
          },
          {
            "name": "Permissionless"
          }
        ]
      }
    }
  ],
  "events": [
    {
      "name": "AddLiquidity",
      "fields": [
        {
          "name": "lpMintAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tokenAAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tokenBAmount",
          "type": "u64",
          "index": false
        }
      ]
    },
    {
      "name": "RemoveLiquidity",
      "fields": [
        {
          "name": "lpUnmintAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tokenAOutAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tokenBOutAmount",
          "type": "u64",
          "index": false
        }
      ]
    },
    {
      "name": "BootstrapLiquidity",
      "fields": [
        {
          "name": "lpMintAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tokenAAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tokenBAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "swap_python",
      "fields": [
        {
          "name": "inAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "outAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tradeFee",
          "type": "u64",
          "index": false
        },
        {
          "name": "protocolFee",
          "type": "u64",
          "index": false
        },
        {
          "name": "hostFee",
          "type": "u64",
          "index": false
        }
      ]
    },
    {
      "name": "SetPoolFees",
      "fields": [
        {
          "name": "tradeFeeNumerator",
          "type": "u64",
          "index": false
        },
        {
          "name": "tradeFeeDenominator",
          "type": "u64",
          "index": false
        },
        {
          "name": "protocolTradeFeeNumerator",
          "type": "u64",
          "index": false
        },
        {
          "name": "protocolTradeFeeDenominator",
          "type": "u64",
          "index": false
        },
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "PoolInfo",
      "fields": [
        {
          "name": "tokenAAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tokenBAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "virtualPrice",
          "type": "f64",
          "index": false
        },
        {
          "name": "currentTimestamp",
          "type": "u64",
          "index": false
        }
      ]
    },
    {
      "name": "TransferAdmin",
      "fields": [
        {
          "name": "admin",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "newAdmin",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "OverrideCurveParam",
      "fields": [
        {
          "name": "newAmp",
          "type": "u64",
          "index": false
        },
        {
          "name": "updatedTimestamp",
          "type": "u64",
          "index": false
        },
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "PoolCreated",
      "fields": [
        {
          "name": "lpMint",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "tokenAMint",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "tokenBMint",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "poolType",
          "type": {
            "defined": "PoolType"
          },
          "index": false
        },
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "PoolEnabled",
      "fields": [
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "enabled",
          "type": "bool",
          "index": false
        }
      ]
    },
    {
      "name": "MigrateFeeAccount",
      "fields": [
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "newAdminTokenAFee",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "newAdminTokenBFee",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "tokenAAmount",
          "type": "u64",
          "index": false
        },
        {
          "name": "tokenBAmount",
          "type": "u64",
          "index": false
        }
      ]
    },
    {
      "name": "CreateLockEscrow",
      "fields": [
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "owner",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "Lock",
      "fields": [
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "owner",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "amount",
          "type": "u64",
          "index": false
        }
      ]
    },
    {
      "name": "ClaimFee",
      "fields": [
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "owner",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "amount",
          "type": "u64",
          "index": false
        },
        {
          "name": "aFee",
          "type": "u64",
          "index": false
        },
        {
          "name": "bFee",
          "type": "u64",
          "index": false
        }
      ]
    },
    {
      "name": "CreateConfig",
      "fields": [
        {
          "name": "tradeFeeNumerator",
          "type": "u64",
          "index": false
        },
        {
          "name": "protocolTradeFeeNumerator",
          "type": "u64",
          "index": false
        },
        {
          "name": "config",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "CloseConfig",
      "fields": [
        {
          "name": "config",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "WithdrawProtocolFees",
      "fields": [
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "protocolAFee",
          "type": "u64",
          "index": false
        },
        {
          "name": "protocolBFee",
          "type": "u64",
          "index": false
        },
        {
          "name": "protocolAFeeOwner",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "protocolBFeeOwner",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "PartnerClaimFees",
      "fields": [
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "feeA",
          "type": "u64",
          "index": false
        },
        {
          "name": "feeB",
          "type": "u64",
          "index": false
        },
        {
          "name": "partner",
          "type": "publicKey",
          "index": false
        }
      ]
    },
    {
      "name": "MoveLockedLp",
      "fields": [
        {
          "name": "pool",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "fromLockEscrow",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "toLockEscrow",
          "type": "publicKey",
          "index": false
        },
        {
          "name": "amount",
          "type": "u64",
          "index": false
        }
      ]
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "MathOverflow",
      "msg": "Math operation overflow"
    },
    {
      "code": 6001,
      "name": "InvalidFee",
      "msg": "Invalid fee setup"
    },
    {
      "code": 6002,
      "name": "InvalidInvariant",
      "msg": "Invalid invariant d"
    },
    {
      "code": 6003,
      "name": "FeeCalculationFailure",
      "msg": "Fee calculation failure"
    },
    {
      "code": 6004,
      "name": "ExceededSlippage",
      "msg": "Exceeded slippage tolerance"
    },
    {
      "code": 6005,
      "name": "InvalidCalculation",
      "msg": "Invalid curve calculation"
    },
    {
      "code": 6006,
      "name": "ZeroTradingTokens",
      "msg": "Given pool token amount results in zero trading tokens"
    },
    {
      "code": 6007,
      "name": "ConversionError",
      "msg": "Math conversion overflow"
    },
    {
      "code": 6008,
      "name": "FaultyLpMint",
      "msg": "LP mint authority must be 'A' vault lp, without freeze authority, and 0 supply"
    },
    {
      "code": 6009,
      "name": "MismatchedTokenMint",
      "msg": "Token mint mismatched"
    },
    {
      "code": 6010,
      "name": "MismatchedLpMint",
      "msg": "LP mint mismatched"
    },
    {
      "code": 6011,
      "name": "MismatchedOwner",
      "msg": "Invalid lp token owner"
    },
    {
      "code": 6012,
      "name": "InvalidVaultAccount",
      "msg": "Invalid vault account"
    },
    {
      "code": 6013,
      "name": "InvalidVaultLpAccount",
      "msg": "Invalid vault lp account"
    },
    {
      "code": 6014,
      "name": "InvalidPoolLpMintAccount",
      "msg": "Invalid pool lp mint account"
    },
    {
      "code": 6015,
      "name": "PoolDisabled",
      "msg": "Pool disabled"
    },
    {
      "code": 6016,
      "name": "InvalidAdminAccount",
      "msg": "Invalid admin account"
    },
    {
      "code": 6017,
      "name": "InvalidProtocolFeeAccount",
      "msg": "Invalid protocol fee account"
    },
    {
      "code": 6018,
      "name": "SameAdminAccount",
      "msg": "Same admin account"
    },
    {
      "code": 6019,
      "name": "IdenticalSourceDestination",
      "msg": "Identical user source and destination token account"
    },
    {
      "code": 6020,
      "name": "ApyCalculationError",
      "msg": "Apy calculation error"
    },
    {
      "code": 6021,
      "name": "InsufficientSnapshot",
      "msg": "Insufficient virtual price snapshot"
    },
    {
      "code": 6022,
      "name": "NonUpdatableCurve",
      "msg": "Current curve is non-updatable"
    },
    {
      "code": 6023,
      "name": "MisMatchedCurve",
      "msg": "New curve is mismatched with old curve"
    },
    {
      "code": 6024,
      "name": "InvalidAmplification",
      "msg": "Amplification is invalid"
    },
    {
      "code": 6025,
      "name": "UnsupportedOperation",
      "msg": "Operation is not supported"
    },
    {
      "code": 6026,
      "name": "ExceedMaxAChanges",
      "msg": "Exceed max amplification changes"
    },
    {
      "code": 6027,
      "name": "InvalidRemainingAccountsLen",
      "msg": "Invalid remaining accounts length"
    },
    {
      "code": 6028,
      "name": "InvalidRemainingAccounts",
      "msg": "Invalid remaining account"
    },
    {
      "code": 6029,
      "name": "MismatchedDepegMint",
      "msg": "Token mint B doesn't matches depeg type token mint"
    },
    {
      "code": 6030,
      "name": "InvalidApyAccount",
      "msg": "Invalid APY account"
    },
    {
      "code": 6031,
      "name": "InvalidTokenMultiplier",
      "msg": "Invalid token multiplier"
    },
    {
      "code": 6032,
      "name": "InvalidDepegInformation",
      "msg": "Invalid depeg information"
    },
    {
      "code": 6033,
      "name": "UpdateTimeConstraint",
      "msg": "Update time constraint violated"
    },
    {
      "code": 6034,
      "name": "ExceedMaxFeeBps",
      "msg": "Exceeded max fee bps"
    },
    {
      "code": 6035,
      "name": "InvalidAdmin",
      "msg": "Invalid admin"
    },
    {
      "code": 6036,
      "name": "PoolIsNotPermissioned",
      "msg": "Pool is not permissioned"
    },
    {
      "code": 6037,
      "name": "InvalidDepositAmount",
      "msg": "Invalid deposit amount"
    },
    {
      "code": 6038,
      "name": "InvalidFeeOwner",
      "msg": "Invalid fee owner"
    },
    {
      "code": 6039,
      "name": "NonDepletedPool",
      "msg": "Pool is not depleted"
    },
    {
      "code": 6040,
      "name": "AmountNotPeg",
      "msg": "Token amount is not 1:1"
    },
    {
      "code": 6041,
      "name": "AmountIsZero",
      "msg": "Amount is zero"
    },
    {
      "code": 6042,
      "name": "TypeCastFailed",
      "msg": "Type cast error"
    },
    {
      "code": 6043,
      "name": "AmountIsNotEnough",
      "msg": "Amount is not enough"
    },
    {
      "code": 6044,
      "name": "InvalidActivationDuration",
      "msg": "Invalid activation duration"
    },
    {
      "code": 6045,
      "name": "PoolIsNotLaunchPool",
      "msg": "Pool is not launch pool"
    },
    {
      "code": 6046,
      "name": "UnableToModifyActivationPoint",
      "msg": "Unable to modify activation point"
    },
    {
      "code": 6047,
      "name": "InvalidAuthorityToCreateThePool",
      "msg": "Invalid authority to create the pool"
    },
    {
      "code": 6048,
      "name": "InvalidActivationType",
      "msg": "Invalid activation type"
    },
    {
      "code": 6049,
      "name": "InvalidActivationPoint",
      "msg": "Invalid activation point"
    },
    {
      "code": 6050,
      "name": "PreActivationSwapStarted",
      "msg": "Pre activation swap window started"
    },
    {
      "code": 6051,
      "name": "InvalidPoolType",
      "msg": "Invalid pool type"
    },
    {
      "code": 6052,
      "name": "InvalidQuoteMint",
      "msg": "Quote token must be SOL,USDC"
    }
  ]
}

idl_ammV2 = {
  "address": "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
  "metadata": {
    "name": "cp_amm",
    "version": "0.1.4",
    "spec": "0.1.0",
    "description": "Created with Anchor"
  },
  "instructions": [
    {
      "name": "add_liquidity",
      "discriminator": [
        181,
        157,
        89,
        67,
        143,
        182,
        52,
        72
      ],
      "accounts": [
        {
          "name": "pool",
          "writable": true,
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "token_a_account",
          "docs": [
            "The user token a account"
          ],
          "writable": true
        },
        {
          "name": "token_b_account",
          "docs": [
            "The user token b account"
          ],
          "writable": true
        },
        {
          "name": "token_a_vault",
          "docs": [
            "The vault token account for input token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_vault",
          "docs": [
            "The vault token account for output token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_mint",
          "docs": [
            "The mint of token a"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "The mint of token b"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ]
        },
        {
          "name": "owner",
          "docs": [
            "owner of position"
          ],
          "signer": true
        },
        {
          "name": "token_a_program",
          "docs": [
            "Token a program"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Token b program"
          ]
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "AddLiquidityParameters"
            }
          }
        }
      ]
    },
    {
      "name": "claim_partner_fee",
      "discriminator": [
        97,
        206,
        39,
        105,
        94,
        94,
        126,
        148
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "token_a_account",
          "docs": [
            "The treasury token a account"
          ],
          "writable": true
        },
        {
          "name": "token_b_account",
          "docs": [
            "The treasury token b account"
          ],
          "writable": true
        },
        {
          "name": "token_a_vault",
          "docs": [
            "The vault token account for input token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_vault",
          "docs": [
            "The vault token account for output token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_mint",
          "docs": [
            "The mint of token a"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "The mint of token b"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "partner",
          "signer": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_program",
          "docs": [
            "Token a program"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Token b program"
          ]
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "max_amount_a",
          "type": "u64"
        },
        {
          "name": "max_amount_b",
          "type": "u64"
        }
      ]
    },
    {
      "name": "claim_position_fee",
      "discriminator": [
        180,
        38,
        154,
        17,
        133,
        33,
        162,
        211
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "token_a_account",
          "docs": [
            "The user token a account"
          ],
          "writable": true
        },
        {
          "name": "token_b_account",
          "docs": [
            "The user token b account"
          ],
          "writable": true
        },
        {
          "name": "token_a_vault",
          "docs": [
            "The vault token account for input token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_vault",
          "docs": [
            "The vault token account for output token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_mint",
          "docs": [
            "The mint of token a"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "The mint of token b"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ]
        },
        {
          "name": "owner",
          "docs": [
            "owner of position"
          ],
          "signer": true
        },
        {
          "name": "token_a_program",
          "docs": [
            "Token a program"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Token b program"
          ]
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "claim_protocol_fee",
      "discriminator": [
        165,
        228,
        133,
        48,
        99,
        249,
        255,
        33
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "token_a_vault",
          "docs": [
            "The vault token account for input token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_vault",
          "docs": [
            "The vault token account for output token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_mint",
          "docs": [
            "The mint of token a"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "The mint of token b"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_account",
          "docs": [
            "The treasury token a account"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  48,
                  9,
                  89,
                  123,
                  106,
                  114,
                  131,
                  251,
                  50,
                  173,
                  254,
                  250,
                  10,
                  80,
                  160,
                  84,
                  143,
                  100,
                  81,
                  249,
                  134,
                  112,
                  30,
                  213,
                  50,
                  166,
                  239,
                  78,
                  53,
                  175,
                  188,
                  85
                ]
              },
              {
                "kind": "account",
                "path": "token_a_program"
              },
              {
                "kind": "account",
                "path": "token_a_mint"
              }
            ],
            "program": {
              "kind": "const",
              "value": [
                140,
                151,
                37,
                143,
                78,
                36,
                137,
                241,
                187,
                61,
                16,
                41,
                20,
                142,
                13,
                131,
                11,
                90,
                19,
                153,
                218,
                255,
                16,
                132,
                4,
                142,
                123,
                216,
                219,
                233,
                248,
                89
              ]
            }
          }
        },
        {
          "name": "token_b_account",
          "docs": [
            "The treasury token b account"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  48,
                  9,
                  89,
                  123,
                  106,
                  114,
                  131,
                  251,
                  50,
                  173,
                  254,
                  250,
                  10,
                  80,
                  160,
                  84,
                  143,
                  100,
                  81,
                  249,
                  134,
                  112,
                  30,
                  213,
                  50,
                  166,
                  239,
                  78,
                  53,
                  175,
                  188,
                  85
                ]
              },
              {
                "kind": "account",
                "path": "token_b_program"
              },
              {
                "kind": "account",
                "path": "token_b_mint"
              }
            ],
            "program": {
              "kind": "const",
              "value": [
                140,
                151,
                37,
                143,
                78,
                36,
                137,
                241,
                187,
                61,
                16,
                41,
                20,
                142,
                13,
                131,
                11,
                90,
                19,
                153,
                218,
                255,
                16,
                132,
                4,
                142,
                123,
                216,
                219,
                233,
                248,
                89
              ]
            }
          }
        },
        {
          "name": "claim_fee_operator",
          "docs": [
            "Claim fee operator"
          ]
        },
        {
          "name": "operator",
          "docs": [
            "Operator"
          ],
          "signer": true,
          "relations": [
            "claim_fee_operator"
          ]
        },
        {
          "name": "token_a_program",
          "docs": [
            "Token a program"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Token b program"
          ]
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "max_amount_a",
          "type": "u64"
        },
        {
          "name": "max_amount_b",
          "type": "u64"
        }
      ]
    },
    {
      "name": "claim_reward",
      "discriminator": [
        149,
        95,
        181,
        242,
        94,
        90,
        158,
        162
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "writable": true,
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "reward_vault",
          "docs": [
            "The vault token account for reward token"
          ],
          "writable": true
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "user_token_account",
          "writable": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ]
        },
        {
          "name": "owner",
          "docs": [
            "owner of position"
          ],
          "signer": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u8"
        },
        {
          "name": "skip_reward",
          "type": "u8"
        }
      ]
    },
    {
      "name": "close_claim_fee_operator",
      "discriminator": [
        38,
        134,
        82,
        216,
        95,
        124,
        17,
        99
      ],
      "accounts": [
        {
          "name": "claim_fee_operator",
          "writable": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "admin",
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "close_config",
      "discriminator": [
        145,
        9,
        72,
        157,
        95,
        125,
        61,
        85
      ],
      "accounts": [
        {
          "name": "config",
          "writable": true
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "close_position",
      "discriminator": [
        123,
        134,
        81,
        0,
        49,
        68,
        98,
        98
      ],
      "accounts": [
        {
          "name": "position_nft_mint",
          "docs": [
            "position_nft_mint"
          ],
          "writable": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ],
          "writable": true
        },
        {
          "name": "pool",
          "writable": true,
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "owner",
          "docs": [
            "Owner of position"
          ],
          "signer": true
        },
        {
          "name": "token_program",
          "docs": [
            "Program to create NFT mint/token account and transfer for token22 account"
          ],
          "address": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "close_token_badge",
      "discriminator": [
        108,
        146,
        86,
        110,
        179,
        254,
        10,
        104
      ],
      "accounts": [
        {
          "name": "token_badge",
          "writable": true
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "rent_receiver",
          "writable": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "create_claim_fee_operator",
      "discriminator": [
        169,
        62,
        207,
        107,
        58,
        187,
        162,
        109
      ],
      "accounts": [
        {
          "name": "claim_fee_operator",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  99,
                  102,
                  95,
                  111,
                  112,
                  101,
                  114,
                  97,
                  116,
                  111,
                  114
                ]
              },
              {
                "kind": "account",
                "path": "operator"
              }
            ]
          }
        },
        {
          "name": "operator"
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "create_config",
      "docs": [
        "ADMIN FUNCTIONS /////"
      ],
      "discriminator": [
        201,
        207,
        243,
        114,
        75,
        111,
        47,
        189
      ],
      "accounts": [
        {
          "name": "config",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  99,
                  111,
                  110,
                  102,
                  105,
                  103
                ]
              },
              {
                "kind": "arg",
                "path": "index"
              }
            ]
          }
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "index",
          "type": "u64"
        },
        {
          "name": "config_parameters",
          "type": {
            "defined": {
              "name": "StaticConfigParameters"
            }
          }
        }
      ]
    },
    {
      "name": "create_dynamic_config",
      "discriminator": [
        81,
        251,
        122,
        78,
        66,
        57,
        208,
        82
      ],
      "accounts": [
        {
          "name": "config",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  99,
                  111,
                  110,
                  102,
                  105,
                  103
                ]
              },
              {
                "kind": "arg",
                "path": "index"
              }
            ]
          }
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "index",
          "type": "u64"
        },
        {
          "name": "config_parameters",
          "type": {
            "defined": {
              "name": "DynamicConfigParameters"
            }
          }
        }
      ]
    },
    {
      "name": "create_position",
      "discriminator": [
        48,
        215,
        197,
        153,
        96,
        203,
        180,
        133
      ],
      "accounts": [
        {
          "name": "owner"
        },
        {
          "name": "position_nft_mint",
          "docs": [
            "position_nft_mint"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "position nft account"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112,
                  111,
                  115,
                  105,
                  116,
                  105,
                  111,
                  110,
                  95,
                  110,
                  102,
                  116,
                  95,
                  97,
                  99,
                  99,
                  111,
                  117,
                  110,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "position_nft_mint"
              }
            ]
          }
        },
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "position",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112,
                  111,
                  115,
                  105,
                  116,
                  105,
                  111,
                  110
                ]
              },
              {
                "kind": "account",
                "path": "position_nft_mint"
              }
            ]
          }
        },
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "payer",
          "docs": [
            "Address paying to create the position. Can be anyone"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "token_program",
          "docs": [
            "Program to create NFT mint/token account and transfer for token22 account"
          ],
          "address": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "create_token_badge",
      "discriminator": [
        88,
        206,
        0,
        91,
        60,
        175,
        151,
        118
      ],
      "accounts": [
        {
          "name": "token_badge",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  116,
                  111,
                  107,
                  101,
                  110,
                  95,
                  98,
                  97,
                  100,
                  103,
                  101
                ]
              },
              {
                "kind": "account",
                "path": "token_mint"
              }
            ]
          }
        },
        {
          "name": "token_mint"
        },
        {
          "name": "admin",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": []
    },
    {
      "name": "fund_reward",
      "discriminator": [
        188,
        50,
        249,
        165,
        93,
        151,
        38,
        63
      ],
      "accounts": [
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "reward_vault",
          "writable": true
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "funder_token_account",
          "writable": true
        },
        {
          "name": "funder",
          "signer": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u8"
        },
        {
          "name": "amount",
          "type": "u64"
        },
        {
          "name": "carry_forward",
          "type": "bool"
        }
      ]
    },
    {
      "name": "initialize_customizable_pool",
      "discriminator": [
        20,
        161,
        241,
        24,
        189,
        221,
        180,
        2
      ],
      "accounts": [
        {
          "name": "creator"
        },
        {
          "name": "position_nft_mint",
          "docs": [
            "position_nft_mint"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "position nft account"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112,
                  111,
                  115,
                  105,
                  116,
                  105,
                  111,
                  110,
                  95,
                  110,
                  102,
                  116,
                  95,
                  97,
                  99,
                  99,
                  111,
                  117,
                  110,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "position_nft_mint"
              }
            ]
          }
        },
        {
          "name": "payer",
          "docs": [
            "Address paying to create the pool. Can be anyone"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "docs": [
            "Initialize an account to store the pool state"
          ],
          "writable": true
        },
        {
          "name": "position",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112,
                  111,
                  115,
                  105,
                  116,
                  105,
                  111,
                  110
                ]
              },
              {
                "kind": "account",
                "path": "position_nft_mint"
              }
            ]
          }
        },
        {
          "name": "token_a_mint",
          "docs": [
            "Token a mint"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "Token b mint"
          ]
        },
        {
          "name": "token_a_vault",
          "docs": [
            "Token a vault for the pool"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  116,
                  111,
                  107,
                  101,
                  110,
                  95,
                  118,
                  97,
                  117,
                  108,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "token_a_mint"
              },
              {
                "kind": "account",
                "path": "pool"
              }
            ]
          }
        },
        {
          "name": "token_b_vault",
          "docs": [
            "Token b vault for the pool"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  116,
                  111,
                  107,
                  101,
                  110,
                  95,
                  118,
                  97,
                  117,
                  108,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "token_b_mint"
              },
              {
                "kind": "account",
                "path": "pool"
              }
            ]
          }
        },
        {
          "name": "payer_token_a",
          "docs": [
            "payer token a account"
          ],
          "writable": true
        },
        {
          "name": "payer_token_b",
          "docs": [
            "creator token b account"
          ],
          "writable": true
        },
        {
          "name": "token_a_program",
          "docs": [
            "Program to create mint account and mint tokens"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Program to create mint account and mint tokens"
          ]
        },
        {
          "name": "token_2022_program",
          "docs": [
            "Program to create NFT mint/token account and transfer for token22 account"
          ],
          "address": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "InitializeCustomizablePoolParameters"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_pool",
      "docs": [
        "USER FUNCTIONS ////"
      ],
      "discriminator": [
        95,
        180,
        10,
        172,
        84,
        174,
        232,
        40
      ],
      "accounts": [
        {
          "name": "creator"
        },
        {
          "name": "position_nft_mint",
          "docs": [
            "position_nft_mint"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "position nft account"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112,
                  111,
                  115,
                  105,
                  116,
                  105,
                  111,
                  110,
                  95,
                  110,
                  102,
                  116,
                  95,
                  97,
                  99,
                  99,
                  111,
                  117,
                  110,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "position_nft_mint"
              }
            ]
          }
        },
        {
          "name": "payer",
          "docs": [
            "Address paying to create the pool. Can be anyone"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "config",
          "docs": [
            "Which config the pool belongs to."
          ]
        },
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "docs": [
            "Initialize an account to store the pool state"
          ],
          "writable": true
        },
        {
          "name": "position",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112,
                  111,
                  115,
                  105,
                  116,
                  105,
                  111,
                  110
                ]
              },
              {
                "kind": "account",
                "path": "position_nft_mint"
              }
            ]
          }
        },
        {
          "name": "token_a_mint",
          "docs": [
            "Token a mint"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "Token b mint"
          ]
        },
        {
          "name": "token_a_vault",
          "docs": [
            "Token a vault for the pool"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  116,
                  111,
                  107,
                  101,
                  110,
                  95,
                  118,
                  97,
                  117,
                  108,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "token_a_mint"
              },
              {
                "kind": "account",
                "path": "pool"
              }
            ]
          }
        },
        {
          "name": "token_b_vault",
          "docs": [
            "Token b vault for the pool"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  116,
                  111,
                  107,
                  101,
                  110,
                  95,
                  118,
                  97,
                  117,
                  108,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "token_b_mint"
              },
              {
                "kind": "account",
                "path": "pool"
              }
            ]
          }
        },
        {
          "name": "payer_token_a",
          "docs": [
            "payer token a account"
          ],
          "writable": true
        },
        {
          "name": "payer_token_b",
          "docs": [
            "creator token b account"
          ],
          "writable": true
        },
        {
          "name": "token_a_program",
          "docs": [
            "Program to create mint account and mint tokens"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Program to create mint account and mint tokens"
          ]
        },
        {
          "name": "token_2022_program",
          "docs": [
            "Program to create NFT mint/token account and transfer for token22 account"
          ],
          "address": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "InitializePoolParameters"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_pool_with_dynamic_config",
      "discriminator": [
        149,
        82,
        72,
        197,
        253,
        252,
        68,
        15
      ],
      "accounts": [
        {
          "name": "creator"
        },
        {
          "name": "position_nft_mint",
          "docs": [
            "position_nft_mint"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "position nft account"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112,
                  111,
                  115,
                  105,
                  116,
                  105,
                  111,
                  110,
                  95,
                  110,
                  102,
                  116,
                  95,
                  97,
                  99,
                  99,
                  111,
                  117,
                  110,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "position_nft_mint"
              }
            ]
          }
        },
        {
          "name": "payer",
          "docs": [
            "Address paying to create the pool. Can be anyone"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "pool_creator_authority",
          "signer": true,
          "relations": [
            "config"
          ]
        },
        {
          "name": "config",
          "docs": [
            "Which config the pool belongs to."
          ]
        },
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "docs": [
            "Initialize an account to store the pool state"
          ],
          "writable": true
        },
        {
          "name": "position",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  112,
                  111,
                  115,
                  105,
                  116,
                  105,
                  111,
                  110
                ]
              },
              {
                "kind": "account",
                "path": "position_nft_mint"
              }
            ]
          }
        },
        {
          "name": "token_a_mint",
          "docs": [
            "Token a mint"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "Token b mint"
          ]
        },
        {
          "name": "token_a_vault",
          "docs": [
            "Token a vault for the pool"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  116,
                  111,
                  107,
                  101,
                  110,
                  95,
                  118,
                  97,
                  117,
                  108,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "token_a_mint"
              },
              {
                "kind": "account",
                "path": "pool"
              }
            ]
          }
        },
        {
          "name": "token_b_vault",
          "docs": [
            "Token b vault for the pool"
          ],
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  116,
                  111,
                  107,
                  101,
                  110,
                  95,
                  118,
                  97,
                  117,
                  108,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "token_b_mint"
              },
              {
                "kind": "account",
                "path": "pool"
              }
            ]
          }
        },
        {
          "name": "payer_token_a",
          "docs": [
            "payer token a account"
          ],
          "writable": true
        },
        {
          "name": "payer_token_b",
          "docs": [
            "creator token b account"
          ],
          "writable": true
        },
        {
          "name": "token_a_program",
          "docs": [
            "Program to create mint account and mint tokens"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Program to create mint account and mint tokens"
          ]
        },
        {
          "name": "token_2022_program",
          "docs": [
            "Program to create NFT mint/token account and transfer for token22 account"
          ],
          "address": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "InitializeCustomizablePoolParameters"
            }
          }
        }
      ]
    },
    {
      "name": "initialize_reward",
      "discriminator": [
        95,
        135,
        192,
        196,
        242,
        129,
        230,
        68
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "reward_vault",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  114,
                  101,
                  119,
                  97,
                  114,
                  100,
                  95,
                  118,
                  97,
                  117,
                  108,
                  116
                ]
              },
              {
                "kind": "account",
                "path": "pool"
              },
              {
                "kind": "arg",
                "path": "reward_index"
              }
            ]
          }
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "signer",
          "signer": true
        },
        {
          "name": "payer",
          "writable": true,
          "signer": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u8"
        },
        {
          "name": "reward_duration",
          "type": "u64"
        },
        {
          "name": "funder",
          "type": "pubkey"
        }
      ]
    },
    {
      "name": "lock_position",
      "discriminator": [
        227,
        62,
        2,
        252,
        247,
        10,
        171,
        185
      ],
      "accounts": [
        {
          "name": "pool",
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "vesting",
          "writable": true,
          "signer": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ]
        },
        {
          "name": "owner",
          "docs": [
            "owner of position"
          ],
          "signer": true
        },
        {
          "name": "payer",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "VestingParameters"
            }
          }
        }
      ]
    },
    {
      "name": "permanent_lock_position",
      "discriminator": [
        165,
        176,
        125,
        6,
        231,
        171,
        186,
        213
      ],
      "accounts": [
        {
          "name": "pool",
          "writable": true,
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ]
        },
        {
          "name": "owner",
          "docs": [
            "owner of position"
          ],
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "permanent_lock_liquidity",
          "type": "u128"
        }
      ]
    },
    {
      "name": "refresh_vesting",
      "discriminator": [
        9,
        94,
        216,
        14,
        116,
        204,
        247,
        0
      ],
      "accounts": [
        {
          "name": "pool",
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ]
        },
        {
          "name": "owner"
        }
      ],
      "args": []
    },
    {
      "name": "remove_all_liquidity",
      "discriminator": [
        10,
        51,
        61,
        35,
        112,
        105,
        24,
        85
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "writable": true,
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "token_a_account",
          "docs": [
            "The user token a account"
          ],
          "writable": true
        },
        {
          "name": "token_b_account",
          "docs": [
            "The user token b account"
          ],
          "writable": true
        },
        {
          "name": "token_a_vault",
          "docs": [
            "The vault token account for input token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_vault",
          "docs": [
            "The vault token account for output token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_mint",
          "docs": [
            "The mint of token a"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "The mint of token b"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ]
        },
        {
          "name": "owner",
          "docs": [
            "owner of position"
          ],
          "signer": true
        },
        {
          "name": "token_a_program",
          "docs": [
            "Token a program"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Token b program"
          ]
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "token_a_amount_threshold",
          "type": "u64"
        },
        {
          "name": "token_b_amount_threshold",
          "type": "u64"
        }
      ]
    },
    {
      "name": "remove_liquidity",
      "discriminator": [
        80,
        85,
        209,
        72,
        24,
        206,
        177,
        108
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "writable": true,
          "relations": [
            "position"
          ]
        },
        {
          "name": "position",
          "writable": true
        },
        {
          "name": "token_a_account",
          "docs": [
            "The user token a account"
          ],
          "writable": true
        },
        {
          "name": "token_b_account",
          "docs": [
            "The user token b account"
          ],
          "writable": true
        },
        {
          "name": "token_a_vault",
          "docs": [
            "The vault token account for input token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_vault",
          "docs": [
            "The vault token account for output token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_mint",
          "docs": [
            "The mint of token a"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "The mint of token b"
          ],
          "relations": [
            "pool"
          ]
        },
        {
          "name": "position_nft_account",
          "docs": [
            "The token account for nft"
          ]
        },
        {
          "name": "owner",
          "docs": [
            "owner of position"
          ],
          "signer": true
        },
        {
          "name": "token_a_program",
          "docs": [
            "Token a program"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Token b program"
          ]
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "RemoveLiquidityParameters"
            }
          }
        }
      ]
    },
    {
      "name": "set_pool_status",
      "discriminator": [
        112,
        87,
        135,
        223,
        83,
        204,
        132,
        53
      ],
      "accounts": [
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "admin",
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "status",
          "type": "u8"
        }
      ]
    },
    {
      "name": "split_position",
      "discriminator": [
        172,
        241,
        221,
        138,
        161,
        29,
        253,
        42
      ],
      "accounts": [
        {
          "name": "pool",
          "writable": true,
          "relations": [
            "first_position",
            "second_position"
          ]
        },
        {
          "name": "first_position",
          "docs": [
            "The first position"
          ],
          "writable": true
        },
        {
          "name": "first_position_nft_account",
          "docs": [
            "The token account for position nft"
          ]
        },
        {
          "name": "second_position",
          "docs": [
            "The second position"
          ],
          "writable": true
        },
        {
          "name": "second_position_nft_account",
          "docs": [
            "The token account for position nft"
          ]
        },
        {
          "name": "first_owner",
          "docs": [
            "Owner of first position"
          ],
          "signer": true
        },
        {
          "name": "second_owner",
          "docs": [
            "Owner of second position"
          ],
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "SplitPositionParameters"
            }
          }
        }
      ]
    },
    {
      "name": "split_position2",
      "discriminator": [
        221,
        147,
        228,
        207,
        140,
        212,
        17,
        119
      ],
      "accounts": [
        {
          "name": "pool",
          "writable": true,
          "relations": [
            "first_position",
            "second_position"
          ]
        },
        {
          "name": "first_position",
          "docs": [
            "The first position"
          ],
          "writable": true
        },
        {
          "name": "first_position_nft_account",
          "docs": [
            "The token account for position nft"
          ]
        },
        {
          "name": "second_position",
          "docs": [
            "The second position"
          ],
          "writable": true
        },
        {
          "name": "second_position_nft_account",
          "docs": [
            "The token account for position nft"
          ]
        },
        {
          "name": "first_owner",
          "docs": [
            "Owner of first position"
          ],
          "signer": true
        },
        {
          "name": "second_owner",
          "docs": [
            "Owner of second position"
          ],
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "numerator",
          "type": "u32"
        }
      ]
    },
    {
      "name": "swap",
      "discriminator": [
        248,
        198,
        158,
        145,
        225,
        117,
        135,
        200
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "docs": [
            "Pool account"
          ],
          "writable": true
        },
        {
          "name": "input_token_account",
          "docs": [
            "The user token account for input token"
          ],
          "writable": true
        },
        {
          "name": "output_token_account",
          "docs": [
            "The user token account for output token"
          ],
          "writable": true
        },
        {
          "name": "token_a_vault",
          "docs": [
            "The vault token account for input token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_b_vault",
          "docs": [
            "The vault token account for output token"
          ],
          "writable": true,
          "relations": [
            "pool"
          ]
        },
        {
          "name": "token_a_mint",
          "docs": [
            "The mint of token a"
          ]
        },
        {
          "name": "token_b_mint",
          "docs": [
            "The mint of token b"
          ]
        },
        {
          "name": "payer",
          "docs": [
            "The user performing the swap"
          ],
          "signer": true
        },
        {
          "name": "token_a_program",
          "docs": [
            "Token a program"
          ]
        },
        {
          "name": "token_b_program",
          "docs": [
            "Token b program"
          ]
        },
        {
          "name": "referral_token_account",
          "docs": [
            "referral token account"
          ],
          "writable": true,
          "optional": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "params",
          "type": {
            "defined": {
              "name": "SwapParameters"
            }
          }
        }
      ]
    },
    {
      "name": "update_reward_duration",
      "discriminator": [
        138,
        174,
        196,
        169,
        213,
        235,
        254,
        107
      ],
      "accounts": [
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "signer",
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u8"
        },
        {
          "name": "new_duration",
          "type": "u64"
        }
      ]
    },
    {
      "name": "update_reward_funder",
      "discriminator": [
        211,
        28,
        48,
        32,
        215,
        160,
        35,
        23
      ],
      "accounts": [
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "signer",
          "signer": true
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u8"
        },
        {
          "name": "new_funder",
          "type": "pubkey"
        }
      ]
    },
    {
      "name": "withdraw_ineligible_reward",
      "discriminator": [
        148,
        206,
        42,
        195,
        247,
        49,
        103,
        8
      ],
      "accounts": [
        {
          "name": "pool_authority",
          "address": "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"
        },
        {
          "name": "pool",
          "writable": true
        },
        {
          "name": "reward_vault",
          "writable": true
        },
        {
          "name": "reward_mint"
        },
        {
          "name": "funder_token_account",
          "writable": true
        },
        {
          "name": "funder",
          "signer": true
        },
        {
          "name": "token_program"
        },
        {
          "name": "event_authority",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  95,
                  95,
                  101,
                  118,
                  101,
                  110,
                  116,
                  95,
                  97,
                  117,
                  116,
                  104,
                  111,
                  114,
                  105,
                  116,
                  121
                ]
              }
            ]
          }
        },
        {
          "name": "program"
        }
      ],
      "args": [
        {
          "name": "reward_index",
          "type": "u8"
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "ClaimFeeOperator",
      "discriminator": [
        166,
        48,
        134,
        86,
        34,
        200,
        188,
        150
      ]
    },
    {
      "name": "settings",
      "discriminator": [
        155,
        12,
        170,
        224,
        30,
        250,
        204,
        130
      ]
    },
    {
      "name": "Pool",
      "discriminator": [
        241,
        154,
        109,
        4,
        17,
        177,
        109,
        188
      ]
    },
    {
      "name": "Position",
      "discriminator": [
        170,
        188,
        143,
        228,
        122,
        64,
        247,
        208
      ]
    },
    {
      "name": "TokenBadge",
      "discriminator": [
        116,
        219,
        204,
        229,
        249,
        116,
        255,
        150
      ]
    },
    {
      "name": "Vesting",
      "discriminator": [
        100,
        149,
        66,
        138,
        95,
        200,
        128,
        241
      ]
    }
  ],
  "events": [
    {
      "name": "EvtAddLiquidity",
      "discriminator": [
        175,
        242,
        8,
        157,
        30,
        247,
        185,
        169
      ]
    },
    {
      "name": "EvtClaimPartnerFee",
      "discriminator": [
        118,
        99,
        77,
        10,
        226,
        1,
        1,
        87
      ]
    },
    {
      "name": "EvtClaimPositionFee",
      "discriminator": [
        198,
        182,
        183,
        52,
        97,
        12,
        49,
        56
      ]
    },
    {
      "name": "EvtClaimProtocolFee",
      "discriminator": [
        186,
        244,
        75,
        251,
        188,
        13,
        25,
        33
      ]
    },
    {
      "name": "EvtClaimReward",
      "discriminator": [
        218,
        86,
        147,
        200,
        235,
        188,
        215,
        231
      ]
    },
    {
      "name": "EvtCloseClaimFeeOperator",
      "discriminator": [
        111,
        39,
        37,
        55,
        110,
        216,
        194,
        23
      ]
    },
    {
      "name": "EvtCloseConfig",
      "discriminator": [
        36,
        30,
        239,
        45,
        58,
        132,
        14,
        5
      ]
    },
    {
      "name": "EvtClosePosition",
      "discriminator": [
        20,
        145,
        144,
        68,
        143,
        142,
        214,
        178
      ]
    },
    {
      "name": "EvtCreateClaimFeeOperator",
      "discriminator": [
        21,
        6,
        153,
        120,
        68,
        116,
        28,
        177
      ]
    },
    {
      "name": "EvtCreateConfig",
      "discriminator": [
        131,
        207,
        180,
        174,
        180,
        73,
        165,
        54
      ]
    },
    {
      "name": "EvtCreateDynamicConfig",
      "discriminator": [
        231,
        197,
        13,
        164,
        248,
        213,
        133,
        152
      ]
    },
    {
      "name": "EvtCreatePosition",
      "discriminator": [
        156,
        15,
        119,
        198,
        29,
        181,
        221,
        55
      ]
    },
    {
      "name": "EvtCreateTokenBadge",
      "discriminator": [
        141,
        120,
        134,
        116,
        34,
        28,
        114,
        160
      ]
    },
    {
      "name": "EvtFundReward",
      "discriminator": [
        104,
        233,
        237,
        122,
        199,
        191,
        121,
        85
      ]
    },
    {
      "name": "EvtInitializePool",
      "discriminator": [
        228,
        50,
        246,
        85,
        203,
        66,
        134,
        37
      ]
    },
    {
      "name": "EvtInitializeReward",
      "discriminator": [
        129,
        91,
        188,
        3,
        246,
        52,
        185,
        249
      ]
    },
    {
      "name": "EvtLockPosition",
      "discriminator": [
        168,
        63,
        108,
        83,
        219,
        82,
        2,
        200
      ]
    },
    {
      "name": "EvtPermanentLockPosition",
      "discriminator": [
        145,
        143,
        162,
        218,
        218,
        80,
        67,
        11
      ]
    },
    {
      "name": "EvtRemoveLiquidity",
      "discriminator": [
        87,
        46,
        88,
        98,
        175,
        96,
        34,
        91
      ]
    },
    {
      "name": "EvtSetPoolStatus",
      "discriminator": [
        100,
        213,
        74,
        3,
        95,
        91,
        228,
        146
      ]
    },
    {
      "name": "EvtSplitPosition2",
      "discriminator": [
        165,
        32,
        203,
        174,
        72,
        100,
        233,
        103
      ]
    },
    {
      "name": "EvtSwap",
      "discriminator": [
        27,
        60,
        21,
        213,
        138,
        170,
        187,
        147
      ]
    },
    {
      "name": "EvtUpdateRewardDuration",
      "discriminator": [
        149,
        135,
        65,
        231,
        129,
        153,
        65,
        57
      ]
    },
    {
      "name": "EvtUpdateRewardFunder",
      "discriminator": [
        76,
        154,
        208,
        13,
        40,
        115,
        246,
        146
      ]
    },
    {
      "name": "EvtWithdrawIneligibleReward",
      "discriminator": [
        248,
        215,
        184,
        78,
        31,
        180,
        179,
        168
      ]
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "MathOverflow",
      "msg": "Math operation overflow"
    },
    {
      "code": 6001,
      "name": "InvalidFee",
      "msg": "Invalid fee setup"
    },
    {
      "code": 6002,
      "name": "ExceededSlippage",
      "msg": "Exceeded slippage tolerance"
    },
    {
      "code": 6003,
      "name": "PoolDisabled",
      "msg": "Pool disabled"
    },
    {
      "code": 6004,
      "name": "ExceedMaxFeeBps",
      "msg": "Exceeded max fee bps"
    },
    {
      "code": 6005,
      "name": "InvalidAdmin",
      "msg": "Invalid admin"
    },
    {
      "code": 6006,
      "name": "AmountIsZero",
      "msg": "Amount is zero"
    },
    {
      "code": 6007,
      "name": "TypeCastFailed",
      "msg": "Type cast error"
    },
    {
      "code": 6008,
      "name": "UnableToModifyActivationPoint",
      "msg": "Unable to modify activation point"
    },
    {
      "code": 6009,
      "name": "InvalidAuthorityToCreateThePool",
      "msg": "Invalid authority to create the pool"
    },
    {
      "code": 6010,
      "name": "InvalidActivationType",
      "msg": "Invalid activation type"
    },
    {
      "code": 6011,
      "name": "InvalidActivationPoint",
      "msg": "Invalid activation point"
    },
    {
      "code": 6012,
      "name": "InvalidQuoteMint",
      "msg": "Quote token must be SOL,USDC"
    },
    {
      "code": 6013,
      "name": "InvalidFeeCurve",
      "msg": "Invalid fee curve"
    },
    {
      "code": 6014,
      "name": "InvalidPriceRange",
      "msg": "Invalid Price Range"
    },
    {
      "code": 6015,
      "name": "PriceRangeViolation",
      "msg": "Trade is over price range"
    },
    {
      "code": 6016,
      "name": "InvalidParameters",
      "msg": "Invalid parameters"
    },
    {
      "code": 6017,
      "name": "InvalidCollectFeeMode",
      "msg": "Invalid collect fee mode"
    },
    {
      "code": 6018,
      "name": "InvalidInput",
      "msg": "Invalid input"
    },
    {
      "code": 6019,
      "name": "CannotCreateTokenBadgeOnSupportedMint",
      "msg": "Cannot create token badge on supported mint"
    },
    {
      "code": 6020,
      "name": "InvalidTokenBadge",
      "msg": "Invalid token badge"
    },
    {
      "code": 6021,
      "name": "InvalidMinimumLiquidity",
      "msg": "Invalid minimum liquidity"
    },
    {
      "code": 6022,
      "name": "InvalidVestingInfo",
      "msg": "Invalid vesting information"
    },
    {
      "code": 6023,
      "name": "InsufficientLiquidity",
      "msg": "Insufficient liquidity"
    },
    {
      "code": 6024,
      "name": "InvalidVestingAccount",
      "msg": "Invalid vesting account"
    },
    {
      "code": 6025,
      "name": "InvalidPoolStatus",
      "msg": "Invalid pool status"
    },
    {
      "code": 6026,
      "name": "UnsupportNativeMintToken2022",
      "msg": "Unsupported native mint token2022"
    },
    {
      "code": 6027,
      "name": "InvalidRewardIndex",
      "msg": "Invalid reward index"
    },
    {
      "code": 6028,
      "name": "InvalidRewardDuration",
      "msg": "Invalid reward duration"
    },
    {
      "code": 6029,
      "name": "RewardInitialized",
      "msg": "Reward already initialized"
    },
    {
      "code": 6030,
      "name": "RewardUninitialized",
      "msg": "Reward not initialized"
    },
    {
      "code": 6031,
      "name": "InvalidRewardVault",
      "msg": "Invalid reward vault"
    },
    {
      "code": 6032,
      "name": "MustWithdrawnIneligibleReward",
      "msg": "Must withdraw ineligible reward"
    },
    {
      "code": 6033,
      "name": "IdenticalRewardDuration",
      "msg": "Reward duration is the same"
    },
    {
      "code": 6034,
      "name": "RewardCampaignInProgress",
      "msg": "Reward campaign in progress"
    },
    {
      "code": 6035,
      "name": "IdenticalFunder",
      "msg": "Identical funder"
    },
    {
      "code": 6036,
      "name": "InvalidFunder",
      "msg": "Invalid funder"
    },
    {
      "code": 6037,
      "name": "RewardNotEnded",
      "msg": "Reward not ended"
    },
    {
      "code": 6038,
      "name": "FeeInverseIsIncorrect",
      "msg": "Fee inverse is incorrect"
    },
    {
      "code": 6039,
      "name": "PositionIsNotEmpty",
      "msg": "Position is not empty"
    },
    {
      "code": 6040,
      "name": "InvalidPoolCreatorAuthority",
      "msg": "Invalid pool creator authority"
    },
    {
      "code": 6041,
      "name": "InvalidConfigType",
      "msg": "Invalid config type"
    },
    {
      "code": 6042,
      "name": "InvalidPoolCreator",
      "msg": "Invalid pool creator"
    },
    {
      "code": 6043,
      "name": "RewardVaultFrozenSkipRequired",
      "msg": "Reward vault is frozen, must skip reward to proceed"
    },
    {
      "code": 6044,
      "name": "InvalidSplitPositionParameters",
      "msg": "Invalid parameters for split position"
    },
    {
      "code": 6045,
      "name": "UnsupportPositionHasVestingLock",
      "msg": "Unsupported split position has vesting lock"
    },
    {
      "code": 6046,
      "name": "SamePosition",
      "msg": "Same position"
    }
  ],
  "types": [
    {
      "name": "AddLiquidityParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "liquidity_delta",
            "docs": [
              "delta liquidity"
            ],
            "type": "u128"
          },
          {
            "name": "token_a_amount_threshold",
            "docs": [
              "maximum token a amount"
            ],
            "type": "u64"
          },
          {
            "name": "token_b_amount_threshold",
            "docs": [
              "maximum token b amount"
            ],
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "BaseFeeConfig",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "cliff_fee_numerator",
            "type": "u64"
          },
          {
            "name": "fee_scheduler_mode",
            "type": "u8"
          },
          {
            "name": "padding",
            "type": {
              "array": [
                "u8",
                5
              ]
            }
          },
          {
            "name": "number_of_period",
            "type": "u16"
          },
          {
            "name": "period_frequency",
            "type": "u64"
          },
          {
            "name": "reduction_factor",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "BaseFeeParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "cliff_fee_numerator",
            "type": "u64"
          },
          {
            "name": "number_of_period",
            "type": "u16"
          },
          {
            "name": "period_frequency",
            "type": "u64"
          },
          {
            "name": "reduction_factor",
            "type": "u64"
          },
          {
            "name": "fee_scheduler_mode",
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "BaseFeeStruct",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "cliff_fee_numerator",
            "type": "u64"
          },
          {
            "name": "fee_scheduler_mode",
            "type": "u8"
          },
          {
            "name": "padding_0",
            "type": {
              "array": [
                "u8",
                5
              ]
            }
          },
          {
            "name": "number_of_period",
            "type": "u16"
          },
          {
            "name": "period_frequency",
            "type": "u64"
          },
          {
            "name": "reduction_factor",
            "type": "u64"
          },
          {
            "name": "padding_1",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "ClaimFeeOperator",
      "docs": [
        "Parameter that set by the protocol"
      ],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "operator",
            "docs": [
              "operator"
            ],
            "type": "pubkey"
          },
          {
            "name": "_padding",
            "docs": [
              "Reserve"
            ],
            "type": {
              "array": [
                "u8",
                128
              ]
            }
          }
        ]
      }
    },
    {
      "name": "settings",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "vault_config_key",
            "docs": [
              "Vault config key"
            ],
            "type": "pubkey"
          },
          {
            "name": "pool_creator_authority",
            "docs": [
              "Only pool_creator_authority can use the current config to initialize new pool. When it's Pubkey::default, it's a public config."
            ],
            "type": "pubkey"
          },
          {
            "name": "pool_fees",
            "docs": [
              "Pool fee"
            ],
            "type": {
              "defined": {
                "name": "PoolFeesConfig"
              }
            }
          },
          {
            "name": "activation_type",
            "docs": [
              "Activation type"
            ],
            "type": "u8"
          },
          {
            "name": "collect_fee_mode",
            "docs": [
              "Collect fee mode"
            ],
            "type": "u8"
          },
          {
            "name": "config_type",
            "docs": [
              "settings type mode, 0 for static, 1 for dynamic"
            ],
            "type": "u8"
          },
          {
            "name": "_padding_0",
            "docs": [
              "padding 0"
            ],
            "type": {
              "array": [
                "u8",
                5
              ]
            }
          },
          {
            "name": "index",
            "docs": [
              "config index"
            ],
            "type": "u64"
          },
          {
            "name": "sqrt_min_price",
            "docs": [
              "sqrt min price"
            ],
            "type": "u128"
          },
          {
            "name": "sqrt_max_price",
            "docs": [
              "sqrt max price"
            ],
            "type": "u128"
          },
          {
            "name": "_padding_1",
            "docs": [
              "Fee curve point",
              "Padding for further use"
            ],
            "type": {
              "array": [
                "u64",
                10
              ]
            }
          }
        ]
      }
    },
    {
      "name": "DynamicConfigParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool_creator_authority",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "DynamicFeeConfig",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "initialized",
            "type": "u8"
          },
          {
            "name": "padding",
            "type": {
              "array": [
                "u8",
                7
              ]
            }
          },
          {
            "name": "max_volatility_accumulator",
            "type": "u32"
          },
          {
            "name": "variable_fee_control",
            "type": "u32"
          },
          {
            "name": "bin_step",
            "type": "u16"
          },
          {
            "name": "filter_period",
            "type": "u16"
          },
          {
            "name": "decay_period",
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "type": "u16"
          },
          {
            "name": "padding_1",
            "type": {
              "array": [
                "u8",
                8
              ]
            }
          },
          {
            "name": "bin_step_u128",
            "type": "u128"
          }
        ]
      }
    },
    {
      "name": "DynamicFeeParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "bin_step",
            "type": "u16"
          },
          {
            "name": "bin_step_u128",
            "type": "u128"
          },
          {
            "name": "filter_period",
            "type": "u16"
          },
          {
            "name": "decay_period",
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "type": "u16"
          },
          {
            "name": "max_volatility_accumulator",
            "type": "u32"
          },
          {
            "name": "variable_fee_control",
            "type": "u32"
          }
        ]
      }
    },
    {
      "name": "DynamicFeeStruct",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "initialized",
            "type": "u8"
          },
          {
            "name": "padding",
            "type": {
              "array": [
                "u8",
                7
              ]
            }
          },
          {
            "name": "max_volatility_accumulator",
            "type": "u32"
          },
          {
            "name": "variable_fee_control",
            "type": "u32"
          },
          {
            "name": "bin_step",
            "type": "u16"
          },
          {
            "name": "filter_period",
            "type": "u16"
          },
          {
            "name": "decay_period",
            "type": "u16"
          },
          {
            "name": "reduction_factor",
            "type": "u16"
          },
          {
            "name": "last_update_timestamp",
            "type": "u64"
          },
          {
            "name": "bin_step_u128",
            "type": "u128"
          },
          {
            "name": "sqrt_price_reference",
            "type": "u128"
          },
          {
            "name": "volatility_accumulator",
            "type": "u128"
          },
          {
            "name": "volatility_reference",
            "type": "u128"
          }
        ]
      }
    },
    {
      "name": "EvtAddLiquidity",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "params",
            "type": {
              "defined": {
                "name": "AddLiquidityParameters"
              }
            }
          },
          {
            "name": "token_a_amount",
            "type": "u64"
          },
          {
            "name": "token_b_amount",
            "type": "u64"
          },
          {
            "name": "total_amount_a",
            "type": "u64"
          },
          {
            "name": "total_amount_b",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtClaimPartnerFee",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "token_a_amount",
            "type": "u64"
          },
          {
            "name": "token_b_amount",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtClaimPositionFee",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "fee_a_claimed",
            "type": "u64"
          },
          {
            "name": "fee_b_claimed",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtClaimProtocolFee",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "token_a_amount",
            "type": "u64"
          },
          {
            "name": "token_b_amount",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtClaimReward",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "mint_reward",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u8"
          },
          {
            "name": "total_reward",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtCloseClaimFeeOperator",
      "docs": [
        "Close claim fee operator"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "claim_fee_operator",
            "type": "pubkey"
          },
          {
            "name": "operator",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "EvtCloseConfig",
      "docs": [
        "Close config"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "config",
            "docs": [
              "settings pubkey"
            ],
            "type": "pubkey"
          },
          {
            "name": "admin",
            "docs": [
              "admin pk"
            ],
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "EvtClosePosition",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "position_nft_mint",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "EvtCreateClaimFeeOperator",
      "docs": [
        "Create claim fee operator"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "operator",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "EvtCreateConfig",
      "docs": [
        "Create static config"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool_fees",
            "type": {
              "defined": {
                "name": "PoolFeeParameters"
              }
            }
          },
          {
            "name": "vault_config_key",
            "type": "pubkey"
          },
          {
            "name": "pool_creator_authority",
            "type": "pubkey"
          },
          {
            "name": "activation_type",
            "type": "u8"
          },
          {
            "name": "sqrt_min_price",
            "type": "u128"
          },
          {
            "name": "sqrt_max_price",
            "type": "u128"
          },
          {
            "name": "collect_fee_mode",
            "type": "u8"
          },
          {
            "name": "index",
            "type": "u64"
          },
          {
            "name": "config",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "EvtCreateDynamicConfig",
      "docs": [
        "Create dynamic config"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "config",
            "type": "pubkey"
          },
          {
            "name": "pool_creator_authority",
            "type": "pubkey"
          },
          {
            "name": "index",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtCreatePosition",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "position_nft_mint",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "EvtCreateTokenBadge",
      "docs": [
        "Create token badge"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "token_mint",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "EvtFundReward",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "funder",
            "type": "pubkey"
          },
          {
            "name": "mint_reward",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u8"
          },
          {
            "name": "amount",
            "type": "u64"
          },
          {
            "name": "transfer_fee_excluded_amount_in",
            "type": "u64"
          },
          {
            "name": "reward_duration_end",
            "type": "u64"
          },
          {
            "name": "pre_reward_rate",
            "type": "u128"
          },
          {
            "name": "post_reward_rate",
            "type": "u128"
          }
        ]
      }
    },
    {
      "name": "EvtInitializePool",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "token_a_mint",
            "type": "pubkey"
          },
          {
            "name": "token_b_mint",
            "type": "pubkey"
          },
          {
            "name": "creator",
            "type": "pubkey"
          },
          {
            "name": "payer",
            "type": "pubkey"
          },
          {
            "name": "alpha_vault",
            "type": "pubkey"
          },
          {
            "name": "pool_fees",
            "type": {
              "defined": {
                "name": "PoolFeeParameters"
              }
            }
          },
          {
            "name": "sqrt_min_price",
            "type": "u128"
          },
          {
            "name": "sqrt_max_price",
            "type": "u128"
          },
          {
            "name": "activation_type",
            "type": "u8"
          },
          {
            "name": "collect_fee_mode",
            "type": "u8"
          },
          {
            "name": "liquidity",
            "type": "u128"
          },
          {
            "name": "sqrt_price",
            "type": "u128"
          },
          {
            "name": "activation_point",
            "type": "u64"
          },
          {
            "name": "token_a_flag",
            "type": "u8"
          },
          {
            "name": "token_b_flag",
            "type": "u8"
          },
          {
            "name": "token_a_amount",
            "type": "u64"
          },
          {
            "name": "token_b_amount",
            "type": "u64"
          },
          {
            "name": "total_amount_a",
            "type": "u64"
          },
          {
            "name": "total_amount_b",
            "type": "u64"
          },
          {
            "name": "pool_type",
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "EvtInitializeReward",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "reward_mint",
            "type": "pubkey"
          },
          {
            "name": "funder",
            "type": "pubkey"
          },
          {
            "name": "creator",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u8"
          },
          {
            "name": "reward_duration",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtLockPosition",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "vesting",
            "type": "pubkey"
          },
          {
            "name": "cliff_point",
            "type": "u64"
          },
          {
            "name": "period_frequency",
            "type": "u64"
          },
          {
            "name": "cliff_unlock_liquidity",
            "type": "u128"
          },
          {
            "name": "liquidity_per_period",
            "type": "u128"
          },
          {
            "name": "number_of_period",
            "type": "u16"
          }
        ]
      }
    },
    {
      "name": "EvtPermanentLockPosition",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "lock_liquidity_amount",
            "type": "u128"
          },
          {
            "name": "total_permanent_locked_liquidity",
            "type": "u128"
          }
        ]
      }
    },
    {
      "name": "EvtRemoveLiquidity",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "owner",
            "type": "pubkey"
          },
          {
            "name": "params",
            "type": {
              "defined": {
                "name": "RemoveLiquidityParameters"
              }
            }
          },
          {
            "name": "token_a_amount",
            "type": "u64"
          },
          {
            "name": "token_b_amount",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtSetPoolStatus",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "status",
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "EvtSplitPosition2",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "first_owner",
            "type": "pubkey"
          },
          {
            "name": "second_owner",
            "type": "pubkey"
          },
          {
            "name": "first_position",
            "type": "pubkey"
          },
          {
            "name": "second_position",
            "type": "pubkey"
          },
          {
            "name": "current_sqrt_price",
            "type": "u128"
          },
          {
            "name": "amount_splits",
            "type": {
              "defined": {
                "name": "SplitAmountInfo"
              }
            }
          },
          {
            "name": "first_position_info",
            "type": {
              "defined": {
                "name": "SplitPositionInfo"
              }
            }
          },
          {
            "name": "second_position_info",
            "type": {
              "defined": {
                "name": "SplitPositionInfo"
              }
            }
          },
          {
            "name": "split_position_parameters",
            "type": {
              "defined": {
                "name": "SplitPositionParameters2"
              }
            }
          }
        ]
      }
    },
    {
      "name": "EvtSwap",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "trade_direction",
            "type": "u8"
          },
          {
            "name": "has_referral",
            "type": "bool"
          },
          {
            "name": "params",
            "type": {
              "defined": {
                "name": "SwapParameters"
              }
            }
          },
          {
            "name": "swap_result",
            "type": {
              "defined": {
                "name": "SwapResult"
              }
            }
          },
          {
            "name": "actual_amount_in",
            "type": "u64"
          },
          {
            "name": "current_timestamp",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtUpdateRewardDuration",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u8"
          },
          {
            "name": "old_reward_duration",
            "type": "u64"
          },
          {
            "name": "new_reward_duration",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "EvtUpdateRewardFunder",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "reward_index",
            "type": "u8"
          },
          {
            "name": "old_funder",
            "type": "pubkey"
          },
          {
            "name": "new_funder",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "EvtWithdrawIneligibleReward",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "reward_mint",
            "type": "pubkey"
          },
          {
            "name": "amount",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "InitializeCustomizablePoolParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool_fees",
            "docs": [
              "pool fees"
            ],
            "type": {
              "defined": {
                "name": "PoolFeeParameters"
              }
            }
          },
          {
            "name": "sqrt_min_price",
            "docs": [
              "sqrt min price"
            ],
            "type": "u128"
          },
          {
            "name": "sqrt_max_price",
            "docs": [
              "sqrt max price"
            ],
            "type": "u128"
          },
          {
            "name": "has_alpha_vault",
            "docs": [
              "has alpha vault"
            ],
            "type": "bool"
          },
          {
            "name": "liquidity",
            "docs": [
              "initialize liquidity"
            ],
            "type": "u128"
          },
          {
            "name": "sqrt_price",
            "docs": [
              "The init price of the pool as a sqrt(token_b/token_a) Q64.64 value"
            ],
            "type": "u128"
          },
          {
            "name": "activation_type",
            "docs": [
              "activation type"
            ],
            "type": "u8"
          },
          {
            "name": "collect_fee_mode",
            "docs": [
              "collect fee mode"
            ],
            "type": "u8"
          },
          {
            "name": "activation_point",
            "docs": [
              "activation point"
            ],
            "type": {
              "option": "u64"
            }
          }
        ]
      }
    },
    {
      "name": "InitializePoolParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "liquidity",
            "docs": [
              "initialize liquidity"
            ],
            "type": "u128"
          },
          {
            "name": "sqrt_price",
            "docs": [
              "The init price of the pool as a sqrt(token_b/token_a) Q64.64 value"
            ],
            "type": "u128"
          },
          {
            "name": "activation_point",
            "docs": [
              "activation point"
            ],
            "type": {
              "option": "u64"
            }
          }
        ]
      }
    },
    {
      "name": "Pool",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool_fees",
            "docs": [
              "Pool fee"
            ],
            "type": {
              "defined": {
                "name": "PoolFeesStruct"
              }
            }
          },
          {
            "name": "token_a_mint",
            "docs": [
              "token a mint"
            ],
            "type": "pubkey"
          },
          {
            "name": "token_b_mint",
            "docs": [
              "token b mint"
            ],
            "type": "pubkey"
          },
          {
            "name": "token_a_vault",
            "docs": [
              "token a vault"
            ],
            "type": "pubkey"
          },
          {
            "name": "token_b_vault",
            "docs": [
              "token b vault"
            ],
            "type": "pubkey"
          },
          {
            "name": "whitelisted_vault",
            "docs": [
              "Whitelisted vault to be able to buy pool before activation_point"
            ],
            "type": "pubkey"
          },
          {
            "name": "partner",
            "docs": [
              "partner"
            ],
            "type": "pubkey"
          },
          {
            "name": "liquidity",
            "docs": [
              "liquidity share"
            ],
            "type": "u128"
          },
          {
            "name": "_padding",
            "docs": [
              "padding, previous reserve amount, be careful to use that field"
            ],
            "type": "u128"
          },
          {
            "name": "protocol_a_fee",
            "docs": [
              "protocol a fee"
            ],
            "type": "u64"
          },
          {
            "name": "protocol_b_fee",
            "docs": [
              "protocol b fee"
            ],
            "type": "u64"
          },
          {
            "name": "partner_a_fee",
            "docs": [
              "partner a fee"
            ],
            "type": "u64"
          },
          {
            "name": "partner_b_fee",
            "docs": [
              "partner b fee"
            ],
            "type": "u64"
          },
          {
            "name": "sqrt_min_price",
            "docs": [
              "min price"
            ],
            "type": "u128"
          },
          {
            "name": "sqrt_max_price",
            "docs": [
              "max price"
            ],
            "type": "u128"
          },
          {
            "name": "sqrt_price",
            "docs": [
              "current price"
            ],
            "type": "u128"
          },
          {
            "name": "activation_point",
            "docs": [
              "Activation point, can be slot or timestamp"
            ],
            "type": "u64"
          },
          {
            "name": "activation_type",
            "docs": [
              "Activation type, 0 means by slot, 1 means by timestamp"
            ],
            "type": "u8"
          },
          {
            "name": "pool_status",
            "docs": [
              "pool status, 0: enable, 1 disable"
            ],
            "type": "u8"
          },
          {
            "name": "token_a_flag",
            "docs": [
              "token a flag"
            ],
            "type": "u8"
          },
          {
            "name": "token_b_flag",
            "docs": [
              "token b flag"
            ],
            "type": "u8"
          },
          {
            "name": "collect_fee_mode",
            "docs": [
              "0 is collect fee in both token, 1 only collect fee in token a, 2 only collect fee in token b"
            ],
            "type": "u8"
          },
          {
            "name": "pool_type",
            "docs": [
              "pool type"
            ],
            "type": "u8"
          },
          {
            "name": "_padding_0",
            "docs": [
              "padding"
            ],
            "type": {
              "array": [
                "u8",
                2
              ]
            }
          },
          {
            "name": "fee_a_per_liquidity",
            "docs": [
              "cumulative"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "fee_b_per_liquidity",
            "docs": [
              "cumulative"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "permanent_lock_liquidity",
            "type": "u128"
          },
          {
            "name": "metrics",
            "docs": [
              "metrics"
            ],
            "type": {
              "defined": {
                "name": "PoolMetrics"
              }
            }
          },
          {
            "name": "creator",
            "docs": [
              "pool creator"
            ],
            "type": "pubkey"
          },
          {
            "name": "_padding_1",
            "docs": [
              "Padding for further use"
            ],
            "type": {
              "array": [
                "u64",
                6
              ]
            }
          },
          {
            "name": "reward_infos",
            "docs": [
              "Farming reward information"
            ],
            "type": {
              "array": [
                {
                  "defined": {
                    "name": "RewardInfo"
                  }
                },
                2
              ]
            }
          }
        ]
      }
    },
    {
      "name": "PoolFeeParameters",
      "docs": [
        "Information regarding fee charges"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "base_fee",
            "docs": [
              "Base fee"
            ],
            "type": {
              "defined": {
                "name": "BaseFeeParameters"
              }
            }
          },
          {
            "name": "padding",
            "docs": [
              "padding"
            ],
            "type": {
              "array": [
                "u8",
                3
              ]
            }
          },
          {
            "name": "dynamic_fee",
            "docs": [
              "dynamic fee"
            ],
            "type": {
              "option": {
                "defined": {
                  "name": "DynamicFeeParameters"
                }
              }
            }
          }
        ]
      }
    },
    {
      "name": "PoolFeesConfig",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "base_fee",
            "type": {
              "defined": {
                "name": "BaseFeeConfig"
              }
            }
          },
          {
            "name": "dynamic_fee",
            "type": {
              "defined": {
                "name": "DynamicFeeConfig"
              }
            }
          },
          {
            "name": "protocol_fee_percent",
            "type": "u8"
          },
          {
            "name": "partner_fee_percent",
            "type": "u8"
          },
          {
            "name": "referral_fee_percent",
            "type": "u8"
          },
          {
            "name": "padding_0",
            "type": {
              "array": [
                "u8",
                5
              ]
            }
          },
          {
            "name": "padding_1",
            "type": {
              "array": [
                "u64",
                5
              ]
            }
          }
        ]
      }
    },
    {
      "name": "PoolFeesStruct",
      "docs": [
        "Information regarding fee charges",
        "trading_fee = amount * trade_fee_numerator / denominator",
        "protocol_fee = trading_fee * protocol_fee_percentage / 100",
        "referral_fee = protocol_fee * referral_percentage / 100",
        "partner_fee = (protocol_fee - referral_fee) * partner_fee_percentage / denominator"
      ],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "base_fee",
            "docs": [
              "Trade fees are extra token amounts that are held inside the token",
              "accounts during a trade, making the value of liquidity tokens rise.",
              "Trade fee numerator"
            ],
            "type": {
              "defined": {
                "name": "BaseFeeStruct"
              }
            }
          },
          {
            "name": "protocol_fee_percent",
            "docs": [
              "Protocol trading fees are extra token amounts that are held inside the token",
              "accounts during a trade, with the equivalent in pool tokens minted to",
              "the protocol of the program.",
              "Protocol trade fee numerator"
            ],
            "type": "u8"
          },
          {
            "name": "partner_fee_percent",
            "docs": [
              "partner fee"
            ],
            "type": "u8"
          },
          {
            "name": "referral_fee_percent",
            "docs": [
              "referral fee"
            ],
            "type": "u8"
          },
          {
            "name": "padding_0",
            "docs": [
              "padding"
            ],
            "type": {
              "array": [
                "u8",
                5
              ]
            }
          },
          {
            "name": "dynamic_fee",
            "docs": [
              "dynamic fee"
            ],
            "type": {
              "defined": {
                "name": "DynamicFeeStruct"
              }
            }
          },
          {
            "name": "padding_1",
            "docs": [
              "padding"
            ],
            "type": {
              "array": [
                "u64",
                2
              ]
            }
          }
        ]
      }
    },
    {
      "name": "PoolMetrics",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "total_lp_a_fee",
            "type": "u128"
          },
          {
            "name": "total_lp_b_fee",
            "type": "u128"
          },
          {
            "name": "total_protocol_a_fee",
            "type": "u64"
          },
          {
            "name": "total_protocol_b_fee",
            "type": "u64"
          },
          {
            "name": "total_partner_a_fee",
            "type": "u64"
          },
          {
            "name": "total_partner_b_fee",
            "type": "u64"
          },
          {
            "name": "total_position",
            "type": "u64"
          },
          {
            "name": "padding",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "Position",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool",
            "type": "pubkey"
          },
          {
            "name": "nft_mint",
            "docs": [
              "nft mint"
            ],
            "type": "pubkey"
          },
          {
            "name": "fee_a_per_token_checkpoint",
            "docs": [
              "fee a checkpoint"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "fee_b_per_token_checkpoint",
            "docs": [
              "fee b checkpoint"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "fee_a_pending",
            "docs": [
              "fee a pending"
            ],
            "type": "u64"
          },
          {
            "name": "fee_b_pending",
            "docs": [
              "fee b pending"
            ],
            "type": "u64"
          },
          {
            "name": "unlocked_liquidity",
            "docs": [
              "unlock liquidity"
            ],
            "type": "u128"
          },
          {
            "name": "vested_liquidity",
            "docs": [
              "vesting liquidity"
            ],
            "type": "u128"
          },
          {
            "name": "permanent_locked_liquidity",
            "docs": [
              "permanent locked liquidity"
            ],
            "type": "u128"
          },
          {
            "name": "metrics",
            "docs": [
              "metrics"
            ],
            "type": {
              "defined": {
                "name": "PositionMetrics"
              }
            }
          },
          {
            "name": "reward_infos",
            "docs": [
              "Farming reward information"
            ],
            "type": {
              "array": [
                {
                  "defined": {
                    "name": "UserRewardInfo"
                  }
                },
                2
              ]
            }
          },
          {
            "name": "padding",
            "docs": [
              "padding for future usage"
            ],
            "type": {
              "array": [
                "u128",
                6
              ]
            }
          }
        ]
      }
    },
    {
      "name": "PositionMetrics",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "total_claimed_a_fee",
            "type": "u64"
          },
          {
            "name": "total_claimed_b_fee",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "RemoveLiquidityParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "liquidity_delta",
            "docs": [
              "delta liquidity"
            ],
            "type": "u128"
          },
          {
            "name": "token_a_amount_threshold",
            "docs": [
              "minimum token a amount"
            ],
            "type": "u64"
          },
          {
            "name": "token_b_amount_threshold",
            "docs": [
              "minimum token b amount"
            ],
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "RewardInfo",
      "docs": [
        "Stores the state relevant for tracking liquidity mining rewards"
      ],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "initialized",
            "docs": [
              "Indicates if the reward has been initialized"
            ],
            "type": "u8"
          },
          {
            "name": "reward_token_flag",
            "docs": [
              "reward token flag"
            ],
            "type": "u8"
          },
          {
            "name": "_padding_0",
            "docs": [
              "padding"
            ],
            "type": {
              "array": [
                "u8",
                6
              ]
            }
          },
          {
            "name": "_padding_1",
            "docs": [
              "Padding to ensure `reward_rate: u128` is 16-byte aligned"
            ],
            "type": {
              "array": [
                "u8",
                8
              ]
            }
          },
          {
            "name": "mint",
            "docs": [
              "Reward token mint."
            ],
            "type": "pubkey"
          },
          {
            "name": "vault",
            "docs": [
              "Reward vault token account."
            ],
            "type": "pubkey"
          },
          {
            "name": "funder",
            "docs": [
              "Authority account that allows to fund rewards"
            ],
            "type": "pubkey"
          },
          {
            "name": "reward_duration",
            "docs": [
              "reward duration"
            ],
            "type": "u64"
          },
          {
            "name": "reward_duration_end",
            "docs": [
              "reward duration end"
            ],
            "type": "u64"
          },
          {
            "name": "reward_rate",
            "docs": [
              "reward rate"
            ],
            "type": "u128"
          },
          {
            "name": "reward_per_token_stored",
            "docs": [
              "Reward per token stored"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "last_update_time",
            "docs": [
              "The last time reward states were updated."
            ],
            "type": "u64"
          },
          {
            "name": "cumulative_seconds_with_empty_liquidity_reward",
            "docs": [
              "Accumulated seconds when the farm distributed rewards but the bin was empty.",
              "These rewards will be carried over to the next reward time window."
            ],
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "SplitAmountInfo",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "permanent_locked_liquidity",
            "type": "u128"
          },
          {
            "name": "unlocked_liquidity",
            "type": "u128"
          },
          {
            "name": "fee_a",
            "type": "u64"
          },
          {
            "name": "fee_b",
            "type": "u64"
          },
          {
            "name": "reward_0",
            "type": "u64"
          },
          {
            "name": "reward_1",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "SplitPositionInfo",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "liquidity",
            "type": "u128"
          },
          {
            "name": "fee_a",
            "type": "u64"
          },
          {
            "name": "fee_b",
            "type": "u64"
          },
          {
            "name": "reward_0",
            "type": "u64"
          },
          {
            "name": "reward_1",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "SplitPositionParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "unlocked_liquidity_percentage",
            "docs": [
              "Percentage of unlocked liquidity to split to the second position"
            ],
            "type": "u8"
          },
          {
            "name": "permanent_locked_liquidity_percentage",
            "docs": [
              "Percentage of permanent locked liquidity to split to the second position"
            ],
            "type": "u8"
          },
          {
            "name": "fee_a_percentage",
            "docs": [
              "Percentage of fee A pending to split to the second position"
            ],
            "type": "u8"
          },
          {
            "name": "fee_b_percentage",
            "docs": [
              "Percentage of fee B pending to split to the second position"
            ],
            "type": "u8"
          },
          {
            "name": "reward_0_percentage",
            "docs": [
              "Percentage of reward 0 pending to split to the second position"
            ],
            "type": "u8"
          },
          {
            "name": "reward_1_percentage",
            "docs": [
              "Percentage of reward 1 pending to split to the second position"
            ],
            "type": "u8"
          },
          {
            "name": "padding",
            "docs": [
              "padding for future"
            ],
            "type": {
              "array": [
                "u8",
                16
              ]
            }
          }
        ]
      }
    },
    {
      "name": "SplitPositionParameters2",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "unlocked_liquidity_numerator",
            "type": "u32"
          },
          {
            "name": "permanent_locked_liquidity_numerator",
            "type": "u32"
          },
          {
            "name": "fee_a_numerator",
            "type": "u32"
          },
          {
            "name": "fee_b_numerator",
            "type": "u32"
          },
          {
            "name": "reward_0_numerator",
            "type": "u32"
          },
          {
            "name": "reward_1_numerator",
            "type": "u32"
          }
        ]
      }
    },
    {
      "name": "StaticConfigParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "pool_fees",
            "type": {
              "defined": {
                "name": "PoolFeeParameters"
              }
            }
          },
          {
            "name": "sqrt_min_price",
            "type": "u128"
          },
          {
            "name": "sqrt_max_price",
            "type": "u128"
          },
          {
            "name": "vault_config_key",
            "type": "pubkey"
          },
          {
            "name": "pool_creator_authority",
            "type": "pubkey"
          },
          {
            "name": "activation_type",
            "type": "u8"
          },
          {
            "name": "collect_fee_mode",
            "type": "u8"
          }
        ]
      }
    },
    {
      "name": "SwapParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "amount_in",
            "type": "u64"
          },
          {
            "name": "minimum_amount_out",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "SwapResult",
      "docs": [
        "Encodes all results of swapping"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "output_amount",
            "type": "u64"
          },
          {
            "name": "next_sqrt_price",
            "type": "u128"
          },
          {
            "name": "lp_fee",
            "type": "u64"
          },
          {
            "name": "protocol_fee",
            "type": "u64"
          },
          {
            "name": "partner_fee",
            "type": "u64"
          },
          {
            "name": "referral_fee",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "TokenBadge",
      "docs": [
        "Parameter that set by the protocol"
      ],
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "token_mint",
            "docs": [
              "token mint"
            ],
            "type": "pubkey"
          },
          {
            "name": "_padding",
            "docs": [
              "Reserve"
            ],
            "type": {
              "array": [
                "u8",
                128
              ]
            }
          }
        ]
      }
    },
    {
      "name": "UserRewardInfo",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "reward_per_token_checkpoint",
            "docs": [
              "The latest update reward checkpoint"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "reward_pendings",
            "docs": [
              "Current pending rewards"
            ],
            "type": "u64"
          },
          {
            "name": "total_claimed_rewards",
            "docs": [
              "Total claimed rewards"
            ],
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "Vesting",
      "serialization": "bytemuck",
      "repr": {
        "kind": "c"
      },
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "position",
            "type": "pubkey"
          },
          {
            "name": "cliff_point",
            "type": "u64"
          },
          {
            "name": "period_frequency",
            "type": "u64"
          },
          {
            "name": "cliff_unlock_liquidity",
            "type": "u128"
          },
          {
            "name": "liquidity_per_period",
            "type": "u128"
          },
          {
            "name": "total_released_liquidity",
            "type": "u128"
          },
          {
            "name": "number_of_period",
            "type": "u16"
          },
          {
            "name": "padding",
            "type": {
              "array": [
                "u8",
                14
              ]
            }
          },
          {
            "name": "padding2",
            "type": {
              "array": [
                "u128",
                4
              ]
            }
          }
        ]
      }
    },
    {
      "name": "VestingParameters",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "cliff_point",
            "type": {
              "option": "u64"
            }
          },
          {
            "name": "period_frequency",
            "type": "u64"
          },
          {
            "name": "cliff_unlock_liquidity",
            "type": "u128"
          },
          {
            "name": "liquidity_per_period",
            "type": "u128"
          },
          {
            "name": "number_of_period",
            "type": "u16"
          }
        ]
      }
    }
  ]
}

idl_orca = {
    "version": "0.6.0",
    "name": "whirlpool",
    "instructions": [
        {
            "name": "initializeConfig",
            "docs": [
                "Initializes a WhirlpoolsConfig account that hosts info & authorities",
                "required to govern a set of Whirlpools.",
                "",
                "### Authority",
                "- \"authority\" - Set authority that is one of ADMINS.",
                "",
                "### Parameters",
                "- `fee_authority` - Authority authorized to initialize fee-tiers and set customs fees.",
                "- `collect_protocol_fees_authority` - Authority authorized to collect protocol fees.",
                "- `reward_emissions_super_authority` - Authority authorized to set reward authorities in pools."
            ],
            "accounts": [
                {
                    "name": "config",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "feeAuthority",
                    "type": "publicKey"
                },
                {
                    "name": "collectProtocolFeesAuthority",
                    "type": "publicKey"
                },
                {
                    "name": "rewardEmissionsSuperAuthority",
                    "type": "publicKey"
                },
                {
                    "name": "defaultProtocolFeeRate",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "initializePool",
            "docs": [
                "Initializes a Whirlpool account.",
                "Fee rate is set to the default values on the config and supplied fee_tier.",
                "",
                "### Parameters",
                "- `bumps` - The bump value when deriving the PDA of the Whirlpool address.",
                "- `tick_spacing` - The desired tick spacing for this pool.",
                "- `initial_sqrt_price` - The desired initial sqrt-price for this pool",
                "",
                "#### Special Errors",
                "`InvalidTokenMintOrder` - The order of mints have to be ordered by",
                "`SqrtPriceOutOfBounds` - provided initial_sqrt_price is not between 2^-64 to 2^64",
                ""
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "feeTier",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "bumps",
                    "type": {
                        "defined": "WhirlpoolBumps"
                    }
                },
                {
                    "name": "tickSpacing",
                    "type": "u16"
                },
                {
                    "name": "initialSqrtPrice",
                    "type": "u128"
                }
            ]
        },
        {
            "name": "initializeTickArray",
            "docs": [
                "Initializes a fixed-length tick_array account to represent a tick-range in a Whirlpool.",
                "",
                "### Parameters",
                "- `start_tick_index` - The starting tick index for this tick-array.",
                "Has to be a multiple of TickArray size & the tick spacing of this pool.",
                "",
                "#### Special Errors",
                "- `InvalidStartTick` - if the provided start tick is out of bounds or is not a multiple of",
                "TICK_ARRAY_SIZE * tick spacing."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "tickArray",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "startTickIndex",
                    "type": "i32"
                }
            ]
        },
        {
            "name": "initializeDynamicTickArray",
            "docs": [
                "Initialize a variable-length tick array for a Whirlpool.",
                "",
                "### Parameters",
                "- `start_tick_index` - The starting tick index for this tick-array.",
                "Has to be a multiple of TickArray size & the tick spacing of this pool.",
                "- `idempotent` - If true, the instruction will not fail if the tick array already exists.",
                "Note: The idempotent option exits successfully if a FixedTickArray is present as well as a DynamicTickArray.",
                "",
                "#### Special Errors",
                "- `InvalidStartTick` - if the provided start tick is out of bounds or is not a multiple of",
                "TICK_ARRAY_SIZE * tick spacing."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "tickArray",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "startTickIndex",
                    "type": "i32"
                },
                {
                    "name": "idempotent",
                    "type": "bool"
                }
            ]
        },
        {
            "name": "initializeFeeTier",
            "docs": [
                "Initializes a fee_tier account usable by Whirlpools in a WhirlpoolConfig space.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority in the WhirlpoolConfig",
                "",
                "### Parameters",
                "- `tick_spacing` - The tick-spacing that this fee-tier suggests the default_fee_rate for.",
                "- `default_fee_rate` - The default fee rate that a pool will use if the pool uses this",
                "fee tier during initialization.",
                "",
                "#### Special Errors",
                "- `InvalidTickSpacing` - If the provided tick_spacing is 0.",
                "- `FeeRateMaxExceeded` - If the provided default_fee_rate exceeds MAX_FEE_RATE."
            ],
            "accounts": [
                {
                    "name": "config",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "feeTier",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "tickSpacing",
                    "type": "u16"
                },
                {
                    "name": "defaultFeeRate",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "initializeReward",
            "docs": [
                "Initialize reward for a Whirlpool. A pool can only support up to a set number of rewards.",
                "",
                "### Authority",
                "- \"reward_authority\" - assigned authority by the reward_super_authority for the specified",
                "reward-index in this Whirlpool",
                "",
                "### Parameters",
                "- `reward_index` - The reward index that we'd like to initialize. (0 <= index <= NUM_REWARDS)",
                "",
                "#### Special Errors",
                "- `InvalidRewardIndex` - If the provided reward index doesn't match the lowest uninitialized",
                "index in this pool, or exceeds NUM_REWARDS, or",
                "all reward slots for this pool has been initialized."
            ],
            "accounts": [
                {
                    "name": "rewardAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardMint",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rewardVault",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "rewardIndex",
                    "type": "u8"
                }
            ]
        },
        {
            "name": "setRewardEmissions",
            "docs": [
                "Set the reward emissions for a reward in a Whirlpool.",
                "",
                "### Authority",
                "- \"reward_authority\" - assigned authority by the reward_super_authority for the specified",
                "reward-index in this Whirlpool",
                "",
                "### Parameters",
                "- `reward_index` - The reward index (0 <= index <= NUM_REWARDS) that we'd like to modify.",
                "- `emissions_per_second_x64` - The amount of rewards emitted in this pool.",
                "",
                "#### Special Errors",
                "- `RewardVaultAmountInsufficient` - The amount of rewards in the reward vault cannot emit",
                "more than a day of desired emissions.",
                "- `InvalidTimestamp` - Provided timestamp is not in order with the previous timestamp.",
                "- `InvalidRewardIndex` - If the provided reward index doesn't match the lowest uninitialized",
                "index in this pool, or exceeds NUM_REWARDS, or",
                "all reward slots for this pool has been initialized."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "rewardVault",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "rewardIndex",
                    "type": "u8"
                },
                {
                    "name": "emissionsPerSecondX64",
                    "type": "u128"
                }
            ]
        },
        {
            "name": "openPosition",
            "docs": [
                "Open a position in a Whirlpool. A unique token will be minted to represent the position",
                "in the users wallet. The position will start off with 0 liquidity.",
                "",
                "### Parameters",
                "- `tick_lower_index` - The tick specifying the lower end of the position range.",
                "- `tick_upper_index` - The tick specifying the upper end of the position range.",
                "",
                "#### Special Errors",
                "- `InvalidTickIndex` - If a provided tick is out of bounds, out of order or not a multiple of",
                "the tick-spacing in this pool."
            ],
            "accounts": [
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "owner",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionMint",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "associatedTokenProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "bumps",
                    "type": {
                        "defined": "OpenPositionBumps"
                    }
                },
                {
                    "name": "tickLowerIndex",
                    "type": "i32"
                },
                {
                    "name": "tickUpperIndex",
                    "type": "i32"
                }
            ]
        },
        {
            "name": "openPositionWithMetadata",
            "docs": [
                "Open a position in a Whirlpool. A unique token will be minted to represent the position",
                "in the users wallet. Additional Metaplex metadata is appended to identify the token.",
                "The position will start off with 0 liquidity.",
                "",
                "### Parameters",
                "- `tick_lower_index` - The tick specifying the lower end of the position range.",
                "- `tick_upper_index` - The tick specifying the upper end of the position range.",
                "",
                "#### Special Errors",
                "- `InvalidTickIndex` - If a provided tick is out of bounds, out of order or not a multiple of",
                "the tick-spacing in this pool."
            ],
            "accounts": [
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "owner",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionMint",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "positionMetadataAccount",
                    "isMut": true,
                    "isSigner": false,
                    "docs": [
                        "https://github.com/metaplex-foundation/mpl-token-metadata/blob/master/programs/token-metadata/program/src/utils/metadata.rs#L78"
                    ]
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "associatedTokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "metadataProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "metadataUpdateAuth",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "bumps",
                    "type": {
                        "defined": "OpenPositionWithMetadataBumps"
                    }
                },
                {
                    "name": "tickLowerIndex",
                    "type": "i32"
                },
                {
                    "name": "tickUpperIndex",
                    "type": "i32"
                }
            ]
        },
        {
            "name": "increaseLiquidity",
            "docs": [
                "Add liquidity to a position in the Whirlpool. This call also updates the position's accrued fees and rewards.",
                "",
                "### Authority",
                "- `position_authority` - authority that owns the token corresponding to this desired position.",
                "",
                "### Parameters",
                "- `liquidity_amount` - The total amount of Liquidity the user is willing to deposit.",
                "- `token_max_a` - The maximum amount of tokenA the user is willing to deposit.",
                "- `token_max_b` - The maximum amount of tokenB the user is willing to deposit.",
                "",
                "#### Special Errors",
                "- `LiquidityZero` - Provided liquidity amount is zero.",
                "- `LiquidityTooHigh` - Provided liquidity exceeds u128::max.",
                "- `TokenMaxExceeded` - The required token to perform this operation exceeds the user defined amount."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayLower",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayUpper",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "liquidityAmount",
                    "type": "u128"
                },
                {
                    "name": "tokenMaxA",
                    "type": "u64"
                },
                {
                    "name": "tokenMaxB",
                    "type": "u64"
                }
            ]
        },
        {
            "name": "decreaseLiquidity",
            "docs": [
                "Withdraw liquidity from a position in the Whirlpool. This call also updates the position's accrued fees and rewards.",
                "",
                "### Authority",
                "- `position_authority` - authority that owns the token corresponding to this desired position.",
                "",
                "### Parameters",
                "- `liquidity_amount` - The total amount of Liquidity the user desires to withdraw.",
                "- `token_min_a` - The minimum amount of tokenA the user is willing to withdraw.",
                "- `token_min_b` - The minimum amount of tokenB the user is willing to withdraw.",
                "",
                "#### Special Errors",
                "- `LiquidityZero` - Provided liquidity amount is zero.",
                "- `LiquidityTooHigh` - Provided liquidity exceeds u128::max.",
                "- `TokenMinSubceeded` - The required token to perform this operation subceeds the user defined amount."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayLower",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayUpper",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "liquidityAmount",
                    "type": "u128"
                },
                {
                    "name": "tokenMinA",
                    "type": "u64"
                },
                {
                    "name": "tokenMinB",
                    "type": "u64"
                }
            ]
        },
        {
            "name": "updateFeesAndRewards",
            "docs": [
                "Update the accrued fees and rewards for a position.",
                "",
                "#### Special Errors",
                "- `TickNotFound` - Provided tick array account does not contain the tick for this position.",
                "- `LiquidityZero` - Position has zero liquidity and therefore already has the most updated fees and reward values."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayLower",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tickArrayUpper",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "collectFees",
            "docs": [
                "Collect fees accrued for this position.",
                "",
                "### Authority",
                "- `position_authority` - authority that owns the token corresponding to this desired position."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "collectReward",
            "docs": [
                "Collect rewards accrued for this position.",
                "",
                "### Authority",
                "- `position_authority` - authority that owns the token corresponding to this desired position."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rewardOwnerAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardVault",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "rewardIndex",
                    "type": "u8"
                }
            ]
        },
        {
            "name": "collectProtocolFees",
            "docs": [
                "Collect the protocol fees accrued in this Whirlpool",
                "",
                "### Authority",
                "- `collect_protocol_fees_authority` - assigned authority in the WhirlpoolConfig that can collect protocol fees"
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "collectProtocolFeesAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenDestinationA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenDestinationB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "swap",
            "docs": [
                "Perform a swap in this Whirlpool",
                "",
                "### Authority",
                "- \"token_authority\" - The authority to withdraw tokens from the input token account.",
                "",
                "### Parameters",
                "- `amount` - The amount of input or output token to swap from (depending on amount_specified_is_input).",
                "- `other_amount_threshold` - The maximum/minimum of input/output token to swap into (depending on amount_specified_is_input).",
                "- `sqrt_price_limit` - The maximum/minimum price the swap will swap to.",
                "- `amount_specified_is_input` - Specifies the token the parameter `amount`represents. If true, the amount represents the input token of the swap.",
                "- `a_to_b` - The direction of the swap. True if swapping from A to B. False if swapping from B to A.",
                "",
                "#### Special Errors",
                "- `ZeroTradableAmount` - User provided parameter `amount` is 0.",
                "- `InvalidSqrtPriceLimitDirection` - User provided parameter `sqrt_price_limit` does not match the direction of the trade.",
                "- `SqrtPriceOutOfBounds` - User provided parameter `sqrt_price_limit` is over Whirlppool's max/min bounds for sqrt-price.",
                "- `InvalidTickArraySequence` - User provided tick-arrays are not in sequential order required to proceed in this trade direction.",
                "- `TickArraySequenceInvalidIndex` - The swap loop attempted to access an invalid array index during the query of the next initialized tick.",
                "- `TickArrayIndexOutofBounds` - The swap loop attempted to access an invalid array index during tick crossing.",
                "- `LiquidityOverflow` - Liquidity value overflowed 128bits during tick crossing.",
                "- `InvalidTickSpacing` - The swap pool was initialized with tick-spacing of 0."
            ],
            "accounts": [
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArray0",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArray1",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArray2",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "oracle",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "amount",
                    "type": "u64"
                },
                {
                    "name": "otherAmountThreshold",
                    "type": "u64"
                },
                {
                    "name": "sqrtPriceLimit",
                    "type": "u128"
                },
                {
                    "name": "amountSpecifiedIsInput",
                    "type": "bool"
                },
                {
                    "name": "aToB",
                    "type": "bool"
                }
            ]
        },
        {
            "name": "closePosition",
            "docs": [
                "Close a position in a Whirlpool. Burns the position token in the owner's wallet.",
                "",
                "### Authority",
                "- \"position_authority\" - The authority that owns the position token.",
                "",
                "#### Special Errors",
                "- `ClosePositionNotEmpty` - The provided position account is not empty."
            ],
            "accounts": [
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "receiver",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionMint",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "setDefaultFeeRate",
            "docs": [
                "Set the default_fee_rate for a FeeTier",
                "Only the current fee authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority in the WhirlpoolConfig",
                "",
                "### Parameters",
                "- `default_fee_rate` - The default fee rate that a pool will use if the pool uses this",
                "fee tier during initialization.",
                "",
                "#### Special Errors",
                "- `FeeRateMaxExceeded` - If the provided default_fee_rate exceeds MAX_FEE_RATE."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "feeTier",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                }
            ],
            "args": [
                {
                    "name": "defaultFeeRate",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "setDefaultProtocolFeeRate",
            "docs": [
                "Sets the default protocol fee rate for a WhirlpoolConfig",
                "Protocol fee rate is represented as a basis point.",
                "Only the current fee authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority that can modify pool fees in the WhirlpoolConfig",
                "",
                "### Parameters",
                "- `default_protocol_fee_rate` - Rate that is referenced during the initialization of a Whirlpool using this config.",
                "",
                "#### Special Errors",
                "- `ProtocolFeeRateMaxExceeded` - If the provided default_protocol_fee_rate exceeds MAX_PROTOCOL_FEE_RATE."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                }
            ],
            "args": [
                {
                    "name": "defaultProtocolFeeRate",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "setFeeRate",
            "docs": [
                "Sets the fee rate for a Whirlpool.",
                "Fee rate is represented as hundredths of a basis point.",
                "Only the current fee authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority that can modify pool fees in the WhirlpoolConfig",
                "",
                "### Parameters",
                "- `fee_rate` - The rate that the pool will use to calculate fees going onwards.",
                "",
                "#### Special Errors",
                "- `FeeRateMaxExceeded` - If the provided fee_rate exceeds MAX_FEE_RATE."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                }
            ],
            "args": [
                {
                    "name": "feeRate",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "setProtocolFeeRate",
            "docs": [
                "Sets the protocol fee rate for a Whirlpool.",
                "Protocol fee rate is represented as a basis point.",
                "Only the current fee authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority that can modify pool fees in the WhirlpoolConfig",
                "",
                "### Parameters",
                "- `protocol_fee_rate` - The rate that the pool will use to calculate protocol fees going onwards.",
                "",
                "#### Special Errors",
                "- `ProtocolFeeRateMaxExceeded` - If the provided default_protocol_fee_rate exceeds MAX_PROTOCOL_FEE_RATE."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                }
            ],
            "args": [
                {
                    "name": "protocolFeeRate",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "setFeeAuthority",
            "docs": [
                "Sets the fee authority for a WhirlpoolConfig.",
                "The fee authority can set the fee & protocol fee rate for individual pools or",
                "set the default fee rate for newly minted pools.",
                "Only the current fee authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority that can modify pool fees in the WhirlpoolConfig"
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newFeeAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "setCollectProtocolFeesAuthority",
            "docs": [
                "Sets the fee authority to collect protocol fees for a WhirlpoolConfig.",
                "Only the current collect protocol fee authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority that can collect protocol fees in the WhirlpoolConfig"
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "collectProtocolFeesAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newCollectProtocolFeesAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "setRewardAuthority",
            "docs": [
                "Set the whirlpool reward authority at the provided `reward_index`.",
                "Only the current reward authority for this reward index has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"reward_authority\" - Set authority that can control reward emission for this particular reward.",
                "",
                "#### Special Errors",
                "- `InvalidRewardIndex` - If the provided reward index doesn't match the lowest uninitialized",
                "index in this pool, or exceeds NUM_REWARDS, or",
                "all reward slots for this pool has been initialized."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newRewardAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "rewardIndex",
                    "type": "u8"
                }
            ]
        },
        {
            "name": "setRewardAuthorityBySuperAuthority",
            "docs": [
                "Set the whirlpool reward authority at the provided `reward_index`.",
                "Only the current reward super authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"reward_authority\" - Set authority that can control reward emission for this particular reward.",
                "",
                "#### Special Errors",
                "- `InvalidRewardIndex` - If the provided reward index doesn't match the lowest uninitialized",
                "index in this pool, or exceeds NUM_REWARDS, or",
                "all reward slots for this pool has been initialized."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardEmissionsSuperAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newRewardAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "rewardIndex",
                    "type": "u8"
                }
            ]
        },
        {
            "name": "setRewardEmissionsSuperAuthority",
            "docs": [
                "Set the whirlpool reward super authority for a WhirlpoolConfig",
                "Only the current reward super authority has permission to invoke this instruction.",
                "This instruction will not change the authority on any `WhirlpoolRewardInfo` whirlpool rewards.",
                "",
                "### Authority",
                "- \"reward_emissions_super_authority\" - Set authority that can control reward authorities for all pools in this config space."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardEmissionsSuperAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newRewardEmissionsSuperAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "twoHopSwap",
            "docs": [
                "Perform a two-hop swap in this Whirlpool",
                "",
                "### Authority",
                "- \"token_authority\" - The authority to withdraw tokens from the input token account.",
                "",
                "### Parameters",
                "- `amount` - The amount of input or output token to swap from (depending on amount_specified_is_input).",
                "- `other_amount_threshold` - The maximum/minimum of input/output token to swap into (depending on amount_specified_is_input).",
                "- `amount_specified_is_input` - Specifies the token the parameter `amount`represents. If true, the amount represents the input token of the swap.",
                "- `a_to_b_one` - The direction of the swap of hop one. True if swapping from A to B. False if swapping from B to A.",
                "- `a_to_b_two` - The direction of the swap of hop two. True if swapping from A to B. False if swapping from B to A.",
                "- `sqrt_price_limit_one` - The maximum/minimum price the swap will swap to in the first hop.",
                "- `sqrt_price_limit_two` - The maximum/minimum price the swap will swap to in the second hop.",
                "",
                "#### Special Errors",
                "- `ZeroTradableAmount` - User provided parameter `amount` is 0.",
                "- `InvalidSqrtPriceLimitDirection` - User provided parameter `sqrt_price_limit` does not match the direction of the trade.",
                "- `SqrtPriceOutOfBounds` - User provided parameter `sqrt_price_limit` is over Whirlppool's max/min bounds for sqrt-price.",
                "- `InvalidTickArraySequence` - User provided tick-arrays are not in sequential order required to proceed in this trade direction.",
                "- `TickArraySequenceInvalidIndex` - The swap loop attempted to access an invalid array index during the query of the next initialized tick.",
                "- `TickArrayIndexOutofBounds` - The swap loop attempted to access an invalid array index during tick crossing.",
                "- `LiquidityOverflow` - Liquidity value overflowed 128bits during tick crossing.",
                "- `InvalidTickSpacing` - The swap pool was initialized with tick-spacing of 0.",
                "- `InvalidIntermediaryMint` - Error if the intermediary mint between hop one and two do not equal.",
                "- `DuplicateTwoHopPool` - Error if whirlpool one & two are the same pool."
            ],
            "accounts": [
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "whirlpoolOne",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "whirlpoolTwo",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountOneA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultOneA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountOneB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultOneB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountTwoA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultTwoA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountTwoB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultTwoB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayOne0",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayOne1",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayOne2",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayTwo0",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayTwo1",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayTwo2",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "oracleOne",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "oracleTwo",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "amount",
                    "type": "u64"
                },
                {
                    "name": "otherAmountThreshold",
                    "type": "u64"
                },
                {
                    "name": "amountSpecifiedIsInput",
                    "type": "bool"
                },
                {
                    "name": "aToBOne",
                    "type": "bool"
                },
                {
                    "name": "aToBTwo",
                    "type": "bool"
                },
                {
                    "name": "sqrtPriceLimitOne",
                    "type": "u128"
                },
                {
                    "name": "sqrtPriceLimitTwo",
                    "type": "u128"
                }
            ]
        },
        {
            "name": "initializePositionBundle",
            "docs": [
                "Initializes a PositionBundle account that bundles several positions.",
                "A unique token will be minted to represent the position bundle in the users wallet."
            ],
            "accounts": [
                {
                    "name": "positionBundle",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleMint",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "positionBundleTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleOwner",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "associatedTokenProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "initializePositionBundleWithMetadata",
            "docs": [
                "Initializes a PositionBundle account that bundles several positions.",
                "A unique token will be minted to represent the position bundle in the users wallet.",
                "Additional Metaplex metadata is appended to identify the token."
            ],
            "accounts": [
                {
                    "name": "positionBundle",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleMint",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "positionBundleMetadata",
                    "isMut": true,
                    "isSigner": false,
                    "docs": [
                        "https://github.com/metaplex-foundation/metaplex-program-library/blob/773a574c4b34e5b9f248a81306ec24db064e255f/token-metadata/program/src/utils/metadata.rs#L100"
                    ]
                },
                {
                    "name": "positionBundleTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleOwner",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "metadataUpdateAuth",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "associatedTokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "metadataProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "deletePositionBundle",
            "docs": [
                "Delete a PositionBundle account. Burns the position bundle token in the owner's wallet.",
                "",
                "### Authority",
                "- `position_bundle_owner` - The owner that owns the position bundle token.",
                "",
                "### Special Errors",
                "- `PositionBundleNotDeletable` - The provided position bundle has open positions."
            ],
            "accounts": [
                {
                    "name": "positionBundle",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleMint",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleOwner",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "receiver",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "openBundledPosition",
            "docs": [
                "Open a bundled position in a Whirlpool. No new tokens are issued",
                "because the owner of the position bundle becomes the owner of the position.",
                "The position will start off with 0 liquidity.",
                "",
                "### Authority",
                "- `position_bundle_authority` - authority that owns the token corresponding to this desired position bundle.",
                "",
                "### Parameters",
                "- `bundle_index` - The bundle index that we'd like to open.",
                "- `tick_lower_index` - The tick specifying the lower end of the position range.",
                "- `tick_upper_index` - The tick specifying the upper end of the position range.",
                "",
                "#### Special Errors",
                "- `InvalidBundleIndex` - If the provided bundle index is out of bounds.",
                "- `InvalidTickIndex` - If a provided tick is out of bounds, out of order or not a multiple of",
                "the tick-spacing in this pool."
            ],
            "accounts": [
                {
                    "name": "bundledPosition",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundle",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionBundleAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "bundleIndex",
                    "type": "u16"
                },
                {
                    "name": "tickLowerIndex",
                    "type": "i32"
                },
                {
                    "name": "tickUpperIndex",
                    "type": "i32"
                }
            ]
        },
        {
            "name": "closeBundledPosition",
            "docs": [
                "Close a bundled position in a Whirlpool.",
                "",
                "### Authority",
                "- `position_bundle_authority` - authority that owns the token corresponding to this desired position bundle.",
                "",
                "### Parameters",
                "- `bundle_index` - The bundle index that we'd like to close.",
                "",
                "#### Special Errors",
                "- `InvalidBundleIndex` - If the provided bundle index is out of bounds.",
                "- `ClosePositionNotEmpty` - The provided position account is not empty."
            ],
            "accounts": [
                {
                    "name": "bundledPosition",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundle",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionBundleTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionBundleAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "receiver",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "bundleIndex",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "openPositionWithTokenExtensions",
            "docs": [
                "Open a position in a Whirlpool. A unique token will be minted to represent the position",
                "in the users wallet. Additional TokenMetadata extension is initialized to identify the token.",
                "Mint and TokenAccount are based on Token-2022.",
                "The position will start off with 0 liquidity.",
                "",
                "### Parameters",
                "- `tick_lower_index` - The tick specifying the lower end of the position range.",
                "- `tick_upper_index` - The tick specifying the upper end of the position range.",
                "- `with_token_metadata_extension` - If true, the token metadata extension will be initialized.",
                "",
                "#### Special Errors",
                "- `InvalidTickIndex` - If a provided tick is out of bounds, out of order or not a multiple of",
                "the tick-spacing in this pool."
            ],
            "accounts": [
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "owner",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionMint",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "token2022Program",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "associatedTokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "metadataUpdateAuth",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "tickLowerIndex",
                    "type": "i32"
                },
                {
                    "name": "tickUpperIndex",
                    "type": "i32"
                },
                {
                    "name": "withTokenMetadataExtension",
                    "type": "bool"
                }
            ]
        },
        {
            "name": "closePositionWithTokenExtensions",
            "docs": [
                "Close a position in a Whirlpool. Burns the position token in the owner's wallet.",
                "Mint and TokenAccount are based on Token-2022. And Mint accout will be also closed.",
                "",
                "### Authority",
                "- \"position_authority\" - The authority that owns the position token.",
                "",
                "#### Special Errors",
                "- `ClosePositionNotEmpty` - The provided position account is not empty."
            ],
            "accounts": [
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "receiver",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionMint",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "token2022Program",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "lockPosition",
            "docs": [
                "Lock the position to prevent any liquidity changes.",
                "",
                "### Authority",
                "- `position_authority` - The authority that owns the position token.",
                "",
                "#### Special Errors",
                "- `PositionAlreadyLocked` - The provided position is already locked.",
                "- `PositionNotLockable` - The provided position is not lockable (e.g. An empty position)."
            ],
            "accounts": [
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionMint",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "lockConfig",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "token2022Program",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "lockType",
                    "type": {
                        "defined": "LockType"
                    }
                }
            ]
        },
        {
            "name": "resetPositionRange",
            "docs": [
                "Reset the position range to a new range.",
                "",
                "### Authority",
                "- `position_authority` - The authority that owns the position token.",
                "",
                "### Parameters",
                "- `new_tick_lower_index` - The new tick specifying the lower end of the position range.",
                "- `new_tick_upper_index` - The new tick specifying the upper end of the position range.",
                "",
                "#### Special Errors",
                "- `InvalidTickIndex` - If a provided tick is out of bounds, out of order or not a multiple of",
                "the tick-spacing in this pool.",
                "- `ClosePositionNotEmpty` - The provided position account is not empty.",
                "- `SameTickRangeNotAllowed` - The provided tick range is the same as the current tick range."
            ],
            "accounts": [
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "newTickLowerIndex",
                    "type": "i32"
                },
                {
                    "name": "newTickUpperIndex",
                    "type": "i32"
                }
            ]
        },
        {
            "name": "transferLockedPosition",
            "docs": [
                "Transfer a locked position to a different token account.",
                "",
                "### Authority",
                "- `position_authority` - The authority that owns the position token."
            ],
            "accounts": [
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "receiver",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "position",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionMint",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "destinationTokenAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "lockConfig",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "token2022Program",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "initializeAdaptiveFeeTier",
            "docs": [
                "Initializes an adaptive_fee_tier account usable by Whirlpools in a WhirlpoolConfig space.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority in the WhirlpoolConfig",
                "",
                "### Parameters",
                "- `fee_tier_index` - The index of the fee-tier that this adaptive fee tier will be initialized.",
                "- `tick_spacing` - The tick-spacing that this fee-tier suggests the default_fee_rate for.",
                "- `initialize_pool_authority` - The authority that can initialize pools with this adaptive fee-tier.",
                "- `delegated_fee_authority` - The authority that can set the base fee rate for pools using this adaptive fee-tier.",
                "- `default_fee_rate` - The default fee rate that a pool will use if the pool uses this",
                "fee tier during initialization.",
                "- `filter_period` - Period determine high frequency trading time window. (seconds)",
                "- `decay_period` - Period determine when the adaptive fee start decrease. (seconds)",
                "- `reduction_factor` - Adaptive fee rate decrement rate.",
                "- `adaptive_fee_control_factor` - Adaptive fee control factor.",
                "- `max_volatility_accumulator` - Max volatility accumulator.",
                "- `tick_group_size` - Tick group size to define tick group index.",
                "- `major_swap_threshold_ticks` - Major swap threshold ticks to define major swap.",
                "",
                "#### Special Errors",
                "- `InvalidTickSpacing` - If the provided tick_spacing is 0.",
                "- `InvalidFeeTierIndex` - If the provided fee_tier_index is same to tick_spacing.",
                "- `FeeRateMaxExceeded` - If the provided default_fee_rate exceeds MAX_FEE_RATE.",
                "- `InvalidAdaptiveFeeConstants` - If the provided adaptive fee constants are invalid."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "adaptiveFeeTier",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "feeTierIndex",
                    "type": "u16"
                },
                {
                    "name": "tickSpacing",
                    "type": "u16"
                },
                {
                    "name": "initializePoolAuthority",
                    "type": "publicKey"
                },
                {
                    "name": "delegatedFeeAuthority",
                    "type": "publicKey"
                },
                {
                    "name": "defaultBaseFeeRate",
                    "type": "u16"
                },
                {
                    "name": "filterPeriod",
                    "type": "u16"
                },
                {
                    "name": "decayPeriod",
                    "type": "u16"
                },
                {
                    "name": "reductionFactor",
                    "type": "u16"
                },
                {
                    "name": "adaptiveFeeControlFactor",
                    "type": "u32"
                },
                {
                    "name": "maxVolatilityAccumulator",
                    "type": "u32"
                },
                {
                    "name": "tickGroupSize",
                    "type": "u16"
                },
                {
                    "name": "majorSwapThresholdTicks",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "setDefaultBaseFeeRate",
            "docs": [
                "Set the default_base_fee_rate for an AdaptiveFeeTier",
                "Only the current fee authority in WhirlpoolsConfig has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority in the WhirlpoolConfig",
                "",
                "### Parameters",
                "- `default_base_fee_rate` - The default base fee rate that a pool will use if the pool uses this",
                "adaptive fee-tier during initialization.",
                "",
                "#### Special Errors",
                "- `FeeRateMaxExceeded` - If the provided default_fee_rate exceeds MAX_FEE_RATE."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "adaptiveFeeTier",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                }
            ],
            "args": [
                {
                    "name": "defaultBaseFeeRate",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "setDelegatedFeeAuthority",
            "docs": [
                "Sets the delegated fee authority for an AdaptiveFeeTier.",
                "The delegated fee authority can set the fee rate for individual pools initialized with the adaptive fee-tier.",
                "Only the current fee authority in WhirlpoolsConfig has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority in the WhirlpoolConfig"
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "adaptiveFeeTier",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newDelegatedFeeAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "setInitializePoolAuthority",
            "docs": [
                "Sets the initialize pool authority for an AdaptiveFeeTier.",
                "Only the initialize pool authority can initialize pools with the adaptive fee-tier.",
                "Only the current fee authority in WhirlpoolsConfig has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority in the WhirlpoolConfig"
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "adaptiveFeeTier",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newInitializePoolAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "setPresetAdaptiveFeeConstants",
            "docs": [
                "Sets the adaptive fee constants for an AdaptiveFeeTier.",
                "Only the current fee authority in WhirlpoolsConfig has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority in the WhirlpoolConfig",
                "",
                "### Parameters",
                "- `filter_period` - Period determine high frequency trading time window. (seconds)",
                "- `decay_period` - Period determine when the adaptive fee start decrease. (seconds)",
                "- `reduction_factor` - Adaptive fee rate decrement rate.",
                "- `adaptive_fee_control_factor` - Adaptive fee control factor.",
                "- `max_volatility_accumulator` - Max volatility accumulator.",
                "- `tick_group_size` - Tick group size to define tick group index.",
                "- `major_swap_threshold_ticks` - Major swap threshold ticks to define major swap."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "adaptiveFeeTier",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                }
            ],
            "args": [
                {
                    "name": "filterPeriod",
                    "type": "u16"
                },
                {
                    "name": "decayPeriod",
                    "type": "u16"
                },
                {
                    "name": "reductionFactor",
                    "type": "u16"
                },
                {
                    "name": "adaptiveFeeControlFactor",
                    "type": "u32"
                },
                {
                    "name": "maxVolatilityAccumulator",
                    "type": "u32"
                },
                {
                    "name": "tickGroupSize",
                    "type": "u16"
                },
                {
                    "name": "majorSwapThresholdTicks",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "initializePoolWithAdaptiveFee",
            "docs": [
                "Initializes a Whirlpool account and Oracle account with adaptive fee.",
                "",
                "### Parameters",
                "- `initial_sqrt_price` - The desired initial sqrt-price for this pool",
                "- `trade_enable_timestamp` - The timestamp when trading is enabled for this pool (within 72 hours)",
                "",
                "#### Special Errors",
                "`InvalidTokenMintOrder` - The order of mints have to be ordered by",
                "`SqrtPriceOutOfBounds` - provided initial_sqrt_price is not between 2^-64 to 2^64",
                "`InvalidTradeEnableTimestamp` - provided trade_enable_timestamp is not within 72 hours or the adaptive fee-tier is permission-less",
                "`UnsupportedTokenMint` - The provided token mint is not supported by the program (e.g. it has risky token extensions)",
                ""
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadgeA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadgeB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "initializePoolAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "oracle",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "adaptiveFeeTier",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "initialSqrtPrice",
                    "type": "u128"
                },
                {
                    "name": "tradeEnableTimestamp",
                    "type": {
                        "option": "u64"
                    }
                }
            ]
        },
        {
            "name": "setFeeRateByDelegatedFeeAuthority",
            "docs": [
                "Sets the fee rate for a Whirlpool by the delegated fee authority in AdaptiveFeeTier.",
                "Fee rate is represented as hundredths of a basis point.",
                "",
                "### Authority",
                "- \"delegated_fee_authority\" - Set authority that can modify pool fees in the AdaptiveFeeTier",
                "",
                "### Parameters",
                "- `fee_rate` - The rate that the pool will use to calculate fees going onwards.",
                "",
                "#### Special Errors",
                "- `FeeRateMaxExceeded` - If the provided fee_rate exceeds MAX_FEE_RATE."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "adaptiveFeeTier",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "delegatedFeeAuthority",
                    "isMut": false,
                    "isSigner": true
                }
            ],
            "args": [
                {
                    "name": "feeRate",
                    "type": "u16"
                }
            ]
        },
        {
            "name": "setConfigFeatureFlag",
            "docs": [
                "Sets the feature flag for a WhirlpoolConfig.",
                "",
                "### Authority",
                "- \"authority\" - Set authority that is one of ADMINS.",
                "",
                "### Parameters",
                "- `feature_flag` - The feature flag that the WhirlpoolConfig will use."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "authority",
                    "isMut": false,
                    "isSigner": true
                }
            ],
            "args": [
                {
                    "name": "featureFlag",
                    "type": {
                        "defined": "ConfigFeatureFlag"
                    }
                }
            ]
        },
        {
            "name": "migrateRepurposeRewardAuthoritySpace",
            "docs": [
                "Migration instruction to repurpose the reward authority space in the Whirlpool.",
                "TODO: This instruction should be removed once all pools have been migrated."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "collectFeesV2",
            "docs": [
                "Collect fees accrued for this position.",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- `position_authority` - authority that owns the token corresponding to this desired position."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "memoProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "remainingAccountsInfo",
                    "type": {
                        "option": {
                            "defined": "RemainingAccountsInfo"
                        }
                    }
                }
            ]
        },
        {
            "name": "collectProtocolFeesV2",
            "docs": [
                "Collect the protocol fees accrued in this Whirlpool",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- `collect_protocol_fees_authority` - assigned authority in the WhirlpoolConfig that can collect protocol fees"
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "collectProtocolFeesAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "tokenMintA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenDestinationA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenDestinationB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "memoProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "remainingAccountsInfo",
                    "type": {
                        "option": {
                            "defined": "RemainingAccountsInfo"
                        }
                    }
                }
            ]
        },
        {
            "name": "collectRewardV2",
            "docs": [
                "Collect rewards accrued for this position.",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- `position_authority` - authority that owns the token corresponding to this desired position."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rewardOwnerAccount",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardMint",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rewardVault",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardTokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "memoProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "rewardIndex",
                    "type": "u8"
                },
                {
                    "name": "remainingAccountsInfo",
                    "type": {
                        "option": {
                            "defined": "RemainingAccountsInfo"
                        }
                    }
                }
            ]
        },
        {
            "name": "decreaseLiquidityV2",
            "docs": [
                "Withdraw liquidity from a position in the Whirlpool. This call also updates the position's accrued fees and rewards.",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- `position_authority` - authority that owns the token corresponding to this desired position.",
                "",
                "### Parameters",
                "- `liquidity_amount` - The total amount of Liquidity the user desires to withdraw.",
                "- `token_min_a` - The minimum amount of tokenA the user is willing to withdraw.",
                "- `token_min_b` - The minimum amount of tokenB the user is willing to withdraw.",
                "",
                "#### Special Errors",
                "- `LiquidityZero` - Provided liquidity amount is zero.",
                "- `LiquidityTooHigh` - Provided liquidity exceeds u128::max.",
                "- `TokenMinSubceeded` - The required token to perform this operation subceeds the user defined amount."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "memoProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayLower",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayUpper",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "liquidityAmount",
                    "type": "u128"
                },
                {
                    "name": "tokenMinA",
                    "type": "u64"
                },
                {
                    "name": "tokenMinB",
                    "type": "u64"
                },
                {
                    "name": "remainingAccountsInfo",
                    "type": {
                        "option": {
                            "defined": "RemainingAccountsInfo"
                        }
                    }
                }
            ]
        },
        {
            "name": "increaseLiquidityV2",
            "docs": [
                "Add liquidity to a position in the Whirlpool. This call also updates the position's accrued fees and rewards.",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- `position_authority` - authority that owns the token corresponding to this desired position.",
                "",
                "### Parameters",
                "- `liquidity_amount` - The total amount of Liquidity the user is willing to deposit.",
                "- `token_max_a` - The maximum amount of tokenA the user is willing to deposit.",
                "- `token_max_b` - The maximum amount of tokenB the user is willing to deposit.",
                "",
                "#### Special Errors",
                "- `LiquidityZero` - Provided liquidity amount is zero.",
                "- `LiquidityTooHigh` - Provided liquidity exceeds u128::max.",
                "- `TokenMaxExceeded` - The required token to perform this operation exceeds the user defined amount."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "memoProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "positionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "position",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "positionTokenAccount",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayLower",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayUpper",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "liquidityAmount",
                    "type": "u128"
                },
                {
                    "name": "tokenMaxA",
                    "type": "u64"
                },
                {
                    "name": "tokenMaxB",
                    "type": "u64"
                },
                {
                    "name": "remainingAccountsInfo",
                    "type": {
                        "option": {
                            "defined": "RemainingAccountsInfo"
                        }
                    }
                }
            ]
        },
        {
            "name": "initializePoolV2",
            "docs": [
                "Initializes a Whirlpool account.",
                "This instruction works with both Token and Token-2022.",
                "Fee rate is set to the default values on the config and supplied fee_tier.",
                "",
                "### Parameters",
                "- `bumps` - The bump value when deriving the PDA of the Whirlpool address.",
                "- `tick_spacing` - The desired tick spacing for this pool.",
                "- `initial_sqrt_price` - The desired initial sqrt-price for this pool",
                "",
                "#### Special Errors",
                "`InvalidTokenMintOrder` - The order of mints have to be ordered by",
                "`SqrtPriceOutOfBounds` - provided initial_sqrt_price is not between 2^-64 to 2^64",
                ""
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadgeA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadgeB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "feeTier",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "tickSpacing",
                    "type": "u16"
                },
                {
                    "name": "initialSqrtPrice",
                    "type": "u128"
                }
            ]
        },
        {
            "name": "initializeRewardV2",
            "docs": [
                "Initialize reward for a Whirlpool. A pool can only support up to a set number of rewards.",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- \"reward_authority\" - assigned authority by the reward_super_authority for the specified",
                "reward-index in this Whirlpool",
                "",
                "### Parameters",
                "- `reward_index` - The reward index that we'd like to initialize. (0 <= index <= NUM_REWARDS)",
                "",
                "#### Special Errors",
                "- `InvalidRewardIndex` - If the provided reward index doesn't match the lowest uninitialized",
                "index in this pool, or exceeds NUM_REWARDS, or",
                "all reward slots for this pool has been initialized."
            ],
            "accounts": [
                {
                    "name": "rewardAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardMint",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rewardTokenBadge",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rewardVault",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "rewardTokenProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "rent",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "rewardIndex",
                    "type": "u8"
                }
            ]
        },
        {
            "name": "setRewardEmissionsV2",
            "docs": [
                "Set the reward emissions for a reward in a Whirlpool.",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- \"reward_authority\" - assigned authority by the reward_super_authority for the specified",
                "reward-index in this Whirlpool",
                "",
                "### Parameters",
                "- `reward_index` - The reward index (0 <= index <= NUM_REWARDS) that we'd like to modify.",
                "- `emissions_per_second_x64` - The amount of rewards emitted in this pool.",
                "",
                "#### Special Errors",
                "- `RewardVaultAmountInsufficient` - The amount of rewards in the reward vault cannot emit",
                "more than a day of desired emissions.",
                "- `InvalidTimestamp` - Provided timestamp is not in order with the previous timestamp.",
                "- `InvalidRewardIndex` - If the provided reward index doesn't match the lowest uninitialized",
                "index in this pool, or exceeds NUM_REWARDS, or",
                "all reward slots for this pool has been initialized."
            ],
            "accounts": [
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "rewardAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "rewardVault",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "rewardIndex",
                    "type": "u8"
                },
                {
                    "name": "emissionsPerSecondX64",
                    "type": "u128"
                }
            ]
        },
        {
            "name": "swapV2",
            "docs": [
                "Perform a swap in this Whirlpool",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- \"token_authority\" - The authority to withdraw tokens from the input token account.",
                "",
                "### Parameters",
                "- `amount` - The amount of input or output token to swap from (depending on amount_specified_is_input).",
                "- `other_amount_threshold` - The maximum/minimum of input/output token to swap into (depending on amount_specified_is_input).",
                "- `sqrt_price_limit` - The maximum/minimum price the swap will swap to.",
                "- `amount_specified_is_input` - Specifies the token the parameter `amount`represents. If true, the amount represents the input token of the swap.",
                "- `a_to_b` - The direction of the swap. True if swapping from A to B. False if swapping from B to A.",
                "",
                "#### Special Errors",
                "- `ZeroTradableAmount` - User provided parameter `amount` is 0.",
                "- `InvalidSqrtPriceLimitDirection` - User provided parameter `sqrt_price_limit` does not match the direction of the trade.",
                "- `SqrtPriceOutOfBounds` - User provided parameter `sqrt_price_limit` is over Whirlppool's max/min bounds for sqrt-price.",
                "- `InvalidTickArraySequence` - User provided tick-arrays are not in sequential order required to proceed in this trade direction.",
                "- `TickArraySequenceInvalidIndex` - The swap loop attempted to access an invalid array index during the query of the next initialized tick.",
                "- `TickArrayIndexOutofBounds` - The swap loop attempted to access an invalid array index during tick crossing.",
                "- `LiquidityOverflow` - Liquidity value overflowed 128bits during tick crossing.",
                "- `InvalidTickSpacing` - The swap pool was initialized with tick-spacing of 0."
            ],
            "accounts": [
                {
                    "name": "tokenProgramA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "memoProgram",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "whirlpool",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenMintA",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintB",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultA",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultB",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArray0",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArray1",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArray2",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "oracle",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "amount",
                    "type": "u64"
                },
                {
                    "name": "otherAmountThreshold",
                    "type": "u64"
                },
                {
                    "name": "sqrtPriceLimit",
                    "type": "u128"
                },
                {
                    "name": "amountSpecifiedIsInput",
                    "type": "bool"
                },
                {
                    "name": "aToB",
                    "type": "bool"
                },
                {
                    "name": "remainingAccountsInfo",
                    "type": {
                        "option": {
                            "defined": "RemainingAccountsInfo"
                        }
                    }
                }
            ]
        },
        {
            "name": "twoHopSwapV2",
            "docs": [
                "Perform a two-hop swap in this Whirlpool",
                "This instruction works with both Token and Token-2022.",
                "",
                "### Authority",
                "- \"token_authority\" - The authority to withdraw tokens from the input token account.",
                "",
                "### Parameters",
                "- `amount` - The amount of input or output token to swap from (depending on amount_specified_is_input).",
                "- `other_amount_threshold` - The maximum/minimum of input/output token to swap into (depending on amount_specified_is_input).",
                "- `amount_specified_is_input` - Specifies the token the parameter `amount`represents. If true, the amount represents the input token of the swap.",
                "- `a_to_b_one` - The direction of the swap of hop one. True if swapping from A to B. False if swapping from B to A.",
                "- `a_to_b_two` - The direction of the swap of hop two. True if swapping from A to B. False if swapping from B to A.",
                "- `sqrt_price_limit_one` - The maximum/minimum price the swap will swap to in the first hop.",
                "- `sqrt_price_limit_two` - The maximum/minimum price the swap will swap to in the second hop.",
                "",
                "#### Special Errors",
                "- `ZeroTradableAmount` - User provided parameter `amount` is 0.",
                "- `InvalidSqrtPriceLimitDirection` - User provided parameter `sqrt_price_limit` does not match the direction of the trade.",
                "- `SqrtPriceOutOfBounds` - User provided parameter `sqrt_price_limit` is over Whirlppool's max/min bounds for sqrt-price.",
                "- `InvalidTickArraySequence` - User provided tick-arrays are not in sequential order required to proceed in this trade direction.",
                "- `TickArraySequenceInvalidIndex` - The swap loop attempted to access an invalid array index during the query of the next initialized tick.",
                "- `TickArrayIndexOutofBounds` - The swap loop attempted to access an invalid array index during tick crossing.",
                "- `LiquidityOverflow` - Liquidity value overflowed 128bits during tick crossing.",
                "- `InvalidTickSpacing` - The swap pool was initialized with tick-spacing of 0.",
                "- `InvalidIntermediaryMint` - Error if the intermediary mint between hop one and two do not equal.",
                "- `DuplicateTwoHopPool` - Error if whirlpool one & two are the same pool."
            ],
            "accounts": [
                {
                    "name": "whirlpoolOne",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "whirlpoolTwo",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenMintInput",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintIntermediate",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenMintOutput",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramInput",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramIntermediate",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenProgramOutput",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountInput",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultOneInput",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultOneIntermediate",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultTwoIntermediate",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenVaultTwoOutput",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenOwnerAccountOutput",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tokenAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "tickArrayOne0",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayOne1",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayOne2",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayTwo0",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayTwo1",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "tickArrayTwo2",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "oracleOne",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "oracleTwo",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "memoProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "amount",
                    "type": "u64"
                },
                {
                    "name": "otherAmountThreshold",
                    "type": "u64"
                },
                {
                    "name": "amountSpecifiedIsInput",
                    "type": "bool"
                },
                {
                    "name": "aToBOne",
                    "type": "bool"
                },
                {
                    "name": "aToBTwo",
                    "type": "bool"
                },
                {
                    "name": "sqrtPriceLimitOne",
                    "type": "u128"
                },
                {
                    "name": "sqrtPriceLimitTwo",
                    "type": "u128"
                },
                {
                    "name": "remainingAccountsInfo",
                    "type": {
                        "option": {
                            "defined": "RemainingAccountsInfo"
                        }
                    }
                }
            ]
        },
        {
            "name": "initializeConfigExtension",
            "docs": [
                "Initializes a WhirlpoolConfigExtension account that hosts info & authorities.",
                "",
                "### Authority",
                "- \"fee_authority\" - Set authority in the WhirlpoolConfig"
            ],
            "accounts": [
                {
                    "name": "config",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "configExtension",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "feeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "setConfigExtensionAuthority",
            "docs": [
                "Sets the config extension authority for a WhirlpoolsConfigExtension.",
                "Only the current config extension authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"config_extension_authority\" - Set authority in the WhirlpoolConfigExtension"
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpoolsConfigExtension",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "configExtensionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newConfigExtensionAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "setTokenBadgeAuthority",
            "docs": [
                "Sets the token badge authority for a WhirlpoolsConfigExtension.",
                "Only the config extension authority has permission to invoke this instruction.",
                "",
                "### Authority",
                "- \"config_extension_authority\" - Set authority in the WhirlpoolConfigExtension"
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpoolsConfigExtension",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "configExtensionAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "newTokenBadgeAuthority",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "initializeTokenBadge",
            "docs": [
                "Initialize a TokenBadge account.",
                "",
                "### Authority",
                "- \"token_badge_authority\" - Set authority in the WhirlpoolConfigExtension",
                "",
                "### Special Errors",
                "- `FeatureIsNotEnabled` - If the feature flag for token badges is not enabled."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpoolsConfigExtension",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadgeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "tokenMint",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadge",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "funder",
                    "isMut": true,
                    "isSigner": true
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "deleteTokenBadge",
            "docs": [
                "Delete a TokenBadge account.",
                "",
                "### Authority",
                "- \"token_badge_authority\" - Set authority in the WhirlpoolConfigExtension",
                "",
                "### Special Errors",
                "- `FeatureIsNotEnabled` - If the feature flag for token badges is not enabled."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpoolsConfigExtension",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadgeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "tokenMint",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadge",
                    "isMut": true,
                    "isSigner": false
                },
                {
                    "name": "receiver",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": []
        },
        {
            "name": "setTokenBadgeAttribute",
            "docs": [
                "Set an attribute on a TokenBadge account.",
                "",
                "### Authority",
                "- \"token_badge_authority\" - Set authority in the WhirlpoolConfigExtension",
                "",
                "### Parameters",
                "- `attribute` - The attribute to set on the TokenBadge account.",
                "",
                "#### Special Errors",
                "- `FeatureIsNotEnabled` - If the feature flag for token badges is not enabled."
            ],
            "accounts": [
                {
                    "name": "whirlpoolsConfig",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "whirlpoolsConfigExtension",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadgeAuthority",
                    "isMut": false,
                    "isSigner": true
                },
                {
                    "name": "tokenMint",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "tokenBadge",
                    "isMut": true,
                    "isSigner": false
                }
            ],
            "args": [
                {
                    "name": "attribute",
                    "type": {
                        "defined": "TokenBadgeAttribute"
                    }
                }
            ]
        },
        {
            "name": "idlInclude",
            "accounts": [
                {
                    "name": "tickArray",
                    "isMut": false,
                    "isSigner": false
                },
                {
                    "name": "systemProgram",
                    "isMut": false,
                    "isSigner": false
                }
            ],
            "args": []
        }
    ],
    "accounts": [
        {
            "name": "AdaptiveFeeTier",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "whirlpoolsConfig",
                        "type": "publicKey"
                    },
                    {
                        "name": "feeTierIndex",
                        "type": "u16"
                    },
                    {
                        "name": "tickSpacing",
                        "type": "u16"
                    },
                    {
                        "name": "initializePoolAuthority",
                        "type": "publicKey"
                    },
                    {
                        "name": "delegatedFeeAuthority",
                        "type": "publicKey"
                    },
                    {
                        "name": "defaultBaseFeeRate",
                        "type": "u16"
                    },
                    {
                        "name": "filterPeriod",
                        "type": "u16"
                    },
                    {
                        "name": "decayPeriod",
                        "type": "u16"
                    },
                    {
                        "name": "reductionFactor",
                        "type": "u16"
                    },
                    {
                        "name": "adaptiveFeeControlFactor",
                        "type": "u32"
                    },
                    {
                        "name": "maxVolatilityAccumulator",
                        "type": "u32"
                    },
                    {
                        "name": "tickGroupSize",
                        "type": "u16"
                    },
                    {
                        "name": "majorSwapThresholdTicks",
                        "type": "u16"
                    }
                ]
            }
        },
        {
            "name": "WhirlpoolsConfig",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "feeAuthority",
                        "type": "publicKey"
                    },
                    {
                        "name": "collectProtocolFeesAuthority",
                        "type": "publicKey"
                    },
                    {
                        "name": "rewardEmissionsSuperAuthority",
                        "type": "publicKey"
                    },
                    {
                        "name": "defaultProtocolFeeRate",
                        "type": "u16"
                    },
                    {
                        "name": "featureFlags",
                        "type": "u16"
                    }
                ]
            }
        },
        {
            "name": "WhirlpoolsConfigExtension",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "whirlpoolsConfig",
                        "type": "publicKey"
                    },
                    {
                        "name": "configExtensionAuthority",
                        "type": "publicKey"
                    },
                    {
                        "name": "tokenBadgeAuthority",
                        "type": "publicKey"
                    }
                ]
            }
        },
        {
            "name": "DynamicTickArray",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "startTickIndex",
                        "type": "i32"
                    },
                    {
                        "name": "whirlpool",
                        "type": "publicKey"
                    },
                    {
                        "name": "tickBitmap",
                        "type": "u128"
                    },
                    {
                        "name": "ticks",
                        "type": {
                            "array": [
                                {
                                    "defined": "DynamicTick"
                                },
                                88
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "FeeTier",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "whirlpoolsConfig",
                        "type": "publicKey"
                    },
                    {
                        "name": "tickSpacing",
                        "type": "u16"
                    },
                    {
                        "name": "defaultFeeRate",
                        "type": "u16"
                    }
                ]
            }
        },
        {
            "name": "TickArray",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "startTickIndex",
                        "type": "i32"
                    },
                    {
                        "name": "ticks",
                        "type": {
                            "array": [
                                {
                                    "defined": "Tick"
                                },
                                88
                            ]
                        }
                    },
                    {
                        "name": "whirlpool",
                        "type": "publicKey"
                    }
                ]
            }
        },
        {
            "name": "LockConfig",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "position",
                        "type": "publicKey"
                    },
                    {
                        "name": "positionOwner",
                        "type": "publicKey"
                    },
                    {
                        "name": "whirlpool",
                        "type": "publicKey"
                    },
                    {
                        "name": "lockedTimestamp",
                        "type": "u64"
                    },
                    {
                        "name": "lockType",
                        "type": {
                            "defined": "LockTypeLabel"
                        }
                    }
                ]
            }
        },
        {
            "name": "Oracle",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "whirlpool",
                        "type": "publicKey"
                    },
                    {
                        "name": "tradeEnableTimestamp",
                        "type": "u64"
                    },
                    {
                        "name": "adaptiveFeeConstants",
                        "type": {
                            "defined": "AdaptiveFeeConstants"
                        }
                    },
                    {
                        "name": "adaptiveFeeVariables",
                        "type": {
                            "defined": "AdaptiveFeeVariables"
                        }
                    },
                    {
                        "name": "reserved",
                        "type": {
                            "array": [
                                "u8",
                                128
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "Position",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "whirlpool",
                        "type": "publicKey"
                    },
                    {
                        "name": "positionMint",
                        "type": "publicKey"
                    },
                    {
                        "name": "liquidity",
                        "type": "u128"
                    },
                    {
                        "name": "tickLowerIndex",
                        "type": "i32"
                    },
                    {
                        "name": "tickUpperIndex",
                        "type": "i32"
                    },
                    {
                        "name": "feeGrowthCheckpointA",
                        "type": "u128"
                    },
                    {
                        "name": "feeOwedA",
                        "type": "u64"
                    },
                    {
                        "name": "feeGrowthCheckpointB",
                        "type": "u128"
                    },
                    {
                        "name": "feeOwedB",
                        "type": "u64"
                    },
                    {
                        "name": "rewardInfos",
                        "type": {
                            "array": [
                                {
                                    "defined": "PositionRewardInfo"
                                },
                                3
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "PositionBundle",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "positionBundleMint",
                        "type": "publicKey"
                    },
                    {
                        "name": "positionBitmap",
                        "type": {
                            "array": [
                                "u8",
                                32
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "TokenBadge",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "whirlpoolsConfig",
                        "type": "publicKey"
                    },
                    {
                        "name": "tokenMint",
                        "type": "publicKey"
                    },
                    {
                        "name": "attributeRequireNonTransferablePosition",
                        "type": "bool"
                    }
                ]
            }
        },
        {
            "name": "Whirlpool",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "whirlpoolsConfig",
                        "type": "publicKey"
                    },
                    {
                        "name": "whirlpoolBump",
                        "type": {
                            "array": [
                                "u8",
                                1
                            ]
                        }
                    },
                    {
                        "name": "tickSpacing",
                        "type": "u16"
                    },
                    {
                        "name": "feeTierIndexSeed",
                        "type": {
                            "array": [
                                "u8",
                                2
                            ]
                        }
                    },
                    {
                        "name": "feeRate",
                        "type": "u16"
                    },
                    {
                        "name": "protocolFeeRate",
                        "type": "u16"
                    },
                    {
                        "name": "liquidity",
                        "type": "u128"
                    },
                    {
                        "name": "sqrtPrice",
                        "type": "u128"
                    },
                    {
                        "name": "tickCurrentIndex",
                        "type": "i32"
                    },
                    {
                        "name": "protocolFeeOwedA",
                        "type": "u64"
                    },
                    {
                        "name": "protocolFeeOwedB",
                        "type": "u64"
                    },
                    {
                        "name": "tokenMintA",
                        "type": "publicKey"
                    },
                    {
                        "name": "tokenVaultA",
                        "type": "publicKey"
                    },
                    {
                        "name": "feeGrowthGlobalA",
                        "type": "u128"
                    },
                    {
                        "name": "tokenMintB",
                        "type": "publicKey"
                    },
                    {
                        "name": "tokenVaultB",
                        "type": "publicKey"
                    },
                    {
                        "name": "feeGrowthGlobalB",
                        "type": "u128"
                    },
                    {
                        "name": "rewardLastUpdatedTimestamp",
                        "type": "u64"
                    },
                    {
                        "name": "rewardInfos",
                        "type": {
                            "array": [
                                {
                                    "defined": "WhirlpoolRewardInfo"
                                },
                                3
                            ]
                        }
                    }
                ]
            }
        }
    ],
    "types": [
        {
            "name": "ConfigFeatureFlag",
            "type": {
                "kind": "enum",
                "variants": [
                    {
                        "name": "TokenBadge",
                        "fields": [
                            "bool"
                        ]
                    }
                ]
            }
        },
        {
            "name": "DynamicTick",
            "type": {
                "kind": "enum",
                "variants": [
                    {
                        "name": "Uninitialized"
                    },
                    {
                        "name": "Initialized",
                        "fields": [
                            {
                                "defined": "DynamicTickData"
                            }
                        ]
                    }
                ]
            }
        },
        {
            "name": "DynamicTickData",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "liquidityNet",
                        "type": "i128"
                    },
                    {
                        "name": "liquidityGross",
                        "type": "u128"
                    },
                    {
                        "name": "feeGrowthOutsideA",
                        "type": "u128"
                    },
                    {
                        "name": "feeGrowthOutsideB",
                        "type": "u128"
                    },
                    {
                        "name": "rewardGrowthsOutside",
                        "type": {
                            "array": [
                                "u128",
                                3
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "LockType",
            "type": {
                "kind": "enum",
                "variants": [
                    {
                        "name": "Permanent"
                    }
                ]
            }
        },
        {
            "name": "LockTypeLabel",
            "type": {
                "kind": "enum",
                "variants": [
                    {
                        "name": "Permanent"
                    }
                ]
            }
        },
        {
            "name": "AdaptiveFeeConstants",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "filterPeriod",
                        "type": "u16"
                    },
                    {
                        "name": "decayPeriod",
                        "type": "u16"
                    },
                    {
                        "name": "reductionFactor",
                        "type": "u16"
                    },
                    {
                        "name": "adaptiveFeeControlFactor",
                        "type": "u32"
                    },
                    {
                        "name": "maxVolatilityAccumulator",
                        "type": "u32"
                    },
                    {
                        "name": "tickGroupSize",
                        "type": "u16"
                    },
                    {
                        "name": "majorSwapThresholdTicks",
                        "type": "u16"
                    },
                    {
                        "name": "reserved",
                        "type": {
                            "array": [
                                "u8",
                                16
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "AdaptiveFeeVariables",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "lastReferenceUpdateTimestamp",
                        "type": "u64"
                    },
                    {
                        "name": "lastMajorSwapTimestamp",
                        "type": "u64"
                    },
                    {
                        "name": "volatilityReference",
                        "type": "u32"
                    },
                    {
                        "name": "tickGroupIndexReference",
                        "type": "i32"
                    },
                    {
                        "name": "volatilityAccumulator",
                        "type": "u32"
                    },
                    {
                        "name": "reserved",
                        "type": {
                            "array": [
                                "u8",
                                16
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "OpenPositionBumps",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "positionBump",
                        "type": "u8"
                    }
                ]
            }
        },
        {
            "name": "OpenPositionWithMetadataBumps",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "positionBump",
                        "type": "u8"
                    },
                    {
                        "name": "metadataBump",
                        "type": "u8"
                    }
                ]
            }
        },
        {
            "name": "PositionRewardInfo",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "growthInsideCheckpoint",
                        "type": "u128"
                    },
                    {
                        "name": "amountOwed",
                        "type": "u64"
                    }
                ]
            }
        },
        {
            "name": "Tick",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "initialized",
                        "type": "bool"
                    },
                    {
                        "name": "liquidityNet",
                        "type": "i128"
                    },
                    {
                        "name": "liquidityGross",
                        "type": "u128"
                    },
                    {
                        "name": "feeGrowthOutsideA",
                        "type": "u128"
                    },
                    {
                        "name": "feeGrowthOutsideB",
                        "type": "u128"
                    },
                    {
                        "name": "rewardGrowthsOutside",
                        "type": {
                            "array": [
                                "u128",
                                3
                            ]
                        }
                    }
                ]
            }
        },
        {
            "name": "TokenBadgeAttribute",
            "type": {
                "kind": "enum",
                "variants": [
                    {
                        "name": "RequireNonTransferablePosition",
                        "fields": [
                            "bool"
                        ]
                    }
                ]
            }
        },
        {
            "name": "WhirlpoolBumps",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "whirlpoolBump",
                        "type": "u8"
                    }
                ]
            }
        },
        {
            "name": "WhirlpoolRewardInfo",
            "docs": [
                "Stores the state relevant for tracking liquidity mining rewards at the `Whirlpool` level.",
                "These values are used in conjunction with `PositionRewardInfo`, `Tick.reward_growths_outside`,",
                "and `Whirlpool.reward_last_updated_timestamp` to determine how many rewards are earned by open",
                "positions."
            ],
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "mint",
                        "docs": [
                            "Reward token mint."
                        ],
                        "type": "publicKey"
                    },
                    {
                        "name": "vault",
                        "docs": [
                            "Reward vault token account."
                        ],
                        "type": "publicKey"
                    },
                    {
                        "name": "extension",
                        "docs": [
                            "reward_infos[0]: Authority account that has permission to initialize the reward and set emissions.",
                            "reward_infos[1]: used for a struct that contains fields for extending the functionality of Whirlpool.",
                            "reward_infos[2]: reserved for future use.",
                            "",
                            "Historical notes:",
                            "Originally, this was a field named \"authority\", but it was found that there was no opportunity",
                            "to set different authorities for the three rewards. Therefore, the use of this field was changed for Whirlpool's future extensibility."
                        ],
                        "type": {
                            "array": [
                                "u8",
                                32
                            ]
                        }
                    },
                    {
                        "name": "emissionsPerSecondX64",
                        "docs": [
                            "Q64.64 number that indicates how many tokens per second are earned per unit of liquidity."
                        ],
                        "type": "u128"
                    },
                    {
                        "name": "growthGlobalX64",
                        "docs": [
                            "Q64.64 number that tracks the total tokens earned per unit of liquidity since the reward",
                            "emissions were turned on."
                        ],
                        "type": "u128"
                    }
                ]
            }
        },
        {
            "name": "AccountsType",
            "type": {
                "kind": "enum",
                "variants": [
                    {
                        "name": "TransferHookA"
                    },
                    {
                        "name": "TransferHookB"
                    },
                    {
                        "name": "TransferHookReward"
                    },
                    {
                        "name": "TransferHookInput"
                    },
                    {
                        "name": "TransferHookIntermediate"
                    },
                    {
                        "name": "TransferHookOutput"
                    },
                    {
                        "name": "SupplementalTickArrays"
                    },
                    {
                        "name": "SupplementalTickArraysOne"
                    },
                    {
                        "name": "SupplementalTickArraysTwo"
                    }
                ]
            }
        },
        {
            "name": "RemainingAccountsInfo",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "slices",
                        "type": {
                            "vec": {
                                "defined": "RemainingAccountsSlice"
                            }
                        }
                    }
                ]
            }
        },
        {
            "name": "RemainingAccountsSlice",
            "type": {
                "kind": "struct",
                "fields": [
                    {
                        "name": "accountsType",
                        "type": {
                            "defined": "AccountsType"
                        }
                    },
                    {
                        "name": "length",
                        "type": "u8"
                    }
                ]
            }
        }
    ],
    "events": [
        {
            "name": "LiquidityDecreased",
            "fields": [
                {
                    "name": "whirlpool",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "position",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "tickLowerIndex",
                    "type": "i32",
                    "index": false
                },
                {
                    "name": "tickUpperIndex",
                    "type": "i32",
                    "index": false
                },
                {
                    "name": "liquidity",
                    "type": "u128",
                    "index": false
                },
                {
                    "name": "tokenAAmount",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "tokenBAmount",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "tokenATransferFee",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "tokenBTransferFee",
                    "type": "u64",
                    "index": false
                }
            ]
        },
        {
            "name": "LiquidityIncreased",
            "fields": [
                {
                    "name": "whirlpool",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "position",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "tickLowerIndex",
                    "type": "i32",
                    "index": false
                },
                {
                    "name": "tickUpperIndex",
                    "type": "i32",
                    "index": false
                },
                {
                    "name": "liquidity",
                    "type": "u128",
                    "index": false
                },
                {
                    "name": "tokenAAmount",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "tokenBAmount",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "tokenATransferFee",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "tokenBTransferFee",
                    "type": "u64",
                    "index": false
                }
            ]
        },
        {
            "name": "PoolInitialized",
            "fields": [
                {
                    "name": "whirlpool",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "whirlpoolsConfig",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "tokenMintA",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "tokenMintB",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "tickSpacing",
                    "type": "u16",
                    "index": false
                },
                {
                    "name": "tokenProgramA",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "tokenProgramB",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "decimalsA",
                    "type": "u8",
                    "index": false
                },
                {
                    "name": "decimalsB",
                    "type": "u8",
                    "index": false
                },
                {
                    "name": "initialSqrtPrice",
                    "type": "u128",
                    "index": false
                }
            ]
        },
        {
            "name": "Traded",
            "fields": [
                {
                    "name": "whirlpool",
                    "type": "publicKey",
                    "index": false
                },
                {
                    "name": "aToB",
                    "type": "bool",
                    "index": false
                },
                {
                    "name": "preSqrtPrice",
                    "type": "u128",
                    "index": false
                },
                {
                    "name": "postSqrtPrice",
                    "type": "u128",
                    "index": false
                },
                {
                    "name": "inputAmount",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "outputAmount",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "inputTransferFee",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "outputTransferFee",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "lpFee",
                    "type": "u64",
                    "index": false
                },
                {
                    "name": "protocolFee",
                    "type": "u64",
                    "index": false
                }
            ]
        }
    ],
    "errors": [
        {
            "code": 6000,
            "name": "InvalidEnum",
            "msg": "Enum value could not be converted"
        },
        {
            "code": 6001,
            "name": "InvalidStartTick",
            "msg": "Invalid start tick index provided."
        },
        {
            "code": 6002,
            "name": "TickArrayExistInPool",
            "msg": "Tick-array already exists in this whirlpool"
        },
        {
            "code": 6003,
            "name": "TickArrayIndexOutofBounds",
            "msg": "Attempt to search for a tick-array failed"
        },
        {
            "code": 6004,
            "name": "InvalidTickSpacing",
            "msg": "Tick-spacing is not supported"
        },
        {
            "code": 6005,
            "name": "ClosePositionNotEmpty",
            "msg": "Position is not empty It cannot be closed"
        },
        {
            "code": 6006,
            "name": "DivideByZero",
            "msg": "Unable to divide by zero"
        },
        {
            "code": 6007,
            "name": "NumberCastError",
            "msg": "Unable to cast number into BigInt"
        },
        {
            "code": 6008,
            "name": "NumberDownCastError",
            "msg": "Unable to down cast number"
        },
        {
            "code": 6009,
            "name": "TickNotFound",
            "msg": "Tick not found within tick array"
        },
        {
            "code": 6010,
            "name": "InvalidTickIndex",
            "msg": "Provided tick index is either out of bounds or uninitializable"
        },
        {
            "code": 6011,
            "name": "SqrtPriceOutOfBounds",
            "msg": "Provided sqrt price out of bounds"
        },
        {
            "code": 6012,
            "name": "LiquidityZero",
            "msg": "Liquidity amount must be greater than zero"
        },
        {
            "code": 6013,
            "name": "LiquidityTooHigh",
            "msg": "Liquidity amount must be less than i64::MAX"
        },
        {
            "code": 6014,
            "name": "LiquidityOverflow",
            "msg": "Liquidity overflow"
        },
        {
            "code": 6015,
            "name": "LiquidityUnderflow",
            "msg": "Liquidity underflow"
        },
        {
            "code": 6016,
            "name": "LiquidityNetError",
            "msg": "Tick liquidity net underflowed or overflowed"
        },
        {
            "code": 6017,
            "name": "TokenMaxExceeded",
            "msg": "Exceeded token max"
        },
        {
            "code": 6018,
            "name": "TokenMinSubceeded",
            "msg": "Did not meet token min"
        },
        {
            "code": 6019,
            "name": "MissingOrInvalidDelegate",
            "msg": "Position token account has a missing or invalid delegate"
        },
        {
            "code": 6020,
            "name": "InvalidPositionTokenAmount",
            "msg": "Position token amount must be 1"
        },
        {
            "code": 6021,
            "name": "InvalidTimestampConversion",
            "msg": "Timestamp should be convertible from i64 to u64"
        },
        {
            "code": 6022,
            "name": "InvalidTimestamp",
            "msg": "Timestamp should be greater than the last updated timestamp"
        },
        {
            "code": 6023,
            "name": "InvalidTickArraySequence",
            "msg": "Invalid tick array sequence provided for instruction."
        },
        {
            "code": 6024,
            "name": "InvalidTokenMintOrder",
            "msg": "Token Mint in wrong order"
        },
        {
            "code": 6025,
            "name": "RewardNotInitialized",
            "msg": "Reward not initialized"
        },
        {
            "code": 6026,
            "name": "InvalidRewardIndex",
            "msg": "Invalid reward index"
        },
        {
            "code": 6027,
            "name": "RewardVaultAmountInsufficient",
            "msg": "Reward vault requires amount to support emissions for at least one day"
        },
        {
            "code": 6028,
            "name": "FeeRateMaxExceeded",
            "msg": "Exceeded max fee rate"
        },
        {
            "code": 6029,
            "name": "ProtocolFeeRateMaxExceeded",
            "msg": "Exceeded max protocol fee rate"
        },
        {
            "code": 6030,
            "name": "MultiplicationShiftRightOverflow",
            "msg": "Multiplication with shift right overflow"
        },
        {
            "code": 6031,
            "name": "MulDivOverflow",
            "msg": "Muldiv overflow"
        },
        {
            "code": 6032,
            "name": "MulDivInvalidInput",
            "msg": "Invalid div_u256 input"
        },
        {
            "code": 6033,
            "name": "MultiplicationOverflow",
            "msg": "Multiplication overflow"
        },
        {
            "code": 6034,
            "name": "InvalidSqrtPriceLimitDirection",
            "msg": "Provided SqrtPriceLimit not in the same direction as the swap."
        },
        {
            "code": 6035,
            "name": "ZeroTradableAmount",
            "msg": "There are no tradable amount to swap."
        },
        {
            "code": 6036,
            "name": "AmountOutBelowMinimum",
            "msg": "Amount out below minimum threshold"
        },
        {
            "code": 6037,
            "name": "AmountInAboveMaximum",
            "msg": "Amount in above maximum threshold"
        },
        {
            "code": 6038,
            "name": "TickArraySequenceInvalidIndex",
            "msg": "Invalid index for tick array sequence"
        },
        {
            "code": 6039,
            "name": "AmountCalcOverflow",
            "msg": "Amount calculated overflows"
        },
        {
            "code": 6040,
            "name": "AmountRemainingOverflow",
            "msg": "Amount remaining overflows"
        },
        {
            "code": 6041,
            "name": "InvalidIntermediaryMint",
            "msg": "Invalid intermediary mint"
        },
        {
            "code": 6042,
            "name": "DuplicateTwoHopPool",
            "msg": "Duplicate two hop pool"
        },
        {
            "code": 6043,
            "name": "InvalidBundleIndex",
            "msg": "Bundle index is out of bounds"
        },
        {
            "code": 6044,
            "name": "BundledPositionAlreadyOpened",
            "msg": "Position has already been opened"
        },
        {
            "code": 6045,
            "name": "BundledPositionAlreadyClosed",
            "msg": "Position has already been closed"
        },
        {
            "code": 6046,
            "name": "PositionBundleNotDeletable",
            "msg": "Unable to delete PositionBundle with open positions"
        },
        {
            "code": 6047,
            "name": "UnsupportedTokenMint",
            "msg": "Token mint has unsupported attributes"
        },
        {
            "code": 6048,
            "name": "RemainingAccountsInvalidSlice",
            "msg": "Invalid remaining accounts"
        },
        {
            "code": 6049,
            "name": "RemainingAccountsInsufficient",
            "msg": "Insufficient remaining accounts"
        },
        {
            "code": 6050,
            "name": "NoExtraAccountsForTransferHook",
            "msg": "Unable to call transfer hook without extra accounts"
        },
        {
            "code": 6051,
            "name": "IntermediateTokenAmountMismatch",
            "msg": "Output and input amount mismatch"
        },
        {
            "code": 6052,
            "name": "TransferFeeCalculationError",
            "msg": "Transfer fee calculation failed"
        },
        {
            "code": 6053,
            "name": "RemainingAccountsDuplicatedAccountsType",
            "msg": "Same accounts type is provided more than once"
        },
        {
            "code": 6054,
            "name": "FullRangeOnlyPool",
            "msg": "This whirlpool only supports full-range positions"
        },
        {
            "code": 6055,
            "name": "TooManySupplementalTickArrays",
            "msg": "Too many supplemental tick arrays provided"
        },
        {
            "code": 6056,
            "name": "DifferentWhirlpoolTickArrayAccount",
            "msg": "TickArray account for different whirlpool provided"
        },
        {
            "code": 6057,
            "name": "PartialFillError",
            "msg": "Trade resulted in partial fill"
        },
        {
            "code": 6058,
            "name": "PositionNotLockable",
            "msg": "Position is not lockable"
        },
        {
            "code": 6059,
            "name": "OperationNotAllowedOnLockedPosition",
            "msg": "Operation not allowed on locked position"
        },
        {
            "code": 6060,
            "name": "SameTickRangeNotAllowed",
            "msg": "Cannot reset position range with same tick range"
        },
        {
            "code": 6061,
            "name": "InvalidAdaptiveFeeConstants",
            "msg": "Invalid adaptive fee constants"
        },
        {
            "code": 6062,
            "name": "InvalidFeeTierIndex",
            "msg": "Invalid fee tier index"
        },
        {
            "code": 6063,
            "name": "InvalidTradeEnableTimestamp",
            "msg": "Invalid trade enable timestamp"
        },
        {
            "code": 6064,
            "name": "TradeIsNotEnabled",
            "msg": "Trade is not enabled yet"
        },
        {
            "code": 6065,
            "name": "RentCalculationError",
            "msg": "Rent calculation error"
        },
        {
            "code": 6066,
            "name": "FeatureIsNotEnabled",
            "msg": "Feature is not enabled"
        },
        {
            "code": 6067,
            "name": "PositionWithTokenExtensionsRequired",
            "msg": "This whirlpool only supports open_position_with_token_extensions instruction"
        }
    ]
}

idls = {
  'dlmm': idl_dlmm,
  'ammV1': idl_ammV1,
  'ammV2': idl_ammV2,
  'metadata': idl_orca,
}