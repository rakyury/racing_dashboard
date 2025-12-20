# Превью экранов (TouchGFX и LVGL)

Ниже — текстовые макеты того, как выглядят экраны демо-профилей. Цвета и стили взяты из современного Motec-подхода: тёмный фон, яркие акценты для критичных значений, заметные подписи и сегментированные шкалы.

## TouchGFX

### Main — дорожный/прогрев
```
┌───────────────────────────────────────────────────────────┐
│ RPM: ████████████ 4200      Shift: ░░░░░░░░░░░░░░░░░░     │
│ Coolant 86°C   Oil 98°C   Batt 13.8V   Ambient 22°C       │
│ Boost 82 kPa   Throttle 18%  Gear 3   Speed 98 km/h       │
│ Lambda 0.96 ⇢ 1.00 (бар-граф)                             │
│ Bottom bar: oil/fuel pressure pills + small warnings      │
└───────────────────────────────────────────────────────────┘
```

### Race — атака круга
```
┌───────────────────────────────────────────────────────────┐
│ RPM: ██████████████████████ 8450  Shift: ████████▲▲▲▲▲    │
│ Boost 185 kPa   Throttle 92%     Gear 5     Speed 212 km/h│
│ Oil P 2.4 bar ▼  Fuel P 2.1 bar ▼  Oil T 118°C ▲          │
│ Lambda 0.86 ⇢ 0.88 (линия фактическая + цель пунктиром)   │
│ Alert ribbon: WARN OilPressLow | CRIT FuelPressLow        │
└───────────────────────────────────────────────────────────┘
```

### Warning — диагностика
```
┌───────────────────────────────────────────────────────────┐
│ Oil P 2.0 bar ▼   Fuel P 2.0 bar ▼   Batt 11.8V ▼         │
│ Coolant 105°C ▲   Oil T 120°C ▲      Ambient 42°C ▲       │
│ Boost 90 kPa ▬    Throttle 12%       RPM 1500              │
│ Large alert block + список последних событий логгера      │
└───────────────────────────────────────────────────────────┘
```

### External video overlay (HDMI/CarPlay/Android Auto)
```
┌───────────────────────────────────────────────────────────┐
│  [Видеопоток фона]                                        │
│  HUD: RPM bar + shift lights по верху                     │
│       Right strip: oil/fuel P, oil/coolant T pills        │
│       Bottom ribbon: текущие алерты                       │
└───────────────────────────────────────────────────────────┘
```

## LVGL

### Cluster — компактный режим
```
┌───────────────────────────────────────┐
│ RPM arc 0..9000 with shift markers    │
│ Boost 140 kPa  | Throttle 45%         │
│ Batt 13.9V     | Gear 4               │
│ Lambda 0.95 ⇢ 1.00 (микро-граф)       │
└───────────────────────────────────────┘
```

### Health — мониторинг
```
┌───────────────────────────────────────┐
│ Oil P 2.2 bar ▼   Fuel P 2.4 bar ▼   │
│ Oil T 115°C ▲     Coolant 104°C ▲    │
│ Alert stack: WARN OilPressLow        │
│              CRIT FuelPressLow       │
└───────────────────────────────────────┘
```

### Demo flow
1. Профиль TouchGFX: main → race → warning → external video.
2. Профиль LVGL: cluster → health при проблемах давления.
3. Оба профиля используют те же каналы (`rpm`, давления, температуры, `boost_kpa`, `throttle`, `lambda_current/target`, `battery_voltage`, `gear`).
