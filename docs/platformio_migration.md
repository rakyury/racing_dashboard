# Racing Dashboard - PlatformIO Migration Guide

## Обзор изменений

Проект полностью мигрирован на **PlatformIO + Arduino Framework** с поддержкой **STM32H7B3** и дисплея **RVT70HSSNWN00 (1024×600)**.

---

## Структура проекта

```
racing_dashboard/
├── platformio.ini          # Конфигурация PlatformIO
├── include/                # Заголовочные файлы
│   ├── config.h            # Глобальные настройки
│   ├── display_config.h    # Конфигурация дисплея
│   ├── theme_manager.h     # Управление темами
│   ├── advanced_logger.h   # Продвинутый логгер
│   └── lap_timer.h         # Система lap timing
├── src/                    # Исходный код
│   ├── main_arduino.cpp    # Главный файл Arduino
│   ├── display_config.cpp
│   ├── theme_manager.cpp
│   └── ...
├── lib/                    # Внешние библиотеки
├── test/                   # Unit-тесты
└── docs/                   # Документация
```

---

## Установка и сборка

### 1. Установка PlatformIO

```bash
# Через pip
pip install platformio

# Или через VS Code
# Установите расширение "PlatformIO IDE"
```

### 2. Клонирование проекта

```bash
git clone <repo_url>
cd racing_dashboard
```

### 3. Сборка проекта

```bash
# Сборка для STM32H7B3
pio run -e stm32h7b3

# Сборка и загрузка
pio run -e stm32h7b3 --target upload

# Мониторинг Serial
pio device monitor -b 115200
```

### 4. Сборка для симулятора (тестирование на ПК)

```bash
pio run -e simulator
./build/simulator/firmware
```

---

## Новые возможности

### 1. Адаптивный UI (DisplayConfig)

**Поддерживаемые разрешения:**
- 1024×600 (RVT70HSSNWN00) - **основной**
- 1280×480 (Ultra-wide)
- 800×480 (Compact)
- 480×320 (Minimal)

**Пример использования:**

```cpp
#include "display_config.h"

// Инициализация для RVT70
const DisplayConfig *config = display_config_init(DISPLAY_PROFILE_1024x600_STANDARD);

// Получение размеров виджета с автомасштабированием
uint16_t width, height;
display_config_scale_widget(400, 300, &width, &height);

// Grid система
uint16_t x, y;
display_config_grid_to_pixels(2, 3, &x, &y);  // Колонка 2, ряд 3
```

---

### 2. Система тем (ThemeManager)

**Предустановленные темы:**
- **Motec Dark** - профессиональная тёмная тема (по умолчанию)
- **AIM Sport Light** - светлая тема для яркого дня
- **Rally HC** - максимальный контраст для жёстких условий
- **Night Mode** - красная тема для ночных гонок
- **Endurance** - синяя тема с пониженной яркостью

**Пример:**

```cpp
#include "theme_manager.h"

ThemeManager theme_mgr;
theme_manager_init(&theme_mgr);

// Установка темы
theme_manager_set_preset(&theme_mgr, THEME_NIGHT_MODE);

// Авто ночной режим
theme_manager_set_auto_night_mode(&theme_mgr, true,
                                  20, 6,              // 20:00 - 06:00
                                  THEME_MOTEC_DARK,   // Дневная тема
                                  THEME_NIGHT_MODE);  // Ночная тема

// Получение активной темы
const Theme *theme = theme_manager_get_active(&theme_mgr);
Color accent = theme->accent;  // RGB{255, 67, 0}
```

---

### 3. Advanced Logger (с компрессией)

**Возможности:**
- Форматы: CSV, Binary, Compressed (zlib), Parquet
- Селективная запись каналов
- Триггерная запись (начало по условию)
- Pre-trigger buffer (запись данных ДО триггера)
- Ротация файлов

**Пример:**

```cpp
#include "advanced_logger.h"

AdvancedLogger logger;
AdvancedLogConfig config = {
    .format = LOG_FORMAT_COMPRESSED_ZLIB,
    .buffer_size_kb = 128,
    .compression_level = 6,
    .default_sample_rate_hz = 200
};

strcpy(config.output_path, "/logs/session.bin");
advanced_logger_init(&logger, &config);

// Добавление каналов
advanced_logger_add_channel(&logger, "rpm", 200.0f);
advanced_logger_add_channel(&logger, "oil_pressure", 50.0f);

// Настройка триггера (начать запись при RPM > 1000)
advanced_logger_set_trigger(&logger, TRIGGER_MODE_THRESHOLD,
                            "rpm", 1000.0f, true, 5000);  // 5 сек pre-trigger

// Запуск
advanced_logger_arm_trigger(&logger);

// Логирование
advanced_logger_log_sample(&logger, "rpm", 4500.0f, millis(), false);

// Статистика
float ratio = advanced_logger_get_compression_ratio(&logger);  // 3.5:1
float throughput = advanced_logger_get_throughput(&logger);     // 45.2 kB/s
```

---

### 4. Lap Timer (GPS-based)

**Функции:**
- Определение финиша/секторов по GPS
- Расчёт дельт к лучшему кругу
- Предсказание времени круга
- База популярных трасс
- Автоопределение трассы
- Экспорт в CSV/Video BBOX

**Пример:**

```cpp
#include "lap_timer.h"

LapTimer lap_timer;
lap_timer_init(&lap_timer);

// Загрузка трассы
lap_timer_load_track_by_name(&lap_timer, "Spa-Francorchamps");

// Или автоопределение
lap_timer.auto_detection_enabled = true;

// Обновление с GPS данными
lap_timer_update(&lap_timer, gps.location.lat(),
                              gps.location.lng(),
                              gps.speed.kmph(),
                              millis());

// Получение дельты
int32_t delta_ms = lap_timer_get_current_delta(&lap_timer);
Serial.printf("Delta: %+.2f sec\n", delta_ms / 1000.0f);

// Лучший круг
const LapRecord *best = lap_timer_get_best_lap(&lap_timer);
if (best) {
    Serial.printf("Best lap: %02d:%02d.%03d\n",
                  (best->lap_time_ms / 60000),
                  (best->lap_time_ms / 1000) % 60,
                  best->lap_time_ms % 1000);
}

// Экспорт
lap_timer_export_to_csv(&lap_timer, "/logs/laps.csv");
```

---

## Конфигурация (config.h)

### Пины STM32H7B3

```cpp
// Display (LTDC)
#define LTDC_HSYNC_PIN PE15
#define LTDC_VSYNC_PIN PE13
#define LTDC_CLK_PIN PE14
#define LTDC_DE_PIN PE12

// CAN Bus
#define CAN1_RX_PIN PA11
#define CAN1_TX_PIN PA12
#define CAN2_RX_PIN PB5
#define CAN2_TX_PIN PB13

// GPS (UART)
#define GPS_UART_RX PD2
#define GPS_UART_TX PC12

// SD Card (SDMMC)
#define SD_D0_PIN PC8
// ...
```

### Feature Flags

```cpp
#define ENABLE_ADVANCED_LOGGING 1
#define ENABLE_LAP_TIMER 1
#define ENABLE_CAN_SECURITY 1
#define ENABLE_CAMERA_MANAGER 1
#define ENABLE_OTA_UPDATES 1
```

---

## TouchGFX интеграция

### Создание виджетов

```cpp
#include "touchgfx_widgets.h"

using namespace firmware;

// Создание тахометра
auto rpm_gauge = std::make_shared<RadialGauge>(
    "rpm",          // Канал
    "RPM",          // Метка
    "×1000",        // Единицы
    0.0,            // Мин
    9000.0          // Макс
);

// Shift light
auto shift_bar = std::make_shared<LinearBar>(
    "rpm",
    "SHIFT",
    "",
    9000.0
);

// Status pill (давление масла)
auto oil_pill = std::make_shared<StatusPill>(
    "oil_pressure",
    "Oil",
    "PSI",
    30.0,           // Warning threshold
    15.0            // Critical threshold
);

// Lambda график
auto lambda_graph = std::make_shared<MixtureGraph>(
    "lambda_current",
    "lambda_target"
);

// Создание экрана
std::vector<std::shared_ptr<TouchGFXWidget>> widgets = {
    rpm_gauge,
    shift_bar,
    oil_pill,
    lambda_graph
};

TouchGFXScreen main_screen("main", "Main Screen", widgets);
TouchGFXPalette palette;  // Использует активную тему
Screen runtime_screen = main_screen.to_runtime_screen(palette);
```

---

## Тестирование

### Unit-тесты

```bash
# Запуск тестов
pio test -e native

# Конкретный тест
pio test -e native -f test_display_config
```

### Пример теста

```cpp
#include <gtest/gtest.h>
#include "display_config.h"

TEST(DisplayConfig, RVT70Resolution) {
    const DisplayConfig *cfg = display_config_init(DISPLAY_PROFILE_1024x600_STANDARD);
    EXPECT_EQ(cfg->width, 1024);
    EXPECT_EQ(cfg->height, 600);
    EXPECT_EQ(cfg->dpi, 150);
}

TEST(DisplayConfig, WidgetScaling) {
    display_config_init(DISPLAY_PROFILE_1024x600_STANDARD);
    uint16_t w, h;
    display_config_scale_widget(400, 300, &w, &h);
    EXPECT_GT(w, 0);
    EXPECT_GT(h, 0);
}
```

---

## Производительность

### Целевые показатели

- **UI частота обновления:** 60 FPS
- **CAN polling:** 200 Hz
- **ADC sampling:** 1000 Hz
- **GPS update:** 25 Hz
- **Logging rate:** 200 Hz

### Оптимизация

```cpp
// В platformio.ini
build_flags =
    -O2                      # Оптимизация
    -ffunction-sections      # Удаление неиспользуемого кода
    -fdata-sections
    -mfpu=fpv5-d16          # FPU ускорение
    -mfloat-abi=hard
```

---

## Troubleshooting

### Проблема: Не компилируется для STM32

**Решение:**
```bash
pio platform install ststm32
pio lib install
```

### Проблема: SD карта не монтируется

**Решение:**
- Проверьте пины в `config.h`
- Убедитесь что карта отформатирована в FAT32
- Проверьте питание 3.3V на SD модуле

### Проблема: GPS не получает fix

**Решение:**
- Проверьте UART baudrate (115200)
- Убедитесь что антенна подключена
- Дождитесь выхода на улицу (cold start может занять 5-10 минут)

---

## Следующие шаги

1. ✅ Адаптация UI под 1024×600
2. ✅ Система тем
3. ✅ Advanced Logger
4. ⏳ CAN Security модуль
5. ⏳ Camera Manager
6. ⏳ OTA Updates
7. ⏳ WiFi конфигуратор

---

## Ресурсы

- [PlatformIO Docs](https://docs.platformio.org/)
- [STM32H7 Reference Manual](https://www.st.com/resource/en/reference_manual/rm0433-stm32h7x2x3-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
- [TouchGFX Documentation](https://support.touchgfx.com/)
- [RVT70HSSNWN00 Datasheet](https://www.riverdi.com/product/rvt70hssnwn00)
