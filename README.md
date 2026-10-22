# LUCKY-20: Fair-Launch Tokens Minted by the Bitcoin Block Hash

LuckyProtocol · [luckyprotocolai.com](https://luckyprotocolai.com) · Activation at Bitcoin block 969,696

**Abstract.** A token on Bitcoin should not let any person decide who receives how much. In most token standards, people set the amounts: a deployer picks the supply and may keep a share, and each minter picks how much to claim. LUCKY-20 lets Bitcoin decide. A MINE transaction names a ticker and nothing else. The last hex digit of the hash of the block that confirms it sets the yield: 500, 1,000, 2,000 or 10,000 tokens, 1,531.25 on average. The minter, the deployer and the project cannot choose that hash, and anyone can check it from public block data. Every ticker has a fixed supply of 21,000,000 tokens, with no premine, no allocation and no per-address cap. Each operation is one small JSON payload in an OP_RETURN output of an ordinary Bitcoin transaction, and tokens sit on Bitcoin outputs: there is no inscription, no sidechain and no bridge. A new ticker is registered by one DEPLOY transaction; the first valid DEPLOY in block order registers it. When a ticker is fully minted, its tokens trade through seller-signed listings that settle atomically on-chain, with no custodian.

## At a glance

- **Minted by Bitcoin itself.** The last hex digit of the confirming block's hash sets each MINE's yield: `f` → 10,000; `c`–`e` → 2,000; `7`–`b` → 1,000; `0`–`6` → 500. The expected yield is 1,531.25 tokens per MINE. Nobody chooses it: not the minter, not the deployer, not the project.
- **Fair launch.** 21,000,000 tokens per ticker. Open mint. No premine, no allocation, no per-address cap. The deployer receives no tokens.
- **Pure Bitcoin L1.** One OP_RETURN payload of at most 63 bytes per transaction, in compact JSON. No inscriptions, no sidechain, no bridge. Tokens live on Bitcoin outputs and move with ordinary Bitcoin transactions.
- **One-transaction deploys.** A single DEPLOY transaction registers a ticker; when several name it, the first valid one in block order registers it. A pending DEPLOY is visible in the mempool, so the app suggests a fast fee and can speed it up.
- **Non-custodial market.** A seller signs a listing. A buyer completes it into one on-chain transaction that pays the seller and moves the tokens together. A ticker's market opens only when it is fully minted and the block that completed its supply has 6 confirmations. The seller receives exactly the listed price.
- **No protocol fee.** The protocol charges no fee. A MINE, a SEND or a DEPLOY is an ordinary Bitcoin transaction that pays only the network fee.
- **Open to verification.** Every balance follows from Bitcoin blocks, starting at block 969,696. Anyone can recompute it.

## 1. Introduction

Tokens on Bitcoin are usually issued by people. A deployer picks the supply and the amount per mint, and sometimes keeps a share. Each minter picks how much to claim, up to a limit. Whoever sets these numbers can favor someone, and every holder must trust that they did not. Some standards also need large inscriptions, or a second chain and a bridge.

What is needed is a token whose issuance is set by Bitcoin rather than by a person. Every mint amount should come from data that no participant controls and that anyone can check. The supply should be fixed and open to everyone from the start. The tokens should live in ordinary Bitcoin transactions. Trading them should not require handing them to anyone.

This document describes such a standard. The amount of each mint is read from the hash of the Bitcoin block that confirms it. A ticker goes through three steps:

1. **Deploy.** A DEPLOY names the ticker and registers it with a supply of 21,000,000.
2. **Mine.** From the block after the DEPLOY, anyone sends MINEs. The hash of the confirming block sets the yield of each MINE, and MINEs are credited until the supply is used up.
3. **Trade.** When the ticker is fully minted and the block that completed its supply has 6 confirmations, its market opens. Holders list tokens, and buyers fill the listings on-chain.

Section 3 explains the minting rule. The other sections build the token system around it.

## 2. Tokens on Bitcoin Outputs

Every LUCKY-20 operation is an ordinary Bitcoin transaction with one OP_RETURN output. That output holds a short JSON payload, in exactly one compact form per operation: no spaces, the keys in a fixed order. Its `p` is always `lucky-20`, and `op` names the operation. There are three operations and no others:

**DEPLOY** registers a new ticker with a supply of 21,000,000:

```
{
  "p": "lucky-20",
  "op": "deploy",
  "tick": "<TICKER>"
}
```

**MINE** creates new tokens on output 0 of the transaction:

```
{
  "p": "lucky-20",
  "op": "mine",
  "tick": "<TICKER>"
}
```

**SEND** moves `AMT` tokens to output 1 and the rest to output 2:

```
{
  "p": "lucky-20",
  "op": "send",
  "tick": "<TICKER>",
  "amt": "<AMT>"
}
```

They are shown with line breaks for reading. On chain each payload is one line with no spaces, for example `{"p":"lucky-20","op":"mine","tick":"LUCKY"}`.

Any other spelling — a space, another key order, a number without quotes — is not a LUCKY-20 payload: only these exact bytes count.

Tokens are bound to transaction outputs. An output that holds tokens is a *token output*. The app calls it a *carrier*. Whoever can spend it owns its tokens. One output can hold several tickers:

| Output | Value | Tokens |
| --- | --- | --- |
| `txid_a:0` | 546 sats | LUCKY 1,000 |
| `txid_b:3` | 546 sats | LUCKY 200 and ABC 500 |

There are no accounts, no contract and no second ledger. By wallet convention a token output holds 546 sats. Amounts are whole tokens, with no decimals.

When a transaction spends token outputs, their tokens form one *input pool*, counted per ticker. The operation decides which outputs receive the pool. A transaction that spends token outputs but has no LUCKY-20 payload moves the whole pool to its first output that is not an OP_RETURN output. This is *default routing*. An ordinary wallet that spends a token output therefore moves the tokens. It does not destroy them. Tokens never go to an OP_RETURN output. They are burned only in the few cases where the rules leave them no usable output. A MINE burns them when its output 0 is missing or is an OP_RETURN output. Where tokens go to the first output that is not an OP_RETURN output, they are burned when the transaction has no such output, or when that output has no address. An input signed as a market listing is the one exception to all of this: its tokens move only with a SEND of their ticker that is applied, and otherwise go to the seller's payment output (Section 7; the [Glossary](glossary.md), under Listing-signed input, says exactly which inputs count).

## 3. Minting by Block Hash

A MINE names a ticker and nothing else:

```
{
  "p": "lucky-20",
  "op": "mine",
  "tick": "<TICKER>"
}
```

It states no amount. When the transaction confirms, its yield is read from the hash of the block that contains it, written the way Bitcoin nodes and block explorers print it. Only the last hex digit counts:

| Last hex digit of the block hash | Tier (tokens) | Digits out of 16 | Probability |
| --- | --- | --- | --- |
| `f` | 10,000 | 1 | 6.25% |
| `c` `d` `e` | 2,000 | 3 | 18.75% |
| `7` `8` `9` `a` `b` | 1,000 | 5 | 31.25% |
| `0` `1` `2` `3` `4` `5` `6` | 500 | 7 | 43.75% |

The last digit of a block hash is evenly spread. Each of the 16 digits is equally likely, and the digit of one block does not depend on any other block. The expected yield of one MINE is:

```
E = (1 × 10,000 + 3 × 2,000 + 5 × 1,000 + 7 × 500) / 16
  = 24,500 / 16
  = 1,531.25 tokens
```

The yield is credited to output 0 of the MINE. Here is the rule applied to the hash of Bitcoin block 0:

```
  MINE tx      {"p":"lucky-20","op":"mine","tick":"LUCKY"}
     |
     |  confirmed in a Bitcoin block
     v
  block hash   000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f
                                                                              |
     +------------------------------------------------------------------------+
     |  last hex digit = f
     v
  tier         f -> 10,000 | c-e -> 2,000 | 7-b -> 1,000 | 0-6 -> 500
     |
     v
  credit       10,000 tokens to output 0 of the MINE
```

**Who decides the amount.** Nobody chooses it.

- The minter only names a ticker, and nothing the minter pays changes the yield. The minter signs and broadcasts the MINE before the block exists. The hash is found later, with the transaction already inside the block.
- The deployer sets no amounts. The supply and the tiers are the same for every ticker.
- The project sets nothing. The rule is a fixed function of public data.
- A Bitcoin miner cannot pick the hash either, because proof-of-work hashes cannot be predicted. What a miner can and cannot do is set out below.

All MINEs confirmed in the same block share one block hash, so they all receive the same tier. The yield is the outcome of the block hash and nothing else.

**What a Bitcoin miner can and cannot do.** A block's hash exists only once the block is complete, and it commits to every transaction in the block. So no one can pick MINEs by their digit: the digit is not known until the block that holds them is finished. A miner's only lever is to discard a finished block and search again. That throws away the block subsidy (3.125 BTC until block 1,050,000) and the block's fees, given up by the miner or its pool, to save at most the fees of the MINEs the block carried. Those MINEs can be mined again in a later block, whose hash is again unknown. Like any Bitcoin transaction, and like BRC-20 and Runes mints, a miner does decide which MINEs enter its block and in what order. Near the end of a ticker's supply, this decides who is credited (Section 4).

## 4. Supply and Fair Launch

Every ticker has a supply of exactly 21,000,000 tokens. The supply is fixed by the rules. It is not a key of any payload, and a deployer cannot set another number. There is no premine and no allocation: the deployer receives no tokens. Every token of every ticker comes from a MINE.

Minting is open. Anyone can mine any registered ticker, from any address, as often as they like. There is no per-address cap. This also means that a large minter can mint a large part of a supply. The remaining supply is public at every block, so every participant can see how close the cap is.

Minting starts in the block after the DEPLOY. A MINE in the same block as the ticker's DEPLOY is invalid and credits nothing, whoever sends it, the deployer included. So every minter has the same first block to mine in.

Each MINE is credited the smaller of its yield and the remaining supply, so the credited total stops at exactly 21,000,000. MINEs are credited in block order, so near the cap the earlier MINEs of a block are credited first. Every tier and the supply are multiples of 500, so the MINE that crosses the cap is credited what is left, itself a multiple of 500. A MINE confirmed after that is credited 0, and what it paid in fees is not refunded. A wallet therefore shows the remaining supply before it builds a MINE.

A ticker is *minted out*, or fully minted, when its credited total reaches 21,000,000. Burning tokens never lowers the credited total, so burned tokens do not reopen minting. Only a reorganization that removes the block that completed its supply can lower it again (Section 8).

## 5. Deploying a Ticker

A ticker is 1 to 8 characters, `A`–`Z` and `0`–`9`. The first valid registration of a ticker in the chain that Bitcoin keeps is final.

A ticker is registered by one transaction:

```
{
  "p": "lucky-20",
  "op": "deploy",
  "tick": "<TICKER>"
}
```

The DEPLOY registers the ticker when the ticker is still free. When two valid DEPLOYs name the same ticker, the first in block order — block height, then position in the block — registers it. The other registers nothing, and what it paid in fees is not refunded.

A DEPLOY names its ticker in plain text. While it waits in the mempool, anyone can read the ticker and send a DEPLOY of the same ticker. Bitcoin miners usually put transactions that pay a higher fee rate first, so a DEPLOY that pays more normally confirms first. The app therefore checks that the ticker is still free right before signing, suggests a fast fee, and can speed up a pending DEPLOY by replacing it with one that pays more. A registration is final once its block has 6 confirmations.

The deployer is the address that signed the whole DEPLOY transaction and contributed the largest share of its inputs. It shows that this address signed the DEPLOY, not who chose the ticker. The deployer receives no tokens.

## 6. Moving Tokens

```
{
  "p": "lucky-20",
  "op": "send",
  "tick": "<TICKER>",
  "amt": "<AMT>"
}
```

A SEND moves `AMT` whole tokens of one ticker to output 1. Everything else in the input pool goes to output 2: the rest of that ticker and all of every other ticker. The outputs are fixed; the payload names none. Amounts are whole numbers from 1 to 21,000,000, written in quotes.

```
inputs     { LUCKY: 1,500, ABC: 500 }
vout0      OP_RETURN {"p":"lucky-20","op":"send","tick":"LUCKY","amt":"1200"}
vout1      { LUCKY: 1,200 }             the recipient
vout2      { LUCKY: 300, ABC: 500 }     back to the sender
```

A SEND applies only when the pool holds at least `AMT` and output 1 exists and is not an OP_RETURN output. Otherwise nothing moves to output 1, and the whole pool goes to output 2. If output 2 is missing or is an OP_RETURN output, what it would receive goes to the transaction's first output that is not an OP_RETURN output.

Because routing is per ticker, one SEND can split a token output that holds several tickers. And because of default routing (Section 2), tokens also move with any Bitcoin transaction that spends them, even one built by a wallet that knows nothing about LUCKY-20.

## 7. Trading

Bitcoin has no contract that can hold tokens during a sale. A LUCKY-20 trade is therefore one Bitcoin transaction built by two people:

- **Listing.** The seller signs a transaction with one input, the token output, and one output, the price paid to the seller's own script. The signature type is `SIGHASH_SINGLE | SIGHASH_ANYONECANPAY`. It covers only that input and that output, so the listing is valid only inside a transaction that pays the seller in full.
- **Fill.** A buyer adds BTC inputs and the outputs that make the transaction a SEND of the tokens to the buyer, then signs and broadcasts it. In one transaction the seller is paid and the buyer receives the tokens. If it does not confirm, nothing moves.
- **Cancel.** A signed listing stays valid for anyone who holds it, so an off-chain cancel means nothing. The seller cancels by moving the tokens on-chain with a SEND back to the seller.

```
 listing (signed by the seller)         fill (completed by the buyer)
 in0   token output, e.g. 1,200 tokens  in0   the seller's token output
 out0  price -> seller                  in1+  the buyer's BTC
                                        out0  price -> seller
                                        out1  546 sats -> buyer (the tokens)
                                        out2  546 sats -> buyer (residual)
                                        out3  OP_RETURN {"p":"lucky-20","op":"send","tick":"<TICKER>","amt":"<AMT>"}
                                        out4  BTC change -> buyer
```

A listing sells the whole balance of a token output that holds a single ticker. To sell part of a balance, or one ticker of an output that holds several, the seller first splits it with a SEND back to the seller. If two buyers fill the same listing, only one transaction can confirm, and the other buyer spends nothing.

The listed input carries the seller's `SIGHASH_SINGLE | SIGHASH_ANYONECANPAY` signature, and tokens on such an input move only with a SEND of their own ticker that is applied. A transaction that spends a listing any other way — with a SEND that does not apply or a SEND of another ticker, with another payload or with none — still pays the seller the price, because the listing's signature requires it, and the tokens stay with the seller on that payment output. It is recorded as a self-trade, with the seller as the buyer. One SEND serves every listing of that ticker in the transaction.

The protocol takes no fee from a sale: the seller receives exactly the listed price, and an applied SEND gives the buyer the tokens.

**The market opens when a ticker is minted out and the block that completed its supply has 6 confirmations**, about an hour later. Before that, the order book accepts no listing of the ticker. While anyone can still mint the ticker, a listing would put a price on something anyone can mint. It would also let a deployer sell into a distribution that is not finished. The wait of 6 confirmations means that a reorganization shallower than 6 blocks can no longer change the amounts the listings sell (Section 8).

Nobody holds funds or tokens for anyone: not the app, not the order book. There is no bonding curve, no pooled liquidity and no market maker. Prices are what sellers ask and buyers pay. The order book can hide or delay a listing, but it cannot move a seller's coins or tokens. Before signing, the buyer's wallet checks the listed token output against the chain (Section 8).

## 8. Verification

The state of every ticker is a function of Bitcoin blocks and the published rules. No trusted party reports it. Anyone who has the block data can recompute it:

1. Start at block 969,696. Ignore every earlier block.
2. Take each transaction in block order. Read its payload, apply the rule for its operation, and route its input pool.
3. For each MINE, take the last hex digit of the confirming block's hash, look up the tier, and credit the smaller of the tier and the remaining supply (Section 4).

Anyone who applies the rules to the same blocks gets the same balances. The yield of a MINE always comes from the block that confirms it in the chain that Bitcoin keeps. The complete indexing procedure — how to find a payload, route every token, credit every MINE and follow a reorganization, with test vectors — is on the [Indexer](developers/indexer.md) page. It is precise enough to build an independent indexer and compare it with any other, output by output.

**Reorganizations and finality.** Now and then Bitcoin replaces its newest block with a competing one. This is a reorganization. LUCKY-20 always follows the chain that Bitcoin keeps: the effects of the replaced block are undone, and the new blocks are applied by the same rules. If the block that confirmed a MINE is replaced, the MINE is credited again from the hash of the block that confirms it in the new chain, so its tier can change. Near the cap its credit can change or become 0, and a minted-out ticker can be minting again. Registrations, transfers and trades follow the new chain the same way. A result is final once its block has 6 confirmations, about an hour. Until then the app shows it as provisional, with its number of confirmations.

A single yield can be checked by hand. The first blocks of Bitcoin show how the rule reads a hash. They are far below block 969,696 and hold no MINE:

| Height | Block hash | Last digit | Tier |
| --- | --- | --- | --- |
| 0 | `000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f` | `f` | 10,000 |
| 1 | `00000000839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048` | `8` | 1,000 |
| 2 | `000000006a625f06636b8bb6ac7b960a8d03705d1ace08b1a19da3fdcc99ddbd` | `d` | 2,000 |
| 4 | `000000004ebadb55ee9096c9a2f8880e09da59c0d68b1c228da88e48844a1485` | `5` | 500 |

A buyer checks a listed token output the same way. The buyer fetches the transaction that created it from a Bitcoin node or a block explorer, compares its script and value, and reads its payload. For an output created by a MINE, the buyer recomputes the yield from the block hash.

## 9. Fees

The protocol charges no fee. A MINE, a SEND (a fill is a SEND) and a DEPLOY take effect without any fee output: the rules never look for one. A fill moves the tokens to the buyer with no protocol fee, and the seller receives exactly the listed price. This holds for every block from 969,696 on.

The Bitcoin network fee is separate, as in any Bitcoin transaction.

## 10. Calculations

**Expected yield.** From Section 3, one MINE is expected to yield 1,531.25 tokens.

**MINEs to mint out.** At the expected yield, a ticker is minted out after about

```
21,000,000 / 1,531.25 ≈ 13,714 MINEs
```

**Bounds.** While supply remains, every valid MINE is credited between 500 and 10,000 tokens: the remaining supply is always a multiple of 500, so even the MINE that crosses the cap is credited at least 500. Minting out therefore takes at least 2,100 valid MINEs (every one in the top tier) and at most 42,000 valid MINEs (every one in the lowest tier):

```
21,000,000 / 10,000 =  2,100
21,000,000 /    500 = 42,000
```

**Blocks, not MINEs.** All MINEs in one block share one tier. The average of 1,531.25 therefore holds over many blocks, not over many MINEs in one block. A ticker minted in a few blocks can end far from 13,714 MINEs. A ticker minted over many blocks tends to end close to it.

## 11. Conclusion

We have described a token standard on Bitcoin in which no person sets the mint amounts. Each MINE yields 500, 1,000, 2,000 or 10,000 tokens, 1,531.25 on average, by the outcome of the hash of the block that confirms it, and is credited the smaller of that yield and the remaining supply. The minter, the deployer and the project cannot choose that yield, and anyone can check it. Each ticker has a fixed supply of 21,000,000, minted openly with no premine, no allocation and no per-address cap. Operations are small JSON payloads in OP_RETURN outputs, and tokens sit on Bitcoin outputs. A ticker is registered by the first valid DEPLOY in block order. Tokens of a minted-out ticker trade through seller-signed listings that settle in one on-chain transaction. The protocol charges no fee. The whole state can be recomputed from Bitcoin blocks alone.

---

| Resource | Where |
| --- | --- |
| Operations | [Deploy](operations/deploy.md) · [Mine](operations/mine.md) · [Send](operations/send.md) |
| Building transactions | [Wallets](developers/wallets.md) |
| App | [luckyprotocolai.com](https://luckyprotocolai.com) |

