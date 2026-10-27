// Scripted answers for the mockup. Later, this adapter is replaced by one that calls Robin's API.
// The answers follow Robin's system prompt and return policy, so the mockup behaves like the real bot.

const IBAN = /\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,4})?\b/i;

const SCRIPT = [
  {
    test: (t) => /ignore|forget your|instructions|system prompt|vergeet je regels|negeer/i.test(t),
    en: "I'm sorry, I can't help with that. Do you have a question about an order, a return or a complaint? I'm happy to help.",
    nl: "Daar kan ik je helaas niet mee helpen. Heb je een vraag over een bestelling, een retour of een klacht? Dan help ik je graag.",
  },
  {
    test: (t) => IBAN.test(t),
    en: "Thanks. Refunds always go back to the payment method you used, so I don't need a bank account number. What's your order number?",
    nl: "Dank je. Een terugbetaling gaat altijd terug naar de betaalmethode die je hebt gebruikt, dus een rekeningnummer heb ik niet nodig. Wat is je bestelnummer?",
  },
  {
    test: (t) => /curtain|made-to-measure|op maat|gordijn/i.test(t),
    en: "I'm sorry your curtains arrived damaged. Made-to-measure products normally can't be returned, but our policy doesn't say what happens when they arrive damaged. Shall I pass this to a colleague who can look at it?",
    nl: "Wat vervelend dat je gordijnen beschadigd zijn aangekomen. Producten op maat kun je normaal niet retourneren, maar ons beleid zegt niet wat er gebeurt als ze beschadigd aankomen. Zal ik dit doorgeven aan een collega?",
  },
  {
    test: (t) => /voucher|compensation|tegoedbon|vergoeding|late|te laat/i.test(t),
    en: "I'm sorry your delivery is late again, I understand that's frustrating. I can't offer a voucher, but I can log a complaint for you. What's your order number?",
    nl: "Wat vervelend dat je bestelling weer te laat is. Een tegoedbon kan ik helaas niet geven, maar ik kan wel een klacht voor je registreren. Wat is je bestelnummer?",
  },
  {
    test: (t) => /\b(\d+|five|six|vijf|zes)\s*(weeks|weken)\b/i.test(t),
    en: "Thanks for checking. You can return products within 30 days of delivery, so after 5 weeks the return window has unfortunately passed. Shall I pass your question to a colleague to see what's possible?",
    nl: "Fijn dat je het even checkt. Je kunt producten binnen 30 dagen na levering retourneren, dus na 5 weken is die termijn helaas voorbij. Zal ik je vraag doorgeven aan een collega om te kijken wat er kan?",
  },
  {
    test: (t) => /return|refund|send (it )?back|retour|terugsturen|terugbetal/i.test(t),
    en: "You can return products within 30 days of delivery, as long as they're unused and in their original packaging. Returns cost €4.95, which is deducted from your refund. What's your order number?",
    nl: "Je kunt producten binnen 30 dagen na levering retourneren, als ze ongebruikt zijn en in de originele verpakking zitten. Een retour kost €4,95, die we van je terugbetaling aftrekken. Wat is je bestelnummer?",
  },
  {
    test: (t) => /weather|weer|recipe|recept|homework|huiswerk/i.test(t),
    en: "I can only help with orders, returns and complaints. Is there anything I can do for you there?",
    nl: "Ik kan je alleen helpen met bestellingen, retouren en klachten. Kan ik daar iets voor je doen?",
  },
];

const DEFAULT = {
  en: "I can help with orders, returns and complaints. Could you tell me a bit more, for example your order number?",
  nl: "Ik help je graag met bestellingen, retouren en klachten. Kun je me iets meer vertellen, bijvoorbeeld je bestelnummer?",
};

const DUTCH = /\b(ik|je|jij|mijn|het|een|niet|wil|kan|bestelling|graag|dank|hoe|wat|waarom)\b/i;

function pickAnswer(text) {
  const lang = DUTCH.test(text) ? "nl" : "en";
  const match = SCRIPT.find((entry) => entry.test(text)) ?? DEFAULT;
  return match[lang];
}

const wait = (ms, signal) =>
  new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    });
  });

export const mockRobinAdapter = {
  async *run({ messages, abortSignal }) {
    const last = messages.at(-1);
    const text = (last?.content ?? [])
      .filter((part) => part.type === "text")
      .map((part) => part.text)
      .join(" ");
    const answer = pickAnswer(text);
    const masked = IBAN.test(text);

    await wait(700, abortSignal); // Robin "thinks" (in the real bot: guardrails + the model)
    const words = answer.split(" ");
    let shown = "";
    for (const word of words) {
      shown = shown ? `${shown} ${word}` : word;
      yield { content: [{ type: "text", text: shown }], metadata: { custom: { masked } } };
      await wait(28, abortSignal);
    }
  },
};
