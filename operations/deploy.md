# Deploy

A deploy registers a new ticker with a fixed supply of 21,000,000 tokens. It takes one transaction. The deployer receives no tokens. Every token comes from a [MINE](mine.md).

## Example

```
{
  "p": "lucky-20",
  "op": "deploy",
  "tick": "LUCKY"
}
```

Shown with line breaks for reading. On chain the payload is one line with no spaces. The payload is compact JSON: no spaces, the keys in this order, no other key.

| Key | Required? | Description |
| --- | --- | --- |
| `p` | Yes | Always `lucky-20`, in lower case. |
| `op` | Yes | `deploy`, in lower case. |
| `tick` | Yes | The ticker: 1 to 8 characters, `A`–`Z` and `0`–`9`, in quotes. |

There is no supply key and no amount key. The supply is always 21,000,000, and the block hash sets the amount of each MINE. Any other spelling — a space, another key order, an extra key — is not a DEPLOY.

## Reference transaction

| vout | value | to |
| --- | --- | --- |
| 0 | 546 sats | you (proof output) |
| 1 | 0 | OP_RETURN with the payload above |
| 2 | change | you (optional) |

## The DEPLOY registers the ticker when it is still free

A DEPLOY registers its ticker when the ticker is not registered yet. A DEPLOY of a ticker that is already registered registers nothing.

Transactions confirmed below block 969,696 do nothing.

## Notes

- **Block order decides.** The first valid DEPLOY of a ticker, by block height and then position in the block, registers it. Another DEPLOY of the same ticker registers nothing, and what it paid in fees is not refunded. The rules look at nothing else: not the fees paid, not the time of broadcast.
- **A pending DEPLOY is public.** The ticker is in plain text, so anyone who reads the mempool can see it and send a DEPLOY of the same ticker. The Bitcoin miner who builds a block sets the order inside it and usually puts a higher fee rate first, so a DEPLOY that pays more normally confirms first. Use a fast fee, signal replace-by-fee, and speed the DEPLOY up if it waits.
- **Final after 6 confirmations.** Until the registering block has 6 confirmations, a reorganization can still change which DEPLOY registered the ticker.
- **The deployer** is the address that signed the whole transaction and contributed the largest share of its inputs. It shows that this address signed the DEPLOY, not who chose the ticker. Input values are summed per address. Only inputs that spend a P2TR output by key path or a P2WPKH output, signed with `SIGHASH_DEFAULT` or `SIGHASH_ALL`, count; an input signed another way, or of another kind, does not. On a tie, the address whose first counted input comes first is the deployer. When no input counts, the ticker is registered with no deployer.
- **Minting starts in the next block.** A MINE in the DEPLOY's own block is invalid.
- **Tokens on the inputs** of a DEPLOY go to the default output: the first output that is not an OP_RETURN output. In the reference layout, that is the proof output. They are burned only when every output is an OP_RETURN output, or when the default output has no address (P2PK, bare multisig, a non-standard script). An input signed as a market listing is the exception: its tokens go to the output its signature pays.
- Wallet steps: [Wallets](../developers/wallets.md#deploy).
