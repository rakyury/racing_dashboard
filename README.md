# racing_dashboard

Проект концепта цифровой приборной панели для гоночного авто. Подробные требования, архитектура и список компонентов находятся в
 [docs/project_spec.md](docs/project_spec.md). Дорожная карта по ключевым этапам валидации и разработки описана в [docs/roadmap.md](docs/roadmap.md).

Черновой пример firmware-логики теперь написан на чистом C и разбит по небольшим модулям в директории `src/` (точка входа — [src/main.c](src/main.c)).
Он включает два демо-профиля интерфейса: TouchGFX (современный Motec-style UI) и LVGL (альтернативный стек).
Подробнее — в [docs/firmware_runtime.md](docs/firmware_runtime.md) и макетах экранов [docs/screen_previews.md](docs/screen_previews.md).
