// pergament.jsx — направление 3: «Сад на пергаменте»
// Современный премиум-минимализм: много белого/айвори, крупная display-serif,
// деликатные акварельные пятна, золотистые и графитовые линии.

const PRG = {
  bg: '#fbfaf6',
  bgDeep: '#f3eee3',
  wash1: 'rgba(168,140,90,0.10)',  // светлая охра
  wash2: 'rgba(80,110,80,0.09)',   // светлая зелень
  ink: '#1a1a1a',
  inkSoft: '#7c7468',
  gold: '#a88a4a',
  graphite: '#3a3833',
  display: '"Cormorant", "Cormorant Garamond", "Playfair Display", serif',
  sans: '"Inter Tight", "Inter", "Helvetica Neue", sans-serif',
};

const Watercolor = ({ x, y, r, color, opacity = 1 }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: r * 2, height: r * 2, borderRadius: '50%', background: color, filter: 'blur(40px)', opacity, pointerEvents: 'none' }} />
);

function PrgForm() {
  const c = window.MOCK_CLIENT;
  const Field = ({ label, value, half }) => (
    <div style={{ marginBottom: 18 }}>
      <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.24em', textTransform: 'uppercase', color: PRG.inkSoft, marginBottom: 8 }}>{label}</div>
      <div style={{ font: `400 ${half ? 18 : 22}px/1.2 ${PRG.display}`, color: PRG.ink, paddingBottom: 8, borderBottom: `1px solid ${PRG.graphite}` }}>{value}</div>
    </div>
  );
  return (
    <div style={{ width: 480, height: 720, background: PRG.bg, padding: '48px 48px', fontFamily: PRG.sans, color: PRG.ink, position: 'relative', overflow: 'hidden' }}>
      <Watercolor x={-60} y={-40} r={120} color={PRG.wash1} />
      <Watercolor x={300} y={500} r={140} color={PRG.wash2} />

      <div style={{ position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 28, height: 28, border: `1px solid ${PRG.gold}`, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', font: `400 14px/1 ${PRG.display}`, color: PRG.gold }}>F</div>
            <div style={{ font: `500 10px/1 ${PRG.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase' }}>Fusion · Hortus</div>
          </div>
          <div style={{ font: `400 9px/1 ${PRG.sans}`, color: PRG.inkSoft, letterSpacing: '0.18em' }}>NEW · 037</div>
        </div>

        <div style={{ marginTop: 48 }}>
          <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', color: PRG.gold, marginBottom: 12 }}>Новая консультация</div>
          <div style={{ font: `300 44px/1 ${PRG.display}`, letterSpacing: '-0.02em' }}>Анкета<br/><em style={{ fontWeight: 300 }}>заказчицы</em></div>
        </div>

        <div style={{ marginTop: 36 }}>
          <Field label="Имя" value={c.fullName} />
          <Field label="Дата рождения" value={c.birthDate} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22 }}>
            <Field label="Время" value={c.birthTime} half />
            <Field label="Место" value={c.birthPlace} half />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22 }}>
            <Field label="Пол" value={c.gender} half />
            <Field label="Глаза" value={c.eyeColor} half />
          </div>

          <div style={{ marginTop: 6, padding: 18, background: 'rgba(255,255,255,0.6)', backdropFilter: 'blur(2px)', border: `1px solid rgba(0,0,0,0.06)`, borderRadius: 2 }}>
            <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.24em', textTransform: 'uppercase', color: PRG.inkSoft, marginBottom: 8 }}>Сад</div>
            <div style={{ font: `400 16px/1.4 ${PRG.display}` }}>{c.garden}</div>
            <div style={{ font: `400 11px/1 ${PRG.sans}`, color: PRG.gold, letterSpacing: '0.12em', marginTop: 6 }}>{c.zone}</div>
          </div>
        </div>

        <button style={{ marginTop: 28, width: '100%', padding: '18px 0', background: PRG.ink, color: PRG.bg, border: 'none', font: `500 10px/1 ${PRG.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', cursor: 'pointer', borderRadius: 1 }}>
          Составить подбор
        </button>

        <div style={{ marginTop: 14, font: `400 11px/1.5 ${PRG.display}`, fontStyle: 'italic', color: PRG.inkSoft, textAlign: 'center' }}>
          сводятся пять источников — они не показываются гостье
        </div>
      </div>
    </div>
  );
}

function PrgExpert() {
  const c = window.MOCK_CLIENT;
  const pool = window.MOCK_POOL;
  const PI = window.PlantIcon;

  return (
    <div style={{ width: 720, height: 900, background: PRG.bg, padding: '40px 44px', fontFamily: PRG.sans, color: PRG.ink, position: 'relative', overflow: 'hidden' }}>
      <Watercolor x={-100} y={-80} r={180} color={PRG.wash1} opacity={0.7} />
      <Watercolor x={500} y={650} r={200} color={PRG.wash2} opacity={0.6} />

      <div style={{ position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ font: `500 10px/1 ${PRG.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', color: PRG.gold, marginBottom: 8 }}>Подбор · экспертный</div>
            <div style={{ font: `300 38px/1 ${PRG.display}`, letterSpacing: '-0.02em' }}>{c.shortName}</div>
            <div style={{ font: `400 11px/1.5 ${PRG.sans}`, color: PRG.inkSoft, marginTop: 6 }}>{c.birthDate} · {c.birthPlace} · глаза {c.eyeColor} · {c.zone}</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ font: `300 56px/1 ${PRG.display}`, color: PRG.gold }}>5</div>
            <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.24em', textTransform: 'uppercase', color: PRG.inkSoft, marginTop: 4 }}>растений в пуле</div>
          </div>
        </div>

        <div style={{ height: 1, background: PRG.graphite, margin: '24px 0 28px' }} />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', gap: 32 }}>
          {/* main column */}
          <div>
            {pool.map((p, i) => (
              <div key={p.id} style={{ display: 'grid', gridTemplateColumns: '64px 1fr auto', gap: 16, padding: '16px 0', borderBottom: i < pool.length - 1 ? `1px solid rgba(0,0,0,0.08)` : 'none' }}>
                <div style={{ width: 64, height: 64, background: 'rgba(255,255,255,0.7)', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', color: PRG.graphite }}>
                  <PI kind={p.icon} size={48} stroke={1.0} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                    <div style={{ font: `400 22px/1 ${PRG.display}` }}>{p.name}</div>
                    <div style={{ font: `400 italic 11px/1 ${PRG.display}`, color: PRG.inkSoft }}>{p.nameLat}</div>
                  </div>
                  <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.24em', textTransform: 'uppercase', color: PRG.gold, marginTop: 6 }}>{p.role}</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                    {p.sources.map((s, j) => (
                      <div key={j} style={{ font: `400 10px/1.3 ${PRG.sans}`, padding: '4px 10px', background: 'rgba(168,138,74,0.08)', border: `1px solid rgba(168,138,74,0.3)`, color: PRG.graphite, borderRadius: 100 }}>
                        {s.sys}
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ font: `300 40px/1 ${PRG.display}`, color: PRG.gold }}>×{p.matches}</div>
                  <div style={{ font: `500 8px/1 ${PRG.sans}`, letterSpacing: '0.24em', textTransform: 'uppercase', color: PRG.inkSoft, marginTop: 4 }}>пересеч.</div>
                </div>
              </div>
            ))}
          </div>

          {/* side */}
          <div>
            <div style={{ background: 'rgba(255,255,255,0.65)', padding: 18, borderRadius: 2, border: `1px solid rgba(0,0,0,0.06)` }}>
              <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.24em', textTransform: 'uppercase', color: PRG.gold, marginBottom: 10 }}>Источники</div>
              <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                {window.MOCK_ORACLES_USED.map((o, i) => (
                  <li key={i} style={{ font: `400 12px/1.4 ${PRG.display}`, padding: '6px 0', borderBottom: i < 4 ? `1px solid rgba(0,0,0,0.05)` : 'none', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 4, height: 4, background: PRG.gold, borderRadius: '50%' }} />
                    {o}
                  </li>
                ))}
              </ul>
            </div>

            <div style={{ marginTop: 16, padding: 18, borderRadius: 2 }}>
              <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.24em', textTransform: 'uppercase', color: PRG.inkSoft, marginBottom: 10 }}>Исключены</div>
              {window.MOCK_EXCLUDED.map((e, i) => (
                <div key={i} style={{ marginBottom: 10 }}>
                  <div style={{ font: `400 14px/1 ${PRG.display}`, color: PRG.graphite, textDecoration: 'line-through', textDecorationColor: PRG.gold }}>{e.name}</div>
                  <div style={{ font: `400 11px/1.4 ${PRG.sans}`, color: PRG.inkSoft, marginTop: 2 }}>{e.reason}</div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 12, padding: 18, background: PRG.ink, color: PRG.bg, borderRadius: 2 }}>
              <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.24em', textTransform: 'uppercase', color: PRG.gold, marginBottom: 8 }}>Подсказка</div>
              <div style={{ font: `400 italic 13px/1.5 ${PRG.display}` }}>«вода» — три из пяти. Группа у въезда: ива + ирисы + кувшинки в чаше.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PrgClient() {
  const c = window.MOCK_CLIENT;
  const main = window.MOCK_POOL[0];
  const others = window.MOCK_POOL.slice(1);
  const PI = window.PlantIcon;

  return (
    <div style={{ width: 480, height: 900, background: PRG.bg, padding: '48px 48px 32px', fontFamily: PRG.sans, color: PRG.ink, position: 'relative', overflow: 'hidden' }}>
      <Watercolor x={-80} y={200} r={160} color={PRG.wash2} opacity={0.7} />
      <Watercolor x={320} y={550} r={150} color={PRG.wash1} opacity={0.7} />

      <div style={{ position: 'relative' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'inline-block', width: 32, height: 32, border: `1px solid ${PRG.gold}`, borderRadius: '50%', font: `400 16px/30px ${PRG.display}`, color: PRG.gold }}>F</div>
          <div style={{ font: `500 10px/1 ${PRG.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', marginTop: 12 }}>Fusion · Hortus</div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 36 }}>
          <div style={{ font: `400 italic 13px/1 ${PRG.display}`, color: PRG.gold }}>персональный сад</div>
          <div style={{ font: `300 44px/1.05 ${PRG.display}`, marginTop: 10, letterSpacing: '-0.02em' }}>{c.shortName}</div>
        </div>

        {/* main */}
        <div style={{ marginTop: 36, textAlign: 'center' }}>
          <div style={{ font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', color: PRG.gold, marginBottom: 18 }}>Главное дерево</div>
          <div style={{ color: PRG.graphite, display: 'flex', justifyContent: 'center' }}>
            <PI kind={main.icon} size={140} stroke={1.0} />
          </div>
          <div style={{ font: `300 38px/1 ${PRG.display}`, marginTop: 16, letterSpacing: '-0.01em' }}>{main.name}</div>
          <div style={{ font: `400 italic 11px/1 ${PRG.display}`, color: PRG.inkSoft, marginTop: 4 }}>{main.nameLat}</div>
          <div style={{ width: 32, height: 1, background: PRG.gold, margin: '18px auto' }} />
          <div style={{ font: `400 italic 16px/1.5 ${PRG.display}`, maxWidth: 320, margin: '0 auto' }}>«{main.storyShort}»</div>
          <div style={{ font: `400 12px/1.7 ${PRG.sans}`, color: PRG.inkSoft, marginTop: 14, maxWidth: 320, margin: '14px auto 0' }}>{main.storyLong}</div>
        </div>

        <div style={{ marginTop: 28 }}>
          <div style={{ textAlign: 'center', font: `500 9px/1 ${PRG.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', color: PRG.gold, marginBottom: 18 }}>Сопровождение</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            {others.map((p) => (
              <div key={p.id} style={{ background: 'rgba(255,255,255,0.6)', padding: 14, borderRadius: 2, border: `1px solid rgba(0,0,0,0.05)` }}>
                <div style={{ color: PRG.graphite }}><PI kind={p.icon} size={36} stroke={1.0} /></div>
                <div style={{ font: `400 16px/1.1 ${PRG.display}`, marginTop: 6 }}>{p.name}</div>
                <div style={{ font: `400 italic 11px/1.3 ${PRG.display}`, color: PRG.inkSoft, marginTop: 4 }}>{p.storyShort}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ position: 'absolute', bottom: 4, left: 0, right: 0, textAlign: 'center' }}>
          <div style={{ font: `400 italic 12px/1.4 ${PRG.display}`, color: PRG.inkSoft, marginBottom: 10 }}>воплотить вашими руками или нашими</div>
          <button style={{ padding: '14px 28px', background: PRG.ink, color: PRG.bg, border: 'none', font: `500 10px/1 ${PRG.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', cursor: 'pointer' }}>
            Записаться
          </button>
        </div>
      </div>
    </div>
  );
}

window.PrgForm = PrgForm;
window.PrgExpert = PrgExpert;
window.PrgClient = PrgClient;
