# Send

A SEND moves tokens of one ticker from the token outputs a transaction spends to output 1. Everything else goes to output 2. A market fill is also a SEND.

## Example

```
{
  "p": "lucky-20",
  "op": "send",
  "tick": "LUCKY",
  "amt": "1200"
}
```

Shown with line breaks for reading. On chain the payload is one line with no spaces. The payload is compact JSON: no spaces, the keys in this order, no other key.

| Key | Required? | Description |
| --- | --- | --- |
| `p` | Yes | Always `lucky-20`, in lower case. |
| `op` | Yes | `send`, in lower case. |
| `tick` | Yes | The ticker to move: 1 to 8 characters, `A`–`Z` and `0`–`9`, in quotes. |
| `amt` | Yes | Whole tokens to move, 1 to 21,000,000, in quotes. Decimal digits only: no sign, no decimal point, no leading zero. |

A payload with a key missing, an extra key, another order, a space, or a value that breaks its rule is not a SEND. The transaction is then treated like one without a LUCKY-20 payload (see Default routing below).

The payload names no output: the positions are fixed. This example moves 1,200 `LUCKY` to output 1 and everything else to output 2.

## Reference transaction

| vout | value | to |
| --- | --- | --- |
| 0 | 0 | OP_RETURN with the payload above |
| 1 | 546 sats | recipient (receives `AMT`) |
| 2 | 546 sats | you (the **residual output**, always present) |
| 3 | change | you, BTC change (optional; it never carries tokens) |

## Result

The SEND is **applied** when both of these hold:

- the inputs hold at least `AMT` of the ticker;
- output 1 exists and is not an OP_RETURN output.

Then `AMT` goes to output 1. The rest of that ticker, and every other ticker on the inputs, goes to output 2.

When the SEND is not applied, nothing goes to output 1. All tokens on the inputs go to output 2.

If output 2 is missing or is an OP_RETURN output, what it would receive goes to the default output instead: the first output that is not an OP_RETURN output.

```
inputs     { LUCKY: 1,500, ABC: 500 }
payload    {"p":"lucky-20","op":"send","tick":"LUCKY","amt":"1200"}
vout1      { LUCKY: 1,200 }             the recipient
vout2      { LUCKY: 300, ABC: 500 }     back to you
```

## Notes

- **One ticker per SEND.** Only the named ticker moves to output 1. One SEND can therefore split a token output that holds several tickers.
- **Keep the residual output.** Output 2 exists even when it receives nothing. Never drop it as dust. Without it, what it would receive goes to the default output — in this layout, the recipient's output 1. It also keeps tokens off the BTC change output, so a later plain BTC spend of the change cannot carry them away.
- **Write the payload byte for byte.** Build it from the template above. Many JSON libraries add a space after `:` or `,`, or write `amt` as a number, unless told otherwise. Such a payload is not a SEND: the transaction is a plain spend, and every token on its inputs goes to the default output — in this layout, the recipient's output 1.
- **Default routing.** A Bitcoin transaction without a LUCKY-20 payload moves all tokens on its inputs to its default output, the first output that is not an OP_RETURN output. The tokens are not destroyed. They are burned only when the transaction has no such output, or when that output has no address.
- **Listed outputs.** An input signed as a market listing moves only through a SEND of its own ticker that is applied. Otherwise its tokens go to the output its signature pays, the seller's. See [Wallets](../developers/wallets.md#trading).
- **Tokens never go to an OP_RETURN output.**
- **A trade is a SEND.** A fill keeps the seller's payment at output 0, the tokens at output 1 and the residual at output 2. See [Wallets](../developers/wallets.md#trading).
- Transactions confirmed below block 969,696 do nothing.
