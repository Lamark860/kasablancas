// prototype-engine.jsx — алгоритм подбора (упрощённый MVP-движок)
// Берёт данные клиента → прогоняет через 5 моковых "оракулов" → возвращает пул растений с пересечениями.

// Минимальная база растений (расширяется со временем).
const PLANTS_DB = {
  iva: { name: 'Ива белая', nameLat: 'Salix alba', element: 'water', icon: 'willow', minZone: 4, isWeed: false, hierarchy: 4, storyShort: 'Тихая вода, в которой видны звёзды.', storyLong: 'Дерево людей, которые чувствуют тоньше, чем говорят. Любит воду, мягкий свет и долгие вечера.' },
  ryabina: { name: 'Рябина обыкновенная', nameLat: 'Sorbus aucuparia', element: 'air', icon: 'rowan', minZone: 3, isWeed: false, hierarchy: 4, storyShort: 'Дерево, которое смотрит за домом.', storyLong: 'В русской традиции — оберег, сажают у крыльца. Цветёт белыми зонтиками, к осени — алые гроздья.' },
  klen: { name: 'Клён остролистный', nameLat: 'Acer platanoides', element: 'air', icon: 'rowan', minZone: 4, isWeed: false, hierarchy: 4, storyShort: 'Тень и осенний пожар.', storyLong: 'Стройное дерево с широкой кроной. Осенью даёт самый яркий цвет в саду.' },
  dub: { name: 'Дуб черешчатый', nameLat: 'Quercus robur', element: 'fire', icon: 'rowan', minZone: 4, isWeed: false, hierarchy: 5, storyShort: 'Сила, которая не торопится.', storyLong: 'Самое медленное и самое верное из деревьев. Сажают тем, у кого хватает терпения ждать.' },
  bereza: { name: 'Берёза повислая', nameLat: 'Betula pendula', element: 'air', icon: 'willow', minZone: 2, isWeed: false, hierarchy: 4, storyShort: 'Светлая, тонкокостная, родная.', storyLong: 'Главное дерево севера. Лёгкая крона, белый ствол, ажурная тень.' },
  sosna: { name: 'Сосна обыкновенная', nameLat: 'Pinus sylvestris', element: 'fire', icon: 'rowan', minZone: 3, isWeed: false, hierarchy: 4, storyShort: 'Смола и солнце.', storyLong: 'Хвойное, всегда зелёное. Любит сухое и солнечное.' },
  pion: { name: 'Пион молочноцветковый', nameLat: 'Paeonia lactiflora', element: 'earth', icon: 'peony', minZone: 3, isWeed: false, hierarchy: 3, storyShort: 'Полнота, которой не нужно ничего доказывать.', storyLong: 'Цветёт коротко, но ради этих десяти дней терпят весь год. Многолетник, живёт полвека.' },
  roza: { name: 'Роза парковая', nameLat: 'Rosa rugosa', element: 'fire', icon: 'peony', minZone: 3, isWeed: false, hierarchy: 3, storyShort: 'То, ради чего разбивают сад.', storyLong: 'Парковые сорта неприхотливы и душисты. Цветут с июня по октябрь.' },
  lavanda: { name: 'Лаванда узколистная', nameLat: 'Lavandula angustifolia', element: 'air', icon: 'lavender', minZone: 5, isWeed: false, hierarchy: 2, storyShort: 'Тёплый камень, на котором сохнут травы.', storyLong: 'Любит солнце и сухую почву. Цветёт и пахнет до заморозков.' },
  gortenziya: { name: 'Гортензия метельчатая', nameLat: 'Hydrangea paniculata', element: 'water', icon: 'hydrangea', minZone: 3, isWeed: false, hierarchy: 3, storyShort: 'Облако, которое не уходит до октября.', storyLong: 'Пышные соцветия меняют цвет от белого через розовый к зелёно-винному. Цветёт до морозов.' },
  iris: { name: 'Ирис сибирский', nameLat: 'Iris sibirica', element: 'water', icon: 'lavender', minZone: 3, isWeed: false, hierarchy: 2, storyShort: 'Радуга на одной грядке.', storyLong: 'Многолетник, любит влагу и солнце. Образует плотные куртины.' },
  romashka: { name: 'Ромашка садовая', nameLat: 'Leucanthemum vulgare', element: 'earth', icon: 'peony', minZone: 3, isWeed: false, hierarchy: 1, storyShort: 'Простая, как утро.', storyLong: 'Многолетник, цветёт всё лето. Самосев, легко расселяется.' },
  shipovnik: { name: 'Шиповник майский', nameLat: 'Rosa majalis', element: 'fire', icon: 'rowan', minZone: 3, isWeed: false, hierarchy: 3, storyShort: 'Колючий, душистый, красный.', storyLong: 'Дикая роза, мать всех садовых сортов. Плодоносит, лекарственный.' },
};

// Друидский календарь (упрощённый — основные 22 знака)
const DRUID_TREES = [
  { from: '12-23', to: '01-01', plant: 'iva', name: 'Яблоня→ива' /* пример: для MVP мапим к доступным */ },
  // упрощённо — на каждую дату возвращаем что-то из базы
];

function druidTreeByDate(date) {
  if (!date) return null;
  const m = date.getMonth() + 1, d = date.getDate();
  // упрощённое сопоставление: главные знаки + пересчёт
  if ((m === 3 && d >= 1 && d <= 10) || (m === 9 && d >= 3 && d <= 12)) return { plant: 'iva', period: m === 3 ? '1–10 марта' : '3–12 сентября', label: 'Ива' };
  if ((m === 4 && d >= 1 && d <= 10) || (m === 10 && d >= 4 && d <= 13)) return { plant: 'ryabina', period: m === 4 ? '1–10 апреля' : '4–13 октября', label: 'Рябина' };
  if ((m === 4 && d >= 11 && d <= 20) || (m === 10 && d >= 14 && d <= 23)) return { plant: 'klen', period: m === 4 ? '11–20 апреля' : '14–23 октября', label: 'Клён' };
  if (m === 3 && d === 21) return { plant: 'dub', period: '21 марта', label: 'Дуб' };
  if (m === 6 && d === 24) return { plant: 'bereza', period: '24 июня', label: 'Берёза' };
  if ((m === 2 && d >= 19) || (m === 8 && d >= 24 && d <= 29)) return { plant: 'sosna', period: 'сосна', label: 'Сосна' };
  if ((m === 6 && d >= 25) || (m === 7 && d <= 4)) return { plant: 'roza', period: '25 июня – 4 июля', label: 'Яблоня (→ роза)' };
  // fallback
  return { plant: 'bereza', period: 'берёза (универсальный)', label: 'Берёза' };
}

function druidFlowerByDate(date) {
  if (!date) return null;
  const m = date.getMonth() + 1, d = date.getDate();
  if (m === 4 && d >= 11 && d <= 20) return { plant: 'gortenziya', period: '11–20 апреля', label: 'Гортензия' };
  if (m === 4 && d >= 21 && d <= 30) return { plant: 'pion', period: '21–30 апреля', label: 'Георгин (→ пион)' };
  if (m === 5 && d >= 22) return { plant: 'romashka', period: '22–31 мая', label: 'Ромашка' };
  if (m === 6 && d >= 22) return { plant: 'roza', period: '22 июня – 1 июля', label: 'Роза' };
  if (m === 7 && d >= 23) return { plant: 'shipovnik', period: '23 июля – 2 августа', label: 'Шиповник' };
  if (m === 8 && d >= 13 && d <= 23) return { plant: 'roza', period: '13–23 августа', label: 'Роза' };
  if (m === 11 && d >= 13 && d <= 22) return { plant: 'pion', period: '13–22 ноября', label: 'Пион' };
  return { plant: 'pion', period: 'пион (универсальный)', label: 'Пион' };
}

function zodiacByDate(date) {
  if (!date) return null;
  const m = date.getMonth() + 1, d = date.getDate();
  if ((m===3 && d>=21) || (m===4 && d<=19)) return { sign: 'Овен', element: 'fire', plants: ['ryabina', 'shipovnik', 'pion'] };
  if ((m===4 && d>=20) || (m===5 && d<=20)) return { sign: 'Телец', element: 'earth', plants: ['lavanda', 'iris', 'roza'] };
  if ((m===5 && d>=21) || (m===6 && d<=20)) return { sign: 'Близнецы', element: 'air', plants: ['lavanda', 'klen'] };
  if ((m===6 && d>=21) || (m===7 && d<=22)) return { sign: 'Рак', element: 'water', plants: ['iva', 'gortenziya', 'iris'] };
  if ((m===7 && d>=23) || (m===8 && d<=22)) return { sign: 'Лев', element: 'fire', plants: ['dub', 'roza', 'pion'] };
  if ((m===8 && d>=23) || (m===9 && d<=22)) return { sign: 'Дева', element: 'earth', plants: ['lavanda', 'romashka'] };
  if ((m===9 && d>=23) || (m===10 && d<=22)) return { sign: 'Весы', element: 'air', plants: ['klen', 'gortenziya', 'roza'] };
  if ((m===10 && d>=23) || (m===11 && d<=21)) return { sign: 'Скорпион', element: 'water', plants: ['ryabina', 'pion'] };
  if ((m===11 && d>=22) || (m===12 && d<=21)) return { sign: 'Стрелец', element: 'fire', plants: ['ryabina', 'dub'] };
  if ((m===12 && d>=22) || (m===1 && d<=19)) return { sign: 'Козерог', element: 'earth', plants: ['sosna', 'dub'] };
  if ((m===1 && d>=20) || (m===2 && d<=18)) return { sign: 'Водолей', element: 'air', plants: ['ryabina', 'lavanda'] };
  return { sign: 'Рыбы', element: 'water', plants: ['iva', 'iris', 'gortenziya'] };
}

function eyeColorPlants(eyeColor) {
  const map = {
    'голубые': ['iva', 'iris', 'lavanda', 'gortenziya'],
    'серые': ['iva', 'lavanda'],
    'зелёные': ['klen', 'sosna'],
    'карие': ['dub', 'ryabina', 'shipovnik'],
    'тёмные': ['ryabina', 'pion', 'shipovnik'],
  };
  return map[eyeColor] || [];
}

function namePlants(name) {
  if (!name) return [];
  const n = name.toLowerCase().split(/\s+/)[0];
  const map = {
    'маргарита': ['romashka', 'pion', 'roza'],
    'роза': ['roza', 'shipovnik'],
    'лилия': ['iris'],
    'татьяна': ['romashka'],
    'екатерина': ['roza'],
    'анна': ['iva'],
    'мария': ['roza', 'pion'],
    'ольга': ['ryabina'],
    'елена': ['lavanda', 'iris'],
    'наталья': ['bereza', 'romashka'],
    'ирина': ['iris'],
  };
  return map[n] || [];
}

function findPlants(person) {
  const date = person.birthDate ? new Date(person.birthDate) : null;
  const oracles = [];

  const dt = druidTreeByDate(date);
  if (dt) oracles.push({ id: 'druid_tree', name: 'Друиды · деревья', detail: dt.period + ' · «' + dt.label + '»', plants: [{ id: dt.plant, weight: 1.0 }] });

  const df = druidFlowerByDate(date);
  if (df) oracles.push({ id: 'druid_flower', name: 'Друиды · цветы', detail: df.period + ' · «' + df.label + '»', plants: [{ id: df.plant, weight: 1.0 }] });

  const z = zodiacByDate(date);
  if (z) oracles.push({ id: 'zodiac', name: 'Зодиак · ' + z.sign, detail: 'стихия ' + z.element, plants: z.plants.map(p => ({ id: p, weight: 0.7 })) });

  const ec = eyeColorPlants(person.eyeColor);
  if (ec.length) oracles.push({ id: 'eye_color', name: 'Цвет глаз · ' + person.eyeColor, detail: 'авторская система', plants: ec.map(p => ({ id: p, weight: 0.5 })) });

  const np = namePlants(person.fullName);
  if (np.length) oracles.push({ id: 'name', name: 'Имя · ' + (person.fullName || '').split(/\s+/)[0], detail: 'этимология / созвучие', plants: np.map(p => ({ id: p, weight: 0.6 })) });

  // Сводим в пул
  const pool = {};
  oracles.forEach(o => {
    o.plants.forEach(({ id, weight }) => {
      if (!pool[id]) pool[id] = { id, plant: PLANTS_DB[id], matches: 0, totalWeight: 0, sources: [] };
      pool[id].matches += 1;
      pool[id].totalWeight += weight;
      pool[id].sources.push({ sys: o.name, detail: o.detail });
    });
  });

  // Климатический фильтр
  const userZone = person.zone || 6;
  const filtered = Object.values(pool).filter(p => p.plant && p.plant.minZone <= userZone);

  // Сортировка
  filtered.sort((a, b) => b.matches - a.matches || b.totalWeight - a.totalWeight || b.plant.hierarchy - a.plant.hierarchy);

  // Назначаем роли
  const result = filtered.slice(0, 5);
  if (result[0]) result[0].role = 'Главное дерево';
  result.slice(1).forEach((r, i) => {
    r.role = ['Сопровождающий', 'Оберег', 'Нижний ярус', 'Кустарниковый акцент'][i] || 'Сопровождающий';
  });

  // Доминирующая стихия (для подсказки)
  const elemCount = {};
  result.forEach(r => { const e = r.plant.element; elemCount[e] = (elemCount[e]||0) + 1; });
  const domElement = Object.entries(elemCount).sort((a,b)=>b[1]-a[1])[0];

  return {
    pool: result,
    oraclesUsed: oracles.map(o => o.name),
    excluded: Object.values(pool).filter(p => p.plant && p.plant.minZone > userZone).map(p => ({ name: p.plant.name, reason: 'не подходит для зоны ' + userZone })),
    dominantElement: domElement ? { element: domElement[0], count: domElement[1] } : null,
  };
}

window.PLANTS_DB = PLANTS_DB;
window.findPlants = findPlants;
