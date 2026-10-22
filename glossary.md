# Glossary

| Term | Meaning |
| --- | --- |
| **Activation height** | Block 969,696. Transactions in earlier blocks do nothing. |
| **Bitcoin miner** | The party that finds a Bitcoin block. Not the same as a minter. |
| **Block hash** | The hash of a Bitcoin block, written the way Bitcoin nodes and block explorers print it (it starts with zeros). Its last hex digit sets the tier of every MINE in that block. |
| **Burn** | Tokens that are routed to no output. This happens only when the rules leave them no usable output. Burned tokens do not lower the minted amount. |
| **Carrier** | Another name for a token output, used in the app. |
| **Confirmation** | A block has 1 confirmation when it is the newest block of the chain, and one more for every block on top of it. A result is final at 6 confirmations. |
| **Credit** | The tokens a MINE actually receives: the smaller of its yield and the remaining supply. |
| **Default output** | The first output of a transaction that is not an OP_RETURN output. |
| **Default routing** | A transaction that spends token outputs without a LUCKY-20 payload moves all their tokens to its default output. An input signed as a listing is the exception (see Listing-signed input). |
| **DEPLOY** | The operation that registers a new ticker with a supply of 21,000,000. |
| **Deployer** | The address that signed the whole registering DEPLOY and contributed the largest share of its inputs. It shows that this address signed the DEPLOY, not who chose the ticker. Empty when no input qualifies. The deployer receives no tokens. |
| **Expected yield** | The average yield of a MINE: (1 × 10,000 + 3 × 2,000 + 5 × 1,000 + 7 × 500) / 16 = 1,531.25 tokens. Near the cap the average credit is lower: a MINE is credited at most what the MINEs before it, in earlier blocks and earlier in its own block, have left. |
| **Fill** | A buyer's transaction that completes a listing into a SEND. It pays the seller and gives the tokens to the buyer in one step, with no protocol fee. If it is not an applied SEND of the listed ticker, the seller is paid and keeps the tokens. |
| **Final** | A result whose block has 6 confirmations. Before that it is provisional: a reorganization can still change it. |
| **Input pool** | All tokens on the outputs a transaction spends, counted per ticker. |
| **Listing** | A one-input, one-output transaction signed by a seller with `SIGHASH_SINGLE \| SIGHASH_ANYONECANPAY`. It sells the whole balance of a token output that holds a single ticker. |
| **Listing-signed input** | An input signed `0x83` (`SIGHASH_SINGLE \| SIGHASH_ANYONECANPAY`, as a listing is signed) whose output with the same index exists and is not an OP_RETURN output. The rules read the signature of two kinds of input only: one that spends a P2TR output by key path (a single witness element of 65 bytes once any annex, a last element starting with `0x50` when there are at least two, is set aside; its last byte is the signature type) and one that spends a P2WPKH output (exactly two witness elements, the first 9 to 73 bytes long; the last byte of the first is the signature type). The tokens of a ticker on a listing-signed input move only through a SEND of that ticker that applies; otherwise they go to the output with the same index. Any other input signed `0x83` (a script-path, P2WSH, P2SH, nested-SegWit included, or P2PKH input, or any input without a witness), and a `0x83` input whose same-index output is missing or is an OP_RETURN output, joins the input pool like every other input. |
| **Mempool** | Where a broadcast transaction waits for a block. Anyone can read it there, including the ticker of a pending DEPLOY. |
| **MINE** | The operation that creates new tokens on output 0. The block hash sets the amount. Valid only in a block after the ticker's DEPLOY. |
| **Minted amount** | The total credited to all MINEs of a ticker. Burns never lower it; only a reorganization that removes credited MINEs does. |
| **Minted out** | A ticker whose minted amount has reached 21,000,000. Also called fully minted. Its market opens when the block that completed its supply has 6 confirmations. |
| **Minter** | The sender of a MINE. |
| **OP_RETURN output** | An output that holds data and can never be spent. It never holds tokens. |
| **Payload** | The compact JSON in the OP_RETURN output, one line with no spaces. At most 63 bytes. Any other spelling is not a payload. |
| **Protocol fee** | None. The protocol charges no fee: a MINE, a SEND or a DEPLOY is valid without any fee output. |
| **Reorganization** | Bitcoin replacing its newest block (or blocks) with a competing branch. LUCKY-20 follows the chain Bitcoin keeps: the effects of the replaced blocks are undone and the new blocks are applied by the same rules, so a MINE confirmed again in another block takes the tier of that block's hash. |
| **Residual output** | The 546-sat output that receives what a SEND does not move: output 2 of a SEND and of a fill. Always present. |
| **SEND** | The operation that moves `AMT` tokens of one ticker to output 1 and everything else to output 2. |
| **Supply** | 21,000,000 tokens for every ticker. Fixed by the rules. Not a key of any payload. |
| **Ticker** | 1 to 8 characters, `A`–`Z` and `0`–`9`. The first valid DEPLOY in block order registers it. |
| **Tier** | One of the four yields: 500, 1,000, 2,000 or 10,000 tokens. |
| **Token output** | A Bitcoin output that holds LUCKY-20 tokens. By wallet convention it holds 546 sats; the rules accept any value. |
| **Unit price** | The listing price in sats divided by the number of tokens: sats per whole token. |
| **Yield** | The tier a MINE receives from the last hex digit of its block hash: `f` → 10,000; `c`–`e` → 2,000; `7`–`b` → 1,000; `0`–`6` → 500. |
