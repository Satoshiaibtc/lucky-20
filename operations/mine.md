# Mine

A MINE creates new tokens of a registered ticker. It names the ticker and nothing else. The hash of the Bitcoin block that confirms it sets the amount.

## Example

```
{
  "p": "lucky-20",
  "op": "mine",
  "tick": "LUCKY"
}
```

Shown with line breaks for reading. On chain the payload is one line with no spaces. The payload is compact JSON: no spaces, the keys in this order, no other key.

| Key | Required? | Description |
| --- | --- | --- |
| `p` | Yes | Always `lucky-20`, in lower case. |
| `op` | Yes | `mine`, in lower case. |
| `tick` | Yes | A registered ticker: 1 to 8 characters, `A`–`Z` and `0`–`9`, in quotes. |

There is no amount key and no output index. Nothing in the payload changes the yield. The new tokens always go to output 0. Any other spelling — a space, another key order, an extra key — is not a MINE.

## Yield

The last hex digit of the confirming block's hash, as block explorers print it, sets the tier:

| Last hex digit | Tier (tokens) | Digits out of 16 |
| --- | --- | --- |
| `f` | 10,000 | 1 |
| `c` `d` `e` | 2,000 | 3 |
| `7` `8` `9` `a` `b` | 1,000 | 5 |
| `0` `1` `2` `3` `4` `5` `6` | 500 | 7 |

Expected yield: (1 × 10,000 + 3 × 2,000 + 5 × 1,000 + 7 × 500) / 16 = **1,531.25 tokens** per MINE.

The credit is the smaller of the yield and the remaining supply.

Example: a MINE of `LUCKY` confirms in a block whose hash ends in `…a8c3`. The last digit is `3`, so output 0 receives 500 `LUCKY`.

## Reference transaction

| vout | value | to |
| --- | --- | --- |
| 0 | 546 sats | you: the **yield output** |
| 1 | 0 | OP_RETURN with the payload above |
| 2 | change | you (optional) |

## Notes

- **Nobody chooses the amount.** The block hash is found after the MINE is already in the block. Nobody can choose it or know it in advance.
- **Use the hash as explorers print it.** Take the block hash exactly as a block explorer or Bitcoin Core prints it. It starts with zeros.
- **Same block, same tier.** Every MINE in one block receives the same tier, because they share one block hash. MINEs are credited in block order, so near the cap the earlier MINEs of a block are credited first. Only the end of the supply can credit less than the tier.
- **A MINE is valid when** the ticker was registered in an earlier block and output 0 exists and is not an OP_RETURN output. An invalid MINE credits nothing. A MINE in the same block as the ticker's DEPLOY is invalid, whoever sends it, the deployer included: minting starts in the block after the DEPLOY. A wallet therefore offers MINE once the DEPLOY has confirmed, so that, barring a chain reorganization, the MINE lands in a later block.
- **Final at 6 confirmations.** Until its block has 6 confirmations, the credit is provisional. If Bitcoin replaces that block (a reorganization), the MINE is credited again from the hash of the block that confirms it in the new chain, and its tier can change.
- **Open mint.** Anyone can mine any registered ticker, as often as they like. There is no per-address cap.
- **After the supply is used up**, a MINE is credited 0, and what it paid in fees is not refunded. Check the remaining supply before you mine.
- **Tokens on the inputs** of a MINE, of every ticker, also go to output 0, even when the MINE is invalid. They are burned only when output 0 is missing or is an OP_RETURN output. An input signed as a market listing is the exception: its tokens go to the output its signature pays.
- **Never pay for a MINE with a token output.** See [Wallets](../developers/wallets.md#never-spend-tokens-as-fees).
- Transactions confirmed below block 969,696 do nothing.
