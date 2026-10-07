// Runs AgentCourt end to end on GenLayer Studio and records every
// transaction hash, consensus result and final agreement state.
//
//   npm run demo
//
// Environment:
//   NETWORK=studio-dev | studionet   (default studio-dev)
//   CONTRACT_ADDRESS=0x...           reuse a deployed contract instead of deploying
//   BUYER_PRIVATE_KEY / SELLER_PRIVATE_KEY   otherwise generated and kept in .demo-accounts.json
//   SCENARIOS=partial,web,accept     subset of scenarios to run

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createAccount, createClient, generatePrivateKey } from "genlayer-js";
import { studioDevnet, studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

const NETWORKS = {
  "studio-dev": {
    chain: studioDevnet,
    explorer: "https://explorer-studio-dev.genlayer.com",
  },
  studionet: {
    chain: studionet,
    explorer: "https://explorer-studio.genlayer.com",
  },
};

const networkName = process.env.NETWORK ?? "studio-dev";
const network = NETWORKS[networkName];
if (!network) {
  throw new Error(`Unknown NETWORK "${networkName}". Use one of: ${Object.keys(NETWORKS).join(", ")}`);
}

const CONTRACT_PATH = new URL("../contracts/AgentCourt.py", import.meta.url);
const ACCOUNTS_PATH = new URL("../.demo-accounts.json", import.meta.url);
const RUNS_DIR = new URL("../demo/runs/", import.meta.url);

// Adjudication runs a web fetch and an LLM call on the leader and on every
// validator, which needs more execution budget than Studio's default quote.
const EXECUTION_BUDGET_MULTIPLIER = 10n;

const DAY = 24 * 60 * 60;

const SCENARIOS = {
  partial: {
    title: "Disputed delivery, partially fulfilled",
    terms:
      "Deliver a competitive analysis report covering exactly 20 named companies in the " +
      "European B2B payments market. For each company the report must include: founding " +
      "year, headquarters, main product, pricing model and one key differentiator. The " +
      "report must end with a ranked shortlist of the top 5 companies.",
    amount: 1000,
    evidence: [
      "Competitive analysis report - European B2B payments (delivered by seller agent)",
      "",
      "Companies covered (14): Adyen, Mollie, Checkout.com, GoCardless, Klarna, Stripe Europe,",
      "Worldline, Nexi, Paysafe, Trustly, SumUp, Payhawk, Pleo, Rapyd Europe.",
      "",
      "Each of the 14 entries lists founding year, headquarters, main product and pricing model.",
      "Key differentiators are given for 9 of the 14 companies.",
      "",
      "Ranked shortlist: 1. Adyen 2. Checkout.com 3. Mollie 4. GoCardless 5. Trustly.",
      "",
      "Not included: the remaining 6 companies were not researched before the deadline.",
    ].join("\n"),
    sellerClaim:
      "The report was delivered on time and covers the most important companies in the " +
      "market, so the agreement is substantially fulfilled.",
    buyerClaim:
      "Only 14 of the 20 required companies are covered and 5 of those are missing the key " +
      "differentiator. The agreement was not fully delivered.",
    resolve: "adjudicate",
  },
  web: {
    title: "Disputed delivery checked against the live web page",
    terms:
      "Publish a public pricing page that lists three subscription tiers named Starter, " +
      "Growth and Enterprise, each with a monthly price in EUR.",
    amount: 500,
    evidence: "The pricing page is live at https://example.com",
    sellerClaim: "The pricing page with all three tiers has been published at the URL above.",
    buyerClaim:
      "The URL does not show any pricing tiers. The seller did not publish the page.",
    resolve: "adjudicate",
  },
  accept: {
    title: "Delivery accepted by the buyer, no dispute",
    terms: "Translate the attached 300-word product description from English into Turkish.",
    amount: 200,
    evidence:
      "Turkish translation delivered: 'AgentCourt, otonom ajanlar arasındaki ticarette " +
      "anlaşmazlıkları GenLayer üzerinde çözen bir protokoldür...' (full text, 312 words).",
    sellerClaim: "The full translation has been delivered.",
    resolve: "accept",
  },
};

function loadAccounts() {
  if (process.env.BUYER_PRIVATE_KEY && process.env.SELLER_PRIVATE_KEY) {
    return {
      buyer: process.env.BUYER_PRIVATE_KEY,
      seller: process.env.SELLER_PRIVATE_KEY,
    };
  }
  if (existsSync(ACCOUNTS_PATH)) {
    return JSON.parse(readFileSync(ACCOUNTS_PATH, "utf8"));
  }
  const keys = { buyer: generatePrivateKey(), seller: generatePrivateKey() };
  writeFileSync(ACCOUNTS_PATH, JSON.stringify(keys, null, 2) + "\n");
  return keys;
}

function plain(value) {
  if (value instanceof Map) {
    return Object.fromEntries([...value].map(([k, v]) => [k, plain(v)]));
  }
  if (Array.isArray(value)) return value.map(plain);
  if (typeof value === "bigint") return Number(value);
  return value;
}

async function studioFees(client) {
  const config = await client.request({ method: "sim_getFeeConfig", params: [] });
  if (!config?.enabled) return undefined;

  const distribution = Object.fromEntries(
    Object.entries(config.defaultFees.distribution).map(([key, value]) => [
      key,
      Array.isArray(value) ? value.map(BigInt) : BigInt(value),
    ]),
  );
  distribution.executionBudgetPerRound *= EXECUTION_BUDGET_MULTIPLIER;
  return { distribution };
}

function summarizeReceipt(receipt) {
  const leader = receipt.consensus_data?.leader_receipt?.[0];
  const votes = Object.values(receipt.consensus_data?.votes ?? {});
  return {
    status: receipt.statusName ?? receipt.status,
    execution: receipt.txExecutionResultName,
    result: leader?.result,
    votes: {
      agree: votes.filter((v) => v === "agree").length,
      disagree: votes.filter((v) => v === "disagree").length,
      total: votes.filter((v) => v !== "idle").length,
    },
  };
}

const keys = loadAccounts();
const buyer = createAccount(keys.buyer);
const seller = createAccount(keys.seller);
const clients = {
  buyer: createClient({ chain: network.chain, account: buyer }),
  seller: createClient({ chain: network.chain, account: seller }),
};

const run = {
  network: networkName,
  chainId: network.chain.id,
  rpc: network.chain.rpcUrls.default.http[0],
  startedAt: new Date().toISOString(),
  buyer: buyer.address,
  seller: seller.address,
  contract: process.env.CONTRACT_ADDRESS ?? null,
  transactions: [],
  scenarios: [],
};

let fees;

async function send(role, label, action) {
  const client = clients[role];
  process.stdout.write(`  ${label} (${role}) ... `);
  const hash = await action(client);
  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    interval: 3000,
    retries: 200,
  });
  const summary = summarizeReceipt(receipt);
  const entry = { label, role, hash, ...summary };
  run.transactions.push(entry);

  const ok = summary.execution === "FINISHED_WITH_RETURN";
  console.log(
    `${ok ? "ok" : "FAILED"}  ${hash}  votes ${summary.votes.agree}/${summary.votes.total}` +
      (ok ? "" : `  ${JSON.stringify(summary.result)}`),
  );
  if (!ok) {
    throw new Error(`${label} did not succeed: ${JSON.stringify(summary.result)}`);
  }
  return { receipt, entry };
}

function write(role, label, functionName, args) {
  return send(role, label, (client) =>
    client.writeContract({ address: run.contract, functionName, args, value: 0n, fees }),
  );
}

async function readAgreement(agreementId) {
  return plain(
    await clients.buyer.readContract({
      address: run.contract,
      functionName: "get_agreement",
      args: [agreementId],
    }),
  );
}

async function runScenario(name) {
  const scenario = SCENARIOS[name];
  console.log(`\n${scenario.title}`);

  const deadline = Math.floor(Date.now() / 1000) + 7 * DAY;
  const steps = [];

  const created = await write("buyer", `${name}: create_agreement`, "create_agreement", [
    seller.address,
    scenario.terms,
    scenario.amount,
    deadline,
  ]);
  steps.push(created.entry);
  const agreementId = Number(
    await clients.buyer.readContract({
      address: run.contract,
      functionName: "get_agreement_count",
      args: [],
    }),
  );

  steps.push((await write("buyer", `${name}: fund_agreement`, "fund_agreement", [agreementId])).entry);
  steps.push(
    (
      await write("seller", `${name}: submit_delivery`, "submit_delivery", [
        agreementId,
        scenario.evidence,
        scenario.sellerClaim,
      ])
    ).entry,
  );

  if (scenario.resolve === "adjudicate") {
    steps.push(
      (await write("buyer", `${name}: open_dispute`, "open_dispute", [agreementId, scenario.buyerClaim])).entry,
    );
    steps.push((await write("buyer", `${name}: adjudicate`, "adjudicate", [agreementId])).entry);
  } else {
    steps.push((await write("buyer", `${name}: accept_delivery`, "accept_delivery", [agreementId])).entry);
  }

  const settled = await write("buyer", `${name}: settle`, "settle", [agreementId]);
  steps.push(settled.entry);

  const agreement = await readAgreement(agreementId);
  console.log(
    `  -> ${agreement.verdict} ${agreement.completion_percent}% ` +
      `(confidence ${agreement.confidence}), status ${agreement.status}`,
  );

  run.scenarios.push({
    name,
    title: scenario.title,
    agreementId,
    settlement: settled.entry.result?.payload?.readable ?? null,
    agreement,
    transactions: steps.map((s) => s.hash),
  });
}

console.log(`Network   ${networkName} (chain ${network.chain.id})`);
console.log(`Buyer     ${buyer.address}`);
console.log(`Seller    ${seller.address}`);

for (const account of [buyer, seller]) {
  await clients.buyer.request({ method: "sim_fundAccount", params: [account.address, 1e18] });
}
fees = await studioFees(clients.buyer);

if (!run.contract) {
  console.log("\nDeploy");
  const { receipt } = await send("buyer", "deploy AgentCourt", (client) =>
    client.deployContract({ code: readFileSync(CONTRACT_PATH, "utf8"), args: [], fees }),
  );
  run.contract = receipt.data?.contract_address ?? receipt.txDataDecoded?.contractAddress;
}
console.log(`Contract  ${run.contract}`);

const selected = (process.env.SCENARIOS ?? Object.keys(SCENARIOS).join(","))
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

for (const name of selected) {
  if (!SCENARIOS[name]) throw new Error(`Unknown scenario "${name}"`);
  await runScenario(name);
}

run.finishedAt = new Date().toISOString();
run.explorer = `${network.explorer}/address/${run.contract}`;

mkdirSync(RUNS_DIR, { recursive: true });
const file = new URL(`${run.startedAt.replace(/[:.]/g, "-")}-${networkName}.json`, RUNS_DIR);
writeFileSync(file, JSON.stringify(run, null, 2) + "\n");

console.log(`\nExplorer  ${run.explorer}`);
console.log(`Saved     ${file.pathname}`);
