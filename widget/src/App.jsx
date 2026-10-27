import { useState } from "react";
import RobinWidget, { MOCK } from "./RobinWidget.jsx";

const MODELS = ["GPT-6 Sol", "GPT-4.1 mini"];
const EFFORTS = ["none", "low", "medium", "high"];

function load(key, fallback) {
  try {
    return localStorage.getItem(`robin.${key}`) ?? fallback;
  } catch {
    return fallback;
  }
}
function save(key, value) {
  try {
    localStorage.setItem(`robin.${key}`, value);
  } catch {
    /* storage unavailable: settings just aren't remembered */
  }
}

function CoursePanel({ settings, setSettings }) {
  const [expanded, setExpanded] = useState(true);
  const update = (key) => (event) => {
    const value = event.target.value;
    if (key !== "passcode") save(key, value);
    setSettings((current) => ({ ...current, [key]: value }));
  };
  return (
    <aside className={`course ${expanded ? "" : "course--collapsed"}`} aria-label="Course settings">
      <button type="button" className="course__toggle" onClick={() => setExpanded((v) => !v)} aria-expanded={expanded}>
        Course settings <span aria-hidden="true">{expanded ? "–" : "+"}</span>
      </button>
      {expanded && (
        <div className="course__body">
          <label>
            First name or nickname
            <input id="robin-name" value={settings.name} onChange={update("name")} autoComplete="off" />
            <small>Shown in Langfuse, so you can find your own chats.</small>
          </label>
          {!MOCK && (
            <label>
              Course passcode
              <input id="robin-passcode" type="password" value={settings.passcode} onChange={update("passcode")} />
            </label>
          )}
          <div className="course__row">
            <label>
              Robin's model
              <select id="robin-model" value={settings.model} onChange={update("model")}>
                {MODELS.map((m) => (
                  <option key={m}>{m}</option>
                ))}
              </select>
            </label>
            <label>
              Reasoning effort
              <select id="robin-effort" value={settings.effort} onChange={update("effort")} disabled={settings.model !== "GPT-6 Sol"}>
                {EFFORTS.map((e) => (
                  <option key={e}>{e}</option>
                ))}
              </select>
            </label>
          </div>
          {MOCK && <p className="course__mock">Preview: Robin's answers are scripted, and these settings have no effect yet.</p>}
        </div>
      )}
    </aside>
  );
}

const PRODUCTS = [
  { name: "Duin vase", note: "Hand-thrown stoneware, 28 cm", price: "€ 49,00", art: "vase" },
  { name: "Kiezel table lamp", note: "Linen shade, oak base", price: "€ 89,00", art: "lamp" },
  { name: "Golf cushion cover", note: "Washed cotton, 50 × 50 cm", price: "€ 34,50", art: "cushion" },
  { name: "Made-to-measure curtains", note: "Heavy linen, your size", price: "from € 129,00", art: "curtain" },
];

function ProductArt({ kind }) {
  const common = { fill: "none", stroke: "var(--ink)", strokeWidth: 2.2, strokeLinejoin: "round", strokeLinecap: "round" };
  return (
    <svg viewBox="0 0 160 160" className="product__svg" aria-hidden="true">
      {kind === "vase" && (
        <>
          <path d="M66 30h28M70 30c0 18-24 26-24 62 0 22 14 38 34 38s34-16 34-38c0-36-24-44-24-62" {...common} fill="var(--clay)" />
          <path d="M58 92c14 6 30 6 44 0" {...common} />
        </>
      )}
      {kind === "lamp" && (
        <>
          <path d="M52 70l12-40h32l12 40z" {...common} fill="var(--sun)" />
          <path d="M80 70v52M60 128h40" {...common} />
          <rect x="70" y="120" width="20" height="10" rx="3" {...common} fill="var(--oak)" />
        </>
      )}
      {kind === "cushion" && (
        <>
          <path d="M38 50c14-8 70-8 84 0 8 20 8 40 0 60-14 8-70 8-84 0-8-20-8-40 0-60z" {...common} fill="var(--sage)" />
          <path d="M60 80c8-10 32-10 40 0" {...common} />
        </>
      )}
      {kind === "curtain" && (
        <>
          <path d="M34 34h92" {...common} />
          <path d="M42 36c-4 30 6 62-2 92h30c-6-30 4-62 0-92z" {...common} fill="var(--fog)" />
          <path d="M90 36c-4 30 6 62-2 92h30c-6-30 4-62 0-92z" {...common} fill="var(--fog)" />
        </>
      )}
    </svg>
  );
}

export default function App() {
  const [settings, setSettings] = useState(() => ({
    name: load("name", ""),
    passcode: "",
    model: load("model", "GPT-6 Sol"),
    effort: load("effort", "medium"),
  }));
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="demo-bar" role="note">
        Demo shop for the course <em>GenAI design for conversations and content</em>. Nest & Co is invented: nothing here is for sale.
      </div>

      <header className="site-header">
        <a className="logo" href="#top" aria-label="Nest & Co home">
          Nest<span>&</span>Co
        </a>
        <nav className="site-nav" aria-label="Main">
          <a href="#shop">Living</a>
          <a href="#shop">Lighting</a>
          <a href="#shop">Textiles</a>
          <a href="#help">Help & returns</a>
        </nav>
        <span className="basket" aria-label="Basket, 0 items">
          Basket <b>0</b>
        </span>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero__text">
            <p className="eyebrow">Autumn collection</p>
            <h1>Homeware that settles in.</h1>
            <p className="hero__lead">
              Stoneware, linen and oak, made in small batches by makers we know by name. Changed your mind? You have 30 days.
            </p>
            <a className="btn" href="#shop">
              Shop the collection
            </a>
          </div>
          <div className="hero__art" aria-hidden="true">
            <div className="hero__shelf" />
            <ProductArt kind="vase" />
            <ProductArt kind="lamp" />
          </div>
        </section>

        <section id="shop" className="products" aria-labelledby="shop-title">
          <h2 id="shop-title">New this week</h2>
          <ul className="product-grid">
            {PRODUCTS.map((p) => (
              <li key={p.name} className="product">
                <div className="product__image">
                  <ProductArt kind={p.art} />
                </div>
                <h3>{p.name}</h3>
                <p className="product__note">{p.note}</p>
                <p className="product__price">{p.price}</p>
              </li>
            ))}
          </ul>
        </section>

        <section id="help" className="help" aria-labelledby="help-title">
          <h2 id="help-title">Returns, simply explained</h2>
          <ul className="help__list">
            <li>
              <b>30 days</b>
              <span>to return a product after delivery</span>
            </li>
            <li>
              <b>Unused</b>
              <span>and in its original packaging</span>
            </li>
            <li>
              <b>€ 4,95</b>
              <span>return costs, free if it arrived damaged</span>
            </li>
            <li>
              <b>14 days</b>
              <span>to get your refund after we receive it</span>
            </li>
          </ul>
          <p className="help__more">Made-to-measure products can't be returned. Questions? Robin is happy to help, bottom right.</p>
        </section>
      </main>

      <footer className="site-footer">
        <span className="logo logo--small">
          Nest<span>&</span>Co
        </span>
        <span>An invented shop, built to practise conversation design.</span>
      </footer>

      <CoursePanel settings={settings} setSettings={setSettings} />
      <RobinWidget
        key={sessionId}
        open={open}
        onOpenChange={setOpen}
        onNewConversation={() => setSessionId(crypto.randomUUID())}
        settings={{ ...settings, sessionId }}
      />
    </>
  );
}
