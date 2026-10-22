# Indexer

This page is the complete indexing procedure of LUCKY-20: how Bitcoin blocks become token balances. It is precise enough to build an independent indexer. Two indexers that follow it, on the same chain, hold the same tokens on every output. The app at [luckyprotocolai.com](https://luckyprotocolai.com) runs an indexer that follows this page.

The [whitepaper](../README.md) explains the rules. This page states them in the order an indexer applies them.

## What an indexer keeps

- **Token balances per output.** For every unspent output that holds tokens: its outpoint (`txid:vout`), its address, and its balance per ticker, in whole tokens.
- **The registry.** For every registered ticker: the DEPLOY that registered it and its block height, its deployer, its minted amount, and the height of the block that completed its supply, once it is minted out.
- **A record of each operation** (optional, but useful to compare indexers): every DEPLOY, MINE and SEND, whether it applied, and why not.

Everything above follows from Bitcoin blocks alone. An indexer may also keep the market's order book and its trade history (see [Market](#8-market)). Balances never depend on them.

## Constants

| Name | Value |
| --- | --- |
| Protocol id (`p`) | `lucky-20` |
| Activation height | 969,696 |
| Supply of every ticker | 21,000,000 |
| Final depth | 6 confirmations |
| Ticker | `[A-Z0-9]{1,8}` |
| `AMT` of a SEND | `[1-9][0-9]{0,7}`, at most 21,000,000 |
| SEND outputs | `AMT` to output 1, the rest to output 2 |
| Token output value | 546 sats by wallet convention; the rules accept any value, 0 included |

## 1. Order

1. Read the chain that Bitcoin keeps (the best chain), from your own Bitcoin node.
2. Ignore every block below 969,696. Nothing in them counts: no balance, no registration.
3. Apply blocks in height order. Inside a block, apply transactions in the order the block lists them.
4. Each transaction sees the state that every earlier transaction left: balances, minted amounts and registrations. Never reorder the transactions of a block (by txid, by fee or otherwise). Block order alone decides which of two DEPLOYs registers a ticker and which MINE receives the last tokens of a supply.
5. The coinbase transaction (position 0) is never a LUCKY-20 transaction. Its outputs are not searched for a payload.
6. Unconfirmed transactions change nothing. A wallet may show them as pending; the state counts only blocks.

## 2. Finding the payload

An **OP_RETURN output** is any output whose `scriptPubKey` starts with the byte `0x6a`. Decide this from the script bytes, not from a node's script-type label.

The **payload** of a transaction is the push of the **lowest-index** output that has the exact form `OP_RETURN <one push>` (a direct push or PUSHDATA1/2/4, nothing after the push) and whose push parses as a LUCKY-20 payload. Every other OP_RETURN output is ignored: a wallet memo, a runestone or a push that does not parse, before or after the payload, changes nothing. A transaction with several OP_RETURN outputs is not invalid for that reason.

**Parsing is byte-exact.** A push is a payload only if its bytes are exactly one of these three forms, with a valid ticker and amount:

```
{"p":"lucky-20","op":"deploy","tick":"<TICKER>"}
{"p":"lucky-20","op":"mine","tick":"<TICKER>"}
{"p":"lucky-20","op":"send","tick":"<TICKER>","amt":"<AMT>"}
```

Everything else is not a payload, even valid JSON with the same meaning: whitespace anywhere, another key order, a missing, extra or repeated key, a number where a string is required, an escape sequence, a ticker in lower or mixed case, another `p` (`LUCKY-20` in upper case included), an operation name in upper case, a byte-order mark, or any byte before `{` or after `}`.

| Push | Parses as |
| --- | --- |
| `{"p":"lucky-20","op":"deploy","tick":"LUCKY"}` | DEPLOY `LUCKY` |
| `{"p":"lucky-20","op":"mine","tick":"LUCKY"}` | MINE `LUCKY` |
| `{"p":"lucky-20","op":"send","tick":"LUCKY","amt":"1200"}` | SEND 1,200 `LUCKY` |
| `{"p":"lucky-20","op":"send","tick":"ABCDEFGH","amt":"21000000"}` | SEND 21,000,000 `ABCDEFGH` (63 bytes, the longest payload) |
| `{"p": "lucky-20","op":"mine","tick":"LUCKY"}` | nothing (whitespace) |
| `{"op":"mine","p":"lucky-20","tick":"LUCKY"}` | nothing (key order) |
| `{"p":"lucky-20","op":"mine","tick":"LUCKY","tick":"LUCKY"}` | nothing (repeated key) |
| `{"p":"lucky-20","op":"send","tick":"LUCKY","amt":1200}` | nothing (a number where a string is required) |
| `{"p":"lucky-20","op":"send","tick":"LUCKY","amt":"01200"}` | nothing (leading zero) |
| `{"p":"lucky-20","op":"mine","tick":"abc"}` | nothing (lower-case ticker) |
| `{"p":"lucky-20","op":"mine","tick":"LUCKY"}` | nothing (escape sequence) |
| `LUCKY-20\|MINE\|LUCKY` | nothing (not JSON) |

A transaction without a payload is a plain Bitcoin spend: its tokens follow default routing (Section 4).

**No fee output.** No rule looks for a fee output. A DEPLOY, MINE or SEND is judged by its payload, its inputs and the outputs its rule names, never by an output that pays a fee.

## 3. Signature type of an input

Two rules read an input's signature type: the deployer of a DEPLOY (Section 5) and listing-signed inputs (Section 4). It is read from the input's witness and the output it spends:

- **P2TR** spent output (`scriptPubKey` = `0x51 0x20` + 32 bytes): set aside an annex (a last witness element that starts with `0x50`, when there are at least two elements). Then a single element of 64 bytes has type `0x00` (`SIGHASH_DEFAULT`), and a single element of 65 bytes has its last byte as its type.
- **P2WPKH** spent output (`scriptPubKey` = `0x00 0x14` + 20 bytes): with exactly two witness elements, the first 9 to 73 bytes long, the type is the last byte of the first element.
- **Every other input** has no type: a script-path spend, P2WSH, P2SH (nested SegWit included), a legacy input, an input without a witness.

## 4. Routing tokens

**Input pool.** The tokens on every output a transaction spends join one pool, counted per ticker. Listing-signed inputs are the exception (below).

**Default output.** The lowest-index output that is not an OP_RETURN output. It must have an address (P2PKH, P2SH, P2WPKH, P2WSH, P2TR or any witness program). If the first output that is not an OP_RETURN output has no address (P2PK, bare multisig, a non-standard script), the tokens routed to the default output are burned: the rule does not skip to the next output.

**Never an OP_RETURN output.** Tokens never go to an OP_RETURN output. An output a rule names (output 0 of a MINE, output 1 or 2 of a SEND) that is an OP_RETURN output is treated as if it did not exist. Any other output can hold tokens, whatever its value.

**Listing-signed inputs.** An input is listing-signed when its signature type is `0x83` (`SIGHASH_SINGLE | SIGHASH_ANYONECANPAY`, the signature of a market listing) and the output with the same index exists and is not an OP_RETURN output. Its tokens do not join the input pool. Its balance of a ticker X moves only through a SEND of X that applies, and then joins that SEND's pool; otherwise it goes to the output with the same index (in a listing, the seller's payment). An input signed `0x83` whose same-index output is missing or is an OP_RETURN output is an ordinary input.

**Routing table.** Where the tokens go, for every transaction at or above block 969,696. "Pool" is the input pool, every ticker, after a SEND's `AMT` has been taken out. This table is normative: where a sentence elsewhere could be read differently, the table decides.

| Payload | Case | The named ticker T | Every other ticker | Listing-signed input i, ticker X |
| --- | --- | --- | --- | --- |
| MINE T | valid (also when it is credited 0 at the cap) | yield + pool → output 0 | → output 0 | X → output i |
| MINE T | not registered yet, or registered in the same block | pool → output 0, no yield | → output 0 | X → output i |
| MINE T | output 0 missing or an OP_RETURN output | **burned** | **burned** | X → output i |
| SEND T AMT | applied: the pool holds ≥ `AMT` of T (listing-signed T counted) and output 1 exists and is not an OP_RETURN output | `AMT` → output 1, the rest → output 2 | → output 2 | X = T: joins the pool; X ≠ T → output i |
| SEND T AMT | not applied | whole pool → output 2 | → output 2 | X → output i |
| SEND T AMT | output 2 missing or an OP_RETURN output (when applied, `AMT` still goes to output 1) | the rest → default output | → default output | as in the two rows above |
| DEPLOY T | registered or not | → default output | → default output | X → output i |
| none | no OP_RETURN output, or no push that parses | → default output | → default output | X → output i |
| any row "→ default output" | no output that is not an OP_RETURN output, or the first one has no address | **burned** | **burned** | unaffected |

The destination is decided once per transaction and applies to every ticker in the pool. Only a SEND's `AMT` is specific to one ticker. Burned tokens never lower a ticker's minted amount.

## 5. DEPLOY

A DEPLOY registers its ticker, with a supply of 21,000,000, when the ticker is not registered yet. Otherwise it registers nothing (`ticker_taken`) and changes no registration.

The first valid DEPLOY in block order registers the ticker: block height, then position in the block. Nothing else gives priority, neither the fee nor the time of broadcast.

**Deployer.** Among the inputs signed over the whole transaction (signature type `0x00` or `0x01`), the address that contributed the most input value, summed per address. An input's value is the value of the output it spends. A tie goes to the address whose first such input has the lower index. Inputs of any other type (`0x02`, `0x03`, `0x81`–`0x83`) and inputs with no type never count. A DEPLOY with no such input still registers the ticker, with an empty deployer. The deployer receives no tokens.

A DEPLOY names no output: its token inputs follow default routing (Section 4).

## 6. MINE

**Validity**, checked in this order. The first rule that fails is the MINE's reason:

1. the ticker is registered (else `not_deployed`);
2. it was registered in an earlier block: the MINE's height is greater than the height of the registering DEPLOY (else `deploy_same_block`);
3. output 0 exists and is not an OP_RETURN output (else `vout0_unusable`).

An invalid MINE credits nothing. Its pool still routes as the routing table says: to output 0, burned only when output 0 is unusable.

**Yield.** Take the hash of the block that confirms the MINE in its **display form**: the double SHA-256 of the 80-byte block header, byte-reversed, exactly as `getblockhash`, `getblockheader` and block explorers print it (it starts with the proof-of-work zeros). Read its last hex digit, in lower case:

```
yield(block_hash) :=
  d = last hex digit of lowercase(block_hash)
  d == 'f'         -> 10,000
  d in 'c'..'e'    ->  2,000
  d in '7'..'b'    ->  1,000
  d in '0'..'6'    ->    500
```

Hashing the header and hex-encoding the digest without reversing it gives the internal byte order. Its last digit is almost always `0`, so an indexer that reads it credits 500 for nearly every MINE and diverges.

**Credit.** A valid MINE is credited `min(yield, remaining supply)` on output 0, where the remaining supply is 21,000,000 minus the ticker's minted amount at that point in block order. Every yield and the supply are multiples of 500, so the MINE that crosses the cap is credited what is left, a multiple of 500. A valid MINE after it is credited 0 (cap exhausted). Its network fee is still spent.

**Minted amount.** The sum of all credits of a ticker. No burn lowers it. A ticker is **minted out** when its minted amount reaches 21,000,000; record the height of the block of the MINE that completed it. Only a reorganization that removes credited MINEs lowers the minted amount (Section 9).

Example: 3,000 tokens are left, and one block whose hash ends in `c` (yield 2,000) holds three valid MINEs of the ticker. The first MINE the block lists is credited 2,000, the second 1,000 (this block completes the supply), and the third 0.

## 7. SEND

A SEND moves `AMT` of its ticker T to output 1, and everything else in the pool to output 2: the rest of T and all of every other ticker. It is **applied** when both hold:

1. the pool holds at least `AMT` of T, counting the T on listing-signed inputs;
2. output 1 exists and is not an OP_RETURN output.

Otherwise nothing moves to output 1, and the whole pool goes to output 2. If output 2 is missing or is an OP_RETURN output, what it would receive goes to the default output.

## 8. Market

A ticker's market opens when it is minted out and the block that completed its supply has 6 confirmations. Before that, an order book accepts no listing of it.

Listings are signed off-chain, so trades are recorded only by an indexer that holds the listings. A spend of a listed output at input `i` is a **fill** when input `i` has signature type `0x83` and output `i` pays at least the listed price to the seller's script. The buyer is the address of output 1 when the transaction is an applied SEND of the listed ticker; otherwise the tokens stay with the seller (Section 4) and the fill is the seller's own, a self-trade. A self-trade does not count toward volume or the last price. Any other spend of a listed output cancels the listing. Balances never depend on any of this: the routing rules alone move the tokens.

## 9. Reorganizations and finality

The state follows the chain that Bitcoin keeps. When Bitcoin replaces its newest blocks with a competing branch, undo every effect of the blocks that left the chain (credits, balances, registrations, minted amounts, fills) and apply the blocks of the new branch by the same rules, in their order. Nothing carries over from a removed block:

- a MINE that confirms again in another block is credited from that block's hash, so its yield can change; near the cap its credit can change or become 0;
- a minted-out ticker whose completing MINE is removed is minting again until the new chain completes its supply;
- registrations, SENDs and fills follow the block order of the new chain; a transaction that does not confirm again has no effect.

A block has 1 confirmation while it is the newest block, and one more for each block on top of it. Its effects are **final** at 6 confirmations. Until then, show every result in it as provisional.

## 10. Test vectors

**Yield by last digit:**

| Last hex digit | Yield |
| --- | --- |
| `0` … `6` | 500 |
| `7` … `b` | 1,000 |
| `c` … `e` | 2,000 |
| `f` | 10,000 |
| `F` (upper-case input) | 10,000 |

**Real block hashes** (display form, recomputed from each block's header). These blocks are far below the activation height and hold no MINE; they pin the byte order:

| Height | Block hash | Yield |
| --- | --- | --- |
| 0 | `000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f` | 10,000 |
| 1 | `00000000839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048` | 1,000 |
| 2 | `000000006a625f06636b8bb6ac7b960a8d03705d1ace08b1a19da3fdcc99ddbd` | 2,000 |
| 4 | `000000004ebadb55ee9096c9a2f8880e09da59c0d68b1c228da88e48844a1485` | 500 |

**Payloads:** the table in Section 2.

**Routing examples:**

| Transaction | Result |
| --- | --- |
| Spends an output with LUCKY 1,500 and ABC 500; payload SEND LUCKY 1,200 | output 1: LUCKY 1,200; output 2: LUCKY 300, ABC 500 |
| The same with `AMT` 2,000 | not applied: output 2 receives LUCKY 1,500 and ABC 500 |
| Spends an output with LUCKY 1,000; no OP_RETURN output; outputs pay A, then B | LUCKY 1,000 to A (default output) |
| Spends an output with LUCKY 1,000; payload MINE ABC, valid, at least 1,000 ABC left, block hash ends in `7` | output 0: LUCKY 1,000 and ABC 1,000 |
| MINE LUCKY in the block that registered LUCKY | invalid (`deploy_same_block`): no yield; its pool still goes to output 0 |

## 11. Comparing indexers

Balances are keyed by outpoint, so two indexers can be compared output by output: at the same block height, every unspent output holds the same tokens in both, and every ticker has the same minted amount and the same deployer. A difference means that one of them broke a rule on this page.

A wallet does not have to trust a single indexer. Before buying a listed output, the buyer's wallet checks it against a second source: it fetches the transaction that created the output from a Bitcoin node or a block explorer and recomputes what the rules put on it (see [Wallets](wallets.md)).
