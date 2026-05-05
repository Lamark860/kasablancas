// herbarium.jsx — направление 1: «Гербарий»
// Светлый кремовый фон, ботанические гравюры, serif-типографика,
// тонкие линии, акценты тёмно-зелёный + охра.

const HERB = {
  bg: '#f5f0e6',
  bgDeep: '#ede6d6',
  ink: '#2a2a26',
  inkSoft: '#5a564c',
  green: '#3a4a32',
  ochre: '#a8782e',
  rule: '#c9bfa8',
  serif: '"EB Garamond", "Cormorant Garamond", "Times New Roman", serif',
  sans: '"Inter Tight", "Helvetica Neue", sans-serif',
};

function HerbForm() {
  const c = window.MOCK_CLIENT;
  const Field = ({ label, value, mono }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 14 }}>
      <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.18em', textTransform: 'uppercase', color: HERB.inkSoft }}>{label}</div>
      <div style={{ font: `400 14px/1.3 ${mono ? 'ui-monospace, monospace' : HERB.serif}`, color: HERB.ink, borderBottom: `1px solid ${HERB.rule}`, paddingBottom: 6 }}>{value}</div>
    </div>
  );
  return (
    <div style={{ width: 480, height: 720, background: HERB.bg, padding: '40px 44px', fontFamily: HERB.serif, color: HERB.ink, position: 'relative', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: `1px solid ${HERB.ink}`, paddingBottom: 10 }}>
        <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: HERB.green }}>Hortus · Anima</div>
        <div style={{ font: `400 9px/1 ${HERB.sans}`, color: HERB.inkSoft, letterSpacing: '0.1em' }}>NO. 037 · 2026</div>
      </div>
      <div style={{ marginTop: 28, marginBottom: 22 }}>
        <div style={{ font: `400 italic 13px/1 ${HERB.serif}`, color: HERB.ochre }}>nova consultatio</div>
        <div style={{ font: `400 32px/1.05 ${HERB.serif}`, marginTop: 8, letterSpacing: '-0.01em' }}>Лист новой<br/>заказчицы</div>
        <div style={{ font: `400 11px/1.5 ${HERB.serif}`, color: HERB.inkSoft, marginTop: 12, fontStyle: 'italic', maxWidth: 320 }}>заполняется экспертом перед составлением подбора. источники не показываются клиенту.</div>
      </div>

      <Field label="имя" value={c.fullName} />
      <Field label="дата рождения" value={c.birthDate} mono />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Field label="время" value={c.birthTime} mono />
        <Field label="место" value={c.birthPlace} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Field label="пол" value={c.gender} />
        <Field label="глаза" value={c.eyeColor} />
      </div>

      <div style={{ marginTop: 8, padding: '14px 0', borderTop: `1px solid ${HERB.rule}`, borderBottom: `1px solid ${HERB.rule}` }}>
        <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.18em', textTransform: 'uppercase', color: HERB.inkSoft, marginBottom: 8 }}>Участок</div>
        <div style={{ font: `400 13px/1.4 ${HERB.serif}` }}>{c.garden}<br/><span style={{ color: HERB.ochre }}>{c.zone}</span></div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 24 }}>
        <div style={{ font: `400 italic 11px/1 ${HERB.serif}`, color: HERB.inkSoft }}>задействуются 5 систем — друиды (деревья · цветы), зодиак, славянский, цвет глаз</div>
      </div>
      <button style={{ marginTop: 18, width: '100%', padding: '14px 0', background: HERB.green, color: HERB.bg, border: 'none', font: `500 11px/1 ${HERB.sans}`, letterSpacing: '0.28em', textTransform: 'uppercase', cursor: 'pointer' }}>Составить подбор</button>

      <div style={{ position: 'absolute', bottom: 18, left: 44, right: 44, display: 'flex', justifyContent: 'space-between', font: `400 italic 10px/1 ${HERB.serif}`, color: HERB.inkSoft, borderTop: `1px solid ${HERB.rule}`, paddingTop: 10 }}>
        <span>fol. I</span>
        <span>internal use only</span>
      </div>
    </div>
  );
}

function HerbExpert() {
  const c = window.MOCK_CLIENT;
  const pool = window.MOCK_POOL;
  const PI = window.PlantIcon;

  return (
    <div style={{ width: 720, height: 900, background: HERB.bg, padding: '36px 40px 28px', fontFamily: HERB.serif, color: HERB.ink, overflow: 'hidden', position: 'relative' }}>
      {/* header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: `1px solid ${HERB.ink}`, paddingBottom: 8 }}>
        <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: HERB.green }}>Подбор · экспертный лист</div>
        <div style={{ font: `400 9px/1 ${HERB.sans}`, letterSpacing: '0.14em', color: HERB.inkSoft }}>{c.shortName.toUpperCase()} · {c.birthDateShort} · {c.zone}</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: 28, marginTop: 18 }}>
        {/* main column */}
        <div>
          <div style={{ font: `400 italic 12px/1 ${HERB.serif}`, color: HERB.ochre }}>пул кандидатов · 5 из 12 после фильтра участка</div>
          <div style={{ font: `400 24px/1.05 ${HERB.serif}`, marginTop: 4, letterSpacing: '-0.01em' }}>5 растений с пересечениями</div>

          {pool.map((p, i) => (
            <div key={p.id} style={{ display: 'grid', gridTemplateColumns: '60px 1fr 70px', gap: 14, padding: '14px 0', borderTop: i === 0 ? `1px solid ${HERB.ink}` : `1px solid ${HERB.rule}`, alignItems: 'start' }}>
              <div style={{ color: HERB.green, paddingTop: 2 }}>
                <PI kind={p.icon} size={56} stroke={1.0} />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                  <div style={{ font: `400 18px/1.1 ${HERB.serif}` }}>{p.name}</div>
                  <div style={{ font: `400 italic 11px/1 ${HERB.serif}`, color: HERB.inkSoft }}>{p.nameLat}</div>
                </div>
                <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.16em', textTransform: 'uppercase', color: HERB.ochre, marginTop: 4 }}>{p.role}</div>
                <ul style={{ margin: '8px 0 0', padding: 0, listStyle: 'none' }}>
                  {p.sources.map((s, j) => (
                    <li key={j} style={{ font: `400 11px/1.45 ${HERB.serif}`, color: HERB.inkSoft, paddingLeft: 12, position: 'relative' }}>
                      <span style={{ position: 'absolute', left: 0, color: HERB.green }}>·</span>
                      <span style={{ color: HERB.ink }}>{s.sys}</span> — {s.detail}
                    </li>
                  ))}
                </ul>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ font: `400 36px/1 ${HERB.serif}`, color: HERB.green }}>{p.matches}</div>
                <div style={{ font: `400 9px/1 ${HERB.sans}`, letterSpacing: '0.12em', textTransform: 'uppercase', color: HERB.inkSoft, marginTop: 2 }}>пересеч.</div>
              </div>
            </div>
          ))}
        </div>

        {/* side column */}
        <div style={{ borderLeft: `1px solid ${HERB.rule}`, paddingLeft: 20 }}>
          <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.18em', textTransform: 'uppercase', color: HERB.inkSoft, marginBottom: 10 }}>Задействованы</div>
          <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
            {window.MOCK_ORACLES_USED.map((o, i) => (
              <li key={i} style={{ font: `400 11px/1.5 ${HERB.serif}`, color: HERB.ink, padding: '6px 0', borderBottom: `1px dotted ${HERB.rule}` }}>{o}</li>
            ))}
          </ul>
          <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.18em', textTransform: 'uppercase', color: HERB.inkSoft, margin: '24px 0 10px' }}>Исключены</div>
          {window.MOCK_EXCLUDED.map((e, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <div style={{ font: `400 italic 12px/1.2 ${HERB.serif}`, color: HERB.ink, textDecoration: 'line-through', textDecorationColor: HERB.ochre }}>{e.name}</div>
              <div style={{ font: `400 10px/1.4 ${HERB.serif}`, color: HERB.inkSoft, marginTop: 2 }}>{e.reason}</div>
            </div>
          ))}

          <div style={{ marginTop: 28, padding: 14, background: HERB.bgDeep, borderLeft: `2px solid ${HERB.ochre}` }}>
            <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.18em', textTransform: 'uppercase', color: HERB.ochre, marginBottom: 6 }}>Заметка</div>
            <div style={{ font: `400 italic 12px/1.4 ${HERB.serif}`, color: HERB.ink }}>стихия «вода» — 3 совпадения. предложить водную композицию у въезда.</div>
          </div>
        </div>
      </div>

      <div style={{ position: 'absolute', bottom: 14, left: 40, right: 40, display: 'flex', justifyContent: 'space-between', font: `400 italic 10px/1 ${HERB.serif}`, color: HERB.inkSoft, borderTop: `1px solid ${HERB.rule}`, paddingTop: 8 }}>
        <span>fol. II · expertus</span>
        <span>не для клиента</span>
      </div>
    </div>
  );
}

function HerbClient() {
  const c = window.MOCK_CLIENT;
  const main = window.MOCK_POOL[0];
  const others = window.MOCK_POOL.slice(1);
  const PI = window.PlantIcon;

  return (
    <div style={{ width: 480, height: 900, background: HERB.bg, padding: '44px 44px 28px', fontFamily: HERB.serif, color: HERB.ink, overflow: 'hidden', position: 'relative' }}>
      <div style={{ textAlign: 'center', borderBottom: `1px solid ${HERB.ink}`, paddingBottom: 12 }}>
        <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.4em', textTransform: 'uppercase', color: HERB.green }}>Hortus · Anima</div>
        <div style={{ font: `400 italic 11px/1 ${HERB.serif}`, color: HERB.inkSoft, marginTop: 6 }}>персональный список растений</div>
      </div>

      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <div style={{ font: `400 italic 13px/1 ${HERB.serif}`, color: HERB.ochre }}>для</div>
        <div style={{ font: `400 28px/1.1 ${HERB.serif}`, marginTop: 4, letterSpacing: '-0.01em' }}>{c.shortName}</div>
      </div>

      {/* main plant */}
      <div style={{ marginTop: 24, padding: '24px 0', borderTop: `1px solid ${HERB.ink}`, borderBottom: `1px solid ${HERB.rule}`, textAlign: 'center' }}>
        <div style={{ font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: HERB.ochre, marginBottom: 14 }}>главное дерево</div>
        <div style={{ color: HERB.green, display: 'flex', justifyContent: 'center' }}>
          <PI kind={main.icon} size={130} stroke={1.0} />
        </div>
        <div style={{ font: `400 32px/1.05 ${HERB.serif}`, marginTop: 12, letterSpacing: '-0.01em' }}>{main.name}</div>
        <div style={{ font: `400 italic 12px/1 ${HERB.serif}`, color: HERB.inkSoft, marginTop: 4 }}>{main.nameLat}</div>
        <div style={{ font: `400 italic 14px/1.5 ${HERB.serif}`, color: HERB.ink, marginTop: 16, maxWidth: 340, marginLeft: 'auto', marginRight: 'auto' }}>«{main.storyShort}»</div>
        <div style={{ font: `400 12px/1.6 ${HERB.serif}`, color: HERB.inkSoft, marginTop: 10, maxWidth: 340, marginLeft: 'auto', marginRight: 'auto' }}>{main.storyLong}</div>
      </div>

      {/* others */}
      <div style={{ marginTop: 18 }}>
        <div style={{ textAlign: 'center', font: `500 9px/1 ${HERB.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: HERB.ochre, marginBottom: 14 }}>сопровождение</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', columnGap: 20, rowGap: 14 }}>
          {others.map((p) => (
            <div key={p.id} style={{ display: 'grid', gridTemplateColumns: '40px 1fr', gap: 10, alignItems: 'start' }}>
              <div style={{ color: HERB.green, paddingTop: 2 }}>
                <PI kind={p.icon} size={36} stroke={1.0} />
              </div>
              <div>
                <div style={{ font: `400 14px/1.15 ${HERB.serif}` }}>{p.name}</div>
                <div style={{ font: `400 italic 10px/1.3 ${HERB.serif}`, color: HERB.inkSoft, marginTop: 2 }}>{p.storyShort}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ position: 'absolute', bottom: 22, left: 44, right: 44, textAlign: 'center', borderTop: `1px solid ${HERB.rule}`, paddingTop: 12 }}>
        <div style={{ font: `400 italic 11px/1.4 ${HERB.serif}`, color: HERB.inkSoft, marginBottom: 8 }}>заложите место силы — посадка экспертом</div>
        <div style={{ font: `500 10px/1 ${HERB.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: HERB.green }}>записаться на консультацию →</div>
      </div>
    </div>
  );
}

window.HerbForm = HerbForm;
window.HerbExpert = HerbExpert;
window.HerbClient = HerbClient;
