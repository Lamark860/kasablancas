// almanac.jsx — направление 2: «Альманах»
// Тёплый бумажный фон, печатные ноты эзотерических альманахов XIX в.,
// символы стихий и фаз луны как декор, чёрно-белые акценты + терракота.

const ALM = {
  paper: '#e8dec5',
  paperDeep: '#d9cda9',
  ink: '#1c1814',
  inkSoft: '#4a3f30',
  terra: '#a64427',
  rule: '#8a7a55',
  display: '"UnifrakturCook", "IM Fell English", "Cormorant Garamond", serif',
  serif: '"IM Fell English", "EB Garamond", "Times New Roman", serif',
  sans: '"IBM Plex Mono", ui-monospace, monospace',
};

// Декоративные SVG-символы
function AlmSymbol({ kind, size = 16 }) {
  const props = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.2 };
  if (kind === 'sun') return (<svg {...props}><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/>{[0,45,90,135,180,225,270,315].map(a=>{const r=a*Math.PI/180;return <line key={a} x1={12+Math.cos(r)*7} y1={12+Math.sin(r)*7} x2={12+Math.cos(r)*10.5} y2={12+Math.sin(r)*10.5}/>;})}</svg>);
  if (kind === 'moon') return (<svg {...props}><path d="M16 4 a 9 9 0 1 0 0 16 a 7 7 0 1 1 0 -16 z" fill="currentColor" stroke="none"/></svg>);
  if (kind === 'water') return (<svg {...props}><path d="M12 4 C 6 12 6 16 6 17 a 6 6 0 0 0 12 0 c 0 -1 0 -5 -6 -13 z"/></svg>);
  if (kind === 'fire') return (<svg {...props}><path d="M12 3 C 14 8 18 9 18 14 a 6 6 0 0 1 -12 0 c 0 -3 2 -4 3 -7 c 1 2 1 4 3 4 c 1 0 0 -3 0 -8 z"/></svg>);
  if (kind === 'earth') return (<svg {...props}><circle cx="12" cy="12" r="9"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="12" y1="3" x2="12" y2="21"/></svg>);
  if (kind === 'air') return (<svg {...props}><path d="M3 9 h 12 a 3 3 0 1 0 -3 -3"/><path d="M3 14 h 16 a 3 3 0 1 1 -3 3"/></svg>);
  if (kind === 'star') return (<svg {...props}>{[0,72,144,216,288].map(a=>{const r=a*Math.PI/180-Math.PI/2;return <line key={a} x1="12" y1="12" x2={12+Math.cos(r)*9} y2={12+Math.sin(r)*9}/>;})}</svg>);
  return null;
}

const PaperGrain = () => (
  <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', backgroundImage: 'radial-gradient(rgba(0,0,0,.04) 1px, transparent 1px)', backgroundSize: '3px 3px', mixBlendMode: 'multiply', opacity: 0.5 }} />
);

function AlmForm() {
  const c = window.MOCK_CLIENT;
  const Field = ({ label, value, sym }) => (
    <div style={{ marginBottom: 18, position: 'relative' }}>
      <div style={{ font: `500 8px/1 ${ALM.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: ALM.terra, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
        {sym && <span style={{ color: ALM.terra }}><AlmSymbol kind={sym} size={11} /></span>}
        {label}
      </div>
      <div style={{ font: `400 16px/1.2 ${ALM.serif}`, color: ALM.ink, fontStyle: 'italic', borderBottom: `1px solid ${ALM.ink}`, paddingBottom: 6 }}>{value}</div>
    </div>
  );
  return (
    <div style={{ width: 480, height: 720, background: ALM.paper, padding: '36px 40px', fontFamily: ALM.serif, color: ALM.ink, position: 'relative', overflow: 'hidden' }}>
      <PaperGrain />
      {/* Top frame */}
      <div style={{ border: `1px solid ${ALM.ink}`, padding: '4px', position: 'relative', zIndex: 1 }}>
        <div style={{ border: `1px solid ${ALM.ink}`, padding: '20px 24px', textAlign: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 14, color: ALM.terra, marginBottom: 8 }}>
            <AlmSymbol kind="sun" size={14} />
            <AlmSymbol kind="moon" size={14} />
            <AlmSymbol kind="star" size={14} />
          </div>
          <div style={{ font: `400 28px/1 ${ALM.display}`, letterSpacing: '0.04em' }}>Almanach Florae</div>
          <div style={{ font: `400 italic 11px/1.3 ${ALM.serif}`, color: ALM.inkSoft, marginTop: 6 }}>о растениях, что приходят к человеку</div>
        </div>
      </div>

      <div style={{ position: 'relative', zIndex: 1, marginTop: 22 }}>
        <div style={{ font: `400 italic 12px/1 ${ALM.serif}`, color: ALM.terra, marginBottom: 4 }}>лист первый · сведения</div>
        <div style={{ font: `400 22px/1.1 ${ALM.display}` }}>о новой госпоже</div>
        <div style={{ height: 1, background: ALM.ink, margin: '12px 0 18px' }} />

        <Field label="имя" value={c.fullName} sym="star" />
        <Field label="час и день" value={`${c.birthDate}, ${c.birthTime}`} sym="sun" />
        <Field label="место" value={c.birthPlace} sym="earth" />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
          <Field label="пол" value={c.gender} sym="moon" />
          <Field label="взгляд" value={c.eyeColor} sym="water" />
        </div>

        <div style={{ marginTop: 6, padding: '12px 14px', background: ALM.paperDeep, border: `1px dashed ${ALM.rule}`, position: 'relative' }}>
          <div style={{ font: `500 8px/1 ${ALM.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: ALM.terra, marginBottom: 4 }}>сад</div>
          <div style={{ font: `400 italic 13px/1.4 ${ALM.serif}` }}>{c.garden}<br/>{c.zone}</div>
        </div>

        <button style={{ marginTop: 22, width: '100%', padding: '14px 0', background: ALM.ink, color: ALM.paper, border: `2px double ${ALM.ink}`, font: `400 13px/1 ${ALM.display}`, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}>
          ✦ открыть лист подбора
        </button>

        <div style={{ marginTop: 14, font: `400 italic 10px/1.4 ${ALM.serif}`, color: ALM.inkSoft, textAlign: 'center' }}>
          сводятся пять источников — древо · цвет · небо · славь · взгляд
        </div>
      </div>
    </div>
  );
}

function AlmExpert() {
  const c = window.MOCK_CLIENT;
  const pool = window.MOCK_POOL;
  const PI = window.PlantIcon;

  return (
    <div style={{ width: 720, height: 900, background: ALM.paper, padding: '32px 36px 24px', fontFamily: ALM.serif, color: ALM.ink, position: 'relative', overflow: 'hidden' }}>
      <PaperGrain />
      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* masthead */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `2px solid ${ALM.ink}`, borderBottom: `1px solid ${ALM.ink}`, padding: '10px 0' }}>
          <div style={{ font: `400 22px/1 ${ALM.display}`, letterSpacing: '0.04em' }}>Almanach Florae</div>
          <div style={{ display: 'flex', gap: 10, color: ALM.terra }}><AlmSymbol kind="sun" size={14}/><AlmSymbol kind="moon" size={14}/><AlmSymbol kind="star" size={14}/></div>
          <div style={{ font: `500 8px/1.4 ${ALM.sans}`, letterSpacing: '0.18em', color: ALM.inkSoft }}>лист II · экспертный<br/>{c.shortName} · {c.birthDateShort}</div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, marginTop: 18 }}>
          {/* left col */}
          <div>
            <div style={{ font: `400 italic 11px/1 ${ALM.serif}`, color: ALM.terra, marginBottom: 4 }}>tabula plantarum</div>
            <div style={{ font: `400 22px/1.1 ${ALM.display}`, marginBottom: 14 }}>Свод растений</div>

            {pool.map((p, i) => (
              <div key={p.id} style={{ marginBottom: 16, paddingBottom: 14, borderBottom: `1px solid ${ALM.rule}` }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ font: `400 11px/1 ${ALM.sans}`, color: ALM.terra }}>{String(i+1).padStart(2,'0')}</span>
                    <span style={{ font: `400 18px/1 ${ALM.display}` }}>{p.name}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    {Array.from({length: p.matches}).map((_, j) => <span key={j} style={{ color: ALM.terra }}>✦</span>)}
                    <span style={{ color: ALM.rule }}>{Array.from({length: 5 - p.matches}).map((_, j) => '·').join('')}</span>
                  </div>
                </div>
                <div style={{ font: `400 italic 10px/1.3 ${ALM.serif}`, color: ALM.inkSoft, marginBottom: 6 }}>{p.nameLat} · {p.role}</div>
                <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                  {p.sources.map((s, j) => (
                    <li key={j} style={{ font: `400 11px/1.5 ${ALM.serif}`, paddingLeft: 16, position: 'relative' }}>
                      <span style={{ position: 'absolute', left: 0, color: ALM.terra }}>—</span>
                      <em style={{ color: ALM.ink }}>{s.sys}.</em> <span style={{ color: ALM.inkSoft }}>{s.detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* right col */}
          <div>
            <div style={{ border: `1px solid ${ALM.ink}`, padding: 16, marginBottom: 16 }}>
              <div style={{ font: `400 italic 11px/1 ${ALM.serif}`, color: ALM.terra, marginBottom: 4 }}>fontes</div>
              <div style={{ font: `400 18px/1.1 ${ALM.display}`, marginBottom: 10 }}>Источники</div>
              <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                {window.MOCK_ORACLES_USED.map((o, i) => (
                  <li key={i} style={{ font: `400 12px/1.5 ${ALM.serif}`, padding: '4px 0', display: 'flex', justifyContent: 'space-between', borderBottom: i < 4 ? `1px dotted ${ALM.rule}` : 'none' }}>
                    <span>{o}</span>
                    <span style={{ color: ALM.terra, fontFamily: ALM.sans, fontSize: 10 }}>✓</span>
                  </li>
                ))}
              </ul>
            </div>

            <div style={{ background: ALM.paperDeep, border: `1px solid ${ALM.rule}`, padding: 16, marginBottom: 16 }}>
              <div style={{ font: `400 italic 11px/1 ${ALM.serif}`, color: ALM.terra, marginBottom: 4 }}>exclusi</div>
              <div style={{ font: `400 18px/1.1 ${ALM.display}`, marginBottom: 10 }}>Исключены</div>
              {window.MOCK_EXCLUDED.map((e, i) => (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ font: `400 italic 13px/1.2 ${ALM.serif}`, textDecoration: 'line-through', textDecorationColor: ALM.terra }}>{e.name}</div>
                  <div style={{ font: `400 11px/1.4 ${ALM.serif}`, color: ALM.inkSoft, marginTop: 2 }}>{e.reason}</div>
                </div>
              ))}
            </div>

            <div style={{ border: `2px double ${ALM.ink}`, padding: 18, textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 14, color: ALM.terra, marginBottom: 8 }}>
                <AlmSymbol kind="water" size={20} />
                <AlmSymbol kind="water" size={20} />
                <AlmSymbol kind="water" size={20} />
              </div>
              <div style={{ font: `400 italic 12px/1.4 ${ALM.serif}`, color: ALM.ink }}>
                Стихия воды — три из пяти. Композиция «у тихой воды» как место силы.
              </div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 14, borderTop: `1px solid ${ALM.ink}`, paddingTop: 8, display: 'flex', justifyContent: 'space-between', font: `400 italic 10px/1 ${ALM.serif}`, color: ALM.inkSoft }}>
          <span>folium II · expertus tantum</span>
          <span>—— ✦ ——</span>
          <span>не для гостьи</span>
        </div>
      </div>
    </div>
  );
}

function AlmClient() {
  const c = window.MOCK_CLIENT;
  const main = window.MOCK_POOL[0];
  const others = window.MOCK_POOL.slice(1);
  const PI = window.PlantIcon;

  return (
    <div style={{ width: 480, height: 900, background: ALM.paper, padding: '36px 40px 28px', fontFamily: ALM.serif, color: ALM.ink, position: 'relative', overflow: 'hidden' }}>
      <PaperGrain />
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ textAlign: 'center', borderTop: `2px solid ${ALM.ink}`, borderBottom: `1px solid ${ALM.ink}`, padding: '12px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12, color: ALM.terra, marginBottom: 4 }}>
            <AlmSymbol kind="sun" size={12}/><AlmSymbol kind="star" size={12}/><AlmSymbol kind="moon" size={12}/>
          </div>
          <div style={{ font: `400 22px/1 ${ALM.display}`, letterSpacing: '0.04em' }}>Almanach Florae</div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 22 }}>
          <div style={{ font: `400 italic 12px/1 ${ALM.serif}`, color: ALM.terra }}>составлено для</div>
          <div style={{ font: `400 30px/1.1 ${ALM.display}`, marginTop: 6 }}>{c.shortName}</div>
        </div>

        {/* main */}
        <div style={{ marginTop: 22, border: `1px solid ${ALM.ink}`, padding: 24, textAlign: 'center', position: 'relative' }}>
          <div style={{ position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)', background: ALM.paper, padding: '0 14px', font: `500 8px/1 ${ALM.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', color: ALM.terra }}>arbor anima</div>
          <div style={{ color: ALM.ink, display: 'flex', justifyContent: 'center', marginTop: 6 }}>
            <PI kind={main.icon} size={130} stroke={1.0} />
          </div>
          <div style={{ font: `400 30px/1.05 ${ALM.display}`, marginTop: 12 }}>{main.name}</div>
          <div style={{ font: `400 italic 11px/1 ${ALM.serif}`, color: ALM.inkSoft, marginTop: 4 }}>{main.nameLat}</div>
          <div style={{ height: 1, width: 40, background: ALM.terra, margin: '14px auto' }} />
          <div style={{ font: `400 italic 14px/1.5 ${ALM.serif}`, marginTop: 6 }}>«{main.storyShort}»</div>
          <div style={{ font: `400 12px/1.6 ${ALM.serif}`, color: ALM.inkSoft, marginTop: 10 }}>{main.storyLong}</div>
        </div>

        <div style={{ marginTop: 18 }}>
          <div style={{ textAlign: 'center', font: `400 italic 12px/1 ${ALM.serif}`, color: ALM.terra, marginBottom: 12 }}>сопровождают</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {others.map((p) => (
              <div key={p.id} style={{ border: `1px dashed ${ALM.rule}`, padding: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ color: ALM.ink }}><PI kind={p.icon} size={36} stroke={1.0} /></span>
                <div>
                  <div style={{ font: `400 14px/1.1 ${ALM.display}` }}>{p.name}</div>
                  <div style={{ font: `400 italic 10px/1.3 ${ALM.serif}`, color: ALM.inkSoft, marginTop: 2 }}>{p.storyShort}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ position: 'absolute', bottom: 22, left: 40, right: 40, textAlign: 'center', borderTop: `1px solid ${ALM.ink}`, paddingTop: 12 }}>
          <div style={{ font: `400 italic 11px/1.4 ${ALM.serif}`, color: ALM.inkSoft, marginBottom: 8 }}>да воплотится сие в саду</div>
          <div style={{ font: `400 13px/1 ${ALM.display}`, color: ALM.ink, letterSpacing: '0.1em' }}>✦ заказать закладку места силы ✦</div>
        </div>
      </div>
    </div>
  );
}

window.AlmForm = AlmForm;
window.AlmExpert = AlmExpert;
window.AlmClient = AlmClient;
