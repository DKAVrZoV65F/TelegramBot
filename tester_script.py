# sender_script.py

import asyncio
import time
import random
import pyautogui
import keyboard
from pygetwindow import getWindowsWithTitle
from pygetwindow import getAllTitles

print("Все открытые окна:", getAllTitles())

questions = [
    "Не совсем понятно, как работает механизм версионирования записей, можете объяснить подробнее?",
    "Объясните, пожалуйста, различия между READ COMMITTED и SNAPSHOT изоляцией транзакций в вашем продукте.",
    "А есть дока по настройке полнотекстового поиска с учетом русской морфологии?",
    "Не понимаю, как правильно использовать хранимые процедуры для пакетной обработки данных.",
    "Можете объяснить, как Red Expert обрабатывает внешние ключи при импорте схемы из другой БД?",
    "А есть ли документация по API для работы с базой из Python приложений?",
    "Не понятно, как оптимизировать запросы, использующие JOIN на несколько таблиц.",
    "Объясните, в чем преимущество вашего формата хранения BLOB по сравнению со стандартным.",
    "Я что-то не понимаю, как настроить триггеры на AFTER UPDATE.",
    "А есть дока по восстановлению базы данных из бэкапа на другой машине?",
    "Не понятно, как работает система привилегий для пользователей. Можно пошаговую инструкцию?",
    "Объясните, как правильно создавать индексы для ускорения выборок по нескольким полям.",
    "Я новичок, не понимаю, с чего начать изучение вашего SQL диалекта.",
    "А есть дока по интеграции с BI-системами, например, Tableau?",
    "Не совсем понятно, как влияют настройки кэширования на производительность.",
    "Объясните, пожалуйста, как работает встроенный планировщик задач.",
    "Не понимаю, как использовать JSON функции для фильтрации данных.",
    "А есть дока по рекомендуемым параметрам конфигурации сервера для высокой нагрузки?",
    "Не понятно, как Red Expert работает с различными кодировками текста.",
    "Объясните, как настроить аудит операций DML и DDL в базе.",
    "Не могу найти, где в Red Expert настраивается таймаут соединения. Объясните?",
    "А есть ли официальный форум или сообщество, где можно задавать такие вопросы?",
    "Не понятно, как работает ваша система репликации. Есть упрощенная схема?",
    "Объясните, пожалуйста, что такое \"computed by\" поля и как их использовать.",
    "А есть дока по миграции с предыдущей версии вашей СУБД на последнюю?",
    "Не понимаю, как правильно оформлять транзакции, чтобы избежать взаимоблокировок.",
    "Можете объяснить принцип работы вашего query-оптимизатора?",
    "А есть ли примеры использования оконных функций в вашем SQL?",
    "Не понятно, как Red Expert управляет временными таблицами.",
    "Объясните, как использовать параметры в хранимых процедурах и функциях.",
    "Я запутался в типах данных для дат и времени. Есть сводная таблица?",
    "А есть дока по лучшим практикам для резервного копирования больших баз данных?",
    "Не совсем понятно, как работают генераторы (sequences) и как их сбрасывать.",
    "Объясните, как осуществляется мониторинг производительности сервера СУБД.",
    "Не понимаю, как правильно настроить права доступа на уровне отдельных столбцов.",
    "А есть дока по использованию вашей СУБД во встраиваемом режиме?",
    "Не понятно, как работают глобальные временные таблицы (GTT).",
    "Объясните, пожалуйста, как Red Expert помогает в отладке SQL-скриптов.",
    "Не могу разобраться с синтаксисом создания представлений (VIEW). Приведите пример.",
    "А есть дока по ограничениям на количество одновременных подключений?",
]
bugs = [
    "У меня не работает экспорт данных в CSV из Red Expert, если в таблице есть NULL значения.",
    "Ошибка при попытке подключения к удаленному серверу через VPN – таймаут.",
    "Кажется, это баг: после обновления драйвера ODBC приложение стало падать.",
    "Не работает автодополнение SQL кода в Red Expert для пользовательских функций.",
    "Ошибка \"Access violation\" при выполнении сложного запроса с подзапросами.",
    "Это точно баг: не сохраняются настройки соединения после перезапуска Red Expert.",
    "У меня не работает отладчик хранимых процедур, точки останова игнорируются.",
    "Ошибка при создании новой таблицы с полем типа TIMESTAMP WITH TIME ZONE.",
    "Нашел баг: Red Expert зависает при попытке открыть очень большую таблицу (>10 млн записей).",
    "Не работает импорт схемы из DDL скрипта, если там есть комментарии.",
    "Ошибка \"Constraint violation\" при вставке данных, хотя все ограничения соблюдены.",
    "Это баг или фича? Не работает изменение порядка колонок в конструкторе таблиц.",
    "У меня постоянно не работает соединение с базой после выхода из спящего режима.",
    "Ошибка при выполнении ALTER TABLE ADD COLUMN – \"table is locked\".",
    "Кажется, баг в оптимизаторе: простой запрос выполняется неоправданно долго.",
    "Не работает функция COUNT(DISTINCT ...) на полях с большим количеством NULL.",
    "Ошибка при копировании базы данных через Red Expert – процесс прерывается на середине.",
    "Нашел баг: некорректно отображаются даты в формате dd.mm.yyyy hh:mm:ss в гриде.",
    "Не работает откат транзакции (ROLLBACK) в некоторых случаях.",
    "Ошибка \"Memory allocation error\" при попытке загрузить большой BLOB в Red Expert.",
    "Не работает поиск по тексту в истории SQL-запросов в Red Expert.",
    "Ошибка \"Invalid character\" при импорте данных из Excel файла с кириллицей.",
    "Баг: Red Expert падает при попытке отредактировать значение в ячейке с очень длинным текстом.",
    "Не работает корректно сортировка по столбцу с типом VARCHAR с учетом регистра.",
    "Ошибка \"Too many open files\" при работе с большим количеством одновременных подключений.",
    "Баг: невозможно удалить пользователя, если у него есть активные сессии.",
    "Не работает функция REPLACE() в SQL, если искомая подстрока пустая.",
    "Ошибка \"Stack overflow\" при выполнении рекурсивной хранимой процедуры.",
    "Баг: Red Expert не запоминает размер и положение окон после закрытия.",
    "Не работает копирование/вставка данных между разными экземплярами Red Expert.",
    "Ошибка \"Index not found\" при попытке перестроить несуществующий индекс.",
    "Баг: при генерации DDL-скрипта для таблицы теряются комментарии к столбцам.",
    "Не работает команда COMMIT RETAIN так, как описано в документации.",
    "Ошибка при попытке создать представление, которое ссылается на другую базу данных.",
    "Баг: Red Expert некорректно обрабатывает символы новой строки в текстовых полях.",
    "Не работает автоматическое обновление статистики для таблиц.",
    "Ошибка \"Deadlock detected\" на простых UPDATE-запросах, чего не должно быть.",
    "Баг: не отображаются все доступные базы данных в дереве объектов Red Expert.",
    "Не работает фильтрация в гриде Red Expert для полей с булевым типом.",
    "Ошибка \"Invalid data type conversion\" при сравнении числового поля с текстовым.",
]
features = [
    "Очень не хватает возможности визуального построения ER-диаграмм в Red Expert.",
    "Предлагаю добавить поддержку темной темы интерфейса.",
    "Было бы здорово, если бы можно было сравнивать данные в двух таблицах, а не только схемы.",
    "Не хватает встроенного инструмента для профилирования запросов с графиками.",
    "Добавьте, пожалуйста, возможность экспорта результатов запроса напрямую в Google Sheets.",
    "Очень не хватает поддержки работы с Git для SQL скриптов прямо из Red Expert.",
    "Хотелось бы иметь возможность настраивать горячие клавиши для часто используемых действий.",
    "Не хватает функции автоматической генерации CRUD-процедур для таблиц.",
    "Предлагаю добавить интеграцию с системами мониторинга, такими как Zabbix или Prometheus.",
    "Было бы отлично, если бы Red Expert поддерживал плагины для расширения функционала.",
    "Не хватает более продвинутого редактора SQL с рефакторингом и анализом кода.",
    "Добавьте, пожалуйста, возможность работы с несколькими активными соединениями в одном окне.",
    "Очень не хватает инструмента для миграции данных между разными СУБД.",
    "Хотелось бы видеть поддержку NoSQL функций, например, для работы с графовыми данными.",
    "Не хватает возможности шифрования данных на уровне столбцов \"из коробки\".",
    "Предлагаю добавить более гибкие настройки форматирования SQL-кода.",
    "Было бы полезно иметь мастер создания сложных отчетов с возможностью экспорта в PDF.",
    "Не хватает поддержки работы с геоданными и пространственными индексами.",
    "Добавьте, пожалуйста, встроенный SSH-клиент для управления сервером.",
    "Очень не хватает функции автоматического создания тестовых данных для таблиц.",
    "Не хватает возможности сохранения часто используемых SQL-запросов в виде шаблонов.",
    "Предлагаю добавить поддержку аутентификации через LDAP или Active Directory.",
    "Было бы удобно иметь встроенный просмотрщик логов сервера СУБД в Red Expert.",
    "Не хватает функции \"умной\" подсказки таблиц и полей на основе контекста запроса.",
    "Добавьте, пожалуйста, возможность отслеживания изменений схемы базы данных.",
    "Очень не хватает поддержки командной строки для автоматизации задач в Red Expert.",
    "Хотелось бы видеть интеграцию с системами управления задачами типа Jira.",
    "Не хватает возможности визуализации плана выполнения запроса.",
    "Предлагаю добавить поддержку временных таблиц (temporal tables) для отслеживания истории изменений данных.",
    "Было бы полезно иметь инструмент для анализа зависимостей между объектами БД.",
    "Не хватает функции поиска и замены текста во всех SQL-скриптах проекта.",
    "Добавьте, пожалуйста, возможность создания пользовательских отчетов о состоянии БД.",
    "Очень не хватает поддержки работы с облачными базами данных (AWS RDS, Azure SQL и т.д.).",
    "Хотелось бы иметь возможность кастомизации панелей инструментов в Red Expert.",
    "Не хватает инструмента для проверки кода на соответствие SQL стандартам.",
    "Предлагаю добавить поддержку работы с большими объектами (LOB) через потоки.",
    "Было бы здорово иметь возможность экспорта/импорта настроек Red Expert.",
    "Не хватает функции автоматического бэкапа открытых SQL-редакторов при сбое.",
    "Добавьте, пожалуйста, поддержку написания юнит-тестов для хранимых процедур.",
    "Очень не хватает возможности совместной работы над SQL-скриптами в реальном времени.",
]
competitors = [
    "А вот в PostgreSQL есть расширение PostGIS для геоданных, у вас есть что-то похожее?",
    "MS SQL Server Management Studio позволяет управлять пользователями очень наглядно, а как у вас с этим?",
    "Слышал, что у Oracle есть мощные инструменты для секционирования таблиц, а что предлагает ваш продукт?",
    "В PostgreSQL есть JSONB, который бинарный и быстрый. Ваш JSON тип такой же эффективный?",
    "Пользовался MS SQL, там удобный SQL Server Profiler. Есть ли аналог в Red Expert?",
    "У Oracle есть Real Application Clusters (RAC), а как у вас реализована кластеризация?",
    "В PostgreSQL очень гибкая система расширений. Насколько легко расширять вашу СУБД?",
    "MS SQL предлагает Always On Availability Groups. Какие у вас решения для высокой доступности?",
    "Многие хвалят производительность Oracle на больших OLAP-запросах. Как вы с ними справляетесь?",
    "У PostgreSQL есть Foreign Data Wrappers для доступа к другим базам. У вас есть такая фича?",
    "В MS SQL удобно работать с Analysis Services. Есть ли у вас встроенные OLAP-возможности?",
    "Oracle славится своей безопасностью. Какие у вас продвинутые фичи по защите данных?",
    "А у PostgreSQL есть возможность писать хранимые процедуры на Python, у вас так можно?",
    "В MS SQL есть Linked Servers. Как у вас реализована работа с данными из других источников?",
    "Слышал, у Oracle очень развиты средства аудита. Что вы предлагаете в этой области?",
    "PostgreSQL поддерживает наследование таблиц. Это есть в вашей системе?",
    "В MS SQL есть FileTable для хранения файлов в БД. Есть ли у вас аналогичное решение?",
    "У Oracle есть функция Flashback для отката изменений. А у вас?",
    "В PostgreSQL есть Materialized Views. Как у вас с этим?",
    "Смотрел на MS SQL, у них есть Columnstore Indexes. Какие типы индексов у вас самые продвинутые?",
    "В PostgreSQL есть утилита pg_dump для логических бэкапов. Ваша утилита такая же гибкая?",
    "MS SQL имеет встроенную поддержку R и Python для анализа данных. Планируете ли вы такое?",
    "Oracle предлагает Exadata как высокопроизводительное решение. Есть ли у вас подобные аппаратные комплексы?",
    "У PostgreSQL очень активное сообщество. Насколько легко найти помощь по вашему продукту?",
    "В MS SQL есть Query Store для отслеживания истории выполнения запросов. Есть аналог?",
    "Oracle предоставляет развитые инструменты для управления ресурсами. Как это реализовано у вас?",
    "PostgreSQL позволяет создавать кастомные типы данных. Ваша СУБД это поддерживает?",
    "В MS SQL есть Change Data Capture (CDC). Как у вас отслеживаются изменения данных?",
    "Oracle имеет давнюю репутацию в корпоративном секторе. На какой рынок вы ориентируетесь?",
    "У PostgreSQL есть TimescaleDB для временных рядов. У вас есть специализированные решения?",
    "MS SQL активно интегрируется с Azure. Какие у вас планы по облачной интеграции?",
    "Oracle предлагает Data Guard для аварийного восстановления. Какие у вас DR-решения?",
    "В PostgreSQL можно использовать различные языки для написания триггеров. У вас только SQL?",
    "MS SQL имеет функцию \"Stretch Database\" для гибридного хранения. Есть ли что-то похожее?",
    "Oracle известен своей поддержкой транзакций на распределенных системах. Как у вас с этим?",
    "PostgreSQL поддерживает параллельное выполнение запросов. Насколько хорошо это работает у вас?",
    "В MS SQL есть PolyBase для запросов к внешним данным. У вас есть подобные коннекторы?",
    "Oracle предлагает GoldenGate для репликации данных. Какие у вас технологии репликации?",
    "PostgreSQL имеет различные типы индексов (GIN, GiST). Насколько богат ваш арсенал индексов?",
    "MS SQL и Oracle предлагают сертификации для специалистов. Есть ли у вас программы сертификации?",
]
irrelevant = [
    "Всем привет! Как погода в вашем городе?",
    "Кто-нибудь смотрел вчерашний футбольный матч?",
    "Подскажите хороший рецепт пиццы.",
    "Мой кот опять уронил вазу, что делать?",
    "Завтра пятница, ура! Какие планы на выходные?",
    "Продам гараж, недорого.",
    "Посоветуйте интересный сериал на вечер.",
    "Кто знает, где можно купить хорошие кроссовки для бега?",
    "Смотрите, какую смешную картинку нашел в интернете!",
    "У кого-нибудь есть скидка в DNS?",
    "Что сегодня на обед готовите?",
    "Наконец-то отпуск! Поеду на море.",
    "Какая музыка вам нравится? Поделитесь плейлистами.",
    "Сегодня международный день чего-то там, поздравляю!",
    "Кто-нибудь разбирается в ремонте стиральных машин?",
    "А вы верите в гороскопы?",
    "Приснился сегодня странный сон...",
    "Кажется, я забыл выключить утюг.",
    "Посоветуйте хорошую книгу почитать.",
    "Эх, скорее бы лето!",
    "Кто последний в очереди за кофе?",
    "Моя собака съела мои тапочки.",
    "Какие планы на Новый Год? Уже придумали?",
    "Ищу попутчиков для поездки в горы.",
    "У кого есть ненужные коробки?",
    "Посоветуйте хороший фильм в жанре фэнтези.",
    "Сегодня такой солнечный день!",
    "У меня сломался компьютер, кто поможет починить?",
    "Кто знает, где можно недорого поесть в центре?",
    "Поделитесь смешными мемами, пожалуйста.",
    "Как научиться играть на гитаре?",
    "Нашел старую монетку, сколько она может стоить?",
    "Кто-нибудь едет на конференцию по программированию на следующей неделе?",
    "Мой ребенок пошел в первый класс!",
    "Забыл дома зонт, а на улице дождь.",
    "Какие цветы подарить девушке на день рождения?",
    "Кто-нибудь пользуется новым iPhone? Как впечатления?",
    "Срочно нужен совет по выбору пылесоса.",
    "Какая ваша любимая компьютерная игра?",
    "Просто решил поздороваться со всеми!",
]

all_messages_grouped = {
    "вопросы": questions,
    "баги": bugs,
    "предложения": features,
    "конкуренты": competitors,
    "ненужные": irrelevant,
}

MIN_DELAY_SECONDS = 5
MAX_DELAY_SECONDS = 20
MESSAGES_PER_CATEGORY_TO_SEND = 40
SHUFFLE_MESSAGES_WITHIN_CATEGORY = True
SHUFFLE_CATEGORIES_ORDER = True

TG_WINDOW_TITLES = ["Telegram", "Telegram Desktop", "Телеграм", "\u200eTest Chat#2"]


def focus_telegram_window():
    for title in TG_WINDOW_TITLES:
        wins = getWindowsWithTitle(title)
        if wins:
            wins[0].activate()
            time.sleep(1)
            return True
    print("❌ Telegram не найден! Откройте Telegram Desktop и попробуйте снова.")
    return False


def calibrate_coordinates():
    print("👉 Переместите курсор в поле ввода Telegram и нажмите Ctrl+C")
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rТекущие координаты: X={x}, Y={y}", end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n✅ Координаты сохранены!")
        return (x, y)


def send_telegram_message(text: str, input_coords: tuple):
    pyautogui.click(*input_coords)
    time.sleep(0.3)

    keyboard.write(text)
    time.sleep(0.5)

    keyboard.press_and_release('enter')
    time.sleep(1)


def main():
    print("🛠 Калибровка:")
    input_coords = calibrate_coordinates()

    print("\n🔥 Начинаем отправку...")
    if not focus_telegram_window():
        return

    category_keys = list(all_messages_grouped.keys())
    if SHUFFLE_CATEGORIES_ORDER:
        random.shuffle(category_keys)

    for category_name in category_keys:
        print(f"\n--- Отправка категории: {category_name} ---")
        messages_to_send = all_messages_grouped[category_name][:]

        if SHUFFLE_MESSAGES_WITHIN_CATEGORY:
            random.shuffle(messages_to_send)

        count_to_send = min(MESSAGES_PER_CATEGORY_TO_SEND, len(messages_to_send))

        for i in range(count_to_send):
            message_text = messages_to_send[i]
            send_telegram_message(message_text, input_coords)

            delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
            print(f"Пауза: {delay:.2f} сек.")
            asyncio.sleep(delay)

            if (i + 1) % 15 == 0:
                print("Дополнительная пауза для предотвращения флуда (30 сек)...")
                asyncio.sleep(30)

    print("\n✅ Все сообщения отправлены успешно!")


if __name__ == "__main__":
    main()
