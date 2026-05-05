// prototype-screens.jsx — пять экранов прототипа

// ── обложка ──
function ScreenCover({ onStart }) {
  return (
    <div style={{ width: '100%', maxWidth: 720, aspectRatio: '3/4', margin: '0 auto', background: VS.coverInk, padding: 12, position: 'relative', boxShadow: '0 30px 80px rgba(0,0,0,.5)' }}>
      <PaperGrain opacity={0.3} />
      <VictorianFrame color={VS.coverGold} padding="44px 36px" cornerSize={64}>
        <div style={{ textAlign: 'center', color: VS.coverGold, position: 'relative' }}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginBottom: 18 }}>
            <VSymbol kind="sun" size={20} color={VS.coverGold} />
            <VSymbol kind="star" size={20} color={VS.coverGold} />
            <VSymbol kind="moon" size={20} color={VS.coverGold} />
          </div>

          <div style={{ font: `400 14px/1 ${VS.serif}`, fontStyle: 'italic', color: VS.coverGoldSoft, letterSpacing: '0.18em', marginBottom: 10 }}>MMXXVI</div>

          <div style={{ font: `400 56px/1 ${VS.display}`, color: VS.coverGold, letterSpacing: '0.02em', marginBottom: 14 }}>Hortus Animæ</div>

          <Vignette color={VS.coverGold} width={260} />

          <div style={{ font: `400 italic 16px/1.5 ${VS.serif}`, color: VS.coverGoldSoft, marginTop: 18, maxWidth: 380, marginLeft: 'auto', marginRight: 'auto' }}>
            альманах растений, что приходят к человеку — по дню, имени, взгляду и звезде
          </div>

          <div style={{ margin: '40px auto', width: 200, height: 1, background: VS.coverGold, opacity: 0.4 }} />

          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <Cameo size={180} color={VS.coverGold}>
              <div style={{ color: VS.coverGold, opacity: 0.85 }}>
                <Botanical kind="peony" size={140} color={VS.coverGold} />
              </div>
            </Cameo>
          </div>

          <div style={{ marginTop: 36 }}>
            <button onClick={onStart} style={{ background: 'transparent', color: VS.coverGold, border: `1px solid ${VS.coverGold}`, padding: '14px 36px', font: `400 12px/1 ${VS.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', cursor: 'pointer' }}>
              ✦  открыть альманах  ✦
            </button>
          </div>

          <div style={{ marginTop: 28, font: `400 italic 11px/1.4 ${VS.serif}`, color: VS.coverGoldSoft, opacity: 0.7 }}>
            internal use · vladislav rev. I
          </div>
        </div>
      </VictorianFrame>
    </div>
  );
}

// ── анкета ──
function ScreenForm({ data, setData, onNext, onBack }) {
  const upd = (k) => (e) => setData({ ...data, [k]: e.target.value });

  const Field = ({ label, k, sym, type = 'text', placeholder }) => (
    <div style={{ marginBottom: 18 }}>
      <div style={{ font: `500 9px/1 ${VS.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: VS.terra, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
        {sym && <VSymbol kind={sym} size={11} color={VS.terra} />}
        {label}
      </div>
      <input
        type={type}
        value={data[k] || ''}
        onChange={upd(k)}
        placeholder={placeholder}
        style={{ width: '100%', font: `400 16px/1.2 ${type === 'date' || type === 'time' ? VS.serif : VS.serif}`, fontStyle: type === 'date' || type === 'time' ? 'normal' : 'italic', color: VS.ink, border: 'none', borderBottom: `1px solid ${VS.ink}`, paddingBottom: 6, background: 'transparent', outline: 'none', colorScheme: 'light' }}
      />
    </div>
  );

  return (
    <div style={{ width: '100%', maxWidth: 640, aspectRatio: '3/4.2', margin: '0 auto', background: VS.paper, padding: 18, position: 'relative', boxShadow: '0 20px 60px rgba(40,30,10,.3)' }}>
      <PaperGrain opacity={0.5} />
      <VictorianFrame color={VS.inkSoft} padding="28px 32px" cornerSize={48}>
        <div style={{ position: 'relative' }}>
          <div style={{ textAlign: 'center', marginBottom: 18 }}>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginBottom: 6 }}>
              <VSymbol kind="sun" size={12} color={VS.terra} />
              <VSymbol kind="moon" size={12} color={VS.terra} />
              <VSymbol kind="star" size={12} color={VS.terra} />
            </div>
            <div style={{ font: `400 italic 12px/1 ${VS.serif}`, color: VS.terra }}>folium I · de hospita</div>
            <div style={{ font: `400 32px/1 ${VS.display}`, color: VS.ink, marginTop: 6 }}>О новой госпоже</div>
            <div style={{ font: `400 italic 11px/1.4 ${VS.serif}`, color: VS.inkFaded, marginTop: 6, maxWidth: 360, margin: '6px auto 0' }}>заполняется экспертом, прежде чем сводить источники</div>
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: 12 }}><Vignette color={VS.rule} width={220} /></div>
          </div>

          <Field label="Имя" k="fullName" sym="star" placeholder="полное имя" />
          <Field label="Дата рождения" k="birthDate" sym="sun" type="date" />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22 }}>
            <Field label="Час" k="birthTime" sym="moon" type="time" />
            <Field label="Место" k="birthPlace" sym="earth" placeholder="город" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22 }}>
            <div style={{ marginBottom: 18 }}>
              <div style={{ font: `500 9px/1 ${VS.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: VS.terra, marginBottom: 6 }}>Пол</div>
              <select value={data.gender || ''} onChange={upd('gender')} style={{ width: '100%', font: `400 16px/1.2 ${VS.serif}`, fontStyle: 'italic', color: VS.ink, border: 'none', borderBottom: `1px solid ${VS.ink}`, paddingBottom: 6, background: 'transparent', outline: 'none', appearance: 'none' }}>
                <option value="женский">женский</option>
                <option value="мужской">мужской</option>
              </select>
            </div>
            <div style={{ marginBottom: 18 }}>
              <div style={{ font: `500 9px/1 ${VS.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: VS.terra, marginBottom: 6 }}>Взгляд</div>
              <select value={data.eyeColor || ''} onChange={upd('eyeColor')} style={{ width: '100%', font: `400 16px/1.2 ${VS.serif}`, fontStyle: 'italic', color: VS.ink, border: 'none', borderBottom: `1px solid ${VS.ink}`, paddingBottom: 6, background: 'transparent', outline: 'none', appearance: 'none' }}>
                <option>голубые</option>
                <option>серые</option>
                <option>зелёные</option>
                <option>карие</option>
                <option>тёмные</option>
              </select>
            </div>
          </div>

          <div style={{ marginTop: 6, padding: '14px 16px', background: VS.paperDeep, border: `1px dashed ${VS.rule}` }}>
            <div style={{ font: `500 9px/1 ${VS.sans}`, letterSpacing: '0.32em', textTransform: 'uppercase', color: VS.terra, marginBottom: 8 }}>Сад</div>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14 }}>
              <input value={data.gardenLocation || ''} onChange={upd('gardenLocation')} placeholder="район, размер участка" style={{ font: `400 14px/1.2 ${VS.serif}`, fontStyle: 'italic', color: VS.ink, border: 'none', borderBottom: `1px solid ${VS.inkFaded}`, paddingBottom: 4, background: 'transparent', outline: 'none' }} />
              <select value={data.zone || 6} onChange={(e) => setData({ ...data, zone: +e.target.value })} style={{ font: `400 14px/1.2 ${VS.serif}`, fontStyle: 'italic', color: VS.ink, border: 'none', borderBottom: `1px solid ${VS.inkFaded}`, paddingBottom: 4, background: 'transparent', outline: 'none' }}>
                <option value={3}>зона 3 · север</option>
                <option value={4}>зона 4 · Урал</option>
                <option value={5}>зона 5 · сев. ср.полоса</option>
                <option value={6}>зона 6 · Москва</option>
                <option value={7}>зона 7 · Чернозёмье</option>
                <option value={8}>зона 8 · Кубань</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 22, paddingTop: 16, borderTop: `1px solid ${VS.rule}` }}>
            <button onClick={onBack} style={{ background: 'transparent', border: 'none', font: `400 italic 12px/1 ${VS.serif}`, color: VS.inkFaded, cursor: 'pointer' }}>← обложка</button>
            <button onClick={onNext} style={{ background: VS.ink, color: VS.paper, border: `2px double ${VS.ink}`, padding: '12px 28px', font: `400 12px/1 ${VS.display}`, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
              ✦ свести источники ✦
            </button>
          </div>
        </div>
      </VictorianFrame>
    </div>
  );
}

// ── загрузка / "сведение источников" ──
function ScreenWeaving({ onDone }) {
  const [step, setStep] = React.useState(0);
  const oracles = ['свод друидов · деревья', 'свод друидов · цветы', 'небо · знак зодиака', 'свод славь · травы и древа', 'взгляд · цвет очей'];
  React.useEffect(() => {
    if (step >= oracles.length) { const t = setTimeout(onDone, 600); return () => clearTimeout(t); }
    const t = setTimeout(() => setStep(step + 1), 550);
    return () => clearTimeout(t);
  }, [step]);
  return (
    <div style={{ width: '100%', maxWidth: 560, aspectRatio: '3/4', margin: '0 auto', background: VS.coverInk, padding: 12, position: 'relative' }}>
      <PaperGrain opacity={0.3} />
      <VictorianFrame color={VS.coverGold} padding="48px 40px" cornerSize={56}>
        <div style={{ textAlign: 'center', color: VS.coverGold }}>
          <div style={{ font: `400 italic 12px/1 ${VS.serif}`, color: VS.coverGoldSoft, marginBottom: 8 }}>conjunctio fontium</div>
          <div style={{ font: `400 36px/1 ${VS.display}`, marginBottom: 24 }}>Сводим источники</div>
          <Vignette color={VS.coverGold} width={220} />
          <ul style={{ marginTop: 30, padding: 0, listStyle: 'none', textAlign: 'left' }}>
            {oracles.map((o, i) => (
              <li key={i} style={{ font: `400 14px/1.4 ${VS.serif}`, color: i < step ? VS.coverGold : VS.coverGoldSoft, opacity: i < step ? 1 : 0.4, padding: '10px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, borderBottom: `1px dotted ${VS.coverGoldSoft}` }}>
                <span style={{ flex: 1, minWidth: 0 }}>{o}</span>
                <span style={{ font: `400 14px/1 ${VS.display}`, flexShrink: 0 }}>{i < step ? '✓' : '·'}</span>
              </li>
            ))}
          </ul>
          <div style={{ marginTop: 24, font: `400 italic 12px/1 ${VS.serif}`, color: VS.coverGoldSoft }}>
            ищем пересечения…
          </div>
        </div>
      </VictorianFrame>
    </div>
  );
}

// ── экспертный лист ──
function ScreenExpert({ data, result, onClient, onBack }) {
  const firstName = (data.fullName || '').split(/\s+/)[0] || '—';
  return (
    <div style={{ width: '100%', maxWidth: 1000, margin: '0 auto', background: VS.paper, padding: 18, position: 'relative', boxShadow: '0 20px 60px rgba(40,30,10,.3)' }}>
      <PaperGrain opacity={0.5} />
      <VictorianFrame color={VS.inkSoft} padding="28px 32px" cornerSize={52}>
        <div style={{ position: 'relative' }}>
          {/* masthead */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: `2px solid ${VS.ink}`, paddingBottom: 10, marginBottom: 4 }}>
            <div>
              <div style={{ display: 'flex', gap: 10, marginBottom: 4, color: VS.terra }}>
                <VSymbol kind="sun" size={12}/><VSymbol kind="moon" size={12}/><VSymbol kind="star" size={12}/>
              </div>
              <div style={{ font: `400 28px/1 ${VS.display}`, color: VS.ink }}>Hortus Animæ</div>
              <div style={{ font: `400 italic 11px/1 ${VS.serif}`, color: VS.inkFaded, marginTop: 2 }}>folium II · expertus tantum · не для гостьи</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ font: `400 italic 12px/1 ${VS.serif}`, color: VS.terra }}>составлено для</div>
              <div style={{ font: `400 22px/1 ${VS.display}`, color: VS.ink, marginTop: 4 }}>{firstName}</div>
              <div style={{ font: `400 11px/1.4 ${VS.serif}`, color: VS.inkFaded, marginTop: 4 }}>{data.birthDate} · {data.birthPlace} · взгляд {data.eyeColor} · зона {data.zone}</div>
            </div>
          </div>
          <div style={{ borderBottom: `1px solid ${VS.inkSoft}`, marginBottom: 16 }} />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 28 }}>
            {/* main */}
            <div>
              <div style={{ font: `400 italic 12px/1 ${VS.serif}`, color: VS.terra }}>tabula plantarum</div>
              <div style={{ font: `400 26px/1.05 ${VS.display}`, color: VS.ink, marginBottom: 14 }}>Свод растений</div>

              {result.pool.length === 0 ? (
                <div style={{ font: `400 italic 13px/1.5 ${VS.serif}`, color: VS.inkFaded }}>введите дату — и появится подбор</div>
              ) : result.pool.map((p, i) => (
                <div key={p.id} style={{ display: 'grid', gridTemplateColumns: '70px 1fr 80px', gap: 16, padding: '14px 0', borderBottom: i < result.pool.length - 1 ? `1px solid ${VS.rule}` : 'none', alignItems: 'flex-start' }}>
                  <div style={{ width: 70, height: 70, background: VS.paperDeep, border: `1px solid ${VS.rule}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: VS.ink }}>
                    <Botanical kind={p.plant.icon} size={56} color={VS.ink} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                      <span style={{ font: `400 12px/1 ${VS.sans}`, color: VS.terra }}>{String(i+1).padStart(2,'0')}</span>
                      <span style={{ font: `400 20px/1 ${VS.display}`, color: VS.ink }}>{p.plant.name}</span>
                      <span style={{ font: `400 italic 11px/1 ${VS.serif}`, color: VS.inkFaded }}>{p.plant.nameLat}</span>
                    </div>
                    <div style={{ font: `500 9px/1 ${VS.sans}`, letterSpacing: '0.18em', textTransform: 'uppercase', color: VS.terra, marginTop: 10, marginBottom: 2, display: 'inline-block', padding: '3px 8px', background: VS.paperDeep, border: `1px solid ${VS.rule}` }}>{p.role}</div>
                    <ul style={{ margin: '10px 0 0', padding: 0, listStyle: 'none' }}>
                      {p.sources.map((s, j) => (
                        <li key={j} style={{ font: `400 12px/1.5 ${VS.serif}`, color: VS.inkSoft, paddingLeft: 14, position: 'relative' }}>
                          <span style={{ position: 'absolute', left: 0, color: VS.terra }}>—</span>
                          <em style={{ color: VS.ink }}>{s.sys}.</em> <span style={{ color: VS.inkFaded }}>{s.detail}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                      {Array.from({length: p.matches}).map((_,j)=><span key={j} style={{ color: VS.terra, font: `400 14px/1 ${VS.display}` }}>✦</span>)}
                    </div>
                    <div style={{ font: `400 36px/1 ${VS.display}`, color: VS.ink, marginTop: 4 }}>{p.matches}</div>
                    <div style={{ font: `500 8px/1 ${VS.sans}`, letterSpacing: '0.18em', textTransform: 'uppercase', color: VS.inkFaded, marginTop: 2 }}>пересеч.</div>
                  </div>
                </div>
              ))}
            </div>

            {/* side */}
            <div>
              <div style={{ border: `1px solid ${VS.ink}`, padding: 16, marginBottom: 14 }}>
                <div style={{ font: `400 italic 11px/1 ${VS.serif}`, color: VS.terra, marginBottom: 4 }}>fontes</div>
                <div style={{ font: `400 18px/1 ${VS.display}`, color: VS.ink, marginBottom: 10 }}>Источники</div>
                <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                  {result.oraclesUsed.map((o, i) => (
                    <li key={i} style={{ font: `400 12px/1.5 ${VS.serif}`, padding: '4px 0', display: 'flex', justifyContent: 'space-between', borderBottom: i < result.oraclesUsed.length - 1 ? `1px dotted ${VS.rule}` : 'none' }}>
                      <span>{o}</span><span style={{ color: VS.terra, font: `400 11px/1 ${VS.sans}` }}>✓</span>
                    </li>
                  ))}
                </ul>
              </div>

              {result.excluded.length > 0 && (
                <div style={{ background: VS.paperDeep, border: `1px solid ${VS.rule}`, padding: 14, marginBottom: 14 }}>
                  <div style={{ font: `400 italic 11px/1 ${VS.serif}`, color: VS.terra, marginBottom: 4 }}>exclusi</div>
                  <div style={{ font: `400 16px/1 ${VS.display}`, color: VS.ink, marginBottom: 8 }}>Исключены</div>
                  {result.excluded.map((e, i) => (
                    <div key={i} style={{ marginBottom: 6 }}>
                      <div style={{ font: `400 italic 13px/1.2 ${VS.serif}`, color: VS.ink, textDecoration: 'line-through', textDecorationColor: VS.terra }}>{e.name}</div>
                      <div style={{ font: `400 11px/1.3 ${VS.serif}`, color: VS.inkFaded, marginTop: 2 }}>{e.reason}</div>
                    </div>
                  ))}
                </div>
              )}

              {result.dominantElement && (
                <div style={{ border: `2px double ${VS.ink}`, padding: 14, textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: 8, color: VS.terra, marginBottom: 6 }}>
                    {Array.from({length: result.dominantElement.count}).map((_,i)=>(<VSymbol key={i} kind={result.dominantElement.element} size={18} color={VS.terra}/>))}
                  </div>
                  <div style={{ font: `400 italic 12px/1.4 ${VS.serif}`, color: VS.ink }}>
                    стихия — <em>{ {water:'вода', fire:'огонь', earth:'земля', air:'воздух'}[result.dominantElement.element] }</em>. {result.dominantElement.count} из {result.pool.length}. Композицию строить вокруг неё.
                  </div>
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 22, paddingTop: 14, borderTop: `1px solid ${VS.ink}` }}>
            <button onClick={onBack} style={{ background: 'transparent', border: 'none', font: `400 italic 12px/1 ${VS.serif}`, color: VS.inkFaded, cursor: 'pointer' }}>← править анкету</button>
            <span style={{ font: `400 italic 11px/1 ${VS.serif}`, color: VS.inkFaded }}>folium II · expertus</span>
            <button onClick={onClient} style={{ background: VS.ink, color: VS.paper, border: `2px double ${VS.ink}`, padding: '12px 28px', font: `400 12px/1 ${VS.display}`, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
              лист гостьи →
            </button>
          </div>
        </div>
      </VictorianFrame>
    </div>
  );
}

// ── клиентский разворот ──
function ScreenClient({ data, result, onBack }) {
  const firstName = (data.fullName || '').split(/\s+/)[0] || 'госпожа';
  const main = result.pool[0];
  const others = result.pool.slice(1);
  if (!main) return <div style={{ padding: 40, color: VS.ink, textAlign: 'center' }}>введите дату на анкете, чтобы увидеть подбор</div>;

  return (
    <div style={{ width: '100%', maxWidth: 720, margin: '0 auto', background: VS.paper, padding: 18, position: 'relative', boxShadow: '0 30px 80px rgba(40,30,10,.4)' }}>
      <PaperGrain opacity={0.5} />
      <VictorianFrame color={VS.ink} padding="40px 44px" cornerSize={64}>
        <div style={{ position: 'relative', textAlign: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 14, marginBottom: 8, color: VS.terra }}>
            <VSymbol kind="sun" size={14}/><VSymbol kind="star" size={14}/><VSymbol kind="moon" size={14}/>
          </div>
          <div style={{ font: `400 24px/1 ${VS.display}`, color: VS.ink, letterSpacing: '0.04em' }}>Hortus Animæ</div>
          <div style={{ font: `400 italic 11px/1.4 ${VS.serif}`, color: VS.inkFaded, marginTop: 4 }}>персональный лист растений</div>
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 10 }}><Vignette color={VS.rule} width={220} /></div>

          <div style={{ marginTop: 24 }}>
            <div style={{ font: `400 italic 13px/1 ${VS.serif}`, color: VS.terra }}>составлено для</div>
            <div style={{ font: `400 38px/1.05 ${VS.display}`, color: VS.ink, marginTop: 6 }}>{firstName}</div>
          </div>

          {/* main */}
          <div style={{ marginTop: 30, padding: '20px 0', borderTop: `1px solid ${VS.ink}`, borderBottom: `1px solid ${VS.rule}` }}>
            <div style={{ font: `500 9px/1 ${VS.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', color: VS.terra, marginBottom: 14 }}>главное дерево</div>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <Cameo size={200} color={VS.ink}>
                <div style={{ color: VS.ink }}>
                  <Botanical kind={main.plant.icon} size={170} color={VS.ink} />
                </div>
              </Cameo>
            </div>
            <div style={{ font: `400 38px/1 ${VS.display}`, color: VS.ink, marginTop: 16 }}>{main.plant.name}</div>
            <div style={{ font: `400 italic 12px/1 ${VS.serif}`, color: VS.inkFaded, marginTop: 4 }}>{main.plant.nameLat}</div>
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: 12 }}><Vignette color={VS.rule} width={180} /></div>
            <div style={{ font: `400 italic 16px/1.5 ${VS.serif}`, color: VS.ink, marginTop: 14, maxWidth: 440, marginLeft: 'auto', marginRight: 'auto' }}>«{main.plant.storyShort}»</div>
            <div style={{ font: `400 13px/1.7 ${VS.serif}`, color: VS.inkSoft, marginTop: 12, maxWidth: 440, marginLeft: 'auto', marginRight: 'auto' }}>{main.plant.storyLong}</div>
          </div>

          {/* others */}
          {others.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <div style={{ font: `500 9px/1 ${VS.sans}`, letterSpacing: '0.36em', textTransform: 'uppercase', color: VS.terra, marginBottom: 16 }}>сопровождают</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
                {others.map((p) => (
                  <div key={p.id} style={{ border: `1px solid ${VS.rule}`, padding: 14, textAlign: 'left', display: 'grid', gridTemplateColumns: '50px 1fr', gap: 12, alignItems: 'center' }}>
                    <div style={{ color: VS.ink }}><Botanical kind={p.plant.icon} size={48} color={VS.ink} /></div>
                    <div>
                      <div style={{ font: `400 16px/1.1 ${VS.display}`, color: VS.ink }}>{p.plant.name}</div>
                      <div style={{ font: `400 italic 11px/1.3 ${VS.serif}`, color: VS.inkFaded, marginTop: 4 }}>{p.plant.storyShort}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginTop: 28, paddingTop: 18, borderTop: `1px solid ${VS.ink}` }}>
            <div style={{ font: `400 italic 13px/1.5 ${VS.serif}`, color: VS.inkSoft, marginBottom: 14, maxWidth: 420, margin: '0 auto 14px' }}>
              да воплотится сие в саду — <br />посадка экспертом, выбор саженцев из питомника
            </div>
            <button style={{ background: VS.ink, color: VS.paper, border: `2px double ${VS.ink}`, padding: '14px 32px', font: `400 13px/1 ${VS.display}`, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
              ✦ заказать закладку места силы ✦
            </button>
          </div>

          <div style={{ marginTop: 22, font: `400 italic 11px/1 ${VS.serif}`, color: VS.inkFaded }}>folium III · domino — лист гостьи</div>

          <button onClick={onBack} style={{ position: 'absolute', top: -12, left: -12, background: 'transparent', border: 'none', font: `400 italic 12px/1 ${VS.serif}`, color: VS.inkFaded, cursor: 'pointer' }}>← вернуться к экспертному</button>
        </div>
      </VictorianFrame>
    </div>
  );
}

window.ScreenCover = ScreenCover;
window.ScreenForm = ScreenForm;
window.ScreenWeaving = ScreenWeaving;
window.ScreenExpert = ScreenExpert;
window.ScreenClient = ScreenClient;
