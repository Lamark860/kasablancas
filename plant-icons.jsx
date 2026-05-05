// plant-icons.jsx — стилизованные SVG-иконки растений (плейсхолдеры)
// Не "фото", а монохромные ботанические значки. Цвет наследуется через currentColor.

function PlantIcon({ kind, size = 64, stroke = 1.2 }) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 64 64',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: stroke,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
  };

  if (kind === 'willow') {
    // Плакучая ива — изогнутый ствол + свисающие ветви
    return (
      <svg {...common}>
        <path d="M32 58 C 30 46 34 38 32 24 C 30 14 36 8 36 6" />
        <path d="M36 10 C 28 16 22 22 18 32" />
        <path d="M36 14 C 30 22 26 28 22 40" />
        <path d="M38 12 C 42 22 46 28 50 38" />
        <path d="M40 16 C 44 26 46 34 48 44" />
        <path d="M34 18 C 32 28 30 36 28 46" />
        <path d="M22 58 L 42 58" strokeWidth={stroke * 0.8} />
      </svg>
    );
  }
  if (kind === 'peony') {
    // Пион — пышный шарообразный цветок
    return (
      <svg {...common}>
        <circle cx="32" cy="26" r="14" />
        <path d="M32 12 C 26 18 26 30 32 34" />
        <path d="M32 12 C 38 18 38 30 32 34" />
        <path d="M18 26 C 24 22 28 26 32 30" />
        <path d="M46 26 C 40 22 36 26 32 30" />
        <path d="M22 18 C 28 22 30 26 32 32" />
        <path d="M42 18 C 36 22 34 26 32 32" />
        <path d="M32 40 L 32 58" />
        <path d="M28 50 L 24 46" />
        <path d="M36 50 L 40 46" />
      </svg>
    );
  }
  if (kind === 'rowan') {
    // Рябина — крона + гроздь ягод
    return (
      <svg {...common}>
        <path d="M32 58 L 32 30" />
        <ellipse cx="32" cy="20" rx="18" ry="14" />
        <path d="M22 22 L 18 18 M 32 14 L 32 8 M 42 22 L 46 18" strokeWidth={stroke * 0.7} />
        <circle cx="28" cy="44" r="2" />
        <circle cx="32" cy="46" r="2" />
        <circle cx="36" cy="44" r="2" />
        <circle cx="30" cy="50" r="2" />
        <circle cx="34" cy="50" r="2" />
      </svg>
    );
  }
  if (kind === 'lavender') {
    // Лаванда — три стебля с колосками
    return (
      <svg {...common}>
        <path d="M20 58 L 20 32" />
        <path d="M32 58 L 32 28" />
        <path d="M44 58 L 44 32" />
        {[20, 32, 44].map((x, i) => {
          const top = i === 1 ? 28 : 32;
          return (
            <g key={x}>
              <ellipse cx={x} cy={top} rx="3" ry="2" />
              <ellipse cx={x} cy={top + 4} rx="3" ry="2" />
              <ellipse cx={x} cy={top + 8} rx="3" ry="2" />
              <ellipse cx={x} cy={top + 12} rx="3" ry="2" />
            </g>
          );
        })}
      </svg>
    );
  }
  if (kind === 'hydrangea') {
    // Гортензия — соцветие из мелких 4-лепестковых цветков
    return (
      <svg {...common}>
        <path d="M32 58 L 32 40" />
        <ellipse cx="32" cy="26" rx="18" ry="16" />
        {[
          [22, 20], [32, 16], [42, 20],
          [18, 28], [28, 26], [38, 26], [46, 30],
          [22, 36], [32, 34], [42, 36],
        ].map(([cx, cy], i) => (
          <g key={i}>
            <circle cx={cx} cy={cy} r="3" />
            <line x1={cx - 3} y1={cy} x2={cx + 3} y2={cy} strokeWidth={stroke * 0.6} />
            <line x1={cx} y1={cy - 3} x2={cx} y2={cy + 3} strokeWidth={stroke * 0.6} />
          </g>
        ))}
      </svg>
    );
  }
  // fallback
  return (
    <svg {...common}>
      <circle cx="32" cy="32" r="20" />
    </svg>
  );
}

window.PlantIcon = PlantIcon;
