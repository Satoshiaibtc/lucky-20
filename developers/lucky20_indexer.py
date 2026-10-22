#!/usr/bin/env python3
"""LUCKY-20 reference indexer.

Reads the chain from a Bitcoin Core node over JSON-RPC and derives every
LUCKY-20 balance by the rules of the Indexer page: the tokens on every
unspent output, and the registry of every ticker (minted amount, deployer,
the block that completed its supply). Python 3.8+, standard library only.

    python3 lucky20_indexer.py --rpc-url http://127.0.0.1:8332 \
        --rpc-user USER --rpc-password PASSWORD --state lucky20-state.json

Bitcoin Core 24.0 or newer, unpruned from block 969,696 (`getblock`
verbosity 3 returns every input's previous output). Released under the
MIT License.
"""
import argparse
import base64
import copy
import json
import os
import time
import urllib.request

ACTIVATION_HEIGHT = 969_696
SUPPLY = 21_000_000
REORG_DEPTH = 12          # blocks whose changes are kept for a rollback
LISTING_SIGHASH = 0x83    # SIGHASH_SINGLE | SIGHASH_ANYONECANPAY

# ---------------------------------------------------------------- payload --

HEAD = b'{"p":"lucky-20","op":"'
TICK = b'","tick":"'
AMT = b',"amt":"'


def valid_ticker(t):
    return 1 <= len(t) <= 8 and all(0x41 <= c <= 0x5A or 0x30 <= c <= 0x39 for c in t)


def parse_payload(push):
    """(op, ticker, amount) for exactly one of the three byte forms, else None."""
    if not push.startswith(HEAD):
        return None
    rest = push[len(HEAD):]
    for op in (b"deploy", b"mine", b"send"):
        if rest.startswith(op + TICK):
            rest = rest[len(op + TICK):]
            break
    else:
        return None
    end = rest.find(b'"')
    if end < 0 or not valid_ticker(rest[:end]):
        return None
    ticker, rest = rest[:end].decode(), rest[end + 1:]
    if op != b"send":
        return (op.decode(), ticker, None) if rest == b"}" else None
    if not rest.startswith(AMT):
        return None
    rest = rest[len(AMT):]
    if not rest.endswith(b'"}'):
        return None
    digits = rest[:-2]
    if not 1 <= len(digits) <= 8 or digits[:1] == b"0" or not digits.isdigit():
        return None
    amount = int(digits)
    return ("send", ticker, amount) if amount <= SUPPLY else None


def is_op_return(spk_hex):
    return spk_hex[:2].lower() == "6a"


def single_push(script):
    """The data of a script that is exactly OP_RETURN <one push>, else None."""
    if len(script) < 2 or script[0] != 0x6A:
        return None
    op = script[1]
    if 0x01 <= op <= 0x4B:
        start, size = 2, op
    elif op == 0x4C and len(script) >= 3:
        start, size = 3, script[2]
    elif op == 0x4D and len(script) >= 4:
        start, size = 4, int.from_bytes(script[2:4], "little")
    elif op == 0x4E and len(script) >= 6:
        start, size = 6, int.from_bytes(script[2:6], "little")
    else:
        return None
    if size > 256 or len(script) != start + size:
        return None
    return script[start:]


def is_coinbase(tx):
    return len(tx["vin"]) == 1 and "coinbase" in tx["vin"][0]


def payload_of(tx):
    """The lowest-index OP_RETURN output whose single push parses."""
    if is_coinbase(tx):
        return None
    for out in tx["vout"]:
        spk = out["scriptPubKey"]["hex"]
        if not is_op_return(spk):
            continue
        push = single_push(bytes.fromhex(spk))
        parsed = parse_payload(push) if push is not None else None
        if parsed:
            return parsed
    return None


def sig_type(prev_spk_hex, witness):
    """Signature type of an input: P2TR key path or P2WPKH only, else None."""
    spk = prev_spk_hex.lower()
    if len(spk) == 68 and spk.startswith("5120"):
        annex = len(witness) >= 2 and witness[-1][:2].lower() == "50"
        if len(witness) - annex != 1:
            return None
        size = len(witness[0]) // 2
        if size == 64:
            return 0x00
        return int(witness[0][-2:], 16) if size == 65 else None
    if len(spk) == 44 and spk.startswith("0014"):
        if len(witness) != 2 or not 9 <= len(witness[0]) // 2 <= 73:
            return None
        return int(witness[0][-2:], 16)
    return None


def address_of(spk):
    if spk.get("address"):
        return spk["address"]
    return (spk.get("addresses") or [None])[0]


def mine_yield(block_hash):
    d = block_hash.lower()[-1]
    if d == "f":
        return 10_000
    if d in "cde":
        return 2_000
    if d in "789ab":
        return 1_000
    return 500


def sats(btc):
    return int(round(btc * 100_000_000))

# ------------------------------------------------------------------ state --


class State:
    def __init__(self):
        self.height = ACTIVATION_HEIGHT - 1
        self.hashes = {}      # height -> block hash (recent blocks)
        self.outputs = {}     # "txid:vout" -> {"address": str|None, "tokens": {ticker: amount}}
        self.tickers = {}     # ticker -> registry entry
        self.undo = {}        # height -> [(table, key, old value)]
        self.journal = None

    def _note(self, table, key):
        if self.journal is not None:
            old = getattr(self, table).get(key)
            self.journal.append((table, key, copy.deepcopy(old)))

    def take_output(self, key):
        if key not in self.outputs:
            return None
        self._note("outputs", key)
        return self.outputs.pop(key)

    def credit(self, key, address, tokens):
        self._note("outputs", key)
        entry = self.outputs.setdefault(key, {"address": address, "tokens": {}})
        for ticker, amount in tokens.items():
            entry["tokens"][ticker] = entry["tokens"].get(ticker, 0) + amount

    def ticker(self, name):
        """The registry entry, journaled before the caller changes it."""
        self._note("tickers", name)
        return self.tickers.get(name)

    def rollback(self, height):
        for table, key, old in reversed(self.undo.pop(height)):
            if old is None:
                getattr(self, table).pop(key, None)
            else:
                getattr(self, table)[key] = old
        self.hashes.pop(height, None)
        self.height = height - 1

    def save(self, path):
        data = {"height": self.height, "hashes": self.hashes,
                "outputs": self.outputs, "tickers": self.tickers}
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, sort_keys=True)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path):
        s = cls()
        with open(path) as f:
            data = json.load(f)
        s.height, s.outputs, s.tickers = data["height"], data["outputs"], data["tickers"]
        s.hashes = {int(h): v for h, v in data["hashes"].items()}
        return s

# ------------------------------------------------------------------ rules --


def deployer_of(inputs):
    """Most input value per address among inputs signed over the whole tx."""
    totals = {}
    for i, inp in enumerate(inputs):
        if inp["address"] is None or inp["sig"] not in (0x00, 0x01):
            continue
        value, first = totals.get(inp["address"], (0, i))
        totals[inp["address"]] = (value + inp["value"], first)
    if not totals:
        return ""
    return max(totals.items(), key=lambda kv: (kv[1][0], -kv[1][1]))[0]


def apply_tx(state, tx, height, block_hash):
    outs = [(is_op_return(o["scriptPubKey"]["hex"]), address_of(o["scriptPubKey"])) for o in tx["vout"]]

    def usable(i):  # exists and is not an OP_RETURN output
        return i < len(outs) and not outs[i][0]

    inputs = []
    for vin in tx["vin"]:
        if "coinbase" in vin:
            continue
        prev = vin["prevout"]["scriptPubKey"]
        inputs.append({"key": f'{vin["txid"]}:{vin["vout"]}', "address": address_of(prev),
                       "value": sats(vin["prevout"]["value"]),
                       "sig": sig_type(prev["hex"], vin.get("txinwitness", []))})

    # 1. The input pool; listing-signed inputs are kept apart.
    pool, listed = {}, []
    for i, inp in enumerate(inputs):
        entry = state.take_output(inp["key"])
        if entry is None:
            continue
        if inp["sig"] == LISTING_SIGHASH and usable(i):
            listed.append((i, dict(entry["tokens"])))
        else:
            for t, a in entry["tokens"].items():
                pool[t] = pool.get(t, 0) + a

    # 2. The payload.
    assign = {}  # output index -> {ticker: amount}
    residual = "default"
    payload = payload_of(tx)
    op, ticker, amount = payload if payload else (None, None, None)

    if op == "mine":
        reg = state.ticker(ticker)
        valid = reg is not None and reg["deploy_block"] < height and usable(0)
        if valid:
            credit = min(mine_yield(block_hash), SUPPLY - reg["minted"])
            if credit > 0:
                reg["minted"] += credit
                if reg["minted"] >= SUPPLY and reg["minted_out_height"] is None:
                    reg["minted_out_height"] = height
                assign.setdefault(0, {})[ticker] = credit
        residual = 0 if usable(0) else "burn"

    elif op == "send":
        held = pool.get(ticker, 0) + sum(b.get(ticker, 0) for _, b in listed)
        if usable(1) and held >= amount:
            for _, b in listed:
                if ticker in b:
                    pool[ticker] = pool.get(ticker, 0) + b.pop(ticker)
            assign.setdefault(1, {})[ticker] = amount
            pool[ticker] -= amount
            if pool[ticker] == 0:
                del pool[ticker]
        residual = 2 if usable(2) else "default"

    elif op == "deploy":
        if state.ticker(ticker) is None:
            state.tickers[ticker] = {"supply": SUPPLY, "minted": 0, "deployer": deployer_of(inputs),
                                     "deploy_txid": tx["txid"], "deploy_block": height,
                                     "minted_out_height": None}

    # 3. The rest of the pool goes to one output, or burns.
    if residual == "default":
        first = next((i for i, (opret, _) in enumerate(outs) if not opret), None)
        residual = first if first is not None and outs[first][1] is not None else "burn"
    if pool and residual != "burn":
        for t, a in pool.items():
            assign.setdefault(residual, {})[t] = assign.get(residual, {}).get(t, 0) + a

    # 4. Listing-signed inputs: what did not move with the SEND goes to vout[i].
    for i, balances in listed:
        for t, a in balances.items():
            assign.setdefault(i, {})[t] = assign.get(i, {}).get(t, 0) + a

    for i, tokens in assign.items():
        tokens = {t: a for t, a in tokens.items() if a > 0}
        if tokens:
            state.credit(f'{tx["txid"]}:{i}', outs[i][1], tokens)

# ------------------------------------------------------------------ chain --


class Rpc:
    def __init__(self, url, user, password):
        self.url = url
        self.auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()

    def call(self, method, *params):
        body = json.dumps({"jsonrpc": "1.0", "id": "lucky20", "method": method,
                           "params": list(params)}).encode()
        req = urllib.request.Request(self.url, body, {"Authorization": self.auth,
                                                      "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            reply = json.load(r)
        if reply.get("error"):
            raise RuntimeError(reply["error"])
        return reply["result"]


def sync(state, rpc, stop_height=None, log=print):
    """Apply blocks up to the node's tip (or stop_height), following reorgs."""
    tip = rpc.call("getblockcount")
    target = tip if stop_height is None else min(tip, stop_height)
    while state.height < target:
        h = state.height + 1
        block = rpc.call("getblock", rpc.call("getblockhash", h), 3)
        parent = state.hashes.get(h - 1)
        if parent is not None and block.get("previousblockhash") != parent:
            if h - 1 not in state.undo:
                log("reorganization deeper than the kept undo records: re-index from activation")
                state.__init__()
                continue
            log(f"reorganization: rolling back block {h - 1}")
            state.rollback(h - 1)
            continue
        state.journal = []
        for tx in block["tx"]:
            apply_tx(state, tx, h, block["hash"])
        state.undo[h], state.journal = state.journal, None
        state.hashes[h] = block["hash"]
        state.undo.pop(h - REORG_DEPTH, None)
        state.hashes.pop(h - REORG_DEPTH, None)
        state.height = h
        if h % 100 == 0 or h == target:
            log(f"block {h}: {len(state.outputs)} token outputs, {len(state.tickers)} tickers")
    return state


def main():
    p = argparse.ArgumentParser(description="LUCKY-20 reference indexer")
    p.add_argument("--rpc-url", default=os.environ.get("LUCKY20_RPC_URL", "http://127.0.0.1:8332"))
    p.add_argument("--rpc-user", default=os.environ.get("LUCKY20_RPC_USER", ""))
    p.add_argument("--rpc-password", default=os.environ.get("LUCKY20_RPC_PASSWORD", ""))
    p.add_argument("--rpc-cookie", help="read user:password from Bitcoin Core's .cookie file")
    p.add_argument("--state", default="lucky20-state.json")
    p.add_argument("--follow", action="store_true", help="keep polling for new blocks")
    args = p.parse_args()

    user, password = args.rpc_user, args.rpc_password
    if args.rpc_cookie:
        with open(args.rpc_cookie) as f:
            user, password = f.read().strip().split(":", 1)
    rpc = Rpc(args.rpc_url, user, password)

    state = State()
    if os.path.exists(args.state):
        state = State.load(args.state)
        if state.hashes.get(state.height) not in (None, rpc.call("getblockhash", state.height)):
            print("saved state is not on the node's chain: re-index from activation")
            state = State()
    while True:
        sync(state, rpc)
        state.save(args.state)
        if not args.follow:
            break
        time.sleep(30)


if __name__ == "__main__":
    main()
