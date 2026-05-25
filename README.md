# NEXUS DEFENSE v2

## Запуск
- **Windows**: двойной клик на `LAUNCH.bat`
- **macOS / Linux**: `python3 server.py` в папке nexus_project

## Зависимости
```
pip install flask
```

## Новое в v2
- 3 режима сложности: Easy / Normal / Hard
- 20 волн вместо 10
- 8 типов врагов (Scout, Soldier, Shielder, Tank, Speedster, Ghost, Regen, Swarm, Titan, Boss)
- 6 башен (Gunner, Cannon, Laser, Sniper, Tesla, Missile)
- Tesla: цепная молния по 3-5 врагам
- Ghost: невидимые враги с пульсирующей прозрачностью
- Regen: враги с регенерацией здоровья
- Titan: мега-танк с огромным HP
- Swarm: рой быстрых слабых врагов
- Улучшенная графика: анимации, частицы, шоквейв-взрывы
- Кроссплатформенность: Windows / macOS / Linux
- Touch-поддержка для мобильных браузеров
- Фиксированный race condition с загрузкой волн

## Управление
- LMB — разместить/выбрать башню
- SPACE — начать волну
- 1-6 — выбрать тип башни
- ESC — главное меню
