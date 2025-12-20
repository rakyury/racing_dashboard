# racing_dashboard

Проект концепта цифровой приборной панели для гоночного авто. Подробные требования, архитектура и список компонентов находятся в [docs/project_spec.md](docs/project_spec.md). Дорожная карта по ключевым этапам валидации и разработки описана в [docs/roadmap.md](docs/roadmap.md).

Черновой пример firmware-логики (условия, TouchGFX-экраны с современным UI, алерты, HDMI/CarPlay/Android Auto) разбит по файлам
в директории `src/` (точка входа — [src/main.cpp](src/main.cpp)); краткое описание и идеи расширения — в
[docs/firmware_runtime.md](docs/firmware_runtime.md).
