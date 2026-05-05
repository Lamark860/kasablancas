// victorian-styles.jsx — общий стиль и переиспользуемые декоративные элементы

const VS = {
  // обложка / экспертный лист (тёмные)
  coverInk: '#1a120b',
  coverDeep: '#2a1a0e',
  coverGold: '#b89254',
  coverGoldSoft: '#8a6a3c',
  // внутренние страницы (кремовые)
  paper: '#ede0c4',
  paperDeep: '#dccfae',
  paperShadow: '#c0b48f',
  // чернила
  ink: '#221a10',
  inkSoft: '#4e3f2a',
  inkFaded: '#7a6a4a',
  rule: '#a8966a',
  // акценты
  terra: '#9a3a1f',
  terraSoft: '#b85a3a',
  rose: '#c47a76',
  leaf: '#5a6a3a',
  // шрифты
  display: '"UnifrakturCook", "IM Fell English SC", serif',
  serif: '"IM Fell English", "EB Garamond", "Cormorant Garamond", serif',
  sans: '"IBM Plex Mono", ui-monospace, monospace',
};

// Текстуры: тонкая зернистость "старой бумаги" — чисто CSS, лёгкая
const PaperGrain = ({ opacity = 0.5 }) => (
  <div style={{
    position: 'absolute', inset: 0, pointerEvents: 'none', mixBlendMode: 'multiply', opacity,
    backgroundImage: 'radial-gradient(rgba(60,40,10,.08) 1px, transparent 1px), radial-gradient(rgba(60,40,10,.06) 1px, transparent 1px)',
    backgroundSize: '3px 3px, 7px 7px', backgroundPosition: '0 0, 1px 2px',
  }}/>
);

// Углловой барочный орнамент (4 поворота)
function CornerOrnament({ size = 60, color, rotate = 0 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 60 60" fill="none" stroke={color} strokeWidth="1" style={{ transform: `rotate(${rotate}deg)` }}>
      <path d="M2 2 L 58 2 L 58 58 L 2 58 Z" strokeWidth="0.5" opacity="0.4" />
      <path d="M4 4 L 24 4 M 4 4 L 4 24" strokeWidth="1.2" />
      <path d="M4 8 C 12 8 16 10 18 18 C 20 20 22 22 24 22" />
      <path d="M8 4 C 8 12 10 16 18 18" />
      <circle cx="20" cy="20" r="2" fill={color} />
      <circle cx="20" cy="20" r="4" />
      <path d="M14 4 L 14 8 M 4 14 L 8 14" strokeWidth="0.6" />
      <path d="M28 4 C 26 8 24 8 22 8" strokeWidth="0.6" />
      <path d="M4 28 C 8 26 8 24 8 22" strokeWidth="0.6" />
    </svg>
  );
}

// Двойная рамка с углами — ядро викторианского оформления
function VictorianFrame({ children, color, padding = '36px', bg = 'transparent', innerInset = 8, cornerSize = 50, style }) {
  return (
    <div style={{ position: 'relative', background: bg, padding, ...style }}>
      <div style={{ position: 'absolute', inset: 6, border: `1.5px solid ${color}`, pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', inset: 6 + innerInset, border: `0.5px solid ${color}`, opacity: 0.6, pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', top: -2, left: -2, color, opacity: 0.85 }}><CornerOrnament size={cornerSize} color={color} rotate={0} /></div>
      <div style={{ position: 'absolute', top: -2, right: -2, color, opacity: 0.85 }}><CornerOrnament size={cornerSize} color={color} rotate={90} /></div>
      <div style={{ position: 'absolute', bottom: -2, right: -2, color, opacity: 0.85 }}><CornerOrnament size={cornerSize} color={color} rotate={180} /></div>
      <div style={{ position: 'absolute', bottom: -2, left: -2, color, opacity: 0.85 }}><CornerOrnament size={cornerSize} color={color} rotate={270} /></div>
      <div style={{ position: 'relative' }}>{children}</div>
    </div>
  );
}

// Овальная "камея" — рамка-медальон с орнаментальной обводкой
function Cameo({ size = 220, color, children, label }) {
  const w = size, h = size * 1.25;
  return (
    <div style={{ position: 'relative', width: w, height: h, margin: '0 auto' }}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <clipPath id={`cameo-clip-${size}`}>
            <ellipse cx={w/2} cy={h/2} rx={w/2 - 16} ry={h/2 - 16} />
          </clipPath>
        </defs>
        {/* outer ornament */}
        <ellipse cx={w/2} cy={h/2} rx={w/2 - 4} ry={h/2 - 4} fill="none" stroke={color} strokeWidth="2" />
        <ellipse cx={w/2} cy={h/2} rx={w/2 - 10} ry={h/2 - 10} fill="none" stroke={color} strokeWidth="0.5" opacity="0.6" />
        <ellipse cx={w/2} cy={h/2} rx={w/2 - 14} ry={h/2 - 14} fill="none" stroke={color} strokeWidth="0.5" opacity="0.4" />
        {/* small dots around */}
        {Array.from({length: 24}).map((_, i) => {
          const a = (i / 24) * Math.PI * 2;
          const cx = w/2 + Math.cos(a) * (w/2 - 7);
          const cy = h/2 + Math.sin(a) * (h/2 - 7);
          return <circle key={i} cx={cx} cy={cy} r="0.8" fill={color} opacity="0.7" />;
        })}
      </svg>
      <div style={{ position: 'absolute', inset: 16, clipPath: 'ellipse(50% 50% at 50% 50%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {children}
      </div>
      {label && <div style={{ position: 'absolute', top: -14, left: '50%', transform: 'translateX(-50%)', font: `400 italic 11px/1 ${VS.serif}`, color, background: VS.paper, padding: '0 10px' }}>{label}</div>}
    </div>
  );
}

// Виньетка-разделитель: горизонтальная орнаментальная полоса
function Vignette({ color, width = 200 }) {
  return (
    <svg width={width} height={20} viewBox="0 0 200 20" fill="none" stroke={color} strokeWidth="1">
      <line x1="0" y1="10" x2="60" y2="10" />
      <line x1="140" y1="10" x2="200" y2="10" />
      <path d="M70 10 C 75 5 80 5 85 10 C 90 15 95 15 100 10 C 105 5 110 5 115 10 C 120 15 125 15 130 10" />
      <circle cx="100" cy="10" r="2.5" fill={color} />
      <circle cx="65" cy="10" r="1.5" />
      <circle cx="135" cy="10" r="1.5" />
    </svg>
  );
}

// Маленький символ (стихия / луна / звезда)
function VSymbol({ kind, size = 14, color = 'currentColor' }) {
  const p = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: color, strokeWidth: 1.2 };
  if (kind === 'water') return (<svg {...p}><path d="M12 4 C 6 12 6 16 6 17 a 6 6 0 0 0 12 0 c 0 -1 0 -5 -6 -13 z"/></svg>);
  if (kind === 'fire') return (<svg {...p}><path d="M12 3 C 14 8 18 9 18 14 a 6 6 0 0 1 -12 0 c 0 -3 2 -4 3 -7 c 1 2 1 4 3 4 c 1 0 0 -3 0 -8 z"/></svg>);
  if (kind === 'earth') return (<svg {...p}><circle cx="12" cy="12" r="9"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="12" y1="3" x2="12" y2="21"/></svg>);
  if (kind === 'air') return (<svg {...p}><path d="M3 9 h 12 a 3 3 0 1 0 -3 -3"/><path d="M3 14 h 16 a 3 3 0 1 1 -3 3"/></svg>);
  if (kind === 'star') return (<svg {...p}>{[270,342,54,126,198].map(a=>{const r=a*Math.PI/180;return <line key={a} x1="12" y1="12" x2={12+Math.cos(r)*9} y2={12+Math.sin(r)*9}/>})}</svg>);
  if (kind === 'sun') return (<svg {...p}><circle cx="12" cy="12" r="3.5"/>{[0,45,90,135,180,225,270,315].map(a=>{const r=a*Math.PI/180;return <line key={a} x1={12+Math.cos(r)*6} y1={12+Math.sin(r)*6} x2={12+Math.cos(r)*9} y2={12+Math.sin(r)*9}/>})}</svg>);
  if (kind === 'moon') return (<svg {...p}><path d="M16 4 a 9 9 0 1 0 0 16 a 7 7 0 1 1 0 -16 z" fill={color} stroke="none"/></svg>);
  return null;
}

// Простая ботаническая иллюстрация (единый стиль для всего прототипа)
function Botanical({ kind, size = 100, color = VS.ink }) {
  const p = { width: size, height: size, viewBox: '0 0 100 100', fill: 'none', stroke: color, strokeWidth: 0.9, strokeLinecap: 'round', strokeLinejoin: 'round' };
  if (kind === 'willow') return (
    <svg {...p}>
      <path d="M50 95 C 48 70 52 50 50 30 C 48 18 56 8 58 6"/>
      <path d="M58 12 C 48 22 36 32 30 50"/>
      <path d="M58 16 C 50 28 42 40 36 56"/>
      <path d="M60 14 C 68 24 74 36 78 52"/>
      <path d="M62 18 C 70 32 74 44 76 60"/>
      <path d="M54 22 C 50 36 46 50 42 64"/>
      <path d="M40 95 L 60 95"/>
      <path d="M30 50 C 32 56 30 60 28 62"/><path d="M36 56 C 38 62 36 66 34 68"/>
      <path d="M78 52 C 76 58 78 62 80 64"/><path d="M76 60 C 74 66 76 70 78 72"/>
      <path d="M42 64 C 40 70 42 74 44 76"/>
    </svg>
  );
  if (kind === 'peony') return (
    <svg {...p}>
      <path d="M50 95 L 50 60"/>
      <path d="M50 80 C 40 78 36 72 38 66"/>
      <path d="M50 76 C 60 76 64 70 62 64"/>
      <circle cx="50" cy="40" r="22"/>
      <path d="M50 18 C 42 26 42 42 50 50"/>
      <path d="M50 18 C 58 26 58 42 50 50"/>
      <path d="M28 40 C 36 34 44 40 50 46"/>
      <path d="M72 40 C 64 34 56 40 50 46"/>
      <path d="M34 28 C 42 32 46 40 50 48"/>
      <path d="M66 28 C 58 32 54 40 50 48"/>
      <path d="M30 50 C 38 50 44 46 50 42"/>
      <path d="M70 50 C 62 50 56 46 50 42"/>
      <circle cx="50" cy="40" r="3" fill={color}/>
    </svg>
  );
  if (kind === 'rowan') return (
    <svg {...p}>
      <path d="M50 95 L 50 50"/>
      <ellipse cx="50" cy="35" rx="28" ry="22"/>
      <path d="M30 38 L 22 32 M 50 22 L 50 12 M 70 38 L 78 32" strokeWidth="0.7"/>
      <path d="M38 28 L 32 22 M 62 28 L 68 22 M 42 18 L 38 14 M 58 18 L 62 14" strokeWidth="0.6"/>
      {[[42,68],[50,70],[58,68],[44,76],[52,78],[56,76],[48,84]].map(([x,y],i)=>(<circle key={i} cx={x} cy={y} r="2.2" fill={color} fillOpacity="0.15"/>))}
      {[[42,68],[50,70],[58,68],[44,76],[52,78],[56,76],[48,84]].map(([x,y],i)=>(<circle key={i+'b'} cx={x} cy={y} r="2.2"/>))}
      <path d="M50 50 L 46 64 M 50 56 L 54 70 M 50 60 L 48 74"/>
    </svg>
  );
  if (kind === 'lavender') return (
    <svg {...p}>
      <path d="M30 95 L 30 50"/>
      <path d="M50 95 L 50 42"/>
      <path d="M70 95 L 70 50"/>
      {[30,50,70].map((x,i) => {
        const top = i===1 ? 42 : 50;
        return (
          <g key={x}>
            {[0,4,8,12,16,20].map((dy,j)=>(<ellipse key={j} cx={x} cy={top+dy} rx="3.5" ry="2.5"/>))}
          </g>
        );
      })}
      <path d="M30 60 L 26 56 M 30 70 L 34 66 M 50 54 L 46 50 M 50 64 L 54 60 M 70 60 L 74 56" strokeWidth="0.7"/>
    </svg>
  );
  if (kind === 'hydrangea') return (
    <svg {...p}>
      <path d="M50 95 L 50 60"/>
      <ellipse cx="50" cy="40" rx="28" ry="24"/>
      {[[34,30],[50,24],[66,30],[28,42],[42,38],[58,38],[72,44],[36,52],[50,48],[64,52],[44,58],[58,58]].map(([cx,cy],i)=>(
        <g key={i}>
          <circle cx={cx} cy={cy} r="4"/>
          <line x1={cx-4} y1={cy} x2={cx+4} y2={cy} strokeWidth="0.5"/>
          <line x1={cx} y1={cy-4} x2={cx} y2={cy+4} strokeWidth="0.5"/>
          <circle cx={cx} cy={cy} r="0.8" fill={color}/>
        </g>
      ))}
      <path d="M50 60 L 44 70 M 50 65 L 56 75" strokeWidth="0.7"/>
    </svg>
  );
  return <svg {...p}><circle cx="50" cy="50" r="30"/></svg>;
}

window.VS = VS;
window.PaperGrain = PaperGrain;
window.CornerOrnament = CornerOrnament;
window.VictorianFrame = VictorianFrame;
window.Cameo = Cameo;
window.Vignette = Vignette;
window.VSymbol = VSymbol;
window.Botanical = Botanical;
