import json
from collections import defaultdict, Counter
import os
from datetime import datetime
import flet as ft


def parse_today_protocols():
    today = datetime.now().strftime("%Y-%m-%d")
    protocols_dir = "project/configuration/protocols"

    total_stats = defaultdict(int)
    total_records_all_files = 0
    files_processed = 0

    if not os.path.exists(protocols_dir):
        print(f"Директория {protocols_dir} не существует")
        return None

    for filename in os.listdir(protocols_dir):
        if filename.startswith("Протокол_") and filename.endswith(".json") and today in filename:
            file_path = os.path.join(protocols_dir, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                defects = data.get('defects', [])

                file_counter = Counter()
                for defect in defects:
                    defect_type = defect.get('type', 'unknown')
                    file_counter[defect_type] += 1

                for defect_type, count in file_counter.items():
                    total_stats[defect_type] += count

                file_total = len(defects)
                total_records_all_files += file_total
                files_processed += 1

                print(f"\nФайл: {filename}")
                print(f"  Всего записей: {file_total}")
                print(f"  По типам:")
                for defect_type, count in sorted(file_counter.items()):
                    print(f"    {defect_type}: {count}")

            except Exception as e:
                print(f"Ошибка при обработке файла {filename}: {e}")

    print(f"Обработано файлов: {files_processed}")
    print(f"Общее количество записей во всех файлах: {total_records_all_files}")
    print("Суммарная статистика по типам дефектов:")
    for defect_type, count in sorted(total_stats.items()):
        percentage = (count / total_records_all_files * 100) if total_records_all_files > 0 else 0
        print(f"  {defect_type}: {count} ({percentage:.1f}%)")

    return total_records_all_files, total_stats


def create_pie_chart_sections(total_records, total_stats):
    color_map = {
        'good': ft.colors.GREEN,
        'omission': ft.colors.CYAN,
        'platform': ft.colors.DEEP_PURPLE,
        'sinks': ft.colors.YELLOW_200,
        'contacts': ft.colors.DEEP_ORANGE,
        'glass': ft.colors.BLUE_200,
        'mechanics': ft.colors.PURPLE,
        'flatness': ft.colors.BROWN,
        'unknown': ft.colors.GREY
    }

    filtered_stats = {k: v for k, v in total_stats.items() if k != 'good'}
    sorted_stats = sorted(filtered_stats.items(), key=lambda x: x[1], reverse=True)

    sections = []
    total_defects = total_records - total_stats.get("good", 0)

    for defect_type, count in sorted_stats:
        if total_defects > 0:
            percentage = (count / total_defects * 100)
            color = color_map.get(defect_type, ft.colors.GREY)
            section = ft.PieChartSection(
                value=percentage,
                color=color,
                radius=96,
                title=f"{percentage:.1f}%",
                title_style=ft.TextStyle(
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                )
            )
            sections.append(section)

    return sections


def create_pie_chart_container(total_records, total_stats):
    sections = create_pie_chart_sections(total_records, total_stats)
    reason_chart = ft.PieChart(sections=sections, sections_space=1, center_space_radius=32)
    return ft.Container(width=288, height=288, content=reason_chart)


def create_statistics_layer():
    app_colors = {
        "red": "#ea1a1a",                 # Красный цвет для слайдера красного фильтра
        "light_red": "#f04242",           # Бледно-красный цвет для измерительных фигур
        "text": "#343e43",                # Текст
        "hover": "#40a8ee",               # Кнопки, на которые наведён курсор
        "green": "#2bda6a",               # Зелёный цвет для слайдера зелёного фильтра
        "active": "#1592e6",              # Заполненные области и рукояти слайдеров, нажатые кнопки
        "top_bar": "#e0e0e0",             # Верхняя полоса и контейнер для видео
        "inactive": "#cecece",            # Ненажатые кнопки, незаполненные области слайдеров
        "unclickable": "#9d9d9d",         # Недоступные сейчас кнопки
        "active_unclickable": "#3584b9",  # Выбранные, но недоступные сейчас кнопки
        "background": "#f5f5f5",          # Фон
    }

    total_records, total_stats = parse_today_protocols()

    total_schemes = ft.TextField(
        label="Корпусов проверено",
        color=app_colors["text"],
        label_style=ft.TextStyle(color=app_colors["text"]),
        keyboard_type=ft.KeyboardType.NUMBER,
        read_only=True,
        width=192,
        border_radius=16,
        value=str(total_records)
    )

    good_schemes = ft.TextField(
        label="Годных корпусов",
        color=app_colors["text"],
        label_style=ft.TextStyle(color=app_colors["text"]),
        keyboard_type=ft.KeyboardType.NUMBER,
        read_only=True,
        width=192,
        border_radius=16,
        value=str(total_stats["good"])
    )

    defective_schemes = ft.TextField(
        label="Бракованных корпусов",
        color=app_colors["text"],
        label_style=ft.TextStyle(color=app_colors["text"]),
        keyboard_type=ft.KeyboardType.NUMBER,
        read_only=True,
        width=192,
        border_radius=16,
        value=str(total_records - total_stats["good"])
    )

    upper_row = ft.Row(
        controls=[
            total_schemes,
            ft.Container(width=64),
            defective_schemes,
            ft.Container(width=64),
            good_schemes
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    reason_container = create_pie_chart_container(total_records, total_stats)

    color_legend_labels = [
        ("Стекло", ft.colors.BLUE_200),
        ("Пузыри", ft.colors.LIGHT_BLUE_900),
        ("Опущение", ft.colors.CYAN),
        ("Раковины", ft.colors.YELLOW_200),
        ("Брак сварки", ft.colors.AMBER),
        ("Гнутые/Битые", ft.colors.PINK),
        ("Незаполнение", ft.colors.ORANGE),
        ("Залив монтажки", ft.colors.DEEP_PURPLE),
        ("Неплоскостность", ft.colors.INDIGO),
        ("Разновысотность", ft.colors.BROWN),
        ("Залив контактов", ft.colors.DEEP_ORANGE),
        ("Механика ободка", ft.colors.PURPLE),
        ("Окалины/Трещины", ft.colors.GREEN_300),
        ("Утяжки/Нависание", ft.colors.GREEN_900),
        ("Непараллельность", ft.colors.RED)
    ]

    elements_per_row = 5

    color_rows = [
        ft.Row(
            controls=[
                ft.Container(
                    width=20,
                    height=20,
                    bgcolor=color,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text(label, color=app_colors["text"]),
                    width=200,
                    alignment=ft.alignment.center_left
                )
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER
        ) for label, color in color_legend_labels
    ]

    color_squares_controls = ft.Column(
        controls=[
            ft.Row(
                controls=color_rows[i:i + elements_per_row],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER
            ) for i in range(0, len(color_rows), elements_per_row)
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    color_squares_with_header = ft.Column(
        controls=[
            ft.Container(height=24),
            ft.Row(
                controls=[
                    ft.Container(width=400, height=32),
                    ft.Text(
                        "Цветовые обозначения типов брака",
                        color=app_colors["text"],
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(width=400, height=32)
                ]
            ),
            ft.Container(height=24),
            color_squares_controls
        ]
    )

    lower_row = ft.Row(
        controls=[
            reason_container,
            ft.Container(width=32),
            color_squares_with_header
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    def refresh_data(e):
        new_records, new_stats = parse_today_protocols()

        total_schemes.value = str(new_records)
        good_schemes.value = str(new_stats.get("good", 0))
        defective_schemes.value = str(new_records - new_stats.get("good", 0))
        new_sections = create_pie_chart_sections(new_records, new_stats)
        reason_container.content.sections = new_sections

        e.page.update()

    refresh_button = ft.ElevatedButton(
        text="Обновить статистику",
        icon=ft.icons.REFRESH,
        on_click=refresh_data,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.BLUE_400,
            padding=20,
        )
    )

    return ft.Tab(
        text="Статистика",
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(height=32),
                            ft.Row(
                              controls=[
                                  ft.Container(
                                      width=700,
                                      height=32
                                  ),
                                  ft.Text(
                                      "Отчёт по результатам инспекции изделий",
                                      color=app_colors["text"],
                                      size=20,
                                      weight=ft.FontWeight.BOLD,
                                      text_align=ft.TextAlign.CENTER
                                  ),
                                  ft.Container(width=700, height=32)
                              ]
                            ),
                            ft.Container(height=32),
                            upper_row,
                            ft.Container(height=32),
                            lower_row,
                            ft.Container(height=32),
                            refresh_button,
                            ft.Container(height=32)
                        ]
                    ),
                    padding=20,
                    border=ft.border.all(3),
                    border_radius=ft.border_radius.all(10),
                    width=1900,
                    margin=ft.margin.only(left=20, top=20, right=20, bottom=10),
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
    )
