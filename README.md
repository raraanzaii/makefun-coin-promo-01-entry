# GAVEL ($GAVEL)

[![make.fun bounty](https://img.shields.io/badge/make.fun-bounty%20entry-blueviolet)](https://make.fun/bounty/makefun-coin-promo-01)

**$GAVEL is the sound an AI agent hears when it gets paid.** The coin is the gavel of
make.fun's AI judge: agents build, the judge deliberates, the gavel falls — and the
winners are paid in USDC on Solana. Every trader knows the feeling of waiting on a
verdict. Hold the gavel.

## The bounty

This repository is an entry for the make.fun bounty **"Launch a coin that sells
make.fun"** ([makefun-coin-promo-01](https://make.fun/bounty/makefun-coin-promo-01)).
make.fun is where people and their AI agents build programs, enter paid bounty
competitions, and are scored and ranked in the open by an AI judge. The coin itself —
its name, logo, story and links, exactly as pump.fun shows them — is the entry.

- Website on the coin: https://make.fun/bounty/makefun-coin-promo-01
- Logo: [`logo.png`](logo.png) (drawn as [`logo.svg`](logo.svg))
- Pump.fun metadata: [`metadata.json`](metadata.json)

## The program

`main.ts` (Node 22, standard library only) hands the gate the record of the launch:
it validates `LAUNCH.json` — the coin's mint and the signature of the transaction that
created it — and copies it to the output directory.

Run it locally:

```sh
mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
```

## The launch

`launch.py` launched the coin on pump.fun from the wallet linked to the make.fun
account: it asks PumpPortal for a create transaction naming the metadata in
`metadata.json`, signs it with the creator and mint keypairs, and sends it to Solana.
The resulting mint and create-transaction signature are recorded in `LAUNCH.json`.

## License

MIT — see [`LICENSE`](LICENSE).
