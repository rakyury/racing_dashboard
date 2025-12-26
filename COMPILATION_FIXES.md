# Исправления ошибок компиляции

## Исправленные ошибки

### 1. ✅ Отсутствующий флаг `ENABLE_VOICE_ALERTS` в config.h
**Проблема**: В `main_arduino.cpp` используется `#ifdef ENABLE_VOICE_ALERTS`, но флаг не был определён в `config.h`

**Решение**: Добавлено в `include/config.h`:
```cpp
#ifndef ENABLE_VOICE_ALERTS
#define ENABLE_VOICE_ALERTS 1
#endif
```

### 2. ✅ Отсутствующий `DEBUG_SERIAL_BAUDRATE` для release режима
**Проблема**: `DEBUG_SERIAL_BAUDRATE` был определён только для DEBUG режима

**Решение**: Добавлено глобальное определение в `include/config.h`:
```cpp
#ifndef DEBUG_SERIAL_BAUDRATE
#define DEBUG_SERIAL_BAUDRATE 115200
#endif
```

### 3. ✅ Неправильная инициализация `CameraManager`
**Проблема**: В `main_arduino.cpp` вызывалась инициализация с несуществующей структурой `CameraConfig`

**Решение**: Изменено на:
```cpp
camera_manager_init(&camera_mgr);
camera_manager_set_trigger_mode(&camera_mgr, TRIGGER_MODE_MANUAL);
camera_manager_set_ignition_trigger(&camera_mgr, true, true);
```

### 4. ✅ Несоответствие имён полей в `CameraTriggerConfig`
**Проблема**: В `camera_manager.cpp` использовалось `mode` вместо `trigger_mode`

**Решение**: Исправлено на `trigger_mode` и добавлено `auto_start_on_ignition`

## Потенциальные проблемы для проверки

### 1. ⚠️ Зависимости библиотек в PlatformIO

**Файл**: `platformio.ini`

Убедитесь, что все библиотеки установлены:
```ini
lib_deps =
    lvgl/lvgl@^8.3.0
    mikalhart/TinyGPSPlus@^1.0.2
    arduino-libraries/SD
    bblanchon/ArduinoJson@^6.21.0
```

**Действие**: Запустите `pio lib install` или установите через VSCode PlatformIO

### 2. ⚠️ Arduino.h функции для STM32

**Файлы**: Все `.cpp` файлы используют `Serial.printf()` и `millis()`

**Проверка**:
- `Serial.printf()` поддерживается в STM32 Arduino Core
- `millis()` и `delay()` доступны
- `HardwareSerial` для GPS

**Действие**: Проверьте совместимость с `framework = arduino` для STM32H7

### 3. ⚠️ Отсутствующие реализации функций

**Файлы**: Некоторые функции объявлены, но не реализованы:

#### camera_manager.h
- `camera_manager_export_telemetry_overlay()` - объявлена, но не реализована
- `camera_manager_set_resolution()` - объявлена, но не реализована
- `camera_manager_set_frame_rate()` - объявлена, но не реализована

**Действие**: Добавить stub-реализации или реализовать позже

### 4. ⚠️ Недостающие включения заголовков

#### advanced_logger.cpp
Может потребоваться:
```cpp
#include <stdlib.h>  // для malloc/free
```

#### voice_alerts.cpp
Может потребоваться:
```cpp
#include <stdarg.h>  // для va_list (voice_alert_queue_formatted)
```

### 5. ⚠️ Типы данных для ARM

**Проблема**: `uint64_t` может вести себя по-разному на разных платформах

**Файлы**:
- `main_arduino.cpp` - использует `uint64_t` для `millis()`
- `advanced_logger.cpp`, `lap_timer.cpp` - используют `uint64_t`

**Проверка**: На STM32 `millis()` возвращает `unsigned long` (32-bit), а не `uint64_t`

**Решение**: Изменить на `unsigned long` или использовать явное приведение типов

### 6. ⚠️ Отсутствующие HAL/Low-level драйверы

Следующие модули требуют платформо-специфичной реализации:
- **TouchGFX** - требует настройки проекта TouchGFX Designer
- **CAN Bus** - требует инициализации STM32 CAN/CAN-FD HAL
- **SD Card** - требует SDMMC HAL конфигурации
- **GPS UART** - требует настройки UART HAL
- **WiFi** (для камеры) - требует ESP32 coprocessor или WiFi модуля

## Рекомендации по сборке

### Шаг 1: Установка PlatformIO
```bash
pip install platformio
```

### Шаг 2: Установка зависимостей
```bash
cd c:/Projects/racing_dashboard
pio lib install
```

### Шаг 3: Сборка проекта
```bash
pio run
```

### Шаг 4: Исправление ошибок компиляции

Если возникнут ошибки с типами данных:
1. Замените все `uint64_t loop_start_ms = millis()` на `unsigned long loop_start_ms = millis()`
2. Добавьте недостающие include файлы
3. Закомментируйте нереализованные функции

### Шаг 5: Загрузка на устройство
```bash
pio run --target upload
```

## Чек-лист перед сборкой

- [x] Добавлен `ENABLE_VOICE_ALERTS` в config.h
- [x] Исправлен `DEBUG_SERIAL_BAUDRATE`
- [x] Исправлена инициализация `CameraManager`
- [x] Исправлены поля `CameraTriggerConfig`
- [ ] Установлен PlatformIO
- [ ] Установлены библиотеки из `lib_deps`
- [ ] Проверены типы данных (`uint64_t` vs `unsigned long`)
- [ ] Добавлены недостающие include файлы
- [ ] Настроены HAL драйверы для STM32H7

## Файлы, которые точно компилируются

✅ **include/config.h** - исправлен
✅ **include/signal_bus.h** - простая реализация
✅ **src/signal_bus.cpp** - компилируется
✅ **include/display_config.h** - базовая структура
✅ **src/display_config.cpp** - компилируется
✅ **include/theme_manager.h** - базовая структура
✅ **src/theme_manager.cpp** - компилируется

## Файлы, требующие проверки

⚠️ **src/main_arduino.cpp** - типы данных millis()
⚠️ **src/advanced_logger.cpp** - malloc, zlib (требует библиотеку)
⚠️ **src/lap_timer.cpp** - использует math.h (M_PI)
⚠️ **src/camera_manager.cpp** - WiFi операции (stub)
⚠️ **src/voice_alerts.cpp** - TTS операции (stub), va_list

## Следующие шаги

1. Установите PlatformIO Core или используйте VSCode extension
2. Запустите `pio run` для получения точных ошибок компиляции
3. Исправьте ошибки по мере их появления
4. Добавьте недостающие HAL конфигурации для STM32H7
5. Настройте TouchGFX проект отдельно
6. Протестируйте на реальном оборудовании
